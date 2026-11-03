"""Local controller lessons: external clock, source-backed assistant, assessment."""
import argparse
import asyncio
import json
import secrets
from pathlib import Path
from starlette.concurrency import run_in_threadpool
from fastapi import Header, HTTPException, Request
from starlette.responses import JSONResponse
from backend.conversation.server import create_app, ROOT, local_token
from backend.training_session import TrainingSession, ActionConflict, ReviewBusy
from backend.training_assessment import generate_review
from backend.training_turn import run_turn as training_turn
from backend.lessons import EXERCISES
from backend.runway_scenarios import DEMONSTRATIONS
from backend.fleet_scenarios import FLEET_DEMONSTRATIONS
from backend.training_environment import ENVIRONMENTS
from modelaccess.contract import Settings

def training_app(adapter, settings, driver, token=None, audit_path=None, review_audit_path=None):
    scenarios={driver.scenario['scenarioId']:driver.scenario}
    app=create_app(adapter,settings,token=token,scenarios=scenarios,
                   audit_path=audit_path or ROOT/'work/training-conversations.jsonl',turn_handler=training_turn)
    app.state.review_timeout_seconds=60.
    app.state.assessment_tasks=set()
    review_audit_path=review_audit_path or (Path(audit_path).with_name(Path(audit_path).stem+'-assessments.jsonl') if audit_path else ROOT/'work/training-assessments.jsonl')
    def auth(value):
        if not secrets.compare_digest(value or '', 'Bearer '+app.state.token):raise HTTPException(401,'Connection token required')

    @app.get('/traffic')
    def traffic(authorization: str|None=Header(default=None)):
        auth(authorization);return driver.snapshot()
    @app.get('/training')
    def training(authorization: str|None=Header(default=None)):
        auth(authorization);return driver.state()
    @app.post('/training/action')
    async def action(request:Request,authorization: str|None=Header(default=None)):
        auth(authorization)
        try:result=driver.action(await request.json())
        except ActionConflict as exc:raise HTTPException(409,str(exc))
        except (ValueError,TypeError,AttributeError) as exc:raise HTTPException(422,str(exc))
        scenarios.clear();scenarios[driver.scenario['scenarioId']]=driver.scenario
        return result

    def record_review_event(event,context,**values):
        path=Path(review_audit_path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a') as stream:
            stream.write(json.dumps(dict(recordVersion=1,event=event,runId=context.run_id,
                revision=context.revision,checkpointId=context.checkpoint_id,actionId=context.action_id,**values))+'\n')

    async def perform_review(context):
        # This retained worker owns the inference lock, independently of the HTTP
        # request's timeout/disconnect. A timed-out MPS call cannot overlap another.
        inference=asyncio.create_task(run_in_threadpool(generate_review,adapter,settings,context,review_audit_path))
        try:
            try:
                review,error=await asyncio.shield(inference)
            except asyncio.CancelledError:
                await inference
                driver.finish_response(context,error='Review interrupted. Your response is saved; please retry.')
                raise
            if error:
                applied=driver.finish_response(context,error='The model review was unavailable or did not pass the response checks. Your response is saved; please retry.')
            else:
                applied=driver.finish_response(context,review=review)
            record_review_event('typed_review_completion',context,stateApplied=applied,modelError=error)
        except Exception:
            driver.finish_response(context,error='Review unavailable. Your response is saved; please retry.')
        finally:
            app.state.busy.release()

    @app.post('/training/response')
    async def response(request:Request,authorization: str|None=Header(default=None)):
        auth(authorization)
        try:
            raw=bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw)>16_384:raise HTTPException(413,'Response request too large')
            body=json.loads(raw)
            context,cached=driver.prepare_response(body,model_available=not app.state.busy.locked())
        except ReviewBusy as exc:raise HTTPException(429,str(exc))
        except ActionConflict as exc:raise HTTPException(409,str(exc))
        except (ValueError,TypeError,AttributeError) as exc:raise HTTPException(422,str(exc))
        if context is None:return cached
        await app.state.busy.acquire()
        task=asyncio.create_task(perform_review(context))
        app.state.assessment_tasks.add(task);task.add_done_callback(app.state.assessment_tasks.discard)
        try:
            await asyncio.wait_for(asyncio.shield(task),timeout=app.state.review_timeout_seconds)
        except asyncio.TimeoutError:
            applied=driver.finish_response(context,error='The review took too long. Your response is saved. Wait for the model to finish, then retry.')
            record_review_event('typed_review_timeout',context,stateApplied=applied,workerStillRunning=not task.done())
        return driver.state()

    @app.middleware('http')
    async def gate_questions(request,call_next):
        if request.url.path=='/training/response' and request.method=='POST':
            # Runs outside the conversation middleware's larger image-body cap,
            # so chunked typed input is stopped before buffering/parsing images.
            try:auth(request.headers.get('authorization'))
            except HTTPException as exc:return JSONResponse({'detail':exc.detail},status_code=exc.status_code)
            raw=bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw)>16_384:return JSONResponse({'detail':'Response request too large'},status_code=413)
            request._body=bytes(raw)
            return await call_next(request)
        if request.url.path!='/conversation' or request.method!='POST':return await call_next(request)
        try:
            auth(request.headers.get('authorization'))
            # Bound before parsing, including chunked requests; do not bypass the
            # conversation service's body limit in this outer middleware.
            raw=bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw)>3_000_000:return JSONResponse({'detail':'Request too large'},status_code=413)
            request._body=bytes(raw);body=json.loads(raw)
            context=driver.begin_question(body)
        except HTTPException as exc:return JSONResponse({'detail':exc.detail},status_code=exc.status_code)
        except ActionConflict as exc:return JSONResponse({'detail':str(exc)},status_code=409)
        except (ValueError,TypeError,AttributeError):return JSONResponse({'detail':'Invalid training request'},status_code=422)
        response=None
        try:
            response=await call_next(request)
        finally:
            current=driver.end_question(body,context,response is not None and response.status_code==200)
        if not current:return JSONResponse({'detail':'Exercise phase changed; ask again'},status_code=409)
        return response
    return app

