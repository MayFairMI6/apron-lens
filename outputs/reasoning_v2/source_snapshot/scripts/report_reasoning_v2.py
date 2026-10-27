"""Summarize frozen V2 records without recomputing scores or opening fresh cases."""
import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from evaluate_reasoning_v2 import OUT, CONDITIONS, BASELINE, CONFIG, digest, read_journal, verify_protocol


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def average(rows, key):
    values = [r[key] for r in rows if r.get(key) is not None]
    return round(statistics.mean(values), 3) if values else None


def summarize(rows):
    metrics = [r['metrics'] for r in rows]
    n = len(rows)
    missing = [r for r in rows if r['metrics']['has_missing_evidence']]
    counts = {key: sum(m[key] for m in metrics) for key in
              ['exact', 'json_valid', 'claims', 'correct_claims', 'gold_claims',
               'invented_fact_id', 'unavailable_fact_id', 'wrong_identity', 'wrong_status',
               'wrong_value', 'wrong_citation', 'supported_citations', 'guard_accepted',
               'guard_accepted_incorrect']}
    latency = [r['seconds'] for r in rows if r['seconds'] is not None]
    return dict(n=n, **counts, exact_rate=ratio(counts['exact'], n),
                claim_precision=ratio(counts['correct_claims'], counts['claims']),
                claim_recall=ratio(counts['correct_claims'], counts['gold_claims']),
                missing_evidence_questions=len(missing),
                missing_evidence_exact=sum(r['metrics']['exact'] for r in missing),
                missing_unknown_set_exact=sum(r['metrics']['unknown_exact'] for r in missing),
                all_unknown_set_exact=sum(m['unknown_exact'] for m in metrics),
                execution_failures=sum(r['error'] is not None for r in rows),
                zero_forward_pass_questions=sum(r.get('forwardPasses') == 0 for r in rows),
                median_seconds=round(statistics.median(latency), 4) if latency else None,
                mean_input_tokens=average(rows, 'inputTokens'),
                mean_output_tokens=average(rows, 'outputTokens'),
                mean_forward_passes=average(rows, 'forwardPasses'),
                missing_latency_records=n-len(latency),
                missing_compute_records=sum(r.get('forwardPasses') is None for r in rows))


def paired(rows, treatment, control):
    a = {r['questionId']: r for r in rows if r['condition'] == treatment}
    b = {r['questionId']: r for r in rows if r['condition'] == control}
    common = sorted(set(a) & set(b))
    deltas = {q: int(a[q]['metrics']['exact']) - int(b[q]['metrics']['exact']) for q in common}
    families = collections.defaultdict(list)
    for q, delta in deltas.items():
        if a[q]['family'] != b[q]['family']:
            raise RuntimeError('Paired rows disagree on family')
        families[a[q]['family']].append(delta)
    by_family = {f: dict(n=len(values), delta=statistics.mean(values)) for f, values in sorted(families.items())}
    return dict(treatment=treatment, control=control, paired_questions=len(common),
                unpaired_treatment=len(set(a)-set(b)), unpaired_control=len(set(b)-set(a)),
                wins=sum(d > 0 for d in deltas.values()), losses=sum(d < 0 for d in deltas.values()),
                ties=sum(d == 0 for d in deltas.values()),
                exact_rate_difference=statistics.mean(deltas.values()) if deltas else None,
                family_count=len(families), family_differences=by_family,
                equal_family_mean_difference=statistics.mean(v['delta'] for v in by_family.values()) if by_family else None,
                interpretation='Descriptive paired comparison only; no independent-question inference or generalization claim')


