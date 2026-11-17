"""Camera evidence: geometry, arm boundaries, no ground-truth reads, no authority."""
import ast
import math
import unittest
from pathlib import Path

import numpy as np

from backend.camera_evidence import ARMS, backproject, locate, observation, on_stand_b
from backend.typed_claims import Claim, check_claim
from backend.stand_clearance_lesson import build_stand_clearance_lesson

ROOT = Path(__file__).resolve().parents[1]


def look_rotation(forward):
    """Unity-style quaternion that turns +Z to `forward` with +Y up (no roll)."""
    fx, fy, fz = forward
    norm = math.sqrt(fx * fx + fy * fy + fz * fz)
    fx, fy, fz = fx / norm, fy / norm, fz / norm
    yaw = math.atan2(fx, fz)
    pitch = -math.asin(fy)
    cy, sy, cp, sp = math.cos(yaw / 2), math.sin(yaw / 2), math.cos(pitch / 2), math.sin(pitch / 2)
    # q = yaw(Y) * pitch(X)
    return dict(w=cy * cp, x=cy * sp, y=sy * cp, z=-sy * sp)


def meta_for(position, target, width=96, height=54, fov=55):
    m11 = 1 / math.tan(math.radians(fov) / 2)
    projection = [0.0] * 16
    projection[0], projection[5] = m11 * height / width, m11
    forward = tuple(t - p for t, p in zip(target, position))
    return dict(width=width, height=height, projection=projection, sourceTime=90.0, trackingAvailable=True,
                cameraPositionMetres=dict(zip('xyz', position)), cameraRotation=look_rotation(forward))


class Geometry(unittest.TestCase):
    def test_centre_pixel_backprojects_along_the_view_axis(self):
        meta = meta_for((72, 12, -35), (45, 1.8, 40))
        distance = math.dist((72, 12, -35), (45, 1.8, 40))
        x, y, z = backproject(meta, meta['width'] / 2 - .5, meta['height'] / 2 - .5, distance)
        self.assertAlmostEqual(x, 45, delta=.05)
        self.assertAlmostEqual(y, 1.8, delta=.05)
        self.assertAlmostEqual(z, 40, delta=.05)

    def test_box_location_uses_depth_and_decides_stand_b(self):
        meta = meta_for((72, 12, -35), (45, 1.8, 40))
        distance = math.dist((72, 12, -35), (45, 1.8, 40))
        depth = np.zeros((meta['height'], meta['width']), dtype=np.float32)
        depth[22:32, 40:56] = distance  # around the centre; rows are bottom-left like the export
        point = locate(meta, depth, (40, 22, 56, 32))
        self.assertTrue(on_stand_b(point))
        self.assertFalse(on_stand_b((76, 1.8, 63)))  # the tanker's position after it leaves
        self.assertIsNone(locate(meta, np.zeros_like(depth), (40, 22, 56, 32)))


class Records(unittest.TestCase):
    def setUp(self):
        self.meta = meta_for((72, 12, -35), (45, 1.8, 40))
        self.depth = np.full((self.meta['height'], self.meta['width']), math.dist((72, 12, -35), (45, 1.8, 40)), np.float32)
        self.common = dict(run_id='R', capture_id='c1', detector='v2-B', threshold=.5, qualified=False)

    def test_rgb_arm_never_claims_a_location(self):
        record = observation(self.meta, [((40, 22, 56, 32), .9)], 'rgb', **self.common)
        self.assertEqual((record['visibleVehicle'], record['confidence']), ('present', .9))
        self.assertNotIn('apronPositionMetres', record)
        self.assertNotIn('onStandB', record)

    def test_depth_arm_adds_position_only_for_a_detection(self):
        seen = observation(self.meta, [((40, 22, 56, 32), .9)], 'rgb_depth', depth=self.depth, **self.common)
        self.assertTrue(seen['onStandB'])
        missed = observation(self.meta, [((40, 22, 56, 32), .2)], 'rgb_depth', depth=self.depth, **self.common)
        self.assertEqual(missed['visibleVehicle'], 'not_detected')
        self.assertNotIn('onStandB', missed)
        self.assertIn('not evidence of absence', missed['note'])
        with self.assertRaises(ValueError):
            observation(self.meta, [], 'rgb_depth', **self.common)
        with self.assertRaises(ValueError):
            observation(self.meta, [], 'depth_only', **self.common)

    def test_qualification_and_tracking_are_carried(self):
        lost = dict(self.meta, trackingAvailable=False)
        record = observation(lost, [((40, 22, 56, 32), .9)], 'rgb', **self.common)
        self.assertEqual((record['trackingValid'], record['detectorQualified']), (False, False))

    def test_a_camera_observation_cannot_establish_release(self):
        world, _, _ = build_stand_clearance_lesson(17)
        record = observation(dict(self.meta, sourceTime=150.0), [((40, 22, 56, 32), .9)], 'rgb_depth',
                             depth=self.depth, run_id=world['scenarioId'], capture_id='c150', detector='v2-B',
                             threshold=.5, qualified=True)
        release = Claim(world['scenarioId'], 'A3', 'TRN103', 'movement_condition', 'released', ('c150',))
        self.assertEqual(check_claim(world, 150, release, [record]).status, 'unknown')
        present = Claim(world['scenarioId'], 'A3', 'TRN103', 'visible_vehicle', 'present', ('c150',))
        self.assertEqual(check_claim(world, 150, present, [record]).status, 'supported')

    def test_module_never_reads_the_mask_or_label_boxes(self):
        source = (ROOT / 'backend/camera_evidence.py').read_text()
        code = ast.unparse(ast.parse(source))  # docstrings/comments removed from strings check below
        self.assertNotIn("'.mask", code)
        self.assertNotIn("['visibleBoxes']", code)
        self.assertNotIn('visual_truth', code)
        self.assertEqual(ARMS, ('rgb', 'rgb_depth'))


if __name__ == '__main__':
    unittest.main()