def main():
    import uvicorn
    from backend.training_adapter import TrainingAdapter
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exercise',choices=EXERCISES+DEMONSTRATIONS+FLEET_DEMONSTRATIONS,default='surface_conflict')
    p.add_argument('--mode',choices=('lesson','continuous','demo'),default='lesson')
    p.add_argument('--environment',choices=ENVIRONMENTS,default=None,help='Visual conditions only; defaults to clear except fog cases, which use their own fog timeline. The fog practice lesson rejects conflicting conditions.')
    p.add_argument('--seed',type=int,default=17);p.add_argument('--port',type=int,default=8767)
    args=p.parse_args()
    if args.exercise in DEMONSTRATIONS+FLEET_DEMONSTRATIONS and args.mode=='lesson':
        p.error('Incident cases require --mode demo or --mode continuous; choose one of the four practice lessons for lesson mode.')
    if args.exercise=='fog_restrictions':
        if args.mode!='lesson':p.error('fog_restrictions is a short practice lesson (210 source seconds); use --mode lesson, or choose fog_visibility for a one-hour demonstration.')
        if args.environment not in (None,'fog'):p.error('fog_restrictions requires its fog timeline; omit --environment or use fog.')
    adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',training_role='controller_awareness',
                            prompt_audit_path=ROOT/'work/training-prompts.jsonl')
    adapter.load() # Preload before announcing that the service is ready.
    # Model startup must not consume exercise time before a viewer can connect.
    driver=TrainingSession(args.seed,args.exercise,args.mode,audit_path=ROOT/'work/training-sessions.jsonl',environment=args.environment)
    settings=Settings(adapter.served_model,768,image_max_side=672)
    local_token();print(f'TRAINING_READY {args.mode} {args.exercise} port={args.port}',flush=True)
    uvicorn.run(training_app(adapter,settings,driver),host='127.0.0.1',port=args.port,access_log=False)

if __name__=='__main__':main()
