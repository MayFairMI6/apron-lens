"""Scored fog interpretation, causal evidence and unchanged existing worlds."""
import copy
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.evidence import validate_scenario, received_facts, build_context
from backend.fog_lesson import FOG_LESSON, build_fog_lesson
from backend.lessons import EXERCISES, build_lesson
from backend.runway_scenarios import DEMONSTRATIONS, build_demonstration
from backend.training import training_app
from backend.training_environment import validate_environment
from backend.training_session import ActionConflict, TrainingSession
from evidencekit import check_references
from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter


def fingerprint_bytes(value):
    """Keep every field; round only finite floats for platform libm portability.

    Nine decimal places is a 1e-9 unit grid (1 micrometre for kilometre
    coordinates; at most 0.5 micrometre rounding error). Integers, booleans,
    strings, order and collection contents remain exact. This does not modify
    production worlds or define their operational accuracy.
    """
    def normalize(item):
        if isinstance(item, float):
            if not math.isfinite(item):raise ValueError('Non-finite world fingerprint value')
            rounded = round(item, 9)
            return 0.0 if rounded == 0 else rounded
        if isinstance(item, dict):return {key: normalize(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):return [normalize(child) for child in item]
        return item
    return json.dumps(normalize(value), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


class FogLessonTests(unittest.TestCase):
    def session(self, seed=17):
        now = [0.]
        return TrainingSession(seed, FOG_LESSON, clock=lambda: now[0], assessment_mode='choice'), now

    def act(self, session, action, **kwargs):
        return session.action(dict(runId=session.run_id, revision=session.revision,
            actionId=f'{len(session.actions)}-{action}', action=action, **kwargs))

    def finish(self, session, now, wrong=False):
        self.act(session, 'ready')
        for probe in session.probes:
            now[0] += 70
            self.assertEqual(session.state()['phase'], 'checkpoint')
            result = self.act(session, 'answer', checkpointId=probe['id'],
                choice=(probe['correct'] + int(wrong)) % 4)
            self.assertEqual(result['feedback']['correct'], not wrong)
            self.act(session, 'continue')
        now[0] += 40
        return session.state()

    def test_twenty_seeds_have_scored_causal_stationary_short_worlds(self):
        orders = set()
        for seed in range(20):
            session, _ = self.session(seed)
            world, slots, probes = build_fog_lesson(seed)
            self.assertEqual((world, slots, probes), build_lesson(seed, FOG_LESSON))
            self.assertEqual((world, slots, probes), build_fog_lesson(seed))
            validate_scenario(world); validate_environment(world['environment'], 210)
            self.assertEqual((world['duration'], slots, world['runwayReservations']), (210, [], []))
            self.assertEqual([p['at'] for p in probes], [60, 120, 180])
            self.assertEqual((session.target, world['fogApronSourceId']), ('A1', 'osm-way-105366849'))
            self.assertEqual(world['demoQuestions'], [])
            self.assertEqual(world['flightShowcases'], [])
            self.assertEqual(world['groundVehicles'], [])
            self.assertEqual(world['incidents'], [])
            for aircraft in world['aircraft']:
                self.assertEqual(aircraft['waypoints'][0]['t'], 0)
                self.assertEqual(aircraft['waypoints'][-1]['t'], 210)
                poses = [{k: v for k, v in p.items() if k != 't'} for p in aircraft['waypoints']]
                self.assertTrue(all(p == poses[0] for p in poses))
            self.assertTrue(all(e['aircraftId'] == 'A1' for e in world['events']))
            self.assertTrue(all(e['receiptTime'] <= 210 for e in world['events']))
            for probe in probes:
                known = {f['event_id'] for f in received_facts(world, probe['at'])}
                self.assertTrue(set(probe['evidenceIds']) <= known)
                check_references(probe['evidenceIds'], session.records, session.scenario['scenarioId'], probe['at'])
                self.assertEqual((len(probe['choices']), len(set(probe['choices'])), probe['aircraftId']), (4, 4, 'A1'))
            orders.add(tuple(p['correct'] for p in probes))
        self.assertGreater(len(orders), 10)

    def test_visual_recovery_and_procedure_status_do_not_authorise_departure(self):
        world, _, _ = build_fog_lesson(17)
        frames = world['environment']['frames']
        self.assertEqual(next(f for f in frames if f['t'] == 100)['fogExtinctionPerMetre'], 0)
        def current(cutoff):
            facts = build_context(world, 'A1', cutoff, 'current', ['movement_condition'])['facts']
            return next(f for f in facts if f['property'] == 'movement_condition' and f['status'] == 'current')
        self.assertIn('procedures in force', current(60)['value'])
        self.assertIn('safeguarding remains', current(60)['value'])
        self.assertIn('procedures in force', current(100)['value'])  # View is already clear.
        self.assertIn('procedures cancelled; safeguarding remains; departure held', current(120)['value'])
        self.assertIn('cancellation requested; confirmation pending', current(150)['value'])
        self.assertIn('safeguarding cancelled; departure clearance still unconfirmed', current(180)['value'])
        self.assertEqual(current(210)['event_id'], 'R008')
        self.assertIn('condensed practice exercise', world['trainingObjective'])
        self.assertIn('short scored practice', world['provenance']['limitations'])
        self.assertEqual(world['lessonTiming']['duration'], 210)
        self.assertEqual(world['lessonTiming']['demonstrationDuration'], 3600)

    def test_wrong_answers_feedback_cutoffs_and_a1_later_reports(self):
        for seed in range(20):
            session, now = self.session(seed)
            self.act(session, 'ready')
            for probe in session.probes:
                now[0] += 100
                state = session.state()
                self.assertEqual((state['phase'], state['sourceTime'], state['rate']), ('checkpoint', probe['at'], 0))
                self.assertEqual(set(state['checkpoint']), {'id', 'at', 'question', 'choices'})
                self.assertIsNone(state['feedback']); self.assertEqual(state['reviews'], [])
                snap = session.snapshot()
                self.assertEqual({r['source_id'] for r in snap['sourceRecords']},
                                 {e['id'] for e in session.scenario['events'] if e['receiptTime'] <= probe['at']})
                with self.assertRaises(ActionConflict):
                    session.begin_question(dict(scenarioId=session.scenario['scenarioId'], checkpoint=probe['at']))
                result = self.act(session, 'answer', checkpointId=probe['id'], choice=(probe['correct']+1)%4)
                feedback = result['feedback']
                self.assertFalse(feedback['correct']); self.assertEqual(feedback['laterReports'], [])
                self.assertNotEqual(feedback['chosen'], feedback['correctAnswer'])
                self.assertTrue(feedback['explanation'])
                self.assertTrue(all(e['receiptTime'] <= probe['at'] and e['aircraftId'] == 'A1' for e in feedback['reports']))
                now[0] += 20
                self.assertEqual(session.state()['sourceTime'], probe['at'])
                self.act(session, 'continue')
            now[0] += 40
            debrief = session.state()
            self.assertEqual((debrief['phase'], debrief['sourceTime'], debrief['score'], debrief['answered']), ('debrief', 210, 0, 3))
            first, second, third = debrief['reviews']
            self.assertEqual([e['id'] for e in first['laterReports']], ['R006', 'R007', 'R008'])
            self.assertEqual([e['id'] for e in second['laterReports']], ['R007', 'R008'])
            self.assertEqual(third['laterReports'], [])
            for review in debrief['reviews']:
                self.assertTrue(all(review['cutoff'] < e['receiptTime'] <= 210 and e['aircraftId'] == 'A1' for e in review['laterReports']))

    def test_retry_next_wrap_and_stale_or_duplicate_actions(self):
        session, now = self.session()
        original = copy.deepcopy(session.scenario); original.pop('scenarioId')
        self.finish(session, now)
        old_run = session.run_id
        body = dict(runId=old_run, revision=session.revision, actionId='retry', action='retry')
        retried = session.action(body)
        self.assertEqual(session.action(body), retried)
        self.assertNotEqual(retried['runId'], old_run)
        current = copy.deepcopy(session.scenario); current.pop('scenarioId')
        self.assertEqual(current, original)
        self.assertEqual((retried['phase'], retried['score'], retried['answered'], retried['targetAircraft']), ('briefing', 0, 0, 'A1'))
        with self.assertRaises(ActionConflict):session.action(dict(body, action='next'))
        with self.assertRaises(ActionConflict):session.action(dict(body, actionId='old-run', action='ready'))
        self.act(session, 'ready')
        with self.assertRaises(ActionConflict):
            session.action(dict(runId=session.run_id, revision=0, actionId='stale', action='ready'))
        for probe in session.probes:
            now[0] += 70; session.state()
            answer = dict(runId=session.run_id, revision=session.revision, actionId=probe['id'], action='answer', checkpointId=probe['id'], choice=probe['correct'])
            accepted = session.action(answer); self.assertEqual(session.action(answer), accepted)
            with self.assertRaises(ActionConflict):session.action(dict(answer, choice=(probe['correct']+1)%4))
            self.act(session, 'continue')
        now[0] += 40; session.state()
        body = dict(runId=session.run_id, revision=session.revision, actionId='next', action='next')
        wrapped = session.action(body); self.assertEqual(session.action(body), wrapped)
        self.assertEqual((wrapped['exercise'], wrapped['targetAircraft']), ('surface_conflict', 'A2'))
        self.assertNotIn('environment', session.scenario)
        previous = TrainingSession(17, 'late_baggage', clock=lambda: now[0], assessment_mode='choice')
        self.finish(previous, now)
        self.assertEqual(self.act(previous, 'next')['exercise'], FOG_LESSON)
        self.assertEqual(previous.scenario['duration'], 210)
        for mode in ('demo', 'continuous'):
            legacy = TrainingSession(17, 'late_baggage', mode, clock=lambda: 0)
            legacy.phase = 'debrief'
            self.assertEqual(self.act(legacy, 'next')['exercise'], 'surface_conflict')

    def test_defaults_conflicting_environments_and_mode_boundaries(self):
        for case in EXERCISES:
            session = TrainingSession(17, case, clock=lambda: 0)
            if case == FOG_LESSON:
                self.assertEqual(session.scenario['environment']['kind'], 'fog')
            else:self.assertNotIn('environment', session.scenario)
        for mode in ('demo', 'continuous'):
            with self.assertRaisesRegex(ValueError, '210-second lesson'):TrainingSession(17, FOG_LESSON, mode)
            fog_demo = TrainingSession(17, 'fog_visibility', mode, clock=lambda: 0)
            clear_compat = TrainingSession(17, 'fog_visibility', mode, clock=lambda: 0, environment='clear')
            self.assertEqual(fog_demo.scenario['environment'], clear_compat.scenario['environment'])
            self.assertEqual(fog_demo.scenario['duration'], 3600)
        for environment in ('clear', 'rain', 'snow', 'dusk'):
            with self.assertRaisesRegex(ValueError, 'requires its fog timeline'):
                TrainingSession(17, FOG_LESSON, environment=environment)
        self.assertEqual(TrainingSession(17, FOG_LESSON, environment='fog').scenario['environment'], self.session()[0].scenario['environment'])

    def test_cli_rejects_conflicting_lesson_options_before_model_load(self):
        from backend.training import main
        for options in (['--mode', 'demo'], ['--mode', 'continuous'], ['--environment', 'clear'], ['--environment', 'snow']):
            with patch('sys.argv', ['training', '--exercise', FOG_LESSON, *options]), patch('backend.training_adapter.TrainingAdapter.load') as load, patch('sys.stderr'):
                with self.assertRaises(SystemExit) as error:main()
                self.assertEqual(error.exception.code, 2); load.assert_not_called()

    def test_service_checkpoint_guards_preserve_all_received_sources(self):
        session, now = self.session()
        with tempfile.TemporaryDirectory() as folder:
            app = training_app(MockAdapter([]), Settings('mock-model', 256, image_max_side=672), session,
                               token='test-token', audit_path=Path(folder)/'calls.jsonl')
            with TestClient(app) as client:
                headers = {'Authorization': 'Bearer test-token'}
                self.act(session, 'ready'); now[0] = 61
                state = client.get('/training', headers=headers).json()
                self.assertEqual((state['phase'], state['targetAircraft']), ('checkpoint', 'A1'))
                snap = client.get('/traffic', headers=headers).json()
                self.assertEqual({s['source_id'] for s in snap['sourceRecords']}, {'R001', 'R002', 'R003', 'R004', 'R005'})
                blocked = client.post('/conversation', headers=headers,
                    json=dict(scenarioId=session.scenario['scenarioId'], checkpoint=60))
                self.assertEqual(blocked.status_code, 409)
                self.assertNotIn('correct', state['checkpoint'])
                self.assertIsNone(state['feedback']); self.assertEqual(state['reviews'], [])

    def test_existing_worlds_match_twenty_seed_prechange_fingerprints(self):
        # Regenerated from an isolated git archive of pre-fourth-lesson commit
        # 92fd08bbb1db3f9c89af09a97b711846317ae8db, never from current output.
        # Complete worlds, reservations and probes, all 20 seeds and 8 cases.
        # Only float serialization is normalized; no fields are discarded.
        baseline = {
            'surface_conflict': 'a8daf596c22d37f9706ed8663a93d417a83d3fd1798e1bebec6f9ef013bee3a6',
            'late_arrival': '38e9b1d4cd683a4159ae4859c7ae60884515a39d13a8b7334a13c567dedd644a',
            'late_baggage': 'dde2b374fb25d8f87e0b7b1690069a62bf4650ce20e09fefd65a398b590bc429',
            'rejected_takeoff': 'ea8474fa0cb80d015a9d70182cc80a4f6d37362421f8c31704aab87a5b67d9c6',
            'occupied_runway_go_around': 'e64898e171e1c38e0f478acf0da3d298d7475345b46d3ff83a91b43e4f8bc1d1',
            'runway_incursion': '1146e65fb998af68e17c7a4f0e5f85d11ec82ae17e168c024015bbfd0cee911c',
            'water_landing': '71c6c2ac7ba4279073c113919f9c66d7f0561dd8c95f5d82185e9038ad4630ab',
            'fog_visibility': 'a5aa420ef418fcd7c885ebd6433c0831a800e279c37df0c4d2e120a56f9650df',
        }
        for case, expected in baseline.items():
            digest = hashlib.sha256()
            builder = build_demonstration if case in DEMONSTRATIONS else build_lesson
            for seed in range(20):digest.update(fingerprint_bytes(builder(seed, case)))
            self.assertEqual(digest.hexdigest(), expected, case)

    def test_portable_fingerprints_keep_meaningful_world_reservation_and_probe_changes(self):
        original = build_lesson(17, 'surface_conflict')
        expected = fingerprint_bytes(original)
        tiny = copy.deepcopy(original)
        waypoint = tiny[0]['aircraft'][0]['waypoints'][0]
        waypoint['x'] = math.nextafter(waypoint['x'], math.inf)
        self.assertEqual(fingerprint_bytes(tiny), expected)
        mutations = [
            lambda w: w[0]['aircraft'][0]['waypoints'][0].update(x=w[0]['aircraft'][0]['waypoints'][0]['x'] + 1e-8),
            lambda w: w[0]['events'][0].update(receiptTime=w[0]['events'][0]['receiptTime'] + 1e-6),
            lambda w: w[0]['events'][0].update(message='Changed report'),
            lambda w: w[0]['events'][0]['facts'][0].update(value='Changed fact'),
            lambda w: w[1][0].update(end=w[1][0]['end'] + .001),
            lambda w: w[2][0].update(correct=(w[2][0]['correct'] + 1) % 4),
            lambda w: w[2][0].update(evidenceIds=['Different source']),
            lambda w: w[0]['aircraft'].reverse(),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = copy.deepcopy(original); mutate(changed)
                self.assertNotEqual(fingerprint_bytes(changed), expected)
        self.assertEqual(fingerprint_bytes({'zero': -0.0}), fingerprint_bytes({'zero': 0.0}))
        self.assertNotEqual(fingerprint_bytes({'value': True}), fingerprint_bytes({'value': 1}))
        for invalid in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):fingerprint_bytes({'value': invalid})


if __name__ == '__main__':unittest.main()
