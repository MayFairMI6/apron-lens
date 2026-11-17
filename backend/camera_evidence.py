"""SUBSTANTIVE: turn one synchronized capture plus detector output into a camera observation.

Two evidence arms share one record format, compatible with `backend.typed_claims`:

- ``rgb``: the detector saw (or did not see) a fuel-transfer vehicle in this
  frame, with its confidence. No location is claimed.
- ``rgb_depth``: the same, plus an apron position estimated from the depth
  image and the camera pose, and whether that position is on Stand B.

Inputs available to an AR device only: RGB-derived detections, the depth
image, the camera pose and projection, the capture time and tracking state.
The object mask and label boxes in the capture are ground truth for scoring
and are never read here. "Not detected" is not evidence of absence, and no
observation establishes a stand release or any other movement authority.
"""
import json
import math
from pathlib import Path
from statistics import median

import numpy as np

# Stand B extent in apron metres, the bounds the Stand B footprint test checks
# (tests/test_stand_clearance_lesson.py). An authored training area, not a survey.
STAND_B_METRES = dict(xMin=12.0, xMax=58.0, zMin=7.0, zMax=57.0)
ARMS = ('rgb', 'rgb_depth')


def load_capture(stem):
    """Metadata and depth for one capture stem (path without extension). Never reads the mask."""
    stem = Path(stem)
    meta = json.loads(stem.with_suffix('.json').read_text())
    depth = np.fromfile(str(stem) + '.depth.f32', dtype='<f4')
    if depth.size != meta['width'] * meta['height']:
        raise ValueError('Depth size does not match the capture')
    return meta, depth.reshape(meta['height'], meta['width'])  # row 0 is the bottom row


def _rotate(quaternion, vector):
    x, y, z, w = (quaternion[k] for k in 'xyzw')
    vx, vy, vz = vector
    # v' = v + 2w(q×v) + 2 q×(q×v)
    cx, cy, cz = y * vz - z * vy, z * vx - x * vz, x * vy - y * vx
    cx2, cy2, cz2 = y * cz - z * cy, z * cx - x * cz, x * cy - y * cx
    return vx + 2 * (w * cx + cx2), vy + 2 * (w * cy + cy2), vz + 2 * (w * cz + cz2)


def backproject(meta, u, v, depth_metres):
    """Apron point (x, y, z metres) for pixel (u, v), bottom-left origin, at linear camera depth."""
    p = meta['projection']  # Unity column-major: m00=p[0], m11=p[5], m02=p[8], m12=p[9]
    ndc_x = 2 * (u + .5) / meta['width'] - 1
    ndc_y = 2 * (v + .5) / meta['height'] - 1
    x_cam = (ndc_x + p[8]) * depth_metres / p[0]
    y_cam = (ndc_y + p[9]) * depth_metres / p[5]
    dx, dy, dz = _rotate(meta['cameraRotation'], (x_cam, y_cam, depth_metres))
    c = meta['cameraPositionMetres']
    return c['x'] + dx, c['y'] + dy, c['z'] + dz


def locate(meta, depth, box):
    """Median apron position of the box's central half, from nonzero depth. Box: x0,y0,x1,y1 top-left origin."""
    x0, y0, x1, y1 = box
    height = meta['height']
    cx0, cx1 = int(x0 + (x1 - x0) * .25), int(math.ceil(x0 + (x1 - x0) * .75))
    # Convert the top-left-origin rows to the depth image's bottom-left rows.
    cy0, cy1 = int(y0 + (y1 - y0) * .25), int(math.ceil(y0 + (y1 - y0) * .75))
    points = []
    for top_row in range(max(0, cy0), min(height, max(cy1, cy0 + 1))):
        row = height - 1 - top_row
        for column in range(max(0, cx0), min(meta['width'], max(cx1, cx0 + 1))):
            value = float(depth[row, column])
            if value > 0:
                points.append(backproject(meta, column, row, value))
    if not points:
        return None
    return tuple(round(median(axis), 2) for axis in zip(*points))


def on_stand_b(point):
    x, _, z = point
    return STAND_B_METRES['xMin'] <= x <= STAND_B_METRES['xMax'] and STAND_B_METRES['zMin'] <= z <= STAND_B_METRES['zMax']


def observation(meta, detections, arm, *, run_id, capture_id, detector, threshold, qualified,
                aircraft_id='A3', flight='TRN103', depth=None):
    """One camera observation. `detections`: list of (box top-left x0,y0,x1,y1, score)."""
    if arm not in ARMS:
        raise ValueError('Unknown evidence arm')
    if arm == 'rgb_depth' and depth is None:
        raise ValueError('The depth arm needs the depth image')
    kept = sorted(((box, score) for box, score in detections if score >= threshold), key=lambda d: -d[1])
    record = dict(captureId=capture_id, runId=run_id, aircraftId=aircraft_id, flightInstance=flight,
                  source='camera', sourceKind='camera_observation', arm=arm,
                  sourceTime=meta['sourceTime'], trackingValid=bool(meta['trackingAvailable']),
                  kind='fuel_transfer_vehicle', visibleVehicle='present' if kept else 'not_detected',
                  confidence=round(float(kept[0][1]), 4) if kept else None,
                  boxes=[[round(float(c), 1) for c in box] for box, _ in kept],
                  detector=detector, detectorQualified=bool(qualified), threshold=threshold,
                  note=('Camera observation, lower authority than a report. "not_detected" is not evidence of '
                        'absence. No observation establishes a stand release.'))
    # Without tracking the frame cannot be placed on the apron, so no location is claimed.
    if arm == 'rgb_depth' and kept and record['trackingValid']:
        point = locate(meta, depth, kept[0][0])
        record['apronPositionMetres'] = None if point is None else dict(zip('xyz', point))
        record['onStandB'] = None if point is None else on_stand_b(point)
    return record
