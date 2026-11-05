"""Replay saved model selections through the refined runtime guard; not new inference."""
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from backend.training_adapter import TrainingAdapter
from backend.training_turn import run_turn
from backend.conversation.state import SessionState
from modelaccess.contract import Settings,ProviderReply,FinishReason,Usage
from modelaccess.local_backbone import LocalBackboneAdapter

root=Path('outputs/assistant-reliability')
def main():
 run=json.loads((root/'run-v2.json').read_text());lock=json.loads((root/'lock-v2.json').read_text())
 assert len([r for r in run['records'] if r['version']=='v8'])==48
 audits=[json.loads(x) for x in (root/'v8-prompts.jsonl').read_text().splitlines()]
 byrequest={}
 for a in audits:byrequest.setdefault(a['requestId'],[]).append(a)
 rows=[]
 with tempfile.TemporaryDirectory() as d:
  adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=Path(d)/'audit')
  settings=Settings(adapter.served_model,768,image_max_side=672)
  for phase,key in [('regression','regressions'),('fresh','fresh')]:
   for ep in lock[key]:
    session=SessionState('replay-'+phase+'-'+ep['name'])
    records=[r for r in run['records'] if r['version']=='v8' and r['phase']==phase and r['episode']==ep['name']]
    for row in records:
     original=row['result'];calls=iter(byrequest[original['requestId']]);used=[]
     def generated(owner,request,effective):
      a=next(calls);used.append(a)
      return ProviderReply(a['rawSelectorOutput'],a['returnedModel'],a['finishReason'],FinishReason(a['finishReason']),Usage(**a['usage']))
     c=row['case']
     with patch.object(LocalBackboneAdapter,'_generate',generated):
      result=run_turn(session,ep['world'],dict(requestId=original['requestId'],turnId=str(row['turn']),expectedRevision=session.revision,aircraftId=None,flightInstance=None,cutoff=c['cutoff'],question=c['question']),adapter,settings)
     keys=['accepted','errors','referent','rawModelOutput','inputTokens','outputTokens','trainingAttemptCount']
     same=all(result[k]==original[k] for k in keys) and len(used)==len(byrequest[original['requestId']])
     rows.append(dict(phase=phase,episode=ep['name'],turn=row['turn'],matched=same))
 report=dict(kind='Saved-output replay; no new model calls',total=len(rows),allMatched=all(r['matched'] for r in rows),rows=rows)
 (root/'final-guard-replay.json').write_text(json.dumps(report,indent=2)+'\n');assert report['allMatched'];print('All',len(rows),'saved turns match under refined guard')
if __name__=='__main__':main()
