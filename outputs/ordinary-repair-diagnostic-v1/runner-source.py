"""Fixed 12-question diagnostic, new wording/identities in four known families.

No production prompt tuning, held-out claim or historical-output replacement.
"""
import json,sys,time,hashlib,uuid
from pathlib import Path
from functools import partial
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.training_adapter import TrainingAdapter
from backend.training_worker import IsolatedTrainingAdapter
from backend.training_turn import run_turn
from backend.conversation.state import SessionState
from modelaccess.contract import Settings
from scripts.history_evaluation import new_cases,score_answer,validate_keys

TEXTS=[
 [(0,'Identify the restriction currently reported for WX410.'),(2,'For the same aircraft, explain the transition from the earlier restriction to the new escort condition, citing both reports.'),(5,'Do these ground restrictions tell us that this aircraft is ready to depart overall?')],
 [(0,'Find the assigned stand for ST204.'),(2,'For that same aircraft, name the stand immediately preceding E4. Do not switch to an aircraft currently at E4.'),(5,'Change my selection to ST305 and state its assigned stand.')],
 [(0,'What does the baggage report establish for SV708?'),(3,'For that aircraft, is there an overall readiness confirmation in the reports we have received?'),(5,'For that aircraft, contrast the earlier ready state with the most recent readiness report.')],
 [(0,'Read out the target off-block estimate for ET111.'),(4,'Actually use ET222: which off-block estimate is available?'),(5,'Keep that aircraft selected and compare its previous and updated off-block estimates.')],
]

def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
 episodes=new_cases()
 for e,(episode,spec) in enumerate(zip(episodes,TEXTS)):
  episode['cases']=[dict(episode['cases'][i],question=text) for i,text in spec]
  raw=json.dumps(episode)
  for i,a in enumerate(episode['world']['aircraft']):raw=raw.replace(a['flightInstance'],'RP'+str(800+e*10+i))
  episodes[e]=json.loads(raw);episodes[e]['world']['scenarioId']='REPAIR-'+episodes[e]['world']['scenarioId']
 validate_keys(episodes)
 files=['backend/training_adapter.py','backend/training_result.py','backend/training_worker.py','scripts/check_ordinary_repair.py','scripts/history_evaluation.py']
 (out/'lock.json').write_text(json.dumps(dict(episodes=episodes,scope='12 diagnostic paraphrases/renamed identities in known families; not independent scenario generalization',sourceHashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}),indent=2))
 factory=partial(TrainingAdapter,'qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=out/'selector.jsonl')
 adapter=IsolatedTrainingAdapter(factory,factory().served_model,audit_path=out/'worker.jsonl');settings=Settings(adapter.served_model,768,image_max_side=672)
 rows=[]
 try:
  adapter.warmup(settings)
  for ep in episodes:
   session=SessionState(uuid.uuid4().hex)
   for i,c in enumerate(ep['cases']):
    start=time.monotonic()
    result=run_turn(session,ep['world'],dict(requestId=uuid.uuid4().hex,turnId=str(i),expectedRevision=session.revision,aircraftId=None,flightInstance=None,cutoff=c['cutoff'],question=c['question']),adapter,settings)
    row=dict(episode=ep['name'],case=c,result=result,score=score_answer(result,ep['world'],c),elapsedSeconds=time.monotonic()-start);rows.append(row)
    with (out/'records.jsonl').open('a') as f:f.write(json.dumps(row,default=str)+'\n')
    print(ep['name'],i,row['score']['passed'],flush=True)
  (out/'summary.json').write_text(json.dumps(dict(completed=len(rows),passed=sum(r['score']['passed'] for r in rows),scope='diagnostic only; no prompt revision'),indent=2))
 finally:adapter.close()
if __name__=='__main__':main()
