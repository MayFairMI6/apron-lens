"""PROCEDURAL: geometry check of the depth arm on development frames only.

Uses the Unity label box (ground truth) solely to test backprojection; the
camera evidence module itself never reads labels. Compares the depth-based
apron position with the tanker's authored route position at the capture time.

    python -m experiments.apron_detector.depth_location_check work/detector-v2/development/validation outputs/checkpoint2-run/detector-v2-depth-location-check.json
"""
import argparse
import glob
import json
import math
import statistics
from pathlib import Path

from backend.camera_evidence import STAND_B_METRES, load_capture, locate, on_stand_b
from experiments.apron_detector.plan import route, tanker_at


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('folder', type=Path)
    cli.add_argument('output', type=Path)
    args = cli.parse_args()
    if 'heldout' in str(args.folder.resolve()).lower():
        raise SystemExit('Development frames only')
    points, rows = route(), []
    for path in sorted(glob.glob(str(args.folder / '*.json'))):
        meta, depth = load_capture(path[:-5])
        for b in meta.get('visibleBoxes', []):
            if b['visiblePixels'] < 150 or min(b['width'], b['height']) < 6:
                continue
            box = (b['xMin'], meta['height'] - (b['yMin'] + b['height']), b['xMin'] + b['width'], meta['height'] - b['yMin'])
            located = locate(meta, depth, box)
            if located is None:
                continue
            tx, tz = tanker_at(points, meta['sourceTime'])
            truth = STAND_B_METRES['xMin'] <= tx <= STAND_B_METRES['xMax'] and STAND_B_METRES['zMin'] <= tz <= STAND_B_METRES['zMax']
            rows.append(dict(frame=Path(path).stem, time=meta['sourceTime'], errorMetres=round(math.hypot(located[0] - tx, located[2] - tz), 2),
                             estimatedOnStandB=on_stand_b(located), trueOnStandB=truth))
    errors = sorted(r['errorMetres'] for r in rows)
    report = dict(folder=str(args.folder), boxes=len(rows), medianErrorMetres=statistics.median(errors),
                  p90ErrorMetres=errors[int(.9 * len(errors))], maxErrorMetres=errors[-1],
                  standBAgreement=sum(r['estimatedOnStandB'] == r['trueOnStandB'] for r in rows),
                  disagreements=[r for r in rows if r['estimatedOnStandB'] != r['trueOnStandB']],
                  note='Development frames; label boxes used only to test geometry. Route position is the vehicle reference point, so a few metres of offset is expected.')
    args.output.write_text(json.dumps(report, indent=1) + '\n')
    print({k: v for k, v in report.items() if k != 'disagreements'}, report['disagreements'])


if __name__ == '__main__':
    main()
