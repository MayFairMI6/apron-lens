"""Frozen, sequential paired pilot; never overwrites prior outputs."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
 fixture=ROOT/'experiments/ordinary_history_repair/fresh-v1.json'
 paths=['backend/training_adapter.py','backend/training_history_guard.py','backend/training_turn.py','backend/training_result.py','backend/training_worker.py','experiments/ordinary_history_repair/baseline.py','experiments/ordinary_history_repair/fresh-v1.json','scripts/check_ordinary_repair.py']
 hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
 regression=json.loads((ROOT/'outputs/ordinary-repair-regression-v2/summary.json').read_text())
 if regression['completed']!=12 or regression['passed']!=12:raise RuntimeError('Regression gate failed; no fresh calls permitted')
 (out/'lock.json').write_text(json.dumps(dict(sourceHashes=hashes,regression=regression,armOrder=['baseline','repair'],gate='All12 regressions pass; repair at least baseline exact, no newly failing case; no delivered wrong flight or unavailable evidence. Descriptive same-domain pilot; no tuning after evaluation.'),indent=2))
 for arm in ('baseline','repair'):
  with (out/(arm+'.log')).open('w') as log:
   subprocess.run([sys.executable,str(ROOT/'scripts/check_ordinary_repair.py'),str(out/arm),str(fixture),arm],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
  print(arm,'complete',flush=True)
  assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),'source changed during pilot'
 rows={a:[json.loads(l) for l in (out/a/'records.jsonl').read_text().splitlines()] for a in ('baseline','repair')}
 assert len(rows['baseline'])==len(rows['repair'])==12
 for b,r in zip(rows['baseline'],rows['repair']):assert b['case']==r['case'] and b['episode']==r['episode']
 count={a:sum(r['score']['passed'] for r in rs) for a,rs in rows.items()}
 regressions=[i for i,(b,r) in enumerate(zip(rows['baseline'],rows['repair'])) if b['score']['passed'] and not r['score']['passed']]
 unsafe=[i for i,r in enumerate(rows['repair']) if r['result']['accepted'] and (not r['score']['identityCorrect'] or not r['score']['claimsSupported'])]
 summary=dict(completedPairs=12,passed=count,newlyFailingCases=regressions,deliveredIdentityOrSupportFailures=unsafe,gate=count['repair']>=count['baseline'] and not regressions and not unsafe,scope='frozen same-domain pilot, no tuning or broad superiority claim')
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
