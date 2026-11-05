"""Summarize an immutable real-model training-comparison run, including failures."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def summarize(run, attempts):
    groups={}
    for row in run['records']:
        groups.setdefault(row['condition'],[]).append(row)
    summaries={}
    for name,rows in groups.items():
        ids={r['result']['requestId'] for r in rows}
        calls=[a for a in attempts if a['requestId'] in ids]
        counts=Counter(a['requestId'] for a in calls)
        summaries[name]=dict(turns=len(rows),completeSupported=sum(r['score']['passed'] for r in rows),
            accepted=sum(r['score']['accepted'] for r in rows),
            identityNotMatched=sum(not r['score']['identityCorrect'] for r in rows),
            incomplete=sum(not r['score']['complete'] for r in rows),
            wrongUnknowns=sum(not r['score']['unknownsCorrect'] for r in rows),
            noncurrentClaims=sum(r['score']['staleClaims'] for r in rows),
            noClaimsOrUnknowns=sum(r['score']['emptyAnswer'] for r in rows),
            clarifications=sum(json.loads(r['result']['rawModelOutput']).get('status')=='clarify' for r in rows if r['result'].get('rawJsonValid')),
            calls=len(calls),retriedTurns=sum(n>1 for n in counts.values()),
            inputTokens=sum(a['usage']['input_tokens'] for a in calls) if all(a['usage']['input_tokens'] is not None for a in calls) else None,
            knownInputTokens=sum(a['usage']['input_tokens'] or 0 for a in calls),
            outputTokens=sum(a['usage']['output_tokens'] for a in calls) if all(a['usage']['output_tokens'] is not None for a in calls) else None,
            knownOutputTokens=sum(a['usage']['output_tokens'] or 0 for a in calls),
            usageComplete=all(a['usage']['input_tokens'] is not None and a['usage']['output_tokens'] is not None for a in calls),
            medianSeconds=round(statistics.median(r['result']['latencySeconds'] for r in rows),3),
            over35Seconds=sum(r['result']['latencySeconds']>35 for r in rows),
            over40Seconds=sum(r['result']['latencySeconds']>40 for r in rows))
    return summaries


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args()
    run=json.loads(a.run.read_text())
    if not run['completed']:raise SystemExit('Run incomplete; do not publish final results')
    attempts=[json.loads(line) for line in a.run.with_suffix('.prompts.jsonl').read_text().splitlines()]
    summary=summarize(run,attempts)
    out=a.run.with_name(a.run.stem+'-summary.json')
    out.write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Current assistant: bounded comparison results','',
        '18 authored turns in three dependent conversations, evaluated in three configurations (54 responses). '
        'Seed 17, Qwen3.5-9B, text only. This is a development comparison, not a held-out benchmark, '
        'professional safety assessment, visual-reasoning test or learner-outcome study.','',
        '| Configuration | Complete supported answers | Validator accepted | Median seconds | Model calls |',
        '|---|---:|---:|---:|---:|']
    for name,s in summary.items():
        lines.append(f"| {name} | {s['completeSupported']}/{s['turns']} | {s['accepted']}/{s['turns']} | {s['medianSeconds']} | {s['calls']} |")
    lines += ['', '| Configuration | Vehicle obstruction | Occupied stand | Baggage delay |', '|---|---:|---:|---:|']
    for name in summary:
        counts = [sum(r['score']['passed'] for r in run['records'] if r['condition']==name and r['exercise']==exercise)
                  for exercise in ('surface_conflict','late_arrival','late_baggage')]
        lines.append('| '+name+' | '+' | '.join(str(n)+'/6' for n in counts)+' |')
    lines+=['','All configurations share the same evidence selector, expansion and validator. The lexical '
        'arm restricts the eligible reports to six ranked facts; history means existing validated reference '
        'memory, not a verbatim chat transcript. The no-history arm starts a fresh session each turn. '
        'No aircraft is selected, making conversation-dependent reference resolution observable.','',
        'Claim values are copied from selected evidence by the existing adapter. The important measured '
        'differences are flight identity, report selection, completeness and appropriate unknowns. '
        'An accepted response can still fail the answer key. A clarification can be appropriate for an arm deprived of history while still failing the full conversation task; it is not an empty-answer defect. Unknown-only answers have no citation requirement.','',
        'The summary JSON includes token totals, retries, identity/coverage/uncertainty failures and responses '
        'exceeding the native 35-second/driver 40-second thresholds. The offline runner does not enforce '
        'those deadlines. Fixed execution order makes latency descriptive, not a controlled speed comparison.','',
        'Failures (including withheld output):','']
    for r in run['records']:
        if not r['score']['passed']:
            lines += [f"- **{r['condition']} / {r['exercise']} / turn {r['turn']+1}**: {r['case']['question']}",
                      '  Score: '+json.dumps(r['score'],sort_keys=True),
                      '  Display: '+json.dumps(r['result'].get('display'),ensure_ascii=False)]
    if all(r['score']['passed'] for r in run['records']):lines.append('No failed turns in this bounded run.')
    lines+=['','No prompts or answer keys were revised in response to these results. A graph database was '
        'not introduced: this comparison does not establish a graph-specific retrieval need. '
        'Retain these results, including ties or losses; do not claim state-of-the-art performance.','',
        'See [protocol](../../docs/course/ASSISTANT_COMPARISON.md), run JSON, actual selector prompt/response '
        'sidecar and source manifest in this directory. Historical frozen research is unchanged.']
    a.run.with_name('RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
