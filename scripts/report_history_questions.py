"""Report history-aware evaluation without rewriting any primary model evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def summarize(run,attempts):
    summaries={}
    for v in ('v5','v6'):
        rows=[r for r in run['records'] if r['version']==v]
        ids={r['result']['requestId'] for r in rows};calls=[a for a in attempts if a['requestId'] in ids]
        counts=Counter(a['requestId'] for a in calls)
        totals={}
        for name in ('input_tokens','output_tokens'):
            vals=[a['usage'][name] for a in calls]
            totals[name]=sum(vals) if all(x is not None for x in vals) else None
            totals['known_'+name]=sum(x or 0 for x in vals)
        summaries[v]=dict(passed=sum(r['score']['passed'] for r in rows),total=len(rows),
            accepted=sum(r['score']['accepted'] for r in rows),
            byMode={m:dict(passed=sum(r['score']['passed'] for r in rows if r['case']['mode']==m),total=sum(r['case']['mode']==m for r in rows)) for m in ('current','history','change')},
            byEpisode={e:dict(passed=sum(r['score']['passed'] for r in rows if r['episode']==e),total=sum(r['episode']==e for r in rows)) for e in dict.fromkeys(r['episode'] for r in rows)},
            calls=len(calls),retriedTurns=sum(n>1 for n in counts.values()),usage=totals,
            medianSeconds=round(statistics.median(r['result']['latencySeconds'] for r in rows),3),
            over35Seconds=sum(r['result']['latencySeconds']>35 for r in rows),over40Seconds=sum(r['result']['latencySeconds']>40 for r in rows))
    return summaries

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args()
    run=json.loads(a.run.read_text())
    if not run['completed']:raise SystemExit('Run is not complete')
    attempts=[]
    for v in ('v5','v6'):attempts += [json.loads(s) for s in a.run.with_suffix('.'+v+'.prompts.jsonl').read_text().splitlines()]
    summary=summarize(run,attempts)
    a.run.with_name(a.run.stem+'-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# History-aware evaluation: new report families','',
        '24 new authored questions in four dependent report scenarios, each tested with frozen v5 and v6. '
        'The new scorer distinguishes current status, named history and before/after change. '
        'The earlier results and scorers are unchanged. This is a development evaluation, not a held-out operational benchmark.','',
        '| Version | Task success | Current | History | Change | Validator accepted |',
        '|---|---:|---:|---:|---:|---:|']
    for v,s in summary.items():
        modes=['{passed}/{total}'.format(**s['byMode'][m]) for m in ('current','history','change')]
        lines.append(f"| {v} | {s['passed']}/{s['total']} | "+' | '.join(modes)+f" | {s['accepted']}/{s['total']} |")
    lines += ['','| Version | Weather route | Stand reassignment | Service withdrawal | Estimate correction |','|---|---:|---:|---:|---:|']
    for v,s in summary.items():lines.append('| '+v+' | '+' | '.join('{passed}/{total}'.format(**x) for x in s['byEpisode'].values())+' |')
    lines += ['','A pass requires the expected flight, required fact coverage, permitted relevant evidence, '
        'correct source values/statuses/citations and exact requested uncertainty. A truthful but incomplete '
        'answer may pass the app validator and fail this evaluation. Correctly labelled superseded facts '
        'are accepted only when the declared history/change question permits them.','',
        'Failed answers:','']
    failures=[r for r in run['records'] if not r['score']['passed']]
    for r in failures:
        lines += [f"- **{r['version']} / {r['episode']} / turn {r['turn']+1} / {r['case']['mode']}**: {r['case']['question']}",
                  '  Required: '+json.dumps(r['case']['required'])+'; unknowns: '+json.dumps(r['case']['unknowns'])+'.',
                  '  Checks: '+json.dumps(r['score'],sort_keys=True)+'.',
                  '  Display: '+json.dumps(r['result'].get('display'),ensure_ascii=False)]
    if not failures:lines.append('No failed turns in this bounded run.')
    lines += ['','The separate old-answer diagnostic re-scores only the two known readiness-change answers. '
        'Both correctly labelled histories pass under the new rule. That diagnostic is post-hoc, uses no '
        'new model calls, and does not replace either old result set or retrospectively promote v6.','',
        'All model prompts and model weights remain frozen. New report worlds are evaluation fixtures, '
        'not new in-app scenes or operational Heathrow data. Four dependent families, fixed version order, '
        'text-only inputs and no selected-aircraft cue limit generalisation. Only current and superseded '
        'statuses are covered; conflicting, expired and scheduled states are not tested. History consists '
        'of the existing reference state rather than a verbatim transcript.','',
        'Actual selector prompts/raw outputs, expanded/displayed answers, attempts and usage are preserved. '
        'The summary records retries, token totals and 35/40-second overruns; offline execution does not '
        'enforce native deadlines. Stop reason remains inferred by the unchanged adapter. Neither structural '
        'acceptance nor this test establishes learning benefit, professional competence or a need for weight training.','',
        'Production stays on v5; no prompt promotion or app behaviour change is made. '
        'See [protocol](../../docs/course/HISTORY_EVALUATION.md), run and lock JSON, '
        'actual prompt sidecars and old-answer diagnostic in this directory.']
    a.run.with_name('RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
