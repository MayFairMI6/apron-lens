"""Local controller replay service: read-only review of one synthetic incident.

Separate from the lesson service (backend/training.py), whose clock, typed checks
and acceptance flow are unchanged. Shares the local bearer token.
"""
import argparse
import asyncio
import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from backend.conversation.server import ROOT, local_token
from backend.replay_session import LEAD_CASE, REPLAY_CASES, ReplayConflict, ReplaySession
from modelaccess.contract import Settings

MAX_BODY = 16_384


def replay_app(adapter, settings, replay, token=None, audit_path=None, turn_handler=None):
    audit_path = Path(audit_path or ROOT / 'work/replay-questions.jsonl')

    @asynccontextmanager
    async def lifespan(app):
        app.state.token = token or local_token()
        app.state.busy = asyncio.Lock()
        if adapter is not None and callable(getattr(adapter, 'warmup', None)):
            await run_in_threadpool(adapter.warmup, settings)
        try:
            print('REPLAY_READY', flush=True)
            yield
        finally:
            if adapter is not None and callable(getattr(adapter, 'close', None)):
                await run_in_threadpool(adapter.close)
    app = FastAPI(title='AirfieldLens controller replay', lifespan=lifespan)

    @app.middleware('http')
    async def guard(request, call_next):
        if not secrets.compare_digest(request.headers.get('authorization') or '', 'Bearer ' + app.state.token):
            return JSONResponse({'detail': 'Connection token required'}, status_code=401)
        if request.method == 'POST':
            raw = bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > MAX_BODY:
                    return JSONResponse({'detail': 'Request too large'}, status_code=413)
            request._body = bytes(raw)
        return await call_next(request)

    async def body_of(request):
        try:
            return json.loads(await request.body())
        except ValueError as exc:
            raise HTTPException(422, 'Invalid replay request') from exc

    def run(function, *args):
        try:
            return function(*args)
        except ReplayConflict as exc:
            raise HTTPException(409, str(exc)) from exc
        except (ValueError, TypeError, AttributeError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get('/health')
    def health():
        return dict(status=getattr(adapter, 'status', 'ready'), provider=getattr(adapter, 'provider', 'none'),
                    model=settings.model if adapter is not None else 'none', assistant=adapter is not None,
                    exercise=replay.exercise, runId=replay.run_id, scenarioHash=replay.scenario_hash, readOnly=True)

    @app.get('/replay')
    def view():
        return replay.view()

    @app.get('/traffic')
    def traffic():
        return replay.snapshot()

    @app.post('/replay/action')
    async def action(request: Request):
        return run(replay.action, await body_of(request))

    @app.post('/replay/observation')
    async def observation(request: Request):
        return run(replay.observe, await body_of(request))

    @app.post('/replay/question')
    async def question(request: Request):
        body = await body_of(request)
        if adapter is None:  # started with --no-model: the replay works, the assistant does not
            raise HTTPException(503, 'The assistant is not loaded in this replay')
        if app.state.busy.locked():
            # A stored answer is still returned; new work waits for the model.
            if isinstance(body, dict) and replay.has_answer(body.get('requestId')):
                return run(replay.begin_question, body)[1]
            raise HTTPException(429, 'The assistant is answering another question; retry shortly')
        async with app.state.busy:
            started = time.time()
            try:
                result = await run_in_threadpool(replay.ask, body, adapter, settings, turn_handler)
            except ReplayConflict as exc:
                raise HTTPException(409, str(exc)) from exc
            except (ValueError, TypeError, AttributeError) as exc:
                raise HTTPException(422, str(exc)) from exc
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open('a') as stream:
                stream.write(json.dumps(dict(result, question=body.get('question'), exercise=replay.exercise,
                                             scenarioHash=replay.scenario_hash, recordedAt=started), default=str) + '\n')
            return result
    return app


def main():
    import uvicorn
    from functools import partial
    from backend.training_adapter import TrainingAdapter
    from backend.training_worker import IsolatedTrainingAdapter
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exercise', choices=REPLAY_CASES, default=LEAD_CASE)
    p.add_argument('--seed', type=int, default=17)
    p.add_argument('--port', type=int, default=8768)
    p.add_argument('--no-model', action='store_true',
                   help='Serve the replay without loading the assistant; questions return 503.')
    args = p.parse_args()
    if args.no_model:
        replay = ReplaySession(args.seed, args.exercise, audit_path=ROOT / 'work/replay-sessions.jsonl')
        local_token()
        print(f'REPLAY_STARTING {args.exercise} port={args.port} (no model)', flush=True)
        uvicorn.run(replay_app(None, None, replay), host='127.0.0.1', port=args.port, access_log=False)
        return
    factory = partial(TrainingAdapter, 'qwen3.5-9b', profile='apronlens-v2-mps',
                      training_role='controller_awareness', prompt_audit_path=ROOT / 'work/replay-prompts.jsonl')
    adapter = IsolatedTrainingAdapter(factory, factory().served_model, audit_path=ROOT / 'work/replay-worker.jsonl')
    replay = ReplaySession(args.seed, args.exercise, audit_path=ROOT / 'work/replay-sessions.jsonl')
    settings = Settings(adapter.served_model, 768, image_max_side=672)
    local_token()
    print(f'REPLAY_STARTING {args.exercise} port={args.port}', flush=True)
    uvicorn.run(replay_app(adapter, settings, replay), host='127.0.0.1', port=args.port, access_log=False)


if __name__ == '__main__':
    main()
