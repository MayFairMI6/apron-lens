# PROCEDURAL: verifies geometry reuse and cutoff-bounded reports in the M2 variations.
import unittest

from backend.evidence import classify, received_facts, validate_scenario
from backend.fleet_incident_variations import (FLEET_VARIATIONS, NEWMAN_BIRD_STRIKE, SINGLE_ENGINE_RETURN,
                                               SYDNEY_ENGINE_FAILURE, WILDLIFE_RETURN, build_fleet_variation)
from backend.fleet_scenarios import FLEET_DEMONSTRATIONS, build_fleet
from test_fleet_scenarios import inside_polygon, polygons_overlap, rectangle


def current_values(world, cutoff):
    return {fact['property']: fact['value'] for fact in classify(received_facts(world, cutoff), cutoff)
            if fact['status'] == 'current'}


class FleetIncidentVariationsTests(unittest.TestCase):
    def test_returns_reuse_landing_path_and_keep_the_new_cases_separate(self):
        self.assertFalse(set(FLEET_VARIATIONS) & set(FLEET_DEMONSTRATIONS))
        for seed in range(20):
            priority, _, _ = build_fleet(seed, 'fleet_b787_priority_landing')
            for exercise in FLEET_VARIATIONS:
                with self.subTest(seed=seed, exercise=exercise):
                    world, reservations, probes = build_fleet_variation(seed, exercise)
                    self.assertEqual((world, reservations, probes), build_fleet_variation(seed, exercise))
                    validate_scenario(world)
                    self.assertEqual(world['aircraft'][0]['waypoints'], priority['aircraft'][0]['waypoints'])
                    self.assertEqual((reservations, probes), (world['runwayReservations'], []))
                    touchdown = next(p['t'] for p in world['aircraft'][0]['phases'] if p['id'] == 'landing_roll')
                    self.assertTrue(all((p['y'] == 0) == (p['t'] >= touchdown) for p in world['aircraft'][0]['waypoints']))
                    for first, second in zip(world['demoQuestions'], world['demoQuestions'][1:]):
                        self.assertGreaterEqual(second['at'] - first['at'], 60)
                    for event in world['events']:
                        self.assertEqual((event['aircraftId'], event['flightInstance']), ('A1', 'TRN101'))
                        self.assertLessEqual(event['receiptTime'], world['duration'])

    def test_changed_parked_types_fit_the_established_parking_footprints(self):
        for exercise in FLEET_VARIATIONS:
            world, _, _ = build_fleet_variation(17, exercise)
            features = world['geography']['features']
            obstacles = [[(p['x'], p['z']) for p in feature['points']] for feature in features
                         if feature['kind'] in ('building', 'jet_bridge') and feature.get('closed')]
            parking = []
            for plane in world['aircraft'][1:]:
                apron = next(f for f in features if f['id'] == plane['parkingApron'])
                bounds = rectangle(plane, plane['waypoints'][0], margin=2)
                self.assertTrue(all(inside_polygon(*p, apron['points']) for p in bounds))
                self.assertFalse(any(polygons_overlap(bounds, other) for other in obstacles + parking))
                parking.append(bounds)

    def test_single_engine_return_exposes_landing_and_recovery_at_separate_cutoffs(self):
        world, _, _ = build_fleet_variation(17, SINGLE_ENGINE_RETURN)
        self.assertEqual(world['aircraft'][0]['aircraftType'], 'b737_800')
        self.assertIn(SYDNEY_ENGINE_FAILURE, world['provenance']['sources'])
        requested, landed, recovery = (q['at'] for q in world['demoQuestions'])
        first = current_values(world, requested)
        self.assertIn('right engine failure', first['movement_condition'])
        self.assertIn('cause unconfirmed', first['movement_condition'])
        self.assertEqual(first['movement_status'], 'airborne on one engine with emergency return requested')
        second = current_values(world, landed)
        self.assertIn('landed safely and stopped', second['movement_status'])
        self.assertIn('runway occupied', second['movement_condition'])
        self.assertIn('recovery requested and runway release unconfirmed', current_values(world, recovery)['movement_condition'])

    def test_wildlife_return_requires_an_inspection_report_to_confirm_strike_and_damage(self):
        world, _, _ = build_fleet_variation(17, WILDLIFE_RETURN)
        self.assertEqual(world['aircraft'][0]['aircraftType'], 'a320_200')
        self.assertIn(NEWMAN_BIRD_STRIKE, world['provenance']['sources'])
        warning, requested, inspected = (q['at'] for q in world['demoQuestions'])
        self.assertIn('strike not reported', current_values(world, warning)['movement_condition'])
        self.assertIn('precautionary return requested', current_values(world, requested)['movement_status'])
        outcome = next(event for event in world['events'] if event['source'] == 'exercise-engineering')
        before = current_values(world, outcome['receiptTime'] - .001)
        self.assertIn('damage and engine effects unconfirmed', before['movement_condition'])
        self.assertIn('landed safely and stopped', before['movement_status'])
        after = current_values(world, inspected)['movement_condition']
        self.assertIn('bird strike and minor flap damage', after)
        self.assertIn('engine condition unconfirmed', after)
