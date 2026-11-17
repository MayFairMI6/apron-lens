"""Print what the driver generates for one exercise and seed: identity hash, reports, cues.

Model-free and read-only. Two machines that print the same hash have the same
authored world (aircraft, motion, reports, reservations) for that exercise and seed.

    .venv-candidates/bin/python -m scripts.describe_scenario fleet_a380_go_around --seed 17
    .venv-candidates/bin/python -m scripts.describe_scenario --all
"""
import argparse
import hashlib
import json

from backend.lessons import EXERCISES, M2_LESSONS
from backend.training_session import DEMONSTRATION_EXERCISES, TrainingSession

LESSONS = EXERCISES + M2_LESSONS


def world(exercise, seed):
    session = TrainingSession(seed, exercise, 'lesson' if exercise in LESSONS else 'continuous', clock=lambda: 0.)
    scenario = {k: v for k, v in session.scenario.items() if k != 'scenarioId'}
    digest = hashlib.sha256(json.dumps(scenario, sort_keys=True).encode()).hexdigest()
    return session, digest


def clock(seconds):
    return f'{int(seconds // 60):02d}:{seconds % 60:04.1f}'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('exercise', nargs='?', choices=LESSONS + DEMONSTRATION_EXERCISES)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--all', action='store_true', help='one line per exercise: name, kind, world hash')
    parser.add_argument('--json', action='store_true', help='machine-readable output for one exercise')
    args = parser.parse_args()
    if args.all:
        for exercise in LESSONS + DEMONSTRATION_EXERCISES:
            session, digest = world(exercise, args.seed)
            kind = 'lesson' if exercise in LESSONS else 'incident'
            print(f'{exercise:34s} {kind:9s} seed={args.seed} reports={len(session.scenario["events"]):3d} sha256={digest}')
        return
    if not args.exercise:
        parser.error('name an exercise or pass --all')
    session, digest = world(args.exercise, args.seed)
    scenario = session.scenario
    cues = session.probes + scenario.get('demoQuestions', [])
    if args.json:
        print(json.dumps(dict(exercise=args.exercise, seed=args.seed, title=session.title, sha256=digest,
                              aircraft=[dict(id=a['id'], flight=a['flightInstance'], type=a.get('aircraftType', ''),
                                             hidden=a.get('hidden', False)) for a in scenario['aircraft']],
                              reports=scenario['events'], cues=cues, reservations=session.reservations), indent=1))
        return
    print(f'{args.exercise} · seed {args.seed} · {session.title}')
    print(f'world sha256 {digest}')
    print('aircraft: ' + ', '.join(f"{a['id']}={a['flightInstance']}" + (f" ({a['aircraftType']})" if a.get('aircraftType') else '')
                                   + (' [hidden]' if a.get('hidden') else '') for a in scenario['aircraft']))
    print('\nreports (happened → received · source · flight)')
    for e in scenario['events']:
        print(f"  {clock(e['eventTime'])} → {clock(e['receiptTime'])} · {e['source']} · {e['flightInstance']} · {e['id']}: {e['message']}")
    print('\nquestions (source time · aircraft)')
    for cue in sorted(cues, key=lambda c: c['at']):
        print(f"  {clock(cue['at'])} · {cue.get('aircraftId', session.target)} · {cue.get('assistantQuestion') or cue.get('question')}")


if __name__ == '__main__':
    main()
