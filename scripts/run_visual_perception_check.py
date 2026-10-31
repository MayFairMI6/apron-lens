"""Perception-only visual check: one rendered view and one question, no reports.

Asks a local model whether the aircraft at a stand has a connected fuel vehicle
and an open cargo hatch, with and without the prompt's prop legend
(VISUAL_KINDS appearance), and scores the answers against authored ground
truth. Development scenarios only (visual_dev_01 at 24/29/31 s, visual_dev_02
at 20/27/33 s), using the renders from
VisualCaptureVerification.SaveObservationSamples. visual_truth is an
evaluation-only module: it is read here for scoring, never on the request path.
Results are development observations, written to work/visual-diag/.

    python scripts/run_visual_perception_check.py --profile apronlens-v2-mps --model qwen3-vl-8b
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modelaccess.contract import ImageInput, Request, Settings
from modelaccess.local_backbone import LocalBackboneAdapter
from modelaccess.repair import parse_json_output
from backend.conversation import visual_truth
from backend.conversation.server import load_scenarios
from backend.conversation.observations import VISUAL_KINDS

scenarios = load_scenarios()
dev01, dev02 = scenarios['V1-visual-observation-dev-01'], scenarios['V2-uniform-livery-dev-02']
# (label, scenario, time, stand, aircraft, flight)
QUESTIONS = [('dev01', dev01, t, 'B', 'A2', 'F2-R1') for t in (24, 29, 31)] + \
            [('dev02', dev02, t, s, a, f) for t in (20, 27, 33) for s, a, f in (('A', 'A1', 'F1-R1'), ('B', 'A2', 'F2-R1'))]
DESCRIBED = (' How they look in this rendering: '
             + '; '.join(f'{k} ({v["appearance"]})' for k, v in VISUAL_KINDS.items()) + '.')


def prompt(stand, described):
    return ('This is an overhead view of a FICTIONAL airfield model; the stands are labelled on the board. '
            f'Look only at the aircraft parked at STAND {stand}. Using only what you can see in the image, is a fuel '
            'vehicle connected to it, and is its cargo hatch open?' + (DESCRIBED if described else '') +
            ' Return JSON only: {"fuel_vehicle":"connected|departed|cannot_tell",'
            '"cargo_door":"open|closed|cannot_tell"}')


def expected(data, aircraft, flight, kind, t):
    truth = visual_truth.prop_value(data, aircraft, flight, kind, t)
    if truth is not None:
        return truth, True
    return ('departed' if kind == 'fuel_vehicle' else 'closed'), False  # no such prop at this aircraft


parser = argparse.ArgumentParser()
parser.add_argument('--model', default='qwen3-vl-8b')
parser.add_argument('--profile', required=True, help='Runtime profile from backbone/models.json')
args = parser.parse_args()
adapter = LocalBackboneAdapter(args.model, profile=args.profile)
adapter.load()
rows = []
for width in (672,):
    for described in (False, True):
        for n, (label, data, t, stand, aircraft, flight) in enumerate(QUESTIONS):
            image = (ROOT / ('work/visual-observation-' + ('' if label == 'dev01' else 'dev02-') + f'{t}s.png')).read_bytes()
            settings = Settings(model=adapter.served_model, max_output_tokens=64, image_max_side=width)
            reply = adapter.generate(Request(f'diag-{width}-{int(described)}-{n}', (('user', prompt(stand, described)),),
                                             settings, (ImageInput(image, 'image/png', t),)))
            answer, _, _, error = parse_json_output(reply.text) if reply.ok else (None, False, (), reply.error)
            for kind in ('fuel_vehicle', 'cargo_door'):
                truth, has_prop = expected(data, aircraft, flight, kind, t)
                said = answer.get(kind) if isinstance(answer, dict) else None
                rows.append(dict(width=width, described=described, scene=label, time=t, stand=stand, kind=kind,
                                 truth=truth, propAuthored=has_prop, said=said, correct=said == truth,
                                 inputTokens=reply.usage.input_tokens, latency=round(reply.latency_seconds, 1),
                                 raw=reply.text, error=error))
            print(f'{width} {"described" if described else "plain    "} {label} t={t} stand {stand}: '
                  + ', '.join(f'{r["kind"]}={r["said"]}({"ok" if r["correct"] else "X:" + r["truth"]})' for r in rows[-2:]),
                  flush=True)

out = ROOT / 'work/visual-diag' / f'perception-{adapter.model_name}-{time.strftime("%Y%m%dT%H%M%S")}.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(model=adapter.served_model, rows=rows), indent=1))
print('\nscore (correct / questions) by width and prompt:')
for width in (672,):
    for described in (False, True):
        sel = [r for r in rows if r['width'] == width and r['described'] == described]
        authored = [r for r in sel if r['propAuthored']]
        print(f'  {width} {"described" if described else "plain    "}: all {sum(r["correct"] for r in sel)}/{len(sel)}, '
              f'authored props {sum(r["correct"] for r in authored)}/{len(authored)}, '
              f'cannot_tell {sum(r["said"] == "cannot_tell" for r in sel)}, '
              f'median input tokens {sorted(r["inputTokens"] or 0 for r in sel)[len(sel)//2]}')
print('->', out.relative_to(ROOT))
