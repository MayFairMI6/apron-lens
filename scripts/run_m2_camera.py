"""Run M2 camera-evidence families in one arm and score them (docs/course/CAMERA_EVIDENCE_COMPARISON.md).

    python scripts/run_m2_camera.py --baseline --camera rgb_depth --camera-form tracked
    python scripts/run_m2_camera.py --profile apronlens-v2-mps --model qwen3.5-9b --camera off
    python scripts/run_m2_camera.py ... --camera rgb --camera-form frame --retry off

Development families: data/m2_dev/families.json (split "development"). Each
family names its scenario and its recorded camera session (`cameraSession`,
a path relative to the repository, or to --sessions for a held-out set). The
Stand B lesson world is built from backend.stand_clearance_lesson; other
scenarios come from the app's resources, or --scenarios for a held-out set.

Every turn runs as the full AR user (selection on, tracking on) through
backend.conversation.turns_m2.run_turn_m2. Each row keeps both attempts, so
the zero-retry and one-retry conditions are scored from the same run. A
held-out run is refused until freeze 2 is approved: there is no freeze 2 yet.

Results go to work/m2-camera/ (never overwritten). Development results are
observations, not evaluation evidence.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter
from backend.conversation import camera as camera_evidence
from backend.conversation.context import receipt_times
from backend.conversation.hosted import add_arguments, prepare, provenance, result_path
from backend.conversation.scoring import baseline_proposal, load_families, turns_of, validate_families
from backend.conversation.scoring_m2 import (SCORING_M2_VERSION, expect_for, first_attempt_view, score_turn_m2,
                                             summarize_m2)
from backend.conversation.server import load_scenarios
from backend.conversation.state import SessionState
from backend.conversation.turns_m2 import (PROMPT_VERSION, RETRY_POLICY_VERSION, VALIDATOR_M2_VERSION,
                                           allowed_for, camera_config, run_turn_m2)
from backend.stand_clearance_lesson import build_stand_clearance_lesson

WORK = ROOT / 'work'
DEFAULT_FAMILIES = ROOT / 'data/m2_dev/families.json'


def development_scenarios():
    scenarios = load_scenarios()
    world, _, _ = build_stand_clearance_lesson(17)
    scenarios[world['scenarioId']] = world
    return scenarios


def check_m2_labels(families, scenarios, sessions_root):
    """Camera label times must be observations of the family's session at or before the cutoff."""
    for family in families['families']:
        times = {r['sourceTime'] for r in json.loads((sessions_root / family['cameraSession']).read_text())['observations']}
        for index, turn in turns_of(family):
            where = f"{family['id']} turn {index + 1}"
            expects = [turn['expect'], *(turn.get('expectByArm') or {}).values()]
            for expect in expects:
                for field in ('cameraMustCite', 'cameraCiteOnly'):
                    bad = [t for t in expect.get(field, []) if t not in times or t > turn['cutoff']]
                    if bad:
                        raise ValueError(f'{where}: {field} {bad} not observations at or before the cutoff')
            if set(turn.get('expectByArm') or {}) - set(camera_evidence.CAMERA_ARMS):
                raise ValueError(f'{where}: expectByArm names an unknown arm')


def baseline_reply(data, session, turn, selected, camera, cutoff):
    """Selection plus bookkeeping: every received fact of the referent, and its latest listed camera entry."""
    receipts = receipt_times(data)
    referent = session.current_referent(cutoff, receipts)
    if referent is None or referent[0] != selected['aircraftId']:
        referent = (selected['aircraftId'], selected['flightInstance'])
    previous = session.previous_turn_for(*referent, cutoff, receipts)
    proposal = baseline_proposal(data, cutoff, referent, previous.cutoff if previous else None)
    listed = allowed_for(camera, cutoff)(*referent)
    latest = max(listed.values(), key=lambda r: r['sourceTime'], default=None)
    proposal['camera'] = [] if latest is None else [dict(
        captureId=latest['captureId'], finding=camera_evidence.finding(latest), place=camera_evidence.place(latest))]
    return MockAdapter([json.dumps(proposal)])


