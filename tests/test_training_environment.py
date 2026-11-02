import copy
import unittest
from backend.training_session import TrainingSession


class TrainingEnvironmentTests(unittest.TestCase):
    def test_conditions_do_not_create_reports_or_change_scoring_or_aircraft(self):
        original = TrainingSession(17, 'late_arrival')
        for kind in ('rain', 'snow', 'dusk'):
            run = TrainingSession(17, 'late_arrival', environment=kind)
            self.assertEqual(run.scenario['events'], original.scenario['events'])
            self.assertEqual(run.probes, original.probes)
            self.assertEqual(run.scenario['aircraft'], original.scenario['aircraft'])
            self.assertEqual([r.wire()['kind'] for r in run.records], ['report'] * len(run.records))
            self.assertEqual(run.scenario['environment']['kind'], kind)
        self.assertNotIn('environment', original.scenario)

    def test_mode_equivalence_retry_and_unsupported_conditions(self):
        for kind in ('rain', 'snow', 'dusk'):
            normal = TrainingSession(17, mode='continuous', clock=lambda: 0, environment=kind)
            fast = TrainingSession(17, mode='demo', clock=lambda: 0, environment=kind)
            self.assertEqual(normal.scenario['environment'], fast.scenario['environment'])
            original = copy.deepcopy(fast.scenario['environment'])
            fast._reset()
            self.assertEqual(fast.scenario['environment'], original)
            self.assertTrue(all(f['t'] in fast.world_boundaries for f in original['frames']))
        with self.assertRaises(ValueError):
            TrainingSession(17, environment='unvalidated-storm')