def report(allow_partial=False):
    protocol, sha, _ = verify_protocol()  # Hashes only; never loads questions or gold.
    rows = read_journal(OUT / 'fresh-runs.jsonl')
    attempts = read_journal(OUT / 'attempts.jsonl')
    if not rows:
        raise RuntimeError('No recorded evaluation to report')
    conditions = CONDITIONS + [BASELINE]
    keys = [(r['questionId'], r['condition']) for r in rows]
    if len(set(keys)) != len(keys):
        raise RuntimeError('Duplicate evaluation records')
    if any(r['protocolSha256'] != sha or r['condition'] not in conditions for r in rows + attempts):
        raise RuntimeError('Unexpected condition or protocol mismatch')
    started = {(r['questionId'], r['condition']) for r in attempts}
    if len(started) != len(attempts) or not set(keys).issubset(started):
        raise RuntimeError('Invalid attempt journal')
    question_ids = {r['questionId'] for r in rows}
    expected = CONFIG['questionCount'] * len(conditions)
    complete = (len(rows) == expected and len(question_ids) == CONFIG['questionCount']
                and all((q, c) in set(keys) for q in question_ids for c in conditions))
    if not complete and not allow_partial:
        raise RuntimeError('Incomplete evaluation; pass --allow-partial to label an interim report')
    by_condition = {c: summarize([r for r in rows if r['condition'] == c]) for c in conditions}
    by_query = {q: {c: summarize([r for r in rows if r['queryType'] == q and r['condition'] == c])
                    for c in conditions} for q in sorted({r['queryType'] for r in rows})}
    by_family = {f: {c: summarize([r for r in rows if r['family'] == f and r['condition'] == c])
                     for c in conditions} for f in sorted({r['family'] for r in rows})}
    contrasts = [paired(rows, 'decisions_state_text', 'legacy_state_text'),
                 paired(rows, 'decisions_state_image', 'decisions_state_text'),
                 paired(rows, 'decisions_unfiltered_text', 'decisions_state_text'),
                 paired(rows, 'decisions_state_text', BASELINE)]
    errors = [dict(questionId=r['questionId'], family=r['family'], queryType=r['queryType'],
                   condition=r['condition'], raw=r['raw'], gold=r['gold'], error=r['error'],
                   metrics=r['metrics']) for r in rows if not r['metrics']['exact']]
    result = dict(protocolSha256=sha, complete=complete, records=len(rows), expectedRecords=expected,
                  unresolvedAttempts=len(started-set(keys)), summary=by_condition,
                  byQueryType=by_query, byFamily=by_family, pairedComparisons=contrasts,
                  caveats=protocol['caveats'], scoresRecomputed=False)
    (OUT / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    (OUT / 'error-catalog.json').write_text(json.dumps(errors, indent=2) + '\n')
    label = 'Complete' if complete else 'INTERIM / INCOMPLETE'
    lines = ['# Fresh typed-evidence evaluation', '',
             f'{label}: {len(rows)}/{expected} records, with a separate deterministic baseline. '
             f"The method was fixed after {CONFIG['developmentTrials']} development trials and "
             f"{CONFIG['developmentSmokeQueries']} real-Unity M1 development smoke queries; source, configuration, "
             'model manifest and the independent fresh-suite hash were frozen before opening fresh questions.', '',
             '| Condition | Raw exact | Missing-evidence exact | Guard accepted | Accepted incorrect | Median seconds | Mean forwards |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for condition, s in by_condition.items():
        lines.append(f"| {condition} | {s['exact']}/{s['n']} | {s['missing_evidence_exact']}/{s['missing_evidence_questions']} | "
                     f"{s['guard_accepted']}/{s['n']} | {s['guard_accepted_incorrect']} | {s['median_seconds']} | {s['mean_forward_passes']} |")
    lines += ['', 'Raw exactness requires every claim ID, value, status, citation and unknown-property flag. '
              'Malformed, interrupted and failed calls remain failures. Guard rejection never counts as a correct raw answer. '
              'The guard checks the deterministic query contract; its accepted-answer precision is not independent evidence of model competence.', '',
              '| Condition | Claim precision | Claim recall | Invented ID | Unavailable ID | Wrong identity | Wrong status | Mean input/output tokens |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for condition, s in by_condition.items():
        precision = f"{s['claim_precision']:.3f}" if s['claim_precision'] is not None else 'n/a'
        recall = f"{s['claim_recall']:.3f}" if s['claim_recall'] is not None else 'n/a'
        lines.append(f"| {condition} | {precision} | {recall} | {s['invented_fact_id']} | {s['unavailable_fact_id']} | "
                     f"{s['wrong_identity']} | {s['wrong_status']} | {s['mean_input_tokens']}/{s['mean_output_tokens']} |")
    lines += ['', 'ID error categories are exclusive in order: nonexistent scenario fact, fact not yet received, then received fact for another identity. '
              'Status/value/citation errors are checked only for available selected-identity facts. '
              'Malformed outputs have zero scored emitted claims but fail whole-answer accuracy; claim precision alone can therefore mislead.', '',
              '| Query type | Legacy exact | Predicate selection exact | Deterministic exact |', '|---|---:|---:|---:|']
    for query, values in by_query.items():
        cells = [f"{values[c]['exact']}/{values[c]['n']}" for c in ['legacy_state_text', 'decisions_state_text', BASELINE]]
        lines.append('| ' + query + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', 'Paired comparisons use the same fresh questions; no comparison mixes old held-out and new fresh accuracy.', '']
    for contrast in contrasts:
        delta = contrast['exact_rate_difference']
        text_delta = f'{delta * 100:+.1f} percentage points' if delta is not None else 'unavailable'
        lines.append(f"- {contrast['treatment']} versus {contrast['control']}: {text_delta}; "
                     f"{contrast['wins']} wins, {contrast['losses']} losses, {contrast['ties']} ties across "
                     f"{contrast['paired_questions']} paired questions / {contrast['family_count']} families.")
    lines += ['', 'Questions within a scenario family are correlated. Per-family differences and query-type results are in summary.json; '
              'these comparisons are descriptive, with no significance or generalization claim.', '',
              'The new condition is a hybrid: Qwen selects literal predicates; a deterministic resolver supplies temporal statuses; '
              'values and source links are copied from selected facts. Missing-evidence flags are composed from those decisions, '
              'and an empty table produces unknown without a model call. This can repair an engineered system while establishing '
              'neither learned temporal inference nor superiority to the separately measured deterministic baseline.', '',
              'The image condition uses a non-diagnostic schematic as a negative control. The unfiltered condition stresses identity selection. '
              'Neither establishes visual reasoning, moving-aircraft prediction, longitudinal memory, operational safety or AR utility. '
              'Pairwise receipt comparisons cache repeated numeric pairs. Variable forward-pass counts, input lengths and output formats mean this is not a matched-compute causal comparison. '
              'Legacy forward passes are inferred from greedy generated-token count; predicate passes are directly counted. '
              'Model loading is excluded from call latency; failed/interrupted calls may lack compute counts.', '',
              'Every legacy raw response, selector decision trace, error and guard result remains in fresh-runs.jsonl. '
              'attempts.jsonl prevents retries, including interrupted calls. Source snapshots and protocol.json fix the method; '
              'this report aggregates saved scores without rescoring. error-catalog.json preserves every non-exact result.', '',
              'Broader research claims require independently reviewed data, more independent scenario families, '
              'visually necessary tasks, genuine temporal inference beyond supplied status labels, and user evaluation on Android.', '']
    (OUT / 'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(dict(complete=complete, records=len(rows), exact={c: s['exact'] for c, s in by_condition.items()}), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-partial', action='store_true')
    report(parser.parse_args().allow_partial)
