import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.server import LocalQwen
from backend.decisions import select_claims
from backend.evidence import load_scenario,build_context
from backend.reasoning import normalized_claims
ROOT=Path(__file__).resolve().parents[1]
queries=[q for q in json.loads((ROOT/'data/reasoning_v1/queries.json').read_text()) if q['split']=='dev']
engine=LocalQwen();output=ROOT/'outputs/reasoning_v2/dev-decisions-trial5.jsonl'
if output.exists():raise RuntimeError('Do not overwrite development run')
for q in queries:
 context=build_context(load_scenario(q['scenarioId']),q['aircraftId'],q['checkpoint'],q['queryType'],q['properties'])
 start=time.perf_counter();raw,trace=select_claims(engine,context);parsed=json.loads(raw)
 exact=normalized_claims(parsed)==normalized_claims(q['gold']) and set(parsed['unknown_properties'])==set(q['gold']['unknown_properties'])
 row=dict(id=q['id'],queryType=q['queryType'],gold=q['gold'],raw=raw,trace=trace,exact=exact,seconds=time.perf_counter()-start)
 with output.open('a') as f:f.write(json.dumps(row)+'\n')
 print(q['id'],exact,round(row['seconds'],2),raw,flush=True)
