# PROCEDURAL: verify scenario timing, motion envelopes and restrictions.
import math
import unittest
from bisect import bisect_right

from backend.evidence import classify, received_facts, validate_scenario
from backend.fleet_incident_variations import FLEET_VARIATIONS
from backend.surface_queue_variations import (APRON_OBSTRUCTION, CONNECTOR_CLOSURE, SURFACE_VARIATIONS,
                                             WEATHER_QUEUES, build_surface_variation)
from backend.training_environment import validate_environment
from backend.training_session import TrainingSession
from backend.turnaround_variations import TURNAROUND_VARIATIONS, WINTER_HANDOVER


def current(world, time, aid, prop):
    return next((f for f in classify(received_facts(world, time), time)
                 if f['aircraftId'] == aid and f['property'] == prop and f['status'] == 'current'), None)


def position_at(points, time):
    upper = bisect_right(points, time, key=lambda point: point['t'])
    if upper == len(points):
        return tuple(points[-1][key] for key in ('x', 'y', 'z'))
    a, b = points[upper - 1], points[upper]
    fraction = (time - a['t']) / (b['t'] - a['t'])
    return tuple(a[key] + fraction * (b[key] - a[key]) for key in ('x', 'y', 'z'))


class SurfaceVariationsTests(unittest.TestCase):
    def test_scenarios_are_deterministic_and_have_eligible_questions(self):
        for profile in SURFACE_VARIATIONS:
            for seed in range(20):
                with self.subTest(seed=seed, profile=profile):
                    world, reservations, probes = build_surface_variation(seed, profile)
                    self.assertEqual((world, reservations, probes), build_surface_variation(seed, profile))
                    self.assertEqual((reservations, probes), (world['runwayReservations'], []))
                    validate_scenario(world)
                    validate_environment(world.get('environment'), world['duration'])
                    for plane in world['aircraft']:
                        times = [p['t'] for p in plane['waypoints']]
                        self.assertEqual((times[0], times[-1]), (0, world['duration']))
                        self.assertEqual(times, sorted(set(times)))
                    for q in world['demoQuestions']:
                        self.assertTrue(any(e['aircraftId'] == q['aircraftId'] for e in received_facts(world, q['at'])))
                    for first, second in zip(world['demoQuestions'], world['demoQuestions'][1:]):
                        self.assertGreaterEqual(second['at'] - first['at'], 60)

    def test_obstruction_corrects_before_release_and_motion_is_clear_of_other_aircraft(self):
        for seed in range(20):
            world, _, _ = build_surface_variation(seed, APRON_OBSTRUCTION)
            passing, neighbour, parked = (p['waypoints'] for p in world['aircraft'])
            # Two generic aircraft fit within a conservative 46 m centre-to-
            # centre exclusion distance at these relative attitudes.
            for half_second in range(0, 541):
                t = half_second / 2
                for other in (neighbour, parked):
                    self.assertGreater(math.dist(position_at(passing, t), position_at(other, t)), .046)
            self.assertAlmostEqual(position_at(neighbour, 15)[2] - .0155, -.0145)
            self.assertGreater(-.025 + .0165, -.0145)
            self.assertIn('route', current(world, 12, 'A1', 'route')['value'])
            self.assertIn('protrudes', current(world, 25, 'A1', 'movement_condition')['value'])
            self.assertIn('fully parked', current(world, 180, 'A2', 'movement_status')['value'])
            self.assertIn('hold remains', current(world, 180, 'A1', 'movement_condition')['value'])
            self.assertIn('released', current(world, 210, 'A1', 'movement_condition')['value'])
            self.assertEqual(position_at(passing, 24), position_at(passing, 214))
            self.assertNotEqual(position_at(passing, 214), position_at(passing, 215))

    def test_connector_notice_future_active_and_late_reopening(self):
        for seed in range(20):
            world, _, _ = build_surface_variation(seed, CONNECTOR_CLOSURE)
            self.assertFalse(world['groundVehicles'])
            self.assertNotIn('ambientTraffic', world)
            scheduled = classify(received_facts(world, 52), 52)[0]
            self.assertEqual((scheduled['status'], scheduled['validFrom'], scheduled['validUntil']), ('scheduled', 120, 300))
            self.assertIsNotNone(current(world, 122, 'A1', 'trajectory_checkpoint'))
            self.assertIn('closed for works', current(world, 150, 'A1', 'movement_condition')['value'])
            self.assertIn('authorised diversion across Stand 307', current(world, 205, 'A1', 'route')['value'])
            self.assertIn('remains closed', current(world, 306, 'A1', 'movement_condition')['value'])
            notice = next(f for f in classify(received_facts(world, 306), 306) if f['property'] == 'trajectory_checkpoint')
            self.assertEqual(notice['status'], 'expired')
            self.assertIn('reopened', current(world, 373, 'A1', 'movement_condition')['value'])

    def test_queue_reservations_footprints_and_stale_report(self):
        for seed in range(20):
            world, _, _ = build_surface_variation(seed, WEATHER_QUEUES)
            self.assertEqual([job['aircraftId'] for job in world['queueDemand']], ['A1', 'A3', 'A2', 'A4'])
            for slots in (world['runwayReservations'], *([r for r in world['standReservations'] if r['stand'] == s] for s in ('A', 'B'))):
                self.assertTrue(all(first['end'] < second['start'] for first, second in zip(slots, slots[1:])))
            for job in world['queueDemand']:
                self.assertGreater(job['movementStart'], job['requestReceived'])
                self.assertIn('released', current(world, job['movementStart'], job['aircraftId'], 'movement_condition')['value'])
            aircraft = [(p['id'], p['waypoints']) for p in world['aircraft']]
            for seconds in range(0, 1210, 2):
                positions = {aid: position_at(points, seconds) for aid, points in aircraft}
                for aid, (x, y, z) in positions.items():
                    self.assertTrue(all(math.dist((x, y, z), other) > .046 for other_id, other in positions.items() if other_id != aid))
                    # A low aircraft whose centre is over the runway pavement
                    # must hold the relevant exclusive ground reservation.
                    if abs(x) <= .9 and abs(z + .4) < .0225 and y <= .003:
                        self.assertTrue(any(r['aircraftId'] == aid and r['start'] <= seconds < r['end']
                                            for r in world['runwayReservations']))
            self.assertEqual((world['queueMetrics']['peakArrival'], world['queueMetrics']['peakDeparture']), (2, 1))
            self.assertEqual(world['queueTrace'][-1]['arrival'], [])
            self.assertEqual(world['queueTrace'][-1]['departure'], [])
            self.assertIn('Stand B occupied', current(world, 465, 'A2', 'movement_condition')['value'])
            self.assertIn('release still awaited', current(world, 751, 'A2', 'movement_condition')['value'])
            final_cue = world['demoQuestions'][-1]['at']
            older = next(f for f in classify(received_facts(world, final_cue), final_cue)
                         if f['value'] == 'Stand B occupied with no slot for TRN102')
            self.assertEqual(older['status'], 'superseded')
            self.assertIn('arrival released', current(world, final_cue, 'A2', 'movement_condition')['value'])

    def test_normal_and_time_lapse_expose_the_same_reports_at_matched_source_times(self):
        for profile in FLEET_VARIATIONS + SURFACE_VARIATIONS + TURNAROUND_VARIATIONS:
            for seed in range(20):
                fast_wall, normal_wall = [0.], [0.]
                fast = TrainingSession(seed, profile, 'demo', clock=lambda: fast_wall[0])
                normal = TrainingSession(seed, profile, 'continuous', clock=lambda: normal_wall[0])
                if profile == WEATHER_QUEUES:
                    self.assertEqual(fast.scenario['queueTrace'], normal.scenario['queueTrace'])
                    self.assertEqual(fast.scenario['environment']['kind'], 'fog')
                if profile == WINTER_HANDOVER:
                    self.assertEqual(fast.scenario['environment']['kind'], 'snow')
                pending_seen = set()
                for seconds in range(5, 601, 5):
                    fast_wall[0] = float(seconds)
                    fast_state = fast.state()
                    world_time = fast_state['sourceTime']
                    normal_wall[0] = world_time
                    normal_time = normal.state()['sourceTime']
                    self.assertAlmostEqual(normal_time, world_time)
                    self.assertEqual(received_facts(fast.scenario, world_time), received_facts(normal.scenario, normal_time))
                    if fast_state['demoCue'] and fast_state['demoCue']['status'] == 'pending':
                        self.assertEqual(fast_state['rate'], 1)
                        pending_seen.add(fast_state['demoCue']['id'])
                    if fast_state['phase'] == 'debrief':
                        break
                self.assertEqual(fast.state()['phase'], 'debrief')
                self.assertEqual(pending_seen, {cue['id'] for cue in fast.scenario['demoQuestions']})
