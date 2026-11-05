import json,os,time,sys,hashlib,importlib.metadata
from pathlib import Path
from functools import partial
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.training_worker import IsolatedTrainingAdapter
from backend.training_adapter import TrainingAdapter
from backend.training_session import TrainingSession
from backend.training import training_app
from modelaccess.contract import Settings,Request
from fastapi.testclient import TestClient
# Choose a new output directory for every invocation; prior receipts are immutable.
OUT=Path(os.environ.get('AIRFIELD_RECOVERY_OUTPUT',str(ROOT/'work/worker-recovery-new-run')))
from scripts.worker_fault_probe import FaultProbeAdapter

def main():
    if OUT.exists():raise RuntimeError('Choose a new AIRFIELD_RECOVERY_OUTPUT directory')
    OUT.mkdir(parents=True)
    factory=partial(FaultProbeAdapter,'qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=OUT/'selector.jsonl')
    model=factory().served_model
    adapter=IsolatedTrainingAdapter(factory,model,audit_path=OUT/'lifecycle.jsonl',startup_timeout=300)
    settings=Settings(model,768,image_max_side=672)
    driver=TrainingSession(17,'fog_restrictions',clock=lambda:0.)
    driver.phase='checkpoint';driver.active_probe=0;driver.source_time=60;driver.revision=2
    app=training_app(adapter,settings,driver,token='local-smoke-only',audit_path=OUT/'conversation.jsonl',review_audit_path=OUT/'typed.jsonl')
    result={'runtime':{p:importlib.metadata.version(p) for p in ('torch','transformers','fastapi')},
            'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('backend/training_worker.py','backend/training.py','backend/training_adapter.py','backend/training_assessment.py')}};headers={'Authorization':'Bearer local-smoke-only'}
    with TestClient(app) as client:
        print('initial warmup ready',flush=True)
        result['initialHealth']=client.get('/health',headers=headers).json()
        adapter.generation_timeout=.2
        fail=adapter.review(Request('forced-hang',(('user','fault injection; no model answer'),),settings))
        result['forcedFailure']={'ok':fail.ok,'error':fail.error,'text':fail.text}
        adapter.generation_timeout=55.
        result['recoveringHealth']=client.get('/health',headers=headers).json()
        deadline=time.monotonic()+300
        while adapter.status not in ('ready','failed') and time.monotonic()<deadline:time.sleep(.2)
        result['replacementHealth']=client.get('/health',headers=headers).json()
        print('replacement state',adapter.status,flush=True)
        if adapter.status!='ready':raise RuntimeError('replacement failed')
        fixture=json.loads((ROOT/'tests/fixtures/typed_practice_cases.json').read_text())
        sample=next(s for s in fixture['complete'] if s['exercise']=='fog_restrictions' and s['checkpointId']=='check-1')
        body=dict(actionId='post-recovery',runId=driver.run_id,revision=driver.revision,checkpointId='check-1',responseText=sample['responseText'])
        start=time.monotonic();response=client.post('/training/response',headers=headers,json=body)
        result['typed']={'httpStatus':response.status_code,'elapsed':time.monotonic()-start,'state':response.json()}
        print('typed',response.status_code,response.json().get('reviewStatus'),flush=True)
        from backend.training_turn import run_turn
        from backend.conversation.state import SessionState
        session=SessionState('recovery-ordinary')
        turn=dict(requestId='ordinary',turnId='ordinary',expectedRevision=0,cutoff=60,aircraftId='A1',flightInstance='TRN101',question='What restrictions apply to TRN101?')
        result['ordinary']=run_turn(session,driver.scenario,turn,adapter,settings)
        print('ordinary',result['ordinary'].get('accepted'),flush=True)
    (OUT/'smoke.json').write_text(json.dumps(result,indent=2,default=str))
    assert not result['forcedFailure']['ok'] and not result['forcedFailure']['text']
    assert result['recoveringHealth']['status']!='ready'
    assert result['replacementHealth']['status']=='ready'
    assert result['typed']['state']['phase']=='feedback'
    assert result['ordinary']['accepted']
    assert adapter.status=='closed'
if __name__=='__main__':main()
