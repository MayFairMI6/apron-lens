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
    python scripts/run_visual_perception_check.py --provider openai --model gpt-6.1-terra --estimate-only
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modelaccess.contract import ImageInput, Request, Settings
from backend.conversation.hosted import add_arguments, prepare, provenance, result_path
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


def check(adapter, model, max_output_tokens, effort, report=print):
    rows = []
    for width in (672,):
        for described in (False, True):
            for n, (label, data, t, stand, aircraft, flight) in enumerate(QUESTIONS):
                image = (ROOT / ('work/visual-observation-' + ('' if label == 'dev01' else 'dev02-') + f'{t}s.png')).read_bytes()
                settings = Settings(model=model, max_output_tokens=max_output_tokens, image_max_side=width,
                                    reasoning_effort=effort)
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
                report(f'{width} {"described" if described else "plain    "} {label} t={t} stand {stand}: '
                       + ', '.join(f'{r["kind"]}={r["said"]}({"ok" if r["correct"] else "X:" + r["truth"]})' for r in rows[-2:]))
    return rows


parser = argparse.ArgumentParser()
add_arguments(parser, 'qwen3-vl-8b')
parser.add_argument('--output', help='Result file; default work/visual-diag/perception-<model>-<time>.json')
parser.add_argument('--max-output-tokens', type=int, help='Default 64 locally; 4000 hosted, where thinking counts against the cap')
args = parser.parse_args()
args.max_output_tokens = args.max_output_tokens or (64 if args.provider == 'local' else 4000)
out = result_path(args.output, ROOT / 'work/visual-diag', f'perception-{args.model}')  # checked before any model time is spent
adapter, model = prepare(args.provider, args.model, args.profile,
                         lambda a, m: check(a, m, args.max_output_tokens, args.reasoning_effort, report=lambda line: None),
                         estimate_only=args.estimate_only, confirm_spend=args.confirm_spend, max_spend=args.max_spend,
                         session_id=f'perception-{time.strftime("%Y%m%dT%H%M%S")}')
if adapter is None:
    sys.exit(0)
rows = check(adapter, model, args.max_output_tokens, args.reasoning_effort, report=lambda line: print(line, flush=True))

inner = getattr(adapter, 'adapter', adapter)
out.write_text(json.dumps(dict(model=model, provider=args.provider, runtime=getattr(inner, 'runtime', None),
                               runtimeProfile=args.profile, reasoningEffort=args.reasoning_effort, **provenance(), rows=rows),
                          indent=1))
print('\nscore (correct / questions) by width and prompt:')
for width in (672,):
    for described in (False, True):
        sel = [r for r in rows if r['width'] == width and r['described'] == described]
        authored = [r for r in sel if r['propAuthored']]
        print(f'  {width} {"described" if described else "plain    "}: all {sum(r["correct"] for r in sel)}/{len(sel)}, '
              f'authored props {sum(r["correct"] for r in authored)}/{len(authored)}, '
              f'cannot_tell {sum(r["said"] == "cannot_tell" for r in sel)}, '
              f'median input tokens {sorted(r["inputTokens"] or 0 for r in sel)[len(sel)//2]}')
print('->', out)
