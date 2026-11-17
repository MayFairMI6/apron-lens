"""PROCEDURAL: camera observations for the recorded Stand B session, from the qualified detector.

Runs the selected detector (fit report + weights) over each session frame and
writes one observation per frame per arm (`rgb`, `rgb_depth`) with
`backend.camera_evidence`. Only RGB, depth, pose and tracking state are used
for the observations. Label boxes are used afterwards, separately, to report
how often the observations were right; that check never feeds back.

    python -m experiments.apron_detector.session_observations work/detector-v2/fit-v3 \
        outputs/checkpoint2-run/detector-v3-heldout.json work/detector-v2/session-render/session \
        outputs/checkpoint2-run/stand-b-session-observations.json
"""
import argparse
import glob
import json
from pathlib import Path

import torch

from backend.camera_evidence import ARMS, load_capture, observation
from experiments.apron_detector import train_v2 as detector


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument('fit', type=Path)
    cli.add_argument('qualification', type=Path)
    cli.add_argument('session', type=Path)
    cli.add_argument('output', type=Path)
    args = cli.parse_args()
    report = json.loads((args.fit / 'fit-report.json').read_text())
    qualification = json.loads(args.qualification.read_text())
    candidate = report['selected']
    chosen = report['candidates'][candidate]
    if qualification['candidate'] != candidate or qualification['weightsSha256'] != chosen['weightsSha256']:
        raise SystemExit('The qualification record is for different weights')
    qualified = bool(qualification.get('qualifiedAsCameraEvidence'))
    weights = args.fit / f'candidate-{candidate}.pt'
    if detector.sha(weights) != chosen['weightsSha256']:
        raise SystemExit('Weights changed after qualification')
    device = detector.device_for(candidate)
    model = detector.build(candidate)
    model.load_state_dict(torch.load(weights, map_location='cpu'))
    model.to(device)
    name = f'stand-b-detector-v3-{candidate}'
    records, check = [], dict(frames=0, agree=0, falsePresent=0, missedPresent=0)
    for meta_path in sorted(glob.glob(str(args.session / '*.json'))):
        stem = meta_path[:-5]
        meta, depth = load_capture(stem)
        boxes, scores = detector.predict(candidate, model, detector.load(Path(stem + '.png')), device)
        detections = [(box.tolist(), float(score)) for box, score in zip(boxes, scores)]
        capture = f"cam-{Path(stem).name}"
        for arm in ARMS:
            records.append(observation(meta, detections, arm, run_id='SESSION', capture_id=f'{capture}-{arm}',
                                       detector=name, threshold=chosen['threshold'], qualified=qualified,
                                       depth=depth if arm == 'rgb_depth' else None))
        # Scoring only (not part of the observations): visible-pixel truth from the export.
        truth = any(b['visiblePixels'] >= 150 for b in meta.get('visibleBoxes', []))
        said = any(score >= chosen['threshold'] for _, score in detections)
        check['frames'] += 1
        check['agree'] += said == truth
        check['falsePresent'] += said and not truth
        check['missedPresent'] += truth and not said
    body = dict(version='stand-b-session-v1', detector=name, qualified=qualified, threshold=chosen['threshold'],
                note='Observations are lower authority than reports and cannot establish a release. runId "SESSION" '
                     'is rebound to the replay run when loaded.',
                presenceCheckAgainstLabels=check, observations=records)
    args.output.write_text(json.dumps(body, indent=1) + '\n')
    print(name, 'qualified' if qualified else 'NOT qualified', check)


if __name__ == '__main__':
    main()
