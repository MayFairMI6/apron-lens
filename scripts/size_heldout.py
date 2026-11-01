"""Size the held-out set from development family runs (planning only, not evidence).

Reads result files from scripts/run_conversation_families.py and reports, per
system, turn accuracy with a Wilson 95% interval, and the number of held-out
turns needed for a target interval half-width. Turns within a family are
correlated, so the count is inflated by a design effect 1 + (m - 1) * icc for
m turns per family; with only a handful of development families the
intra-family correlation cannot be estimated reliably, so a range is shown.
For a paired comparison of two systems on the same turns, the discordance rate
(turns where exactly one is correct) sets the number of turns needed to detect
a given accuracy difference (McNemar normal approximation, alpha 0.05, power 0.8),
inflated by the same design-effect range because paired differences within a
family are correlated too.

    python scripts/size_heldout.py work/conversation-families/qwen3-vl-8b-*.json work/conversation-families/baseline-*.json
"""
import argparse
import json
import math
from pathlib import Path

Z95, Z80 = 1.959964, 0.841621


def wilson(correct, n):
    if n == 0:
        return (0.0, 1.0)
    p = correct / n
    centre = (p + Z95 ** 2 / (2 * n)) / (1 + Z95 ** 2 / n)
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / (1 + Z95 ** 2 / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def turns_for_half_width(p, half_width, design_effect):
    return math.ceil(Z95 ** 2 * p * (1 - p) / half_width ** 2 * design_effect)


def paired_turns(discordance, difference):
    """Turns needed to detect `difference` given the discordant-pair rate (McNemar, normal approximation)."""
    if discordance < difference:  # equality is feasible: every discordant pair favours one system
        return None
    return math.ceil(((Z95 * math.sqrt(discordance) + Z80 * math.sqrt(discordance - difference ** 2)) / difference) ** 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('results', nargs='+', type=Path)
    parser.add_argument('--turns-per-family', type=float, default=2.0)
    args = parser.parse_args()
    runs = {}
    for path in args.results:
        data = json.loads(path.read_text())
        name = data['model'].split('/')[-1].split('@')[0] + ('' if data['images'] == 'on' else ' (no images)')
        runs[name] = {(t['family'], t['turn']): t['scores']['correct'] for t in data['turns']}
    m = args.turns_per_family
    print(f'{"system":<34}{"correct":>9}{"95% CI":>16}   held-out turns for +/-10 pp (icc 0 / 0.3 / 0.6)')
    for name, turns in runs.items():
        n, k = len(turns), sum(turns.values())
        low, high = wilson(k, n)
        p = min(max(k / n, 0.05), 0.95)
        sizes = [turns_for_half_width(p, 0.10, 1 + (m - 1) * icc) for icc in (0.0, 0.3, 0.6)]
        print(f'{name:<34}{k:>4}/{n:<4}{f"{low:.2f}-{high:.2f}":>16}   ' + ' / '.join(map(str, sizes)))
    names = list(runs)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = set(runs[a]) & set(runs[b])
            if not shared:
                continue
            discordant = sum(runs[a][key] != runs[b][key] for key in shared) / len(shared)
            effects = [1 + (m - 1) * icc for icc in (0.0, 0.3, 0.6)]
            needs = {d: paired_turns(max(discordant, 0.2), d) for d in (0.10, 0.15, 0.20)}
            print(f'paired {a} vs {b}: discordance {discordant:.2f} (planning floor 0.20); turns to detect a gap '
                  '(icc 0 / 0.3 / 0.6): ' + ', '.join(
                      f'{int(d * 100)} pp: ' + ('-' if v is None else ' / '.join(str(math.ceil(v * e)) for e in effects))
                      for d, v in needs.items()))


if __name__ == '__main__':
    main()
