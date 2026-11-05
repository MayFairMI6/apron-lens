"""Report preserved v5/v6 prompt-revision results without modifying inference records."""
import argparse
import json
from pathlib import Path
from scripts.report_training_comparison import summarize


def report_data(run,attempts):
    fresh=[dict(r,condition=r['version']) for r in run['records'] if r['phase']=='fresh']
    summary=summarize(dict(records=fresh),attempts)
    old={(r['exercise'],r['turn']):r for r in fresh if r['version']=='v5'}
    new={(r['exercise'],r['turn']):r for r in fresh if r['version']=='v6'}
    if set(old)!=set(new) or len(old)!=24:raise ValueError('Incomplete paired evaluation')
    improved=[k for k in old if not old[k]['score']['passed'] and new[k]['score']['passed']]
    regressed=[k for k in old if old[k]['score']['passed'] and not new[k]['score']['passed']]
    regression=[r for r in run['records'] if r['phase']=='observed_regression']
    gate=len(regression)==18 and all(r['score']['passed'] for r in regression) and len(improved)>len(regressed) and not regressed and all(r['score']['passed'] for r in new.values() if r['exercise']=='explicit_readiness')
    assert gate==run['adopt']
    return dict(summary=summary,improved=improved,regressed=regressed,adoptionGate=gate,
                regressionPassed=sum(r['score']['passed'] for r in regression),regressionTotal=len(regression))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args()
    run=json.loads(a.run.read_text())
    if not run['completed']:raise SystemExit('Evaluation not completed; preserve unfinished/failing evidence')
    attempts=[]
    for v in ('v5','v6'):attempts += [json.loads(s) for s in a.run.with_suffix('.'+v+'.prompts.jsonl').read_text().splitlines()]
    data=report_data(run,attempts)
    a.run.with_name(a.run.stem+'-summary.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# Readiness prompt revision: results','',
        'The original v5 comparison remains unchanged. This new instruction-only revision is evaluated '
        'first on 18 observed regression turns and then on 24 fresh authored questions for each version. '
        'Model weights, evidence, answer expansion, validator and retry policy are unchanged.','',
        f"Observed regression: **{data['regressionPassed']}/{data['regressionTotal']}** for v6. This includes the known failure and is development evidence, not an unseen test.",'',
        '| Fresh-question configuration | Task success | Validator accepted | Median seconds | Calls |',
        '|---|---:|---:|---:|---:|']
    for v,s in data['summary'].items():lines.append(f"| {v} | {s['completeSupported']}/{s['turns']} | {s['accepted']}/{s['turns']} | {s['medianSeconds']} | {s['calls']} |")
    lines += ['',f"Paired improvements: {len(data['improved'])}; paired regressions: {len(data['regressed'])}. Predeclared offline adoption gate: **{'passed' if data['adoptionGate'] else 'failed'}**. Native/service acceptance is recorded separately.",'',
        '| Version | Vehicle | Stand | Baggage | Explicit readiness |','|---|---:|---:|---:|---:|']
    for v in ('v5','v6'):
        counts=[sum(r['score']['passed'] for r in run['records'] if r['phase']=='fresh' and r['version']==v and r['exercise']==e) for e in ('surface_conflict','late_arrival','late_baggage','explicit_readiness')]
        lines.append('| '+v+' | '+' | '.join(str(n)+'/6' for n in counts)+' |')
    lines += ['','Failed fresh answers:','']
    for r in run['records']:
        if r['phase']=='fresh' and not r['score']['passed']:
            lines += [f"- **{r['version']} / {r['exercise']} / turn {r['turn']+1}:** {r['case']['question']}",
                      '  Expected facts: '+json.dumps(r['case']['required'])+'; requested unknowns: '+json.dumps(r['case']['unknowns'])+'.',
                      '  Display: '+json.dumps(r['result'].get('display'),ensure_ascii=False)]
    if all(r['score']['passed'] for r in run['records'] if r['phase']=='fresh'):lines.append('No failed fresh answers in this run.')
    lines += ['','The v6 prompt was fixed before fresh inference and was not adjusted afterward. '
        'Positive and negative readiness reports are synthetic evaluation fixtures, never added to app lessons. '
        'Questions immediately before and at receipt test evidence availability; service questions test against '
        'indiscriminate readiness abstention. There are four dependent episodes and one fresh scenario seed, '
        'not 48 independent samples. These results do not establish generalization, professional safety, '
        'learner benefit, graph benefit or weight-training benefit.','',
        'The inherited strict current-only scorer also rejects correctly labelled superseded facts. In the v5 readiness-change answer, both old ready and current not-ready reports were accurately labelled; its penalty must not be described as a factual error. The question wording can reasonably invite this history. Preserve the score but qualify any apparent fresh-question advantage.','',
        'All arms use the same selector/expansion/validator. Existing reference memory is not verbatim dialogue. '
        'No aircraft is selected; no images are supplied. Supported but irrelevant extras and prose quality '
        'are not fully scored. Offline latency uses fixed order and does not enforce native deadlines; '
        'engine stop reasons remain inferred. Actual prompts, raw selections, usage and retries are in '
        'the two audit sidecars. Source/case hashes are fixed in the pre-run lock.','',
        'See [protocol](../../docs/course/PROMPT_REVISION.md), [original comparison](../assistant-comparison/RESULTS.md), '
        'run JSON and summary JSON. No original result has been overwritten.']
    a.run.with_name('RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(data,indent=2))

if __name__=='__main__':main()
