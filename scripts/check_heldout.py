"""Check a held-out conversation set without showing its questions or labels.

    python scripts/check_heldout.py --families ~/heldout/families.json --scenarios ~/heldout/scenarios
    python scripts/check_heldout.py ... --record    # after the author finishes: commit the hashes

The set (families.json, scenarios/*.json and renders.json) lives outside the
repository. This checks every scenario with the backend's rules (event times,
supersession, rotations) and the structural rules Unity's Scenario.Validate
enforces, then checks the labels against their scenarios
(backend/conversation/scoring.validate_families) and the image list against
renders.json. It prints only error locations and counts. --record writes
config/heldout-<set>.json (the families file's "set": m1, m2 or final), the
hashes a formal run checks (backend/conversation/guards.load_heldout_set).

The Unity render (HeldoutRender.Run, see docs/REVIEW_DISPOSITIONS.md) runs
Scenario.Validate itself, so a scenario must also load there.
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.evidence import FIELDS, validate_scenario
from backend.conversation.guards import HELDOUT_SETS, heldout_record, heldout_record_path, outside_repo
from backend.conversation.identity import validate_rotations
from backend.conversation.observations import VISUAL_KINDS
from backend.conversation.scoring import turns_of, validate_families

MAX_AIRCRAFT = 4  # Scenario.MaxAircraft
TYPES = ('rotation-correction', 'ambiguous-reference', 'late-report', 'no-change', 'missing-evidence',
         'conflicting-reports', 'superseded-report', 'visual-observation', 'scene-change', 'ar-pointing',
         'tracking-interruption', 'viewpoint')  # or other:<name>; docs/AR_SCOPE.md


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_structure(data):
    """The Unity-side rules the backend validators don't cover (Scenario.Validate, ValidateProps)."""
    if not (number(data.get('duration')) and data['duration'] > 0 and number(data.get('targetWidth'))
            and data['targetWidth'] > 0):
        raise ValueError('needs positive duration and targetWidth')
    aircraft = data.get('aircraft') or []
    if not 2 <= len(aircraft) <= MAX_AIRCRAFT:
        raise ValueError(f'needs two to {MAX_AIRCRAFT} aircraft')
    if data.get('clockWhileUntracked', 'pauses') not in ('pauses', 'runs'):
        raise ValueError('clockWhileUntracked must be "pauses" or "runs"')
    if data.get('livery', 'indexed') not in ('indexed', 'uniform'):
        raise ValueError('livery must be "indexed" or "uniform"')
    if len({a['id'] for a in aircraft}) != len(aircraft):
        raise ValueError('duplicate aircraft ID')
    for a in aircraft:
        points = a.get('waypoints') or []
        if not points or any(not (number(p.get('t')) and number(p.get('x')) and number(p.get('z'))) for p in points) \
                or any(b['t'] <= p['t'] for p, b in zip(points, points[1:])):
            raise ValueError(f'aircraft {a["id"]}: waypoints need increasing times')
    flights = {(e['aircraftId'], e['flightInstance']) for e in data['events']}
    flights |= {(a['id'], a['flightInstance']) for a in aircraft if a.get('flightInstance')}
    flights |= {(a['id'], r['flightInstance']) for a in aircraft for r in a.get('rotations') or []}
    props = data.get('visualProps') or []
    if len({p['id'] for p in props}) != len(props):
        raise ValueError('duplicate visual prop ID')
    for p in props:
        kind, states = VISUAL_KINDS.get(p.get('kind')), p.get('states') or []
        if (p.get('aircraftId'), p.get('flightInstance')) not in flights:
            raise ValueError(f'prop {p["id"]}: must belong to a scenario aircraft and flight')
        if kind is None or not states or states[0].get('t') != 0 \
                or any(s.get('value') not in kind['values'] for s in states) \
                or any(b['t'] <= s['t'] for s, b in zip(states, states[1:])):
            raise ValueError(f'prop {p["id"]}: invalid kind, value or state times (states start at t 0)')
    for o in data.get('occluders') or []:
        if not o.get('id') or not all(number(o.get(k)) and o[k] > 0 for k in ('width', 'depth', 'height')):
            raise ValueError('occluder needs an ID and positive size and height')


def load_set(families_path, scenarios_dir):
    errors, scenarios = [], {}
    for path in sorted(Path(scenarios_dir).glob('*.json')):
        try:
            data = json.loads(path.read_text())
            if not str(data.get('scenarioId', '')).startswith('H-'):
                raise ValueError('scenarioId must start with "H-"')
            if data['scenarioId'] in scenarios:
                raise ValueError('duplicate scenarioId')
            check_structure(data)
            validate_scenario(data)
            validate_rotations(data)
            scenarios[data['scenarioId']] = data
        except (ValueError, KeyError, TypeError) as error:
            errors.append(f'{path.name}: {error}')
    families = json.loads(Path(families_path).read_text())
    return families, scenarios, errors


