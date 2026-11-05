"""Six exposed development probes; never a held-out comparison or deployment gate."""
import json,sys,hashlib,time
from pathlib import Path
from functools import partial
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.training_adapter import TrainingAdapter
from backend.training_worker import IsolatedTrainingAdapter
from backend.training_session import TrainingSession
from modelaccess.contract import Request,Settings
from experiments.typed_claim_review.candidate import prompt_for,expand_review,VERSION

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    fixtures=json.loads((ROOT/'tests/fixtures/typed_practice_cases.json').read_text())
    cases=[fixtures['complete'][3],fixtures['complete'][6],fixtures['fog_variations'][0],fixtures['arrival_variations'][0],fixtures['fog_variations'][2],fixtures['fog_variations'][4]]
    if len(sys.argv)>2:
        texts=json.loads(Path(sys.argv[2]).read_text())
        cases=[dict(c,responseText=t) for c,t in zip(cases,texts)]
        assert len(cases)==6
    source=ROOT/'experiments/typed_claim_review/candidate.py'
    (out/'lock.json').write_text(json.dumps(dict(version=VERSION,sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),cases=cases,policy='Exposed development only. No tuning against fresh evaluation. Stop and review any failure before proceeding.'),indent=2))
    factory=partial(TrainingAdapter,'qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=out/'selector.jsonl')
    adapter=IsolatedTrainingAdapter(factory,factory().served_model,audit_path=out/'worker.jsonl')
    settings=Settings(adapter.served_model,900,image_max_side=672)
    try:
        adapter.warmup(settings)
        for i,c in enumerate(cases):
            s=TrainingSession(17,c['exercise'],clock=lambda:0.);index=int(c['checkpointId'][-1])-1
            s.phase='checkpoint';s.active_probe=index;s.source_time=s.probes[index]['at'];s.revision=2
            context,_=s.prepare_response(dict(actionId=str(i),runId=s.run_id,revision=2,checkpointId=c['checkpointId'],responseText=c['responseText']))
            payload=json.loads(context.payload_json);prompt=prompt_for(payload)
            result=adapter.review(Request('claim-dev-'+str(i),(('user',prompt),),settings))
            review=None;error=None
            try:
                if not result.ok:raise ValueError(result.error)
                review=expand_review(result.text,payload)
            except Exception as exc:error=str(exc)
            expected=c.get('expectedStatuses',{x['id']:'met' for x in payload['criteria']})
            actual={} if review is None else {x['criterionId']:x['status'] for x in review['points']}
            row=dict(index=i,payload=payload,prompt=prompt,result=asdict(result),review=review,error=error,expected=expected,actual=actual,exact=expected==actual)
            with (out/'records.jsonl').open('a') as f:f.write(json.dumps(row,default=str)+'\n')
            print(i,'exact',row['exact'],'error',error,flush=True)
            if adapter.status!='ready':
                limit=time.monotonic()+300
                while adapter.status=='starting' or adapter.status=='recovering':
                    if time.monotonic()>limit:raise RuntimeError('Recovery did not finish')
                    time.sleep(.2)
    finally:adapter.close()
if __name__=='__main__':main()
