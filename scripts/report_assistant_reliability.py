"""Summarize the new B04 run without rewriting any earlier result."""
import hashlib,json,statistics
from pathlib import Path

def summarize(root=Path('outputs/assistant-reliability')):
 r=json.loads((root/'run-v2.json').read_text());lock=json.loads((root/'lock-v2.json').read_text())
 groups={}
 for phase,version in [('regression','v8'),('fresh','v5'),('fresh','v8')]:
  rows=[x for x in r['records'] if (x['phase'],x['version'])==(phase,version)]
  groups[phase+'-'+version]=dict(passed=sum(x['score']['passed'] for x in rows),total=len(rows),
   attempts=sum(x['result'].get('trainingAttemptCount',1) for x in rows),
   maxSeconds=max([x['result']['latencySeconds'] for x in rows],default=0),
   failures=[dict(episode=x['episode'],turn=x['turn'],score=x['score']) for x in rows if not x['score']['passed']])
 audits=[json.loads(l) for l in (root/'typed-audit-v2.jsonl').read_text().splitlines()] if (root/'typed-audit-v2.jsonl').exists() else []
 indexed=json.loads((root/'typed-indexed-v1.json').read_text()) if (root/'typed-indexed-v1.json').exists() else dict(completed=False,rows=[])
 indexed_audit=[json.loads(l) for l in (root/'typed-indexed-audit.jsonl').read_text().splitlines()] if (root/'typed-indexed-audit.jsonl').exists() else []
 return dict(completed=len(r['records'])==72 and indexed['completed'],groups=groups,indexedTyped=dict(total=len(indexed['rows']),passed=sum(x['passed'] for x in indexed['rows']),attempts=len(indexed_audit),invalidAttempts=sum(not x['contractAccepted'] for x in indexed_audit),maxSeconds=max([x['elapsedSeconds'] for x in indexed['rows']],default=0),failures=[x for x in indexed['rows'] if not x['passed']]),typedRetryOnlyTrial=dict(total=len(r['typed']),passed=sum(x['passed'] for x in r['typed']),
  attempts=len(audits),invalidAttempts=sum(not x['contractAccepted'] for x in audits),
  maxSeconds=max([x['elapsedSeconds'] for x in r['typed']],default=0),failures=[x for x in r['typed'] if not x['passed']]),
  loadSeconds=r['loadSeconds'],warmup=r['warmup'],
  oldArtifactsPreserved=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in lock['preserved'].items()),
  limits='Authored development cases and same-family paraphrases, not held-out or independent operational scenarios. Fixed version order. Typed semantics remain fallible. Warmup is not a hard inference deadline or stuck-worker cancellation.')
if __name__=='__main__':
 s=summarize();Path('outputs/assistant-reliability/summary-v2.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
