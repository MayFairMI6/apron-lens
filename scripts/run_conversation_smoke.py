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
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]

from modelaccess.contract import Settings
from modelaccess.local_backbone import LocalBackboneAdapter
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='qwen2.5-vl-3b')
    parser.add_argument('--profile', required=True, help='Runtime profile from backbone/models.json')
    parser.add_argument('--max-output-tokens', type=int, default=512)
    args = parser.parse_args()
    adapter = LocalBackboneAdapter(args.model, profile=args.profile)
    settings = Settings(model=adapter.served_model, max_output_tokens=args.max_output_tokens, image_max_side=672)
    adapter.load()
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
        print(f"{name} turn {index}: {'accepted' if result['accepted'] else 'withheld ' + ','.join(result['errors'])}", flush=True)
    out = WORK / 'conversation-smoke'
    out.mkdir(parents=True, exist_ok=True)
    path = out / f'{args.model}-{time.strftime("%Y%m%dT%H%M%S")}.json'
    path.write_text(json.dumps(dict(model=adapter.served_model, runtime=adapter.runtime, promptVersion=PROMPT_VERSION,
                                    note='Development smoke run; not evaluation evidence.', turns=rows), indent=1))
    print(f"accepted {sum(r['accepted'] for r in rows)} of {len(rows)} -> {path.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
