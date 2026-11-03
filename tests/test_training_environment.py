import copy
import unittest
from backend.training_session import TrainingSession
from backend.training_environment import attach_environment, validate_environment


class TrainingEnvironmentTests(unittest.TestCase):
    def test_conditions_do_not_create_reports_or_change_scoring_or_aircraft(self):
        original = TrainingSession(17, 'late_arrival')
        for kind in ('rain', 'snow', 'dusk', 'fog'):
            run = TrainingSession(17, 'late_arrival', environment=kind)
            self.assertEqual(run.scenario['events'], original.scenario['events'])
            self.assertEqual(run.probes, original.probes)
            self.assertEqual(run.scenario['aircraft'], original.scenario['aircraft'])
            self.assertEqual([r.wire()['kind'] for r in run.records], ['report'] * len(run.records))
            self.assertEqual(run.scenario['environment']['kind'], kind)
        self.assertNotIn('environment', original.scenario)

    def test_mode_equivalence_retry_and_unsupported_conditions(self):
        for kind in ('rain', 'snow', 'dusk', 'fog'):
            normal = TrainingSession(17, mode='continuous', clock=lambda: 0, environment=kind)
            fast = TrainingSession(17, mode='demo', clock=lambda: 0, environment=kind)
            self.assertEqual(normal.scenario['environment'], fast.scenario['environment'])
            original = copy.deepcopy(fast.scenario['environment'])
            fast._reset()
            self.assertEqual(fast.scenario['environment'], original)
            self.assertTrue(all(f['t'] in fast.world_boundaries for f in original['frames']))
        with self.assertRaises(ValueError):
            TrainingSession(17, environment='unvalidated-storm')

    def test_fog_is_authored_visual_curve_with_early_recovery(self):
        world = {'predictionBoundaries': [125, 600], 'events': [{'id': 'unchanged'}]}
        attach_environment(world, 'fog')
        plan = world['environment']
        self.assertEqual((plan['version'], plan['kind']), (2, 'fog'))
        frames = {f['t']: f for f in plan['frames']}
        self.assertEqual(frames[0]['fogExtinctionPerMetre'], 0)
        self.assertGreater(frames[300]['fogExtinctionPerMetre'], 0)
        self.assertEqual(frames[600]['fogExtinctionPerMetre'], frames[1600]['fogExtinctionPerMetre'])
        self.assertGreater(frames[1600]['fogExtinctionPerMetre'], frames[1800]['fogExtinctionPerMetre'])
        self.assertGreater(frames[1800]['fogExtinctionPerMetre'], frames[2200]['fogExtinctionPerMetre'])
        self.assertEqual(frames[2400]['fogExtinctionPerMetre'], 0)
        self.assertEqual(frames[3000]['fogExtinctionPerMetre'], 0)
        self.assertEqual(world['events'], [{'id': 'unchanged'}])
        self.assertIn(125, world['predictionBoundaries'])
        self.assertTrue(all(f['precipitation'] == 0 for f in plan['frames']))
        self.assertTrue(all(set(f) == {'t', 'precipitation', 'daylight', 'fogExtinctionPerMetre'} for f in plan['frames']))

    def test_legacy_profiles_are_exactly_preserved(self):
        for kind, precipitation, daylight in (
                ('rain', (.15, .5, .85, .35, .1), (1,) * 5),
                ('snow', (.1, .4, .7, .25, .1), (1,) * 5),
                ('dusk', (0,) * 5, (.95, .7, .3, .08, .05))):
            world = {}
            attach_environment(world, kind)
            self.assertEqual(world['environment'], dict(version=1, kind=kind, frames=[
                dict(t=t, precipitation=p, daylight=d) for t, p, d in
                zip((0, 600, 1800, 3000, 3600), precipitation, daylight)]))
        world = {'events': ['existing']}
        attach_environment(world, 'clear')
        self.assertEqual(world, {'events': ['existing']})

    def test_environment_contract_rejects_bad_versions_and_values(self):
        world = {}
        attach_environment(world, 'fog')
        original = world['environment']
        for version in (0, 1, 3):
            plan = copy.deepcopy(original)
            plan['version'] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                validate_environment(plan, 3600)
        for field, values in {'fogExtinctionPerMetre': (-.1, .01001, float('nan'), float('inf'), True),
                              'precipitation': (-1, .1, float('inf')),
                              'daylight': (-1, 1.1, float('nan')),
                              't': (-1, 0, 3601, float('inf'))}.items():
            for value in values:
                plan = copy.deepcopy(original)
                plan['frames'][1][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_environment(plan, 3600)
        for duration in (0, -1, float('inf'), float('nan')):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                validate_environment(original, duration)
        plan = copy.deepcopy(original)
        plan['frames'] = [dict(t=0), dict(t=3600)]
        validate_environment(plan, 3600)  # Omitted strength has a clear default.
        validate_environment(None, 3600)
        validate_environment({}, 3600)
        self.assertEqual(world['environment'], original)
