"""Conversational service: POST /conversation (development path).

Separate from the frozen /reason server (backend/server.py), which is not
modified. It shares that server's bearer token so the app keeps one secret.
Sessions live in memory, each bound to the scenario and mode it started with;
restarting the service starts new sessions. Images
are used for inference and hashed for the audit; their bytes are never stored.
Before binding, check_bind refuses a non-loopback address whenever the adapter
can spend money (any provider other than the local backbone or the mock).
"""
import argparse
import asyncio
import base64
import hashlib
import io
import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.concurrency import run_in_threadpool

from modelaccess.contract import Settings
from backend.conversation.guards import check_bind
from backend.conversation.state import (DEVELOPMENT, DuplicateRequestConflict, SeekBackwardInFormalRun,
                                        SessionState, StaleRevision)
from backend.conversation.turns import PROMPT_VERSION, run_turn
from backend.conversation.validate import VALIDATOR_VERSION

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / 'unity/SurfaceSafetyCoach/Assets/Resources'
TOKEN_PATH = ROOT / 'work/qwen-server-token.txt'  # shared with the /reason server
AUDIT_PATH = ROOT / 'work/conversation-requests.jsonl'
LOCAL_PROVIDERS = ('local-backbone', 'mock')
MAX_BODY = 3_000_000


def local_token():
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    if not TOKEN_PATH.exists():
        TOKEN_PATH.write_text(secrets.token_urlsafe(32))
        TOKEN_PATH.chmod(0o600)
    return TOKEN_PATH.read_text().strip()


def load_scenarios(directory=SCENARIO_DIR):
    """scenarioId -> scenario data, for every scenario resource the app can load."""
    scenarios = {}
    for path in sorted(Path(directory).glob('*.json')):
        data = json.loads(path.read_text())
        if 'scenarioId' in data and 'events' in data:
            scenarios[data['scenarioId']] = data
    return scenarios


def decode_image(value):
    """Return (bytes, media type, sha256) for a PNG or JPEG of bounded size."""
    from PIL import Image
    try:
        raw = base64.b64decode(value, validate=True)
        image = Image.open(io.BytesIO(raw))
        if image.format not in ('PNG', 'JPEG') or image.width * image.height > 2_000_000:
            raise ValueError
        image.load()
    except Exception as exc:
        raise ValueError('Invalid or oversized scene image') from exc
    return raw, 'image/png' if image.format == 'PNG' else 'image/jpeg', hashlib.sha256(raw).hexdigest()


class ConversationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    requestId: str = Field(min_length=1, max_length=80)
    turnId: str = Field(min_length=1, max_length=80)
    sessionId: str = Field(min_length=1, max_length=80)
    mode: str = Field(default=DEVELOPMENT, pattern='^(development|formal)$')
    scenarioId: str = Field(min_length=1, max_length=80)
    # Both absent (or "" from Unity) for the text-only condition: nothing selected.
    aircraftId: str | None = Field(default=None, min_length=1, max_length=20)
    flightInstance: str | None = Field(default=None, min_length=1, max_length=40)
    checkpoint: float = Field(ge=0, le=3600)
    expectedRevision: int = Field(ge=0)
    question: str = Field(min_length=1, max_length=400)
    imageBase64: str | None = Field(default=None, min_length=1, max_length=2_800_000)
    imageCaptureTime: float | None = Field(default=None, ge=0, le=3600)
    tapViewport: list[float] | None = Field(default=None, min_length=2, max_length=2)
    lastSeen: float | None = Field(default=None, le=3600)  # tracking interruption; Unity sends -1 for none
    backInView: float | None = Field(default=None, le=3600)  # when tracking returned; -1 for none
    # The app's tracking losses as [start, end, start, end, ...] (JsonUtility can't write nested arrays); [] for none.
    awayIntervals: list[float] | None = Field(default=None, max_length=40)  # StandReplay.MaxAwayIntervals = 20 pairs

    # Unity's JsonUtility cannot omit a field: an unset string is written as "" and an
    # unset array as []. Both mean "not provided".
    @field_validator('imageBase64', 'tapViewport', 'aircraftId', 'flightInstance', 'awayIntervals', mode='before')
    @classmethod
    def unset_is_none(cls, value):
        return None if value in ('', []) else value

    @model_validator(mode='after')
    def selection_is_a_pair(self):
        if (self.aircraftId is None) != (self.flightInstance is None):
            raise ValueError('aircraftId and flightInstance are given together, or both left out (text-only)')
        return self

    @field_validator('lastSeen', 'backInView', mode='before')
    @classmethod
    def negative_is_none(cls, value):
        return None if isinstance(value, (int, float)) and value < 0 else value

    @field_validator('imageCaptureTime', mode='before')
    @classmethod
    def no_time_without_image(cls, value, info):
        return None if info.data.get('imageBase64') is None else value


