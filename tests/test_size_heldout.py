"""Held-out sizing arithmetic (scripts/size_heldout.py)."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('size_heldout', Path(__file__).resolve().parents[1] / 'scripts/size_heldout.py')
size = importlib.util.module_from_spec(spec)
spec.loader.exec_module(size)


class Sizing(unittest.TestCase):
    def test_wilson_interval(self):
        low, high = size.wilson(8, 16)
        self.assertAlmostEqual(low, 0.28, places=2)
        self.assertAlmostEqual(high, 0.72, places=2)
        self.assertEqual(size.wilson(0, 0), (0.0, 1.0))

    def test_turns_for_ten_points_at_one_half(self):
        self.assertEqual(size.turns_for_half_width(0.5, 0.10, 1.0), 97)
        self.assertGreater(size.turns_for_half_width(0.5, 0.10, 1.3), 97)

    def test_paired_turns_shrink_with_a_larger_gap(self):
        self.assertGreater(size.paired_turns(0.31, 0.10), size.paired_turns(0.31, 0.15))
        self.assertIsNone(size.paired_turns(0.10, 0.20))
        self.assertEqual(size.paired_turns(0.20, 0.20), 37)  # the equality boundary is feasible


if __name__ == '__main__':
    unittest.main()
