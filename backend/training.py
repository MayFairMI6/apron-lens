"""Local controller lessons: external clock, source-backed assistant, assessment."""
import argparse
import json
import secrets
from fastapi import Header, HTTPException, Request
from starlette.responses import JSONResponse
from backend.conversation.server import create_app, ROOT, local_token
from backend.training_session import TrainingSession, ActionConflict
from backend.lessons import EXERCISES
from backend.training_environment import ENVIRONMENTS
from modelaccess.contract import Settings

def training_app(adapter, settings, driver, token=None, audit_path=None):
    scenarios={driver.scenario['scenarioId']:driver.scenario}
    app=create_app(adapter,settings,token=token,scenarios=scenarios,
                   audit_path=audit_path or ROOT/'work/training-conversations.jsonl')
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

    @app.middleware('http')
    async def gate_questions(request,call_next):
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
    p.add_argument('--exercise',choices=EXERCISES,default='surface_conflict')
    p.add_argument('--mode',choices=('lesson','continuous','demo'),default='lesson')
    p.add_argument('--environment',choices=ENVIRONMENTS,default='clear',help='Visual conditions driven by scenario time; not weather reports')
    p.add_argument('--seed',type=int,default=17);p.add_argument('--port',type=int,default=8767)
    args=p.parse_args()
    adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',training_role='controller_awareness',
                            prompt_audit_path=ROOT/'work/training-prompts.jsonl')
    adapter.load() # Preload before announcing that the service is ready.
    # Model startup must not consume exercise time before a viewer can connect.
    driver=TrainingSession(args.seed,args.exercise,args.mode,audit_path=ROOT/'work/training-sessions.jsonl',environment=args.environment)
    settings=Settings(adapter.served_model,768,image_max_side=672)
    local_token();print(f'TRAINING_READY {args.mode} {args.exercise} port={args.port}',flush=True)
    uvicorn.run(training_app(adapter,settings,driver),host='127.0.0.1',port=args.port,access_log=False)

if __name__=='__main__':main()
