"""Summarize every frozen run, including malformed and withheld answers."""
import collections,csv,hashlib,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/reasoning_v1'
protocol=json.loads((OUT/'protocol.json').read_text());sha=hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest()
queries=json.loads((ROOT/'data/reasoning_v1/queries.json').read_text());gold={q['id']:q for q in queries}
rows=[]
for split,expected in [('dev',96),('heldout',48)]:
 part=[json.loads(x) for x in (OUT/f'{split}-runs.jsonl').read_text().splitlines()]
 assert len(part)==expected and len({(r['questionId'],r['condition']) for r in part})==expected
 assert all(r['protocolSha256']==sha for r in part)
 rows+=part

def summary(rs):
 n=len(rs);metrics=[r['metrics'] for r in rs];claims=sum(m['claims'] for m in metrics)
 unknown=[r for r in rs if gold[r['questionId']]['gold']['unknown_properties']]
 gold_claims=sum(len(gold[r['questionId']]['gold']['claims']) for r in rs)
 return dict(n=n,exact=sum(m['exact'] for m in metrics),json_valid=sum(m['json_valid'] for m in metrics),
   claims=claims,correct_claims=sum(m['correct_claims'] for m in metrics),gold_claims=gold_claims,
   supported_citations=sum(m['supported_citations'] for m in metrics),
   wrong_identity_claims=sum(m['wrong_identity'] for m in metrics),
   unavailable_or_wrong_status_claims=sum(m['invalid_time'] for m in metrics),
   unsupported_value_claims=sum(m['unsupported_value'] for m in metrics),
   unknown_questions=len(unknown),unknown_exact=sum(r['metrics']['abstention_exact'] for r in unknown),
   guard_accepted=sum(m['guard_accepted'] for m in metrics),
   guard_accepted_incorrect=sum(m['guard_accepted'] and not m['exact'] for m in metrics),
   execution_failures=sum(r['error'] is not None for r in rs),
   median_seconds=round(statistics.median(r['seconds'] for r in rs),3),
   mean_input_tokens=round(statistics.mean(r['inputTokens'] for r in rs),1),
   mean_output_tokens=round(statistics.mean(r['outputTokens'] for r in rs),1))
summary_data={split:{c:summary([r for r in rows if r['split']==split and r['condition']==c]) for c in protocol['conditions']} for split in ('dev','heldout')}
by_family={f:{c:summary([r for r in rows if r['family']==f and r['condition']==c]) for c in protocol['conditions']} for f in sorted({r['family'] for r in rows})}
# Exploratory paired cluster bootstrap; only four held-out families -> very imprecise.
held=[r for r in rows if r['split']=='heldout'];families=sorted({r['family'] for r in held});deltas=[]
for family in families:
 def acc(cond):
  values=[r['metrics']['exact'] for r in held if r['family']==family and r['condition']==cond]
  return sum(values)/len(values)
 deltas.append(acc('state_aware_text')-acc('unfiltered_history_text'))
rng=random.Random(20261027);boots=sorted(sum(rng.choice(deltas) for _ in deltas)/len(deltas) for _ in range(5000))
pair=dict(contrast='state_aware_text minus unfiltered_history_text',cluster_count=4,
 mean_difference=sum(deltas)/4,exploratory_bootstrap_95_percent_interval=[boots[125],boots[4874]],
 caution='Only four hand-authored clusters; interval is exploratory and does not establish generalization.')
result=dict(protocol_sha256=sha,summary=summary_data,by_family=by_family,paired_comparison=pair,
 deterministic_baseline=dict(dev='24/24',heldout='12/12',scope='Supported structured questions; same hand-authored gold labels. Not a learned-model result.'))
(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'per-query.csv').open('w') as f:
 fields=['split','questionId','scenarioId','family','condition','exact','json_valid','guard_accepted','wrong_identity','invalid_time','seconds','inputTokens','outputTokens']
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
 for r in rows:writer.writerow({key:r.get(key,r['metrics'].get(key)) for key in fields})