def rendered_images(renders, base):
    """Image names the Unity render writes for renders.json: heldout/<scenarioId>-<time>s.png."""
    names, errors = set(), []
    for r in renders:
        path = Path(base) / r['scenarioFile']
        if not path.exists():
            errors.append(f'renders.json: {r["scenarioFile"]} not found')
            continue
        scenario_id = json.loads(path.read_text()).get('scenarioId')
        names |= {f'heldout/{scenario_id}-{t:g}s.png' for t in r['times']}
    return names, errors


def check_families(families, scenarios, rendered):
    errors = []
    if families.get('split') != 'heldout' or not families.get('version') or families.get('set') not in HELDOUT_SETS:
        errors.append(f'families.json needs "split": "heldout", a version and "set": one of {", ".join(HELDOUT_SETS)}')
    name = families.get('set')
    for family in families.get('families', []):
        kind = family.get('type', '')
        if kind not in TYPES and not (kind.startswith('other:') and len(kind) > 6):
            errors.append(f'{family.get("id")}: type must be one of docs/AR_SCOPE.md\'s types or other:<name>')
        for index, turn in turns_of(family):
            where = f'{family.get("id")} turn {index + 1}'
            expect, data = turn.get('expect', {}), scenarios.get(turn.get('scenario'))
            if name in ('m1', 'final') and not turn.get('textOnly'):
                errors.append(f'{where}: every {name} turn needs textOnly')
            if name == 'm1' and turn.get('image'):
                errors.append(f'{where}: the m1 set has no images')
            if name == 'm2' and not turn.get('image'):
                errors.append(f'{where}: every m2 turn needs an image')
            if turn.get('lastSeen') is not None and data is not None and data.get('clockWhileUntracked') != 'runs':
                errors.append(f'{where}: a lastSeen turn needs a scenario with "clockWhileUntracked": "runs"')
            if data is not None and not (number(turn.get('cutoff')) and 0 <= turn['cutoff'] <= data['duration']):
                errors.append(f'{where}: cutoff outside its scenario')
            if not set(expect.get('unknowns', [])) <= set(FIELDS):
                errors.append(f'{where}: unknowns must be properties from backend/evidence.FIELDS')
            for kind, value in (expect.get('observations') or {}).items():
                if kind not in VISUAL_KINDS or (value is not None and value not in VISUAL_KINDS[kind]['values']):
                    errors.append(f'{where}: invalid observation label')
            if expect.get('observations') and not turn.get('image'):
                errors.append(f'{where}: observation labels need an image')
            if turn.get('image'):
                expected = f'heldout/{turn.get("scenario")}-{turn["cutoff"]:g}s.png'
                if turn['image'] != expected:
                    errors.append(f'{where}: image must be named {expected}')
                elif turn['image'] not in rendered:
                    errors.append(f'{where}: image is not listed in renders.json')
    try:
        validate_families(families, scenarios)
    except (ValueError, KeyError) as error:
        errors.append(f'labels: {error}')
    return errors


def counts(families):
    turns = [(family, turn) for family in families['families'] for _, turn in turns_of(family)]
    per_family = Counter(len(family['turns']) for family in families['families'])
    statuses = Counter('/'.join(sorted(turn['expect']['status'])) for _, turn in turns)
    criteria = Counter(key for _, turn in turns for key in turn['expect'] if key != 'status')
    types = Counter(family.get('type') for family in families['families'])
    images = sum(1 for _, turn in turns if turn.get('image'))
    return dict(families=len(families['families']), turns=len(turns), turnsPerFamily=dict(sorted(per_family.items())),
                imageTurns=images, imageShare=round(images / len(turns), 3) if turns else 0,
                scenarios=len({turn['scenario'] for _, turn in turns}), types=dict(types), statuses=dict(statuses),
                textOnlyTurns=sum(1 for _, turn in turns if turn.get('textOnly')),
                lastSeenTurns=sum(1 for _, turn in turns if turn.get('lastSeen') is not None),
                labelledCriteria=dict(criteria))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--families', required=True)
    parser.add_argument('--scenarios', required=True)
    parser.add_argument('--renders', help='Default: renders.json next to the families file')
    parser.add_argument('--record', action='store_true', help='Write config/heldout-<set>.json when the set passes')
    args = parser.parse_args()
    errors = [f'{name} must be outside the repository' for name, path in
              (('--families', args.families), ('--scenarios', args.scenarios)) if not outside_repo(path)]
    families, scenarios, scenario_errors = load_set(args.families, args.scenarios)
    renders_path = Path(args.renders or Path(args.families).with_name('renders.json'))
    renders = json.loads(renders_path.read_text()) if renders_path.exists() else []
    if not renders_path.exists():
        errors.append(f'missing {renders_path.name}')
    rendered, render_errors = rendered_images(renders, renders_path.parent)
    errors += scenario_errors + render_errors + check_families(families, scenarios, rendered)
    for error in errors:
        print('error:', error)
    print(json.dumps(counts(families) if families.get('families') else {}, indent=1))
    if errors:
        raise SystemExit(f'{len(errors)} error(s).')
    print('Held-out set passes.')
    if args.record:
        path = heldout_record_path(families)
        path.write_text(json.dumps(heldout_record(args.families, args.scenarios), indent=2) + '\n')
        print(f'Wrote {path.relative_to(ROOT)}; commit it before the formal run.')


if __name__ == '__main__':
    main()
