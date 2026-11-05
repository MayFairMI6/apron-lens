"""Fixed six exposed NLI development cases. No production integration."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.typed_relation_review.candidate import (
    VERSION,MODEL_ID,MODEL_REVISION,THRESHOLD,LABELS,DEADLINE_SECONDS,NLIEngine,evaluate)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--model-dir',default=MODEL_ID)
    parser.add_argument('--batch-size',type=int,default=8)
    parser.add_argument('--case-source',type=Path,default=ROOT/'outputs/compact-review-development-v2/records.jsonl')
    args=parser.parse_args()
    if args.batch_size<1: parser.error('batch size must be positive')
    source=args.case_source.resolve()
    if source.suffix=='.json':
        document=json.loads(source.read_text());cases=document['cases'] if isinstance(document,dict) else document
    else:cases=[json.loads(line) for line in source.read_text().splitlines()]
    if not cases:raise ValueError('no cases')
    for index,case in enumerate(cases):
        if 'payload' not in case:raise ValueError('each case requires frozen payload')
        case.setdefault('index',index)
        if 'expected' not in case:case['expected']=case['expectedStatuses']
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    files=[ROOT/'experiments/typed_relation_review/candidate.py',ROOT/'experiments/typed_relation_review/propositions.py',
           Path(__file__).resolve(),ROOT/'backend/training_assessment.py']
    freeze=out/'source';freeze.mkdir()
    hashes={}
    for path in files:
        relative=path.relative_to(ROOT);hashes[str(relative)]=hashlib.sha256(path.read_bytes()).hexdigest()
        dest=freeze/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    lock=dict(version=VERSION,modelId=MODEL_ID,modelRevision=MODEL_REVISION,device='cpu',
        sourceHashes=hashes,caseSource=str(source.relative_to(ROOT)),
        caseSourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),threshold=THRESHOLD,
        labels=LABELS,batchSize=args.batch_size,deadlineSeconds=DEADLINE_SECONDS,
        policy='Exposed development only. Each source is frozen before calls. No tuning against fresh pilot; no retries or weight training. Threshold is uncalibrated.',
        createdAt=time.time())
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    started=time.monotonic()
    try:
        engine=NLIEngine(args.model_dir,batch_size=args.batch_size)
    except Exception as exc:
        (out/'startup.json').write_text(json.dumps(dict(ok=False,error=type(exc).__name__+': '+str(exc),elapsedSeconds=time.monotonic()-started))+'\n')
        raise
    (out/'startup.json').write_text(json.dumps(dict(ok=True,elapsedSeconds=time.monotonic()-started,maxInputTokens=engine.max_length,torchVersion=engine.torch.__version__,threads=engine.torch.get_num_threads()))+'\n')
    summary=[]
    for case in cases:
        payload=case['payload'];engine.records=[];engine.planned_pairs=[];engine.semantic_rule_audit=[]
        started=time.monotonic();review=None;error=None
        try:
            review=evaluate(payload,engine,started+DEADLINE_SECONDS)
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
        actual={} if review is None else {p['criterionId']:p['status'] for p in review['points']}
        row=dict(index=case['index'],payload=payload,expected=case['expected'],actual=actual,
            exact=actual==case['expected'],review=review,error=error,elapsedSeconds=time.monotonic()-started,
            plannedPairs=engine.planned_pairs,pairs=engine.records,semanticRuleAudit=engine.semantic_rule_audit)
        with (out/'records.jsonl').open('a') as stream:
            stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        print(row['index'],'exact',row['exact'],'error',error,'seconds',round(row['elapsedSeconds'],3),flush=True)
        summary.append({k:row[k] for k in ('index','exact','error','elapsedSeconds')})
    (out/'summary.json').write_text(json.dumps(dict(accepted=sum(r['error'] is None for r in summary),exact=sum(r['exact'] for r in summary),count=len(cases),developmentPass=all(r['exact'] for r in summary),cases=summary),indent=2)+'\n')


if __name__=='__main__': main()
