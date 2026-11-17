"""Local Qwen service. No cloud calls; synthetic scene images are not persisted."""
import argparse
import asyncio
import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from backend.reasoning import ROOT, context_for, decode_image, validate_answer
from backend.evidence import expected_selection
from backend.query_parser import VERSION as PARSER_VERSION, parse
from backend.engine import VLMEngine, load_engine
from backend.models import PRIMARY_MODEL, model_names

TOKEN_PATH = ROOT / 'work/qwen-server-token.txt'
AUDIT_PATH = ROOT / 'work/qwen-requests.jsonl'


def local_token():
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    if not TOKEN_PATH.exists():
        TOKEN_PATH.write_text(secrets.token_urlsafe(32))
        TOKEN_PATH.chmod(0o600)
    return TOKEN_PATH.read_text().strip()


class ReasonRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    requestId: str = Field(min_length=1, max_length=80)
    scenarioId: str = Field(min_length=1, max_length=80)
    aircraftId: str = Field(min_length=1, max_length=20)
    checkpoint: float = Field(ge=0, le=3600)
    # Omit queryType to have the model parse `question`; give it to skip the model entirely.
    queryType: str | None = Field(default=None, pattern='^(latest|current|change)$')
    properties: list[str] = Field(default_factory=list, max_length=10)
    # Optional: typed report queries never use the image for inference.
    imageBase64: str | None = Field(default=None, min_length=1, max_length=2_800_000)
    question: str = Field(default='What does the latest received report say for this aircraft, when did it happen and arrive, and what remains unconfirmed?', min_length=1, max_length=400)


# Historical evaluation scripts load the evaluated model by this name.
LocalQwen = VLMEngine


def create_app(engine=None, token=None, model=PRIMARY_MODEL):
    @asynccontextmanager
    async def lifespan(app):
        app.state.engine = engine or await run_in_threadpool(load_engine, model)
        app.state.token = token or local_token()
        app.state.busy = asyncio.Lock()
        yield
    app = FastAPI(title='Airfield replay reasoning', lifespan=lifespan)

    def authenticate(authorization):
        if not secrets.compare_digest(authorization or '', 'Bearer ' + app.state.token):
            raise HTTPException(401, 'Connection token required')

    @app.middleware('http')
    async def bound_body(request, call_next):
        # Enforce a real body bound including requests without Content-Length.
        if request.method == 'POST':
            from starlette.responses import JSONResponse
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 3_000_000:
                    return JSONResponse({'detail': 'Request too large'}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    @app.get('/health')
    def health(authorization: Annotated[str | None, Header()] = None):
        authenticate(authorization)
        return {'status': 'ready', 'model': app.state.engine.manifest['model_id'],
                'revision': app.state.engine.manifest['revision'], 'device': app.state.engine.device}

    @app.post('/reason')
    async def reason(body: ReasonRequest, authorization: Annotated[str | None, Header()] = None):
        authenticate(authorization)
        try:
            # Reject bad identities, times and properties before any model call.
            context_for(body.scenarioId, body.aircraftId, body.checkpoint, body.queryType or 'latest', body.properties)
            image_hash = decode_image(body.imageBase64)[1] if body.imageBase64 is not None else None
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if app.state.busy.locked():
            raise HTTPException(429, 'Model is answering another request; retry shortly')
        async with app.state.busy:
            start = time.perf_counter()
            parsed = None
            if body.queryType is None:
                try:
                    parsed = await run_in_threadpool(parse, app.state.engine, body.question)
                except Exception as exc:
                    raise HTTPException(503, 'Local model failed to parse the question; inspect server log') from exc
                query_type, properties = parsed['queryType'], parsed['properties']
            else:
                query_type, properties = body.queryType, body.properties
            context = context_for(body.scenarioId, body.aircraftId, body.checkpoint, query_type, properties)
            # Code answers the query: values, temporal statuses, sources and every time comparison.
            raw = json.dumps(expected_selection(context))
            result = validate_answer(raw, context)
            result.update(requestId=body.requestId, scenarioId=body.scenarioId, aircraftId=body.aircraftId,
                          flightInstance=context['flightInstance'], checkpoint=body.checkpoint,
                          model=app.state.engine.manifest['model_id'], revision=app.state.engine.manifest['revision'],
                          elapsedSeconds=round(time.perf_counter() - start, 2),
                          inputTokens=parsed['inputTokens'] if parsed else 0, outputTokens=0,
                          queryType=query_type, properties=properties, parsedBy='model' if parsed else 'request',
                          decisionVersion=PARSER_VERSION, forwardPasses=parsed['forwardPasses'] if parsed else 0,
                          imageUsedForInference=False,
                          modelRole=('Qwen interprets the question as a query type and topics. Code answers it from '
                                     'the received reports; values, times and sources are copied, never generated.')
                                    if parsed else 'No model call: the request named the query.',
                          eligibleEvidenceIds=[e['id'] for e in context['evidence']])
            # No image bytes, authentication secrets, or raw camera frames in the audit.
            audit = dict(result, imageSha256=image_hash, question=body.question,
                         parseTrace=parsed['trace'] if parsed else None,
                         evidence=context['evidence'], recordedAt=time.time())
            AUDIT_PATH.parent.mkdir(exist_ok=True)
            with AUDIT_PATH.open('a') as stream:
                stream.write(json.dumps(audit) + '\n')
            return result
    return app


if __name__ == '__main__':
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--model', choices=model_names(), default=PRIMARY_MODEL)
    args = parser.parse_args()
    local_token()
    print(f'Local token stored in work/qwen-server-token.txt; {args.model} is loading.', flush=True)
    uvicorn.run(create_app(model=args.model), host=args.host, port=args.port, access_log=False)
