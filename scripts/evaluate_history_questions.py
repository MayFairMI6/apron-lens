"""New authored report families scored with frozen question-specific temporal scope."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from backend.training_adapter_v5 import TrainingAdapter as V5
from backend.training_adapter_v6 import TrainingAdapter as V6
from backend.training_turn import run_turn
from backend.conversation.state import SessionState
from modelaccess.contract import Settings
from scripts.history_evaluation import SCORER_VERSION,new_cases,validate_keys,score_answer

VERSION='varied-history-evaluation-v1'

def diagnostic_old_answers():
    from scripts.evaluate_prompt_revision import make_world
    path=Path('outputs/prompt-revision/v6-run.json');old=json.loads(path.read_text())
    w=make_world('explicit_readiness',29)
    key=dict(aircraftId='A2',flight='TRN102',cutoff=220,mode='change',
        required=['EVAL_READY:overall_readiness','EVAL_NOT_READY:overall_readiness'],
        allowed=['EVAL_READY:overall_readiness','EVAL_NOT_READY:overall_readiness'],unknowns=[])
    rows=[]
    for r in old['records']:
        if r['phase']=='fresh' and r['exercise']=='explicit_readiness' and r['turn']==3:
            rows.append(dict(version=r['version'],requestId=r['result']['requestId'],originalScore=r['score'],
                diagnosticScore=score_answer(r['result'],w,key),key=key))
    return dict(kind='Post-hoc diagnostic only; no model rerun and no replacement of original scores or promotion gate.',
        originalFile=str(path),originalSha256=hashlib.sha256(path.read_bytes()).hexdigest(),records=rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--validate-only',action='store_true');a=p.parse_args()
    episodes=new_cases();validate_keys(episodes)
    if a.validate_only:print('24 questions: fixed modes/required/allowed evidence validated');return
    if a.output.exists() or a.output.with_suffix('.lock.json').exists():raise SystemExit('Refusing overwrite')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    files=['scripts/history_evaluation.py','scripts/evaluate_history_questions.py','backend/training_adapter_v5.py','backend/training_adapter_v6.py','backend/training_turn.py']
    originals=subprocess.check_output(['git','ls-tree','-r','--name-only','70948a7','outputs/assistant-comparison','outputs/prompt-revision'],text=True).splitlines()
    original_hashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in originals}
    for f,h in original_hashes.items():assert hashlib.sha256(subprocess.check_output(['git','show','70948a7:'+f])).hexdigest()==h
    lock=dict(version=VERSION,scorerVersion=SCORER_VERSION,episodes=episodes,
        sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        sourceHashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},originalResultHashes=original_hashes,
        design='4 authored report families, 24 dependent turns each version; no prompt edits, no promotion rule; no images/selection; identical receipt cutoffs and separate sessions.',
        limits='Authored development evaluation; fixed version order; no operational/learner validation; offline deadlines; stop reason inferred by unchanged adapter.')
    a.output.with_suffix('.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    a.output.with_name('old-answer-diagnostic.json').write_text(json.dumps(diagnostic_old_answers(),indent=2)+'\n')
    v5=V5('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=a.output.with_suffix('.v5.prompts.jsonl'));v5.load()
    v6=V6('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=a.output.with_suffix('.v6.prompts.jsonl'));v6._engine=v5._engine
    settings=Settings(v5.served_model,768,image_max_side=672)
    report=dict(version=VERSION,scorerVersion=SCORER_VERSION,lockSha256=hashlib.sha256(a.output.with_suffix('.lock.json').read_bytes()).hexdigest(),
        runtime=v5.run_metadata(),records=[],completed=False)
    for version,adapter in [('v5',v5),('v6',v6)]:
        for ep in episodes:
            session=SessionState(uuid.uuid4().hex)
            for index,case in enumerate(ep['cases']):
                result=run_turn(session,ep['world'],dict(requestId=uuid.uuid4().hex,turnId=str(index),expectedRevision=session.revision,
                    aircraftId=None,flightInstance=None,cutoff=case['cutoff'],question=case['question']),adapter,settings)
                row=dict(version=version,episode=ep['name'],turn=index,case=case,result=result,score=score_answer(result,ep['world'],case))
                report['records'].append(row);a.output.write_text(json.dumps(report,indent=2)+'\n')
                print(json.dumps(dict(version=version,episode=ep['name'],turn=index,mode=case['mode'],passed=row['score']['passed'],latency=result['latencySeconds'])),flush=True)
    report['completed']=True
    report['summary']={v:dict(passed=sum(r['score']['passed'] for r in report['records'] if r['version']==v),total=24) for v in ('v5','v6')}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']),flush=True)

if __name__=='__main__':main()
