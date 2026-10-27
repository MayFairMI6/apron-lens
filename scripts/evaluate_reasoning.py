"""Frozen, append-only real-model evaluation. No retries or silent fallback answers."""
import argparse,datetime,hashlib,json,platform,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from backend.evidence import load_scenario,build_context,expected_selection
from backend.reasoning import prompt_for,parse_claims,normalized_claims,validate_answer,PROMPT_VERSION,MODEL_PATH
from backend.server import LocalQwen
ROOT=Path(__file__).resolve().parents[1];SUITE=ROOT/'data/reasoning_v1';OUT=ROOT/'outputs/reasoning_v1'
CONDITIONS=['unfiltered_history_text','scoped_history_text','state_aware_text','state_aware_image']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def files():
 paths=['backend/evidence.py','backend/reasoning.py','backend/server.py','scripts/evaluate_reasoning.py','data/reasoning_v1/manifest.json']
 return {p:digest(ROOT/p) for p in paths}
def check_suite():
 manifest=json.loads((SUITE/'manifest.json').read_text())
 for p,sha in manifest['files'].items():
  if digest(SUITE/p)!=sha:raise RuntimeError('Dataset changed: '+p)
def freeze():
 check_suite();path=OUT/'protocol.json'
 if path.exists():raise RuntimeError('Protocol already frozen; create a new version rather than overwrite')
 protocol=dict(createdUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files(),
  model=json.loads((MODEL_PATH/'download-manifest.json').read_text()),conditions=CONDITIONS,
  decoding=dict(do_sample=False,max_new_tokens=512),promptVersion=PROMPT_VERSION,
  split='24 development questions in 8 families; 12 held-out questions in 4 author-known composition families',
  primary='Raw exact claim/value/status/citation and unknown-property set accuracy; all failures included',
  secondary=['raw citation support','wrong-identity and temporal errors','abstention on unknown-property cases','guard withholding and coverage','latency and tokens'],
  baseline='Deterministic resolver for the same explicit query type/properties; no learned component',
  caveats=['Single developer authored data and labels; no expert review','Four held-out clusters too few for broad claims','Synthetic negative-control image has no answer-bearing operational information','Not a test of visual understanding or open-ended aviation reasoning','Context lengths differ; input/output tokens are reported; not equal-token-budget causal comparison'])
 OUT.mkdir(exist_ok=True);path.write_text(json.dumps(protocol,indent=2)+'\n');print('FROZEN',digest(path))
def score(raw,context,gold):
 result=dict(json_valid=False,exact=False,claims=0,correct_claims=0,supported_citations=0,wrong_identity=0,
             invalid_time=0,unsupported_value=0,abstention_exact=False)
 try:
  parsed=parse_claims(raw);result['json_valid']=True;result['claims']=len(parsed['claims'])
  result['exact']=normalized_claims(parsed)==normalized_claims(gold) and set(parsed['unknown_properties'])==set(gold['unknown_properties'])
  result['abstention_exact']=set(parsed['unknown_properties'])==set(gold['unknown_properties'])
  gold_set=set(normalized_claims(gold));facts={f['fact_id']:f for f in context['facts']}
  allfacts={f['fact_id']:f for f in context['receivedFacts']}
  for c in parsed['claims']:
   atom=normalized_claims({'claims':[c]})[0]
   result['correct_claims']+=atom in gold_set
   f=facts.get(c['fact_id'])
   if f is None:
    result['wrong_identity']+=c['fact_id'] in allfacts
    result['invalid_time']+=c['fact_id'] not in allfacts
    continue
   result['invalid_time']+=c['status']!=f['status']
   result['unsupported_value']+=c['value']!=f['value']
   result['supported_citations']+=(c['value']==f['value'] and c['evidence_ids']==[f['event_id']])
 except (ValueError,TypeError,KeyError):pass
 guarded=validate_answer(raw,context)
 result['guard_accepted']=guarded['resultStatus']=='generated';result['guard_errors']=guarded['validationErrors']
 return result,guarded

def run(split,resume=False):
 check_suite();protocol=OUT/'protocol.json';frozen=json.loads(protocol.read_text())
 if files()!=frozen['files']:raise RuntimeError('Code changed after protocol freeze; do not tune this version')
 queries=[q for q in json.loads((SUITE/'queries.json').read_text()) if q['split']==split]
 path=OUT/f'{split}-runs.jsonl'
 if path.exists() and not resume:raise RuntimeError('Run exists; use --resume for missing requests only')
 old=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
 if any(row['protocolSha256']!=digest(protocol) for row in old):raise RuntimeError('Run/protocol mismatch')
 done={(r['questionId'],r['condition']) for r in old};engine=LocalQwen()
 for index,q in enumerate(queries):
  context=build_context(load_scenario(q['scenarioId']),q['aircraftId'],q['checkpoint'],q['queryType'],q['properties'])
  order=CONDITIONS[index%4:]+CONDITIONS[:index%4]
  for cond in order:
   if (q['id'],cond) in done:continue
   condition=cond.rsplit('_',1)[0];prompt=prompt_for(context,q['question'],condition)
   image=Image.open(SUITE/q['image']).convert('RGB') if cond.endswith('_image') else None
   started=time.perf_counter();error=None
   try:raw,inputs,outputs=engine.generate(prompt,image)
   except Exception as exc:raw='';inputs=outputs=0;error=f'{type(exc).__name__}: {exc}'
   metrics,guarded=score(raw,context,q['gold'])
   row=dict(questionId=q['id'],scenarioId=q['scenarioId'],family=q['family'],split=split,condition=cond,
     protocolSha256=digest(protocol),model=engine.manifest,device=engine.device,python=platform.python_version(),
     checkpoint=q['checkpoint'],queryType=q['queryType'],properties=q['properties'],gold=q['gold'],
     raw=raw,prompt=prompt,promptSha256=hashlib.sha256(prompt.encode()).hexdigest(),
     imageSha256=digest(SUITE/q['image']) if image is not None else None,
     inputTokens=inputs,outputTokens=outputs,seconds=round(time.perf_counter()-started,3),error=error,
     metrics=metrics,guarded=guarded,recordedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
   with path.open('a') as stream:stream.write(json.dumps(row)+'\n');stream.flush()
   print(f"{split} {q['id']} {cond}: exact={metrics['exact']} accepted={metrics['guard_accepted']} {row['seconds']}s",flush=True)
 print('COMPLETE',split,len(queries)*len(CONDITIONS),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--split',choices=['dev','heldout']);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
 if args.freeze:freeze()
 elif args.split:run(args.split,args.resume)
 else:parser.error('Choose --freeze or --split')