def run(families, scenarios, sessions_root, arm, form, adapter, settings, baseline=False, retry=True, report=print):
    rows, sessions = [], {}
    for family in families['families']:
        session_path = sessions_root / family['cameraSession']
        for index, turn in turns_of(family):
            data = scenarios[turn['scenario']]
            records = camera_evidence.load_session(session_path, arm, data['scenarioId'])
            camera = camera_config(arm, form, records)
            by_id = {r['captureId']: r for r in records}
            session = sessions.setdefault((family['id'], turn['scenario']),
                                          SessionState(f"{family['id']}:{turn['scenario']}"))
            selected = turn['selected']
            request = dict(requestId=f"{family['id']}-{index + 1}", turnId=f"{family['id']}-{index + 1}",
                           expectedRevision=session.revision, aircraftId=selected['aircraftId'],
                           flightInstance=selected['flightInstance'], cutoff=turn['cutoff'],
                           question=turn['question'], lastSeen=turn.get('lastSeen'),
                           backInView=turn.get('backInView'))
            turn_adapter = baseline_reply(data, session, turn, selected, camera, turn['cutoff']) if baseline else adapter
            result = run_turn_m2(session, data, request, turn_adapter, settings, camera, retry=retry)
            expect = expect_for(turn['expect'], turn.get('expectByArm'), arm)
            scores = score_turn_m2(expect, result, by_id)
            first = score_turn_m2(expect, first_attempt_view(result), by_id)
            rows.append(dict(family=family['id'], type=family.get('type', 'other'), turn=index + 1,
                             scenario=turn['scenario'], cutoff=turn['cutoff'], selected=selected,
                             lastSeen=turn.get('lastSeen'), question=turn['question'], expect=expect,
                             accepted=result['accepted'], errors=result['errors'], referent=result['referent'],
                             display=result['display'], attempts=result['attempts'],
                             firstAttempt=result['firstAttempt'], latencySeconds=result['latencySeconds'],
                             inputTokens=result['inputTokens'], outputTokens=result['outputTokens'],
                             rawModelOutput=result['rawModelOutput'], firstRawModelOutput=result['firstRawModelOutput'],
                             prompt=result['prompt'], scores=scores, firstAttemptScores=first))
            report(f"{family['id']} turn {index + 1}: {'correct' if scores['correct'] else 'wrong'}"
                   f" ({'accepted' if result['accepted'] else 'withheld ' + ','.join(result['errors'])}"
                   f"{', retried' if result['attempts'] == 2 else ''})")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_arguments(parser, 'qwen3.5-9b')
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--families', default=str(DEFAULT_FAMILIES))
    parser.add_argument('--scenarios', help='Held-out scenario folder (refused until freeze 2 is approved)')
    parser.add_argument('--camera', choices=camera_evidence.CAMERA_ARMS, required=True)
    parser.add_argument('--camera-form', choices=camera_evidence.CAMERA_FORMS, default='tracked')
    parser.add_argument('--retry', choices=('on', 'off'), default='on')
    parser.add_argument('--output')
    parser.add_argument('--max-output-tokens', type=int)
    args = parser.parse_args()
    args.max_output_tokens = args.max_output_tokens or (512 if args.provider == 'local' else 8000)
    if args.scenarios is not None:
        raise SystemExit('Freeze 2 is not approved yet; held-out M2 runs are refused.')
    families = load_families(args.families)
    if families['split'] != 'development':
        raise SystemExit('Only development families can run before freeze 2.')
    scenarios = development_scenarios()
    validate_families(families, scenarios)
    check_m2_labels(families, scenarios, ROOT)
    stem = ('baseline' if args.baseline else args.model) + f'-{args.camera}-{args.camera_form}' \
        + ('' if args.retry == 'on' else '-noretry')
    path = result_path(args.output, WORK / 'm2-camera', stem)

    def settings_for(model):
        return Settings(model=model, max_output_tokens=args.max_output_tokens, image_max_side=672,
                        reasoning_effort=args.reasoning_effort)

    retry = args.retry == 'on'
    if args.baseline:
        adapter, model = None, 'deterministic-baseline'
    else:
        adapter, model = prepare(args.provider, args.model, args.profile,
                                 lambda a, m: run(families, scenarios, ROOT, args.camera, args.camera_form, a,
                                                  settings_for(m), retry=retry, report=lambda line: None),
                                 estimate_only=args.estimate_only, confirm_spend=args.confirm_spend,
                                 max_spend=args.max_spend, session_id=f'm2-{time.strftime("%Y%m%dT%H%M%S")}')
        if adapter is None:
            return
    rows = run(families, scenarios, ROOT, args.camera, args.camera_form, adapter, settings_for(model),
               baseline=args.baseline, retry=retry, report=lambda line: print(line, flush=True))
    summary, first = summarize_m2(rows), summarize_m2(rows, 'firstAttemptScores')
    inner = getattr(adapter, 'adapter', adapter)
    path.write_text(json.dumps(dict(
        model=model, provider='baseline' if args.baseline else args.provider, runtime=getattr(inner, 'runtime', None),
        runtimeProfile=args.profile, cameraArm=args.camera, cameraForm=args.camera_form, retry=args.retry,
        familiesVersion=families['version'], split=families['split'], promptVersion=PROMPT_VERSION,
        validatorM2Version=VALIDATOR_M2_VERSION, retryPolicy=RETRY_POLICY_VERSION if retry else 'none',
        cameraDescriptionVersion=camera_evidence.CAMERA_DESCRIPTION_VERSION, scoringVersion=SCORING_M2_VERSION,
        settings=dict(maxOutputTokens=args.max_output_tokens, reasoningEffort=args.reasoning_effort),
        note='Development run; not evaluation evidence.', **provenance(),
        summary=summary, firstAttemptSummary=first, turns=rows), indent=1))
    a = summary['all']
    f = first['all']
    print(f"{model} {args.camera}/{args.camera_form}: correct {a['correct']}/{a['turns']} "
          f"(first attempt {f['correct']}/{f['turns']}); authority {a['authority'][0]}/{a['authority'][1]}")
    print('->', path)


if __name__ == '__main__':
    main()
