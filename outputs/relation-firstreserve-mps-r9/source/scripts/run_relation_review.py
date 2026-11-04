"""Version-frozen typed-review evaluation. Labels never enter evaluate()."""
import argparse,hashlib,importlib,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('fixture',type=Path);p.add_argument('--module',default='experiments.typed_relation_review.candidate');p.add_argument('--development-cache',nargs='+',type=Path);a=p.parse_args()
m=importlib.import_module(a.module)
raw=a.fixture.read_text();cases=json.loads(raw)['cases'] if a.fixture.suffix=='.json' else [json.loads(l) for l in raw.splitlines()]
a.output.mkdir(parents=True,exist_ok=False)
source=Path(m.__file__).parent;paths=list(source.glob('*.py'))+[Path(__file__),ROOT/'backend/training_assessment.py']
if a.module.endswith('mps_candidate'):paths.append(ROOT/'modelaccess/nli.py')
if a.development_cache:paths.append(ROOT/'scripts/relation_development_cache.py')
hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
for x in paths:
 dest=a.output/'source'/x.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(x,dest)
lock=dict(module=a.module,version=m.VERSION,sourceHashes=hashes,fixture=str(a.fixture),fixtureSHA256=hashlib.sha256(raw.encode()).hexdigest(),model=m.MODEL_ID,revision=m.MODEL_REVISION,threshold=m.THRESHOLD,createdAt=time.time())
if a.module.endswith('mps_candidate'):
 import importlib.metadata
 snapshot=Path.home()/'.cache/huggingface/hub'/('models--'+m.MODEL_ID.replace('/','--'))/'snapshots'/m.MODEL_REVISION
 lock['modelArtifactSHA256']={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(snapshot.iterdir()) if x.is_file() and x.name!='README.md'}
 lock['runtimeProfile']=dict(device='mps',noFallback=True,batchSize=8,tokenBound=512,packages={x:importlib.metadata.version(x) for x in ('torch','transformers','tokenizers','safetensors')})
(a.output/'lock.json').write_text(json.dumps(lock,indent=2))
start=time.monotonic();engine=m.NLIEngine(m.MODEL_ID)
if a.development_cache:
 from scripts.relation_development_cache import DevelopmentCache
 engine=DevelopmentCache(engine,m,a.development_cache,hashlib.sha256(raw.encode()).hexdigest())
 (a.output/'development-cache.json').write_text(json.dumps(engine.manifest,indent=2))
(a.output/'startup.json').write_text(json.dumps(dict(seconds=time.monotonic()-start,torch=engine.torch.__version__,device=getattr(engine,'device','cpu'),runtime=getattr(engine,'runtime',None))))
rows=[]
for c in cases:
 engine.records=[];engine.planned_pairs=[];engine.semantic_rule_audit=[];engine.typed_state_audit=[];start=time.monotonic();review=None;error=None
 try:review=m.evaluate(c['payload'],engine,start+m.DEADLINE_SECONDS)
 except Exception as exc:error=type(exc).__name__+': '+str(exc)
 actual={} if review is None else {x['criterionId']:x['status'] for x in review['points']}
 row=dict(index=c['index'],payload=c['payload'],expected=c['expected'],actual=actual,exact=actual==c['expected'],review=review,error=error,elapsedSeconds=time.monotonic()-start,pairs=engine.records,plannedPairs=engine.planned_pairs,semanticRuleAudit=getattr(engine,'semantic_rule_audit',[]),typedStateAudit=getattr(engine,'typed_state_audit',[]))
 rows.append(row)
 with (a.output/'records.jsonl').open('a') as f:f.write(json.dumps(row,default=str)+'\n')
 print(c['index'],row['exact'],actual,error,flush=True)
assert all(hashlib.sha256((ROOT/x).read_bytes()).hexdigest()==h for x,h in hashes.items()),'source changed during evaluation'
summary=dict(count=len(rows),exact=sum(x['exact'] for x in rows),delivered=sum(x['review'] is not None for x in rows),validCount=sum(all(s=='met' for s in x['expected'].values()) for x in rows),validExact=sum(x['exact'] and all(s=='met' for s in x['expected'].values()) for x in rows),falseCredit=[dict(index=x['index'],criterion=k) for x in rows for k,v in x['actual'].items() if v=='met' and x['expected'][k]!='met'])
if a.development_cache:summary['developmentCache']=engine.verify()
(a.output/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
