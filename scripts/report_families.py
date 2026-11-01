"""Summarise conversation-family result files for a milestone report, without questions or labels.

    python scripts/report_families.py RESULT.json [RESULT.json ...] [--baseline-label baseline] [--seed 7]

Each result file is one system under one condition (run_conversation_families.py).
Prints Markdown:
- accuracy per system and condition, with a Wilson 95% interval;
- accuracy by family type (from the families file the run used, when given with --families);
- paired differences between conditions of the same system and between systems in the same
  condition, on the turns both ran, with a 95% interval from a bootstrap over families (turns
  within a family are correlated, so families, not turns, are resampled);
- criterion pass rates and withheld vs accepted-but-wrong counts.
Only counts, rates and family IDs are printed, so the output can go into a report in the repository.
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from size_heldout import wilson  # noqa: E402

CRITERIA = ('referent', 'cites', 'changed', 'unknowns', 'observations')


def factors_off(result):
    return frozenset(name for name, on in (('images', result.get('images') == 'on'),
                                           ('selection', result.get('selection', 'on') == 'on'),
                                           ('tracking', result.get('tracking', 'on') == 'on')) if not on)


def label(result, shared=frozenset()):
    model = result['model'].split('/')[-1].split('@')[0]
    off = sorted(factors_off(result) - shared)
    return model, 'full' if not off else 'no ' + ', no '.join(off)


def correct_by_turn(result):
    return {(t['family'], t['turn']): bool(t['scores']['correct']) for t in result['turns']}


def bootstrap_difference(a, b, draws=2000, seed=7):
    """Mean of a - b over shared turns, with a 95% interval resampling families."""
    shared = sorted(set(a) & set(b))
    families = defaultdict(list)
    for key in shared:
        families[key[0]].append(a[key] - b[key])
    names = sorted(families)
    point = sum(sum(v) for v in families.values()) / len(shared)
    rng, means = random.Random(seed), []
    for _ in range(draws):
        sample = [rng.choice(names) for _ in names]
        diffs = [d for name in sample for d in families[name]]
        means.append(sum(diffs) / len(diffs))
    means.sort()
    return point, means[int(.025 * draws)], means[int(.975 * draws) - 1], len(shared), len(names)


def pct(x):
    return f'{100 * x:.0f}%'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('results', nargs='+')
    parser.add_argument('--families', help='The families file the runs used, for the by-type table')
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    results = [json.loads(Path(path).read_text()) for path in args.results]
    shared = frozenset.intersection(*(factors_off(r) for r in results))  # e.g. images off in every M1 run
    runs, off = {}, {}
    for result in results:
        runs[label(result, shared)] = result
        off[label(result, shared)] = factors_off(result)
    if shared:
        print(f'Every run here has {", ".join(sorted(shared))} off; "full" means the other AR factors are on.\n')
    types = {}
    if args.families:
        types = {f['id']: f.get('type', '?') for f in json.loads(Path(args.families).read_text())['families']}

    print('| System | Condition | Correct | 95% interval | Withheld | Accepted but wrong |')
    print('|---|---|---|---|---|---|')
    for (model, condition), result in runs.items():
        turns = result['turns']
        n, c = len(turns), sum(t['scores']['correct'] for t in turns)
        low, high = wilson(c, n)
        withheld = sum(1 for t in turns if not t['accepted'])
        wrong = sum(1 for t in turns if t['accepted'] and not t['scores']['correct'])
        print(f'| {model} | {condition} | {c}/{n} ({pct(c / n)}) | {pct(low)}–{pct(high)} | {withheld} | {wrong} |')

    if types:
        names = sorted(set(types.values()))
        print('\n| System | Condition | ' + ' | '.join(names) + ' |')
        print('|---|---|' + '---|' * len(names))
        for (model, condition), result in runs.items():
            cells = []
            for name in names:
                turns = [t for t in result['turns'] if types.get(t['family']) == name]
                cells.append(f'{sum(t["scores"]["correct"] for t in turns)}/{len(turns)}' if turns else '–')
            print(f'| {model} | {condition} | ' + ' | '.join(cells) + ' |')

    print('\nPaired differences (first minus second; 95% interval from a family bootstrap):\n')
    print('| First | Second | Difference | 95% interval | Turns | Families |')
    print('|---|---|---|---|---|---|')
    keys = list(runs)
    for i, first in enumerate(keys):
        for second in keys[i + 1:]:
            same_model, same_condition = first[0] == second[0], off[first] == off[second]
            if not ((same_model and len(off[first] ^ off[second]) == 1) or (same_condition and not same_model)):
                continue  # one factor at a time
            d, low, high, n, families = bootstrap_difference(correct_by_turn(runs[first]), correct_by_turn(runs[second]),
                                                             seed=args.seed)
            print(f'| {first[0]} ({first[1]}) | {second[0]} ({second[1]}) | {100 * d:+.0f} pp | '
                  f'{100 * low:+.0f} to {100 * high:+.0f} pp | {n} | {families} |')

    print('\nCriterion pass rates (passed / labelled):\n')
    print('| System | Condition | ' + ' | '.join(CRITERIA) + ' |')
    print('|---|---|' + '---|' * len(CRITERIA))
    for (model, condition), result in runs.items():
        cells = []
        for criterion in CRITERIA:
            scored = [t['scores'][criterion] for t in result['turns'] if t['scores'][criterion] is not None]
            cells.append(f'{sum(scored)}/{len(scored)}' if scored else '–')
        print(f'| {model} | {condition} | ' + ' | '.join(cells) + ' |')


if __name__ == '__main__':
    main()