errors=[dict(question=r['questionId'],condition=r['condition'],split=r['split'],raw=r['raw'],gold=r['gold'],errors=r['metrics']['guard_errors']) for r in rows if not r['metrics']['exact']]
(OUT/'error-catalog.json').write_text(json.dumps(errors,indent=2)+'\n')
lines=['# Typed evidence reasoning: reproducible pilot','',
'Qwen2.5-VL-3B-Instruct was tested on 36 questions from 12 original fictional scenario families. '
'The final protocol ran 144 model requests: 96 development and 48 held-out. Four composition families '
'(12 questions) were held out from model-driven prompt changes. All scenarios and labels were authored '
'by the same developer, so this is an author-known synthetic pilot, not an independently curated benchmark.','',
'## What changed','',
'Qwen selects atomic facts with values, temporal statuses, and citations. The validator checks every field '
'against the selected flight’s received evidence and checks query coverage. Only accepted selections are '
'rendered, using deterministic templates. The original merged-claim citation bug is therefore blocked '
'within this typed schema. This is constrained, source-linked rendering—not a general free-text entailment verifier.','',
'The state engine distinguishes receipt time from event time, applies validity intervals and explicit '
'supersession, preserves old plans as history, and treats unresolved conflicting values as unknown. '
'A delayed older update does not overwrite a received newer replacement. Expiring a replacement does '
'not revive an explicitly superseded plan.','',
'## Held-out results','',
'| Condition | Raw exact answers | Valid schema | Accepted by guard | Accepted but incorrect | Median seconds |',
'|---|---:|---:|---:|---:|---:|']
for c,s in summary_data['heldout'].items():lines.append(f"| {c} | {s['exact']}/{s['n']} | {s['json_valid']}/{s['n']} | {s['guard_accepted']}/{s['n']} | {s['guard_accepted_incorrect']} | {s['median_seconds']} |")
lines+=['| deterministic state engine | 12/12 | n/a | n/a | n/a | not benchmarked |','',
'Raw exactness requires the complete correct set of claim IDs, values, statuses, citations, and unknown '
'properties. Failures and malformed JSON remain in the denominator. Accepted coverage is reported '
'separately so rejection cannot be mistaken for model competence. The guard uses the deterministic '
'query contract; a high accepted-answer precision is a property of that contract, not an independent '
'model-accuracy improvement.','',
'| Condition | Supported citations / emitted claims | Correct abstention sets on unknown questions | Wrong-identity claims | Unavailable-ID or wrong-status claims | Mean input / output tokens |',
'|---|---:|---:|---:|---:|---:|']
for c,s in summary_data['heldout'].items():lines.append(f"| {c} | {s['supported_citations']}/{s['claims']} | {s['unknown_exact']}/{s['unknown_questions']} | {s['wrong_identity_claims']} | {s['unavailable_or_wrong_status_claims']} | {s['mean_input_tokens']} / {s['mean_output_tokens']} |")
lines+=['','Citation support here means exact source/value support for the typed atom; temporal status is '
'scored separately. Malformed responses have zero emitted scored claims but still fail answer accuracy; '
'do not interpret citation precision alone as end-to-end quality.','',
'## Interpretation','',
'The deterministic baseline answers all supported questions correctly. These tasks therefore do not '
'establish that an LLM is necessary or superior. The meaningful research direction is measuring when '
'context selection, temporal constraints, and controlled abstention improve a model, then extending '
'evaluation to genuinely visual or open-ended tasks that the state engine cannot answer alone.','',
f"The paired state-aware versus unfiltered text difference is {pair['mean_difference']*100:.1f} percentage points. "
f"An exploratory family-bootstrap interval is [{boots[125]*100:.1f}, {boots[4874]*100:.1f}] points; "
'four held-out families are insufficient for a strong generalization claim.','',
'The image condition uses the same non-diagnostic schematic at all checkpoints as a negative control. '
'It is intentionally not evidence for service status or plan validity. Its result does not demonstrate '
'visual reasoning, motion prediction, longitudinal memory, or AR usefulness. Context lengths differ '
'across retrieval conditions; token counts are reported, but this is not a matched-input-budget study.','',
'## Development history and reproducibility','',
'The initial format-only development pilot was stopped after recurrent schema errors. Its raw outputs '
'and frozen protocol remain in initial-format-pilot/. The final prompt adds a concrete output example; '
'a lossless parser normalization unwraps a single extra claim object. No missing value, status, or '
'citation is invented. No prompt or engine changes were made after the final protocol freeze, and no '
'held-out model outputs were used to tune it.','',
'Protocol: protocol.json. Dataset and per-file hashes: ../../data/reasoning_v1/manifest.json. '
'Raw prompts, outputs, tokens, timing, and errors: dev-runs.jsonl and heldout-runs.jsonl. '
'Per-question scores: per-query.csv. Full errors: error-catalog.json.','',
'Reproduce with scripts/evaluate_reasoning.py using a new output/version for changed code. '
'--resume runs only missing requests under the identical protocol hash. Run scripts/report_reasoning.py '
'to regenerate this report. Model revision and deterministic decoding are fixed in the protocol.','',
'## Before a research-grade performance claim','',
'Obtain independent domain review of facts, event semantics, and gold answers; expand the number of '
'independent families; preregister the next version before testing; compare matched evidence budgets; '
'add multi-frame, visually necessary questions with geometry withheld from model input; measure '
'calibrated abstention and robust source attribution; and evaluate the actual Android UI with users. '
'No airport safety, training-effectiveness, or accident-reduction claim follows from this pilot.','',
'## Literature grounding','',
'The separation of answer correctness from citation quality follows the evaluation concerns in '
'[Gao et al., EMNLP 2023, ALCE](https://aclanthology.org/2023.emnlp-main.398/). '
'Atomic fact assessment is motivated by [Min et al., EMNLP 2023, FActScore](https://aclanthology.org/2023.emnlp-main.741/). '
'This project does not reproduce either benchmark or claim equivalent metrics: it verifies a much '
'narrower typed scenario schema without an NLI judge.','']
(OUT/'REPORT.md').write_text('\n'.join(lines))
print(json.dumps(summary_data['heldout'],indent=2))