def create_app(adapter, settings, token=None, scenarios=None, audit_path=AUDIT_PATH):
    @asynccontextmanager
    async def lifespan(app):
        app.state.token = token or local_token()
        app.state.scenarios = load_scenarios() if scenarios is None else scenarios
        app.state.sessions = {}
        app.state.busy = asyncio.Lock()
        yield
    app = FastAPI(title='ApronLens conversation', lifespan=lifespan)

    # A route dependency, so the token is checked before the body is validated.
    def authenticate(authorization: Annotated[str | None, Header()] = None):
        if not secrets.compare_digest(authorization or '', 'Bearer ' + app.state.token):
            raise HTTPException(401, 'Connection token required')

    @app.middleware('http')
    async def bound_body(request, call_next):
        if request.method == 'POST':
            from starlette.responses import JSONResponse
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > MAX_BODY:
                    return JSONResponse({'detail': 'Request too large'}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    @app.get('/health', dependencies=[Depends(authenticate)])
    def health():
        return {'status': 'ready', 'provider': adapter.provider, 'model': settings.model,
                'promptVersion': PROMPT_VERSION, 'validatorVersion': VALIDATOR_VERSION,
                'scenarios': sorted(app.state.scenarios)}

    @app.post('/conversation', dependencies=[Depends(authenticate)])
    async def conversation(body: ConversationRequest):
        data = app.state.scenarios.get(body.scenarioId)
        if data is None:
            raise HTTPException(422, 'Unknown scenario')
        # A session belongs to the scenario and mode it started with: scenarios reuse
        # aircraft and flight IDs, so memory and stored results must not carry across.
        scenario_id, session = app.state.sessions.setdefault(
            body.sessionId, (body.scenarioId, SessionState(body.sessionId, body.mode)))
        if scenario_id != body.scenarioId:
            raise HTTPException(409, 'Session belongs to another scenario; start a new session')
        if session.mode != body.mode:
            raise HTTPException(409, 'Session mode cannot change; start a new session')
        turn = dict(requestId=body.requestId, turnId=body.turnId, expectedRevision=body.expectedRevision,
                    aircraftId=body.aircraftId, flightInstance=body.flightInstance, cutoff=body.checkpoint,
                    question=body.question, tap=body.tapViewport, lastSeen=body.lastSeen,
                    backInView=body.backInView, awayIntervals=body.awayIntervals)
        image_hash = None
        if body.imageBase64 is not None:
            try:
                turn['image'], turn['imageMediaType'], image_hash = decode_image(body.imageBase64)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            turn['imageCaptureTime'] = body.imageCaptureTime
        if app.state.busy.locked():
            raise HTTPException(429, 'Model is answering another request; retry shortly')
        async with app.state.busy:
            try:
                served = await run_in_threadpool(run_turn, session, data, turn, adapter, settings)
            except (StaleRevision, SeekBackwardInFormalRun, DuplicateRequestConflict) as exc:
                raise HTTPException(409, str(exc)) from exc
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
        result = {k: v for k, v in served.items() if k not in ('prompt', 'rawModelOutput')}
        if 'prompt' in served:  # first serving of this request ID; retries are not re-audited
            audit = dict(result, scenarioId=body.scenarioId, question=body.question, imageSha256=image_hash,
                         prompt=served['prompt'], rawModelOutput=served['rawModelOutput'], recordedAt=time.time())
            Path(audit_path).parent.mkdir(exist_ok=True)
            with Path(audit_path).open('a') as stream:
                stream.write(json.dumps(audit, default=str) + '\n')
        return result
    return app


if __name__ == '__main__':
    import uvicorn
    from modelaccess.local_backbone import LocalBackboneAdapter
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--model', default='qwen2.5-vl-3b')
    parser.add_argument('--profile', required=True, help='Runtime profile from backbone/models.json, e.g. apronlens-v2-mps')
    parser.add_argument('--max-output-tokens', type=int, default=512)
    parser.add_argument('--image-max-side', type=int, default=672)
    args = parser.parse_args()
    adapter = LocalBackboneAdapter(args.model, profile=args.profile)
    check_bind(args.host, hosted_enabled=adapter.provider not in LOCAL_PROVIDERS)
    settings = Settings(model=adapter.served_model, max_output_tokens=args.max_output_tokens,
                        image_max_side=args.image_max_side)
    local_token()
    print(f'Local token in {TOKEN_PATH.relative_to(ROOT)}; serving {adapter.served_model} on /conversation.', flush=True)
    uvicorn.run(create_app(adapter, settings), host=args.host, port=args.port, access_log=False)
