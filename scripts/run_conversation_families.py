"""Run the conversation families through the /conversation turn handler and score them.

Families and labels: data/conversation_dev/families.json (development split) or
--families PATH. Each family runs in its own session per scenario, as the
server would. --images off removes every evidence image (the without-image
condition); --baseline runs the deterministic baseline from
backend/conversation/scoring.py through the same turn handler and validator.

Results (with per-turn scores and a per-family summary) are written to
work/conversation-families/ or --output, never overwritten. Development
results are observations, not evaluation evidence.

    python scripts/run_conversation_families.py --profile apronlens-v2-mps --model qwen2.5-vl-3b
    python scripts/run_conversation_families.py --baseline
    python scripts/run_conversation_families.py --provider openai --model gpt-6-luna --estimate-only
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter
from backend.conversation import freeze
from backend.conversation.context import receipt_times
from backend.conversation.hosted import add_arguments, prepare, provenance, result_path
from backend.conversation.scoring import (SCORING_VERSION, baseline_proposal, load_families, required_images,
                                          score_turn, summarize, turns_of, validate_families)
from backend.conversation.server import load_scenarios
from backend.conversation.state import SessionState
from backend.conversation.turns import PROMPT_VERSION, REFERENT_RULE_VERSION, run_turn

WORK = ROOT / 'work'
DEFAULT_FAMILIES = ROOT / 'data/conversation_dev/families.json'


def run_families(families, scenarios, adapter, settings, images=True, baseline=False, report=print):
    rows, sessions = [], {}
    for family in families['families']:
        for index, turn in turns_of(family):
            data = scenarios[turn['scenario']]
            session = sessions.setdefault((family['id'], turn['scenario']),
                                          SessionState(f'{family["id"]}:{turn["scenario"]}'))
            selected = turn['selected']
            request = dict(requestId=f'{family["id"]}-{index + 1}', turnId=f'{family["id"]}-{index + 1}',
                           expectedRevision=session.revision, aircraftId=selected['aircraftId'],
                           flightInstance=selected['flightInstance'], cutoff=turn['cutoff'], question=turn['question'])
            image = turn.get('image')
            image_used = bool(images and image and (WORK / image).exists())
            image_sha256 = None
            if image_used:
                image_bytes = (WORK / image).read_bytes()
                image_sha256 = hashlib.sha256(image_bytes).hexdigest()  # renders are not frozen; record each one
                request.update(image=image_bytes, imageMediaType='image/png', imageCaptureTime=turn['cutoff'])
            turn_adapter = adapter
            if baseline:
                receipts = receipt_times(data)
                referent = session.current_referent(turn['cutoff'], receipts)
                if referent is None or referent[0] != selected['aircraftId']:
                    referent = (selected['aircraftId'], selected['flightInstance'])
                previous = session.previous_turn_for(*referent, turn['cutoff'], receipts)
                turn_adapter = MockAdapter([json.dumps(baseline_proposal(
                    data, turn['cutoff'], referent, previous.cutoff if previous else None))])
            result = run_turn(session, data, request, turn_adapter, settings)
            scores = score_turn(turn['expect'], result)
            rows.append(dict(family=family['id'], turn=index + 1, scenario=turn['scenario'], cutoff=turn['cutoff'],
                             selected=selected, question=turn['question'], image=image, imageUsed=image_used,
                             imageSha256=image_sha256,
                             accepted=result['accepted'], errors=result['errors'], referent=result['referent'],
                             referentSource=result.get('referentSource'), currentReferent=result['currentReferent'],
                             display=result['display'], latencySeconds=result['latencySeconds'],
                             inputTokens=result['inputTokens'], outputTokens=result['outputTokens'],
                             rawModelOutput=result['rawModelOutput'], scores=scores))
            report(f"{family['id']} turn {index + 1}: {'correct' if scores['correct'] else 'wrong'}"
                   f" ({'accepted' if result['accepted'] else 'withheld ' + ','.join(result['errors'])})")
    return rows


def print_summary(summary, report=print):
    report(f"{'family':<28}{'correct':>9}  " + '  '.join(f'{c:>12}' for c in ('referent', 'cites', 'changed', 'unknowns', 'observations')))
    for key, s in sorted(summary.items(), key=lambda item: item[0] == 'all'):  # 'all' last
        cells = '  '.join(f'{s[c][0]:>5}/{s[c][1]:<6}' if s[c][1] else f'{"-":>12}'
                          for c in ('referent', 'cites', 'changed', 'unknowns', 'observations'))
        report(f'{key:<28}{s["correct"]:>4}/{s["turns"]:<4}  {cells}')


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser, 'qwen2.5-vl-3b')
    parser.add_argument('--baseline', action='store_true', help='Run the deterministic baseline instead of a model')
    parser.add_argument('--families', default=str(DEFAULT_FAMILIES))
    parser.add_argument('--images', choices=('on', 'off'), default='on')
    parser.add_argument('--output', help='Result file; default work/conversation-families/<model>-<time>.json')
    parser.add_argument('--max-output-tokens', type=int,
                        help='Default 512 locally; 8000 hosted, where thinking counts against the cap')
    args = parser.parse_args()
    args.max_output_tokens = args.max_output_tokens or (512 if args.provider == 'local' else 8000)
    scenarios = load_scenarios()
    families = validate_families(load_families(args.families), scenarios)
    if families['split'] != 'development':
        freeze.require_approved()  # a formal run uses only an approved, unchanged method
    images = args.images == 'on'
    missing = [name for name in required_images(families) if not (WORK / name).exists()] if images else []
    if missing:  # an images-on run without its images would silently become the images-off condition
        raise SystemExit(f'Missing evidence images in work/: {", ".join(missing)}. Render them with Unity '
                         '(VisualCaptureVerification.SaveObservationSamples) or copy them from the Mac, '
                         'or run the without-image condition explicitly with --images off.')
    stem = ('baseline' if args.baseline else args.model) + ('' if images else '-noimages')
    path = result_path(args.output, WORK / 'conversation-families', stem)  # checked before any model time is spent

    def settings_for(model):
        return Settings(model=model, max_output_tokens=args.max_output_tokens, image_max_side=672,
                        reasoning_effort=args.reasoning_effort)

    if args.baseline:
        adapter, model = None, 'deterministic-baseline'
    else:
        adapter, model = prepare(args.provider, args.model, args.profile,
                                 lambda a, m: run_families(families, scenarios, a, settings_for(m), images, report=lambda line: None),
                                 estimate_only=args.estimate_only, confirm_spend=args.confirm_spend,
                                 max_spend=args.max_spend, session_id=f'families-{time.strftime("%Y%m%dT%H%M%S")}')
        if adapter is None:
            return
    rows = run_families(families, scenarios, adapter, settings_for(model), images, baseline=args.baseline,
                        report=lambda line: print(line, flush=True))
    summary = summarize(rows)
    inner = getattr(adapter, 'adapter', adapter)
    path.write_text(json.dumps(dict(
        model=model, provider='baseline' if args.baseline else args.provider, runtime=getattr(inner, 'runtime', None),
        runtimeProfile=args.profile, images=args.images, familiesVersion=families['version'], split=families['split'],
        promptVersion=PROMPT_VERSION, referentRule=REFERENT_RULE_VERSION, scoringVersion=SCORING_VERSION,
        freeze=freeze.status(),
        note='Development run; not evaluation evidence.' if families['split'] == 'development' else '',
        **provenance(), summary=summary, turns=rows), indent=1))
    print_summary(summary)
    print('->', path)


if __name__ == '__main__':
    main()
