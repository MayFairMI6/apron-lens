"""Development smoke run of the /conversation turn path with a local model.

Development data only:
- the inline two-rotation fixture from tests/test_conversation.py;
- visual_dev_01 and visual_dev_02 with sample renders from
  VisualCaptureVerification.SaveObservationSamples (work/visual-observation-*.png);
- reasoning_v1 development families D01 and D03-D08, with turns generated from
  scenario events. The v1 question and gold file is never read, and neither are
  the H01-H04 families or data/reasoning_v2_fresh.
D02 is skipped: it carries an F2-R0 report but declares no rotations.

Results are development observations, not evaluation evidence. They are written
to work/conversation-smoke/, which is not tracked.

    python scripts/run_conversation_smoke.py --profile apronlens-v2-mps
    python scripts/run_conversation_smoke.py --provider anthropic --model claude-sonnet-5-5 --estimate-only

A hosted run is priced first and makes paid calls only with --confirm-spend,
within --max-spend, through the budget ledger (backend/conversation/hosted.py).
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]

from modelaccess.contract import Settings
from backend.conversation.hosted import add_arguments, prepare
from backend.conversation.context import changed_facts, snapshot
from backend.conversation.server import load_scenarios
from backend.conversation.state import SessionState
from backend.conversation.turns import PROMPT_VERSION, run_turn
from test_conversation import two_rotation_scenario

WORK = ROOT / 'work'


def dialogue():
    """(session, scenario, cutoff, aircraft, flight, question, image file or None) per turn."""
    scenarios = load_scenarios()
    fixture = two_rotation_scenario()
    dev01, dev02 = scenarios['V1-visual-observation-dev-01'], scenarios['V2-uniform-livery-dev-02']
    turns = [
        ('A-correction', fixture, 25, 'A2', 'F2-R1', 'Which stand is this aircraft assigned to?', None),
        ('A-correction', fixture, 25, 'A2', 'F2-R1', 'I mean its next rotation.', None),
        ('A-correction', fixture, 30, 'A2', 'F2-R1', 'Has anything changed for it since you answered?', None),
        ('A-correction', fixture, 30, 'A1', 'F1-R1', 'Which stand is this one on?', None),
        ('B-late-report', fixture, 25, 'A2', 'F2-R1', 'Which stand is this aircraft assigned to?', None),
        ('B-late-report', fixture, 30, 'A2', 'F2-R1', 'Has anything changed since you answered?', None),
        ('C-image-dev01', dev01, 24, 'A2', 'F2-R1', 'Is fuelling finished for this aircraft?', 'visual-observation-24s.png'),
        ('D-image-dev02', dev02, 20, 'A1', 'F1-R1', 'Is the fuel vehicle still at this aircraft?', 'visual-observation-dev02-20s.png'),
    ]
    for path in sorted((ROOT / 'data/reasoning_v1/scenarios').glob('D0*.json')):
        if path.stem == 'D02':
            continue
        data = json.loads(path.read_text())
        flights = {}
        for e in data['events']:
            flights.setdefault((e['aircraftId'], e['flightInstance']), []).append(e)
        (aircraft, flight), events = max(flights.items(), key=lambda kv: len(kv[1]))
        receipts = sorted({e['receiptTime'] for e in events})
        first = receipts[0]
        later = next((r for r in receipts[1:] if changed_facts(snapshot(data, aircraft, flight, first),
                                                                snapshot(data, aircraft, flight, r))), receipts[-1])
        turns += [(f'R2-{path.stem}', data, first, aircraft, flight, 'What is the latest received status for this aircraft?', None),
                  (f'R2-{path.stem}', data, later, aircraft, flight, 'Has anything changed since you answered?', None)]
    return turns


def run_dialogue(adapter, settings, report=print):
    sessions, rows = {}, []
    for index, (name, data, cutoff, aircraft, flight, question, image) in enumerate(dialogue(), 1):
        if image and not (WORK / image).exists():
            print(f'skipping turn {index}: {image} missing; run VisualCaptureVerification.SaveObservationSamples', flush=True)
            continue
        session = sessions.setdefault(name, SessionState(name))
        turn = dict(requestId=f'smoke-{index}', turnId=f'turn-{index}', expectedRevision=session.revision,
                    aircraftId=aircraft, flightInstance=flight, cutoff=cutoff, question=question)
        if image:
            turn.update(image=(WORK / image).read_bytes(), imageMediaType='image/png', imageCaptureTime=cutoff)
        result = run_turn(session, data, turn, adapter, settings)
        rows.append(dict(session=name, turn=index, cutoff=cutoff, selected=f'{aircraft}/{flight}', question=question,
                         image=image, accepted=result['accepted'], errors=result['errors'], referent=result['referent'],
                         currentReferent=result['currentReferent'], changes=result['changes'],
                         rawJsonValid=result['rawJsonValid'], repairs=result['repairs'],
                         latencySeconds=result['latencySeconds'], inputTokens=result['inputTokens'],
                         outputTokens=result['outputTokens'], finishReason=result['finishReason'],
                         answer=result['display']['answer'], rawModelOutput=result['rawModelOutput']))
        report(f"{name} turn {index}: {'accepted' if result['accepted'] else 'withheld ' + ','.join(result['errors'])}")
    return rows


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser, 'qwen2.5-vl-3b')
    parser.add_argument('--max-output-tokens', type=int,
                        help='Default 512 locally; 8000 hosted, where thinking counts against the cap')
    args = parser.parse_args()
    args.max_output_tokens = args.max_output_tokens or (512 if args.provider == 'local' else 8000)

    def settings_for(model):
        return Settings(model=model, max_output_tokens=args.max_output_tokens, image_max_side=672,
                        reasoning_effort=args.reasoning_effort)

    def run(adapter, model):
        return run_dialogue(adapter, settings_for(model), report=lambda line: None)

    adapter, model = prepare(args.provider, args.model, args.profile, run, estimate_only=args.estimate_only,
                             confirm_spend=args.confirm_spend, max_spend=args.max_spend,
                             session_id=f'smoke-{time.strftime("%Y%m%dT%H%M%S")}')
    if adapter is None:
        return
    rows = run_dialogue(adapter, settings_for(model), report=lambda line: print(line, flush=True))
    out = WORK / 'conversation-smoke'
    out.mkdir(parents=True, exist_ok=True)
    path = out / f'{args.model}-{time.strftime("%Y%m%dT%H%M%S")}.json'
    inner = getattr(adapter, 'adapter', adapter)
    path.write_text(json.dumps(dict(model=model, provider=args.provider, runtime=getattr(inner, 'runtime', None),
                                    reasoningEffort=args.reasoning_effort, promptVersion=PROMPT_VERSION,
                                    note='Development smoke run; not evaluation evidence.', turns=rows), indent=1))
    print(f"accepted {sum(r['accepted'] for r in rows)} of {len(rows)} -> {path.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
