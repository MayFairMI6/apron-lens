# PROCEDURAL: verifies the P01 evidence cutoffs and authored scene against regressions.
"""P01 stand-clearance lesson: report order, cutoffs, typed review and isolation from M1."""
import json
import math
import unittest
from unittest.mock import patch

from backend.evidence import validate_scenario, received_facts, build_context
from backend.lessons import EXERCISES, M2_LESSONS, build_lesson
from backend.stand_clearance_lesson import STAND_CLEARANCE_LESSON, DURATION, build_stand_clearance_lesson
from backend.training_assessment import M2_RUBRICS, M2_TYPED_QUESTIONS, RUBRICS, TYPED_QUESTIONS, rubric_for, typed_question_for
from backend.training_session import ActionConflict, TrainingSession
from evidencekit import check_references


def act(session, action, **kwargs):
    return session.action(dict(runId=session.run_id, revision=session.revision,
        actionId=f'{len(session.actions)}-{action}', action=action, **kwargs))


class StandClearanceLessonTests(unittest.TestCase):
    def session(self, seed=17, assessment_mode='choice'):
        now = [0.]
        return TrainingSession(seed, STAND_CLEARANCE_LESSON, clock=lambda: now[0], assessment_mode=assessment_mode), now

    def current_condition(self, world, cutoff):
        facts = build_context(world, 'A3', cutoff, 'current', ['movement_condition'])['facts']
        return next((f for f in facts if f['property'] == 'movement_condition' and f['status'] == 'current'), None)

    def test_twenty_seeds_build_valid_deterministic_worlds(self):
        orders = set()
        for seed in range(20):
            world, slots, probes = build_stand_clearance_lesson(seed)
            self.assertEqual((world, slots, probes), build_lesson(seed, STAND_CLEARANCE_LESSON))
            self.assertEqual((world, slots, probes), build_stand_clearance_lesson(seed))
            validate_scenario(world)
            self.assertEqual((world['duration'], slots), (DURATION, []))
            self.assertEqual([p['at'] for p in probes], [60, 120, 180])
            self.assertTrue(all(e['receiptTime'] <= DURATION for e in world['events']))
            for aircraft in world['aircraft'] + world['groundVehicles']:
                times = [p['t'] for p in aircraft['waypoints']]
                self.assertEqual((times[0], times[-1]), (0, DURATION))
                self.assertEqual(times, sorted(times))
            session, _ = self.session(seed)
            for probe in probes:
                known = {f['event_id'] for f in received_facts(world, probe['at'])}
                self.assertTrue(set(probe['evidenceIds']) <= known)
                check_references(probe['evidenceIds'], session.records, session.scenario['scenarioId'], probe['at'])
                self.assertEqual((len(probe['choices']), len(set(probe['choices'])), probe['aircraftId']), (4, 4, 'A3'))
            orders.add(tuple(p['correct'] for p in probes))
        self.assertGreater(len(orders), 10)

    def test_removal_report_keeps_the_hold_until_the_check_is_complete(self):
        world, _, _ = build_stand_clearance_lesson(17)
        self.assertIsNone(self.current_condition(world, 15))
        self.assertEqual(self.current_condition(world, 60)['value'], 'hold: Stand B clearance check pending')
        at_120 = self.current_condition(world, 120)['value']
        self.assertIn('removal reported', at_120)
        self.assertIn('check pending', at_120)
        self.assertEqual(self.current_condition(world, 180)['value'],
                         'Stand B clearance check complete; exercise arrival hold released')
        # Each hold update supersedes the one before it for the same flight and property.
        holds = [e for e in world['events'] if e['facts'][0]['property'] == 'movement_condition']
        self.assertEqual(len(holds), 4)
        for older, newer in zip(holds, holds[1:]):
            self.assertEqual(newer['facts'][0]['supersedes'], [older['id'] + ':movement_condition'])

    def test_vehicle_leaves_before_the_removal_report_and_aircraft_waits_for_release(self):
        world, _, _ = build_stand_clearance_lesson(17)
        vehicle = world['groundVehicles'][0]['waypoints']
        removed = next(e for e in world['events'] if 'removal reported' in e['facts'][0]['value'])
        released = next(e for e in world['events'] if 'released' in e['facts'][0]['value'])
        start = (vehicle[0]['x'], vehicle[0]['z'])
        first_away = next(i for i, p in enumerate(vehicle) if (p['x'], p['z']) != start)
        starts_leaving = vehicle[first_away - 1]['t']
        self.assertEqual((starts_leaving, removed['eventTime'], removed['receiptTime']), (88, 92, 95))
        self.assertEqual(released['receiptTime'], 150)
        inbound = next(a for a in world['aircraft'] if a['id'] == 'A3')['waypoints']
        first_away = next(i for i, p in enumerate(inbound) if (p['x'], p['z']) != (inbound[0]['x'], inbound[0]['z']))
        self.assertEqual(inbound[first_away - 1]['t'], 158)
        self.assertLess(inbound[-2]['t'], DURATION)
        self.assertEqual((round(inbound[-1]['x'], 6), round(inbound[-1]['z'], 6)), (.035, .04))
        self.assertIn('check pending', self.current_condition(world, 95)['value'])
        self.assertIn('check pending', self.current_condition(world, 149.999)['value'])
        self.assertIn('hold released', self.current_condition(world, 150)['value'])
        for aircraft in world['aircraft']:
            if aircraft['id'] != 'A3':
                poses = {(p['x'], p['z']) for p in aircraft['waypoints']}
                self.assertEqual(len(poses), 1)

    def test_full_vehicle_footprint_is_outside_stand_at_removal_event_and_receipt(self):
        world, _, _ = build_stand_clearance_lesson(17)
        service_vehicle, = world['groundVehicles']
        self.assertTrue(service_vehicle['preciseHeading'])
        waypoints = service_vehicle['waypoints']

        def bounds_metres(time):
            start, end = next((a, b) for a, b in zip(waypoints, waypoints[1:]) if a['t'] <= time <= b['t'])
            fraction = (time - start['t']) / (end['t'] - start['t'])
            x, z, heading = (start[k] + fraction * (end[k] - start[k]) for k in ('x', 'z', 'heading'))
            # P01StandScenery tanker body, wheels and windshield fit within
            # these half-extents in metres. Project the rotated box onto X/Z.
            half_width, half_length = 1.9, 5.65
            sine, cosine = abs(math.sin(math.radians(heading))), abs(math.cos(math.radians(heading)))
            dx = cosine * half_width + sine * half_length
            dz = sine * half_width + cosine * half_length
            return (x * 1000 - dx, x * 1000 + dx, z * 1000 - dz, z * 1000 + dz)

        x_min, x_max, z_min, z_max = bounds_metres(60)
        self.assertTrue(12 < x_min < x_max < 58 and 7 < z_min < z_max < 57)
        for tenth in range(920, 1001):
            time = tenth / 10
            x_min, _, z_min, _ = bounds_metres(time)
            self.assertTrue(z_min > 57 or x_min > 58, f'Tanker intersects Stand B at {time} seconds')
        self.assertEqual(waypoints[-1], dict(waypoints[-2], t=float(DURATION)))

    def test_choice_lesson_runs_to_debrief_with_cutoff_bounded_feedback(self):
        for seed in range(5):
            session, now = self.session(seed)
            self.assertEqual((session.target, session.title), ('A3', 'An arriving stand not clear of equipment'))
            act(session, 'ready')
            for probe in session.probes:
                now[0] += 100
                state = session.state()
                self.assertEqual((state['phase'], state['sourceTime']), ('checkpoint', probe['at']))
                feedback = act(session, 'answer', checkpointId=probe['id'], choice=probe['correct'])['feedback']
                self.assertTrue(feedback['correct'])
                self.assertTrue(all(e['receiptTime'] <= probe['at'] for e in feedback['reports']))
                act(session, 'continue')
            now[0] += 40
            debrief = session.state()
            self.assertEqual((debrief['phase'], debrief['score'], debrief['answered']), ('debrief', 3, 3))
            self.assertIn('stops before contact', debrief['perspectives'][-1]['text'])

    def test_typed_questions_and_private_criteria_cite_eligible_reports(self):
        for index in range(3):
            session, _ = self.session(assessment_mode='typed')
            probe = session.probes[index]
            session.phase = 'checkpoint'; session.active_probe = index; session.source_time = probe['at']
            state = session.state()
            self.assertEqual(set(state['checkpoint']), {'id', 'at', 'question'})
            self.assertEqual(state['checkpoint']['question'], M2_TYPED_QUESTIONS[STAND_CLEARANCE_LESSON][index])
            self.assertEqual(typed_question_for(STAND_CLEARANCE_LESSON, probe), state['checkpoint']['question'])
            reports = [e for e in session.scenario['events'] if e['receiptTime'] <= probe['at']]
            criteria = rubric_for(STAND_CLEARANCE_LESSON, probe, reports)
            self.assertEqual([c['id'] for c in criteria][-1], 'grounding')
            eligible = {e['id'] for e in reports}
            for criterion in criteria:
                self.assertTrue(set(criterion['evidenceIds']) <= eligible)
            self.assertNotIn('correct', json.dumps(state['checkpoint']))

    def test_m1_rotation_and_research_tables_are_unchanged(self):
        self.assertEqual(EXERCISES, ('surface_conflict', 'late_arrival', 'late_baggage', 'fog_restrictions'))
        self.assertEqual(M2_LESSONS, (STAND_CLEARANCE_LESSON,))
        self.assertNotIn(STAND_CLEARANCE_LESSON, RUBRICS)
        self.assertNotIn(STAND_CLEARANCE_LESSON, TYPED_QUESTIONS)
        self.assertEqual(set(M2_RUBRICS), set(M2_TYPED_QUESTIONS))
        self.assertEqual([len(r) for r in M2_RUBRICS[STAND_CLEARANCE_LESSON]], [2, 2, 2])
        session, now = self.session()
        session.phase = 'debrief'
        self.assertEqual(act(session, 'next')['exercise'], STAND_CLEARANCE_LESSON)

    def test_mode_and_environment_boundaries(self):
        for mode in ('demo', 'continuous'):
            with self.assertRaisesRegex(ValueError, '210-second lesson'):
                TrainingSession(17, STAND_CLEARANCE_LESSON, mode)
        for environment in ('rain', 'snow', 'dusk', 'fog'):
            with self.assertRaisesRegex(ValueError, 'no weather timeline'):
                TrainingSession(17, STAND_CLEARANCE_LESSON, environment=environment)
        self.assertNotIn('environment', TrainingSession(17, STAND_CLEARANCE_LESSON, environment='clear').scenario)

    def test_cli_rejects_conflicting_options_before_model_load(self):
        from backend.training import main
        for options in (['--mode', 'demo'], ['--environment', 'snow']):
            with patch('sys.argv', ['training', '--exercise', STAND_CLEARANCE_LESSON, *options]), \
                    patch('backend.training_adapter.TrainingAdapter.load') as load, patch('sys.stderr'):
                with self.assertRaises(SystemExit) as error:main()
                self.assertEqual(error.exception.code, 2); load.assert_not_called()


if __name__ == '__main__':unittest.main()
