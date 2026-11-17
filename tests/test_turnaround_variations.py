# PROCEDURAL: verify receipt cutoffs, movement release and protected turnaround status.
import unittest

from backend.evidence import validate_scenario
from backend.training_environment import validate_environment
from backend.turnaround_variations import (DEBRIS_RECOVERY, FUEL_INTERRUPTION, TURNAROUND_VARIATIONS,
                                           WINTER_HANDOVER, build_turnaround_variation)
from test_surface_queue_variations import current, position_at


class TurnaroundVariationsTests(unittest.TestCase):
    def test_deterministic_authored_worlds_have_ordered_paths_and_questions(self):
        for profile in TURNAROUND_VARIATIONS:
            for seed in range(20):
                world, reservations, probes = build_turnaround_variation(seed, profile)
                self.assertEqual((world, reservations, probes), build_turnaround_variation(seed, profile))
                self.assertEqual((reservations, probes), ([], []))
                validate_scenario(world)
                validate_environment(world.get('environment'), world['duration'])
                for plane in world['aircraft']:
                    times = [point['t'] for point in plane['waypoints']]
                    self.assertEqual((times[0], times[-1]), (0, world['duration']))
                    self.assertEqual(times, sorted(set(times)))
                for first, second in zip(world['demoQuestions'], world['demoQuestions'][1:]):
                    self.assertGreaterEqual(second['at'] - first['at'], 60)

    def test_debris_recovery_and_inspection_do_not_move_the_aircraft(self):
        for seed in range(20):
            world, _, _ = build_turnaround_variation(seed, DEBRIS_RECOVERY)
            points = world['aircraft'][0]['waypoints']
            prop = 'movement_condition'
            self.assertIn('origin unconfirmed', current(world, 160, 'A1', prop)['value'])
            self.assertIn('still closed', current(world, 223, 'A1', prop)['value'])
            self.assertIn('reopened and released', current(world, 250, 'A1', prop)['value'])
            self.assertEqual(position_at(points, 0), position_at(points, 257))
            self.assertNotEqual(position_at(points, 257), position_at(points, 258))

    def test_winter_conditions_service_readiness_and_release_are_independent(self):
        for seed in range(20):
            world, _, _ = build_turnaround_variation(seed, WINTER_HANDOVER)
            points = world['aircraft'][0]['waypoints']
            prop = 'movement_condition'
            self.assertIn('inspection and release pending', current(world, 149, 'A1', prop)['value'])
            self.assertIn('de-icing outstanding', current(world, 259, 'A1', 'overall_readiness')['value'])
            self.assertIn('ready for apron movement', current(world, 357, 'A1', 'overall_readiness')['value'])
            self.assertIn('movement release pending', current(world, 357, 'A1', prop)['value'])
            self.assertIn('released to use the west apron lane', current(world, 409, 'A1', prop)['value'])
            self.assertEqual(position_at(points, 0), position_at(points, 418))
            self.assertNotEqual(position_at(points, 418), position_at(points, 419))

    def test_fuelling_completion_does_not_establish_overall_readiness(self):
        for seed in range(20):
            world, _, _ = build_turnaround_variation(seed, FUEL_INTERRUPTION)
            self.assertIn('interrupted', current(world, 73, 'A1', 'fuel_status')['value'])
            self.assertIn('water with exclusion still active', current(world, 181, 'A1', 'movement_condition')['value'])
            self.assertIn('exclusion lifted', current(world, 327, 'A1', 'movement_condition')['value'])
            self.assertEqual(current(world, 327, 'A1', 'fuel_status')['value'], 'fuelling complete')
            self.assertIn('still unconfirmed', current(world, 327, 'A1', 'overall_readiness')['value'])
            self.assertEqual(len({(p['x'], p['z']) for p in world['aircraft'][0]['waypoints']}), 1)
