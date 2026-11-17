"""Controller replay: one cutoff, read-only scenario, stale answers and run isolation."""
import copy
import json
import unittest
from pathlib import Path

from backend.bluebird_inbound import BLUEBIRD_787, HANDOFF, build_bluebird_inbound
from backend.conversation.turns import run_turn
from backend.fleet_scenarios import build_fleet
from backend.replay_session import LEAD_CASE, REPLAY_CASES, ReplayConflict, ReplaySession
from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter

SETTINGS = Settings('mock-model', 256, image_max_side=672)
GO_AROUND = 'go-around: Runway 09R occupied by TRN102'


def reply(**overrides):
    base = dict(status='answer', referent={'aircraftId': 'A1', 'flightInstance': 'TRN101'}, claims=[],
                unknowns=[], explanationChanged=None, changesNotDiscussed=[], memoryUpdate=None,
                rationale='', observations=[])
    base.update(overrides)
    return json.dumps(base)


def claim(fid, value, status, eid):
    return {'fact_id': fid, 'value': value, 'status': status, 'evidence_ids': [eid]}


GO_AROUND_REPLY = reply(claims=[claim('F003:movement_condition', GO_AROUND, 'current', 'F003')])


class ReplayCase(unittest.TestCase):
    def replay(self, exercise=LEAD_CASE, seed=17):
        now = [0.]
        session = ReplaySession(seed, exercise, clock=lambda: now[0])
        self.count = 0
        return session, now

    def act(self, s, action, **values):
        self.count += 1
        return s.action(dict(actionId=f'a{self.count}', runId=s.run_id, viewRevision=s.view_revision,
                             action=action, **values))

    def ask(self, s, adapter, question='What is the latest reported movement for this flight?', request=None):
        self.count += 1
        return s.ask(dict(requestId=request or f'q{self.count}', runId=s.run_id, viewRevision=s.view_revision,
                          question=question), adapter, SETTINGS, run_turn)

    def prompt(self, adapter, index=-1):
        return adapter.calls[index][0].messages[0][1]


class LeadCase(ReplayCase):
    def test_a380_leads_and_the_787_handoff_follows(self):
        self.assertEqual(REPLAY_CASES[:2], (LEAD_CASE, BLUEBIRD_787))
        s, _ = self.replay()
        view = s.view()
        self.assertEqual((view['selectedAircraft'], view['selectedFlight'], view['readOnly']), ('A1', 'TRN101', True))
        types = {a['aircraftId']: a['aircraftType'] for a in view['scene']}
        self.assertEqual((types['A1'], types['A2']), ('a380_800', 'b737_800'))

    def test_every_replay_case_is_the_drivers_world_over_twenty_seeds(self):
        from backend.training_session import TrainingSession
        for exercise in REPLAY_CASES:
            for seed in range(20):
                replay = ReplaySession(seed, exercise, clock=lambda: 0.)
                mode = 'lesson' if exercise == 'stand_clearance' else 'continuous'
                driver = TrainingSession(seed, exercise, mode, clock=lambda: 0.).scenario
                ours = replay.scenario()
                # The lesson driver adds its visual weather profile; reports, aircraft and motion must match.
                for key in ('events', 'aircraft', 'runwayReservations'):
                    self.assertEqual(ours.get(key), driver.get(key), (exercise, seed, key))
                end = replay.view()
                self.assertEqual(replay.action(dict(actionId='e', runId=replay.run_id, viewRevision=end['viewRevision'],
                                                    action='seek', cutoff=replay.end))['reports'][-1]['id'],
                                 max(ours['events'], key=lambda e: (e['receiptTime'], e['id']))['id'])

    def test_scenario_is_the_drivers_and_never_changes(self):
        s, _ = self.replay()
        authored, _, _ = build_fleet(17, LEAD_CASE)
        mine = s.scenario()
        self.assertEqual({k: v for k, v in mine.items() if k != 'scenarioId'},
                         {k: v for k, v in authored.items() if k != 'scenarioId'})
        mine['events'].clear()
        mine['runwayReservations'][0]['end'] = 0
        self.act(s, 'seek', cutoff=301)
        self.act(s, 'note', text='Runway still occupied; next approach unconfirmed.')
        self.act(s, 'select', aircraftId='A2')
        self.act(s, 'play')
        self.assertEqual(s.verify_unchanged(), ReplaySession(17, clock=lambda: 0.).scenario_hash)
        self.assertEqual(len(s.scenario()['events']), 5)
        self.assertEqual(s.scenario()['runwayReservations'], authored['runwayReservations'])

    def test_report_is_excluded_before_receipt_and_included_at_receipt(self):
        s, _ = self.replay()
        before = self.act(s, 'seek', cutoff=104.999)
        self.assertEqual([r['id'] for r in before['reports']], ['F001', 'F002'])
        # The go-around is already in the authored motion; its report is not yet received.
        self.assertEqual(next(a for a in before['scene'] if a['aircraftId'] == 'A1')['phase'], 'go_around')
        at = self.act(s, 'jump', markerId='R-F003')
        self.assertEqual(at['cutoff'], 105)
        row = at['reports'][-1]
        self.assertEqual((row['id'], row['eventTime'], row['receiptTime'], row['ageSeconds'], row['sinceReceiptSeconds']),
                         ('F003', 104, 105, 1, 0))
        self.assertEqual((row['sourceKind'], row['source']), ('airport_report', 'exercise-operations'))

    def test_timeline_markers_never_carry_report_content(self):
        s, _ = self.replay()
        view = s.view()
        text = json.dumps(dict(view, scene=None))
        for e in s.scenario()['events'][1:]:
            self.assertNotIn(e['message'], text)
            self.assertNotIn(e['facts'][0]['value'], text)
        self.assertEqual([m['id'] for m in view['timeline']],
                         ['R-F001', 'R-F002', 'P-A1-go_around', 'R-F003', 'P-A1-climb', 'R-F004', 'R-F005'])
        self.assertEqual([m['passed'] for m in view['timeline']], [True] + [False] * 6)
        for marker in view['timeline'][1:]:
            self.assertEqual(marker['eventTime'], -1)
            self.assertIn(marker['label'], ('Movement change', 'Report or observation received'))
        self.assertEqual(self.act(s, 'seek', cutoff=s.end + .005)['cutoff'], s.end)

    def test_what_changed_across_receipt_go_around_and_climb(self):
        s, _ = self.replay()
        self.assertEqual(s.changes('A2', 0, 85), ['F002:movement_status'])
        self.assertEqual(s.changes('A1', 85, 105), ['F003:movement_condition'])
        self.assertEqual(s.changes('A1', 105, 113), ['F004:movement_status'])
        self.act(s, 'jump', markerId='R-F004')
        self.assertEqual(s.view()['changedSince'], dict(cutoff=112, factIds=['F004:movement_status']))
        end = self.act(s, 'jump', markerId='R-F005')
        facts = {f['factId']: f for r in end['selectedReports'] for f in r['facts']}
        self.assertEqual(facts['F003:movement_condition']['status'], 'superseded')
        self.assertEqual((facts['F005:movement_condition']['status'], facts['F005:movement_condition']['value']),
                         ('current', 'runway still occupied; another approach unconfirmed'))
        self.assertEqual(facts['F004:movement_status']['status'], 'current')  # no landing is ever reported

    def test_both_aircraft_stay_separate(self):
        s, _ = self.replay()
        view = self.act(s, 'jump', markerId='R-F004')
        a380, b737 = (next(a for a in view['scene'] if a['aircraftId'] == i) for i in ('A1', 'A2'))
        self.assertGreater(a380['y'], 0)
        self.assertEqual((b737['y'], b737['phase']), (0, 'runway_occupied'))
        self.assertEqual({r['flightInstance'] for r in view['selectedReports']}, {'TRN101'})
        switched = self.act(s, 'select', aircraftId='A2')
        self.assertEqual((switched['selectedFlight'], [r['id'] for r in switched['selectedReports']]), ('TRN102', ['F002']))
        self.assertEqual(switched['viewRevision'], view['viewRevision'] + 1)
        self.assertEqual(self.act(s, 'select', aircraftId='A2')['viewRevision'], switched['viewRevision'])

    def test_seeking_back_and_forward_gives_the_same_view_for_one_cutoff(self):
        s, _ = self.replay()
        first = self.act(s, 'seek', cutoff=90)
        later = self.act(s, 'seek', cutoff=301)
        self.assertEqual(len(later['reports']), 5)
        back = self.act(s, 'seek', cutoff=90)
        for key in ('reports', 'scene', 'evidenceDigest', 'changedSince', 'cameraObservations'):
            self.assertEqual(back[key], first[key], key)
        self.assertEqual([r['id'] for r in back['reports']], ['F001', 'F002'])

    def test_play_pause_and_rates_use_the_replays_own_clock(self):
        s, now = self.replay()
        self.act(s, 'play', rate=4.)
        now[0] = 10
        self.assertEqual(s.view()['cutoff'], 40)
        self.act(s, 'pause')
        now[0] = 100
        self.assertEqual(s.view()['cutoff'], 40)
        self.act(s, 'play')
        now[0] = 1000
        view = s.view()
        self.assertEqual((view['cutoff'], view['playing']), (s.end, False))
        with self.assertRaises(ReplayConflict):
            self.act(s, 'play')
        with self.assertRaises(ValueError):
            self.act(s, 'seek', cutoff=s.end + 1)  # beyond float rounding
        with self.assertRaises(ValueError):
            self.act(s, 'play', rate=30)


class Controls(ReplayCase):
    def test_repeated_actions_apply_once_and_reused_ids_conflict(self):
        s, _ = self.replay()
        self.act(s, 'seek', cutoff=120)
        body = dict(actionId='note-1', runId=s.run_id, viewRevision=s.view_revision, action='note', text='Check TRN102.')
        first = s.action(copy.deepcopy(body))
        self.act(s, 'seek', cutoff=200)
        self.assertEqual(s.action(copy.deepcopy(body)), first)  # a retry after the view moved on
        self.assertEqual(len(s.notes), 1)
        with self.assertRaises(ReplayConflict):
            s.action(dict(body, text='Different'))
        with self.assertRaises(ReplayConflict):
            s.action(dict(actionId='old', runId=s.run_id, viewRevision=0, action='pause'))

    def test_notes_are_annotations_tied_to_run_and_cutoff(self):
        s, _ = self.replay()
        self.act(s, 'seek', cutoff=110)
        revision = s.view_revision
        view = self.act(s, 'note', text='  TRN101 went around; TRN102 still on 09R.  ')
        note = view['notes'][0]
        self.assertEqual((note['runId'], note['cutoff'], note['aircraftId'], note['flightInstance'], note['kind']),
                         (s.run_id, 110, 'A1', 'TRN101', 'annotation'))
        self.assertEqual(note['text'], 'TRN101 went around; TRN102 still on 09R.')
        self.assertEqual(note['evidenceIds'], ['F001', 'F003'])  # F004 and F005 are not yet received
        self.assertEqual((view['viewRevision'], view['reports']), (revision, s.view()['reports']))
        for text in ('', ' ', 'x' * 281, None):
            with self.assertRaises(ValueError):
                self.act(s, 'note', text=text)

    def test_runs_are_isolated(self):
        a, _ = self.replay()
        b, _ = self.replay()
        self.assertNotEqual(a.run_id, b.run_id)
        self.assertEqual(a.scenario_hash, b.scenario_hash)
        self.act(a, 'seek', cutoff=113)
        self.act(a, 'note', text='Run A only.')
        self.ask(a, MockAdapter([reply(claims=[claim('F004:movement_status', 'climbing away after go-around', 'current', 'F004')])]))
        with self.assertRaises(ReplayConflict):
            b.action(dict(actionId='x', runId=a.run_id, viewRevision=0, action='pause'))
        with self.assertRaises(ReplayConflict):
            b.begin_question(dict(requestId='q', runId=a.run_id, viewRevision=0, question='Latest?'))
        view = b.view()
        self.assertEqual((view['cutoff'], view['notes'], b.memory_turns), (0, [], []))
        self.assertEqual(len(a.memory_turns), 1)

    def test_camera_observations_follow_the_same_cutoff(self):
        s, _ = self.replay()
        self.act(s, 'seek', cutoff=100)
        body = dict(actionId='c1', runId=s.run_id, aircraftId='A2', kind='aircraft_on_runway', value='present',
                    confidence=.8, captureTime=98)
        with self.assertRaises(ValueError):
            s.observe(dict(body, actionId='c0', captureTime=101))
        view = s.observe(body)
        self.assertEqual(s.observe(body), view)
        seen = view['cameraObservations'][0]
        self.assertEqual((seen['sourceKind'], seen['flightInstance'], seen['captureTime'], seen['ageSeconds']),
                         ('camera_observation', 'TRN102', 98, 2))
        self.assertNotIn('camera_observation', {r['sourceKind'] for r in view['reports']})
        self.assertEqual(self.act(s, 'seek', cutoff=97)['cameraObservations'], [])
        self.assertEqual(len(self.act(s, 'seek', cutoff=98)['cameraObservations']), 1)
        s.verify_unchanged()


class AssistantContext(ReplayCase):
    def test_answer_uses_the_selected_aircraft_and_cutoff(self):
        s, _ = self.replay()
        self.act(s, 'jump', markerId='R-F003')
        adapter = MockAdapter([GO_AROUND_REPLY])
        result = self.ask(s, adapter, 'Why is TRN101 going around?')
        self.assertTrue(result['accepted'])
        self.assertEqual((result['cutoff'], result['aircraftId'], result['runId']), (105, 'A1', s.run_id))
        self.assertIn('Event 104 s; received 105 s. [F003]', result['display']['answer'])
        prompt = self.prompt(adapter)
        self.assertIn('F003', prompt)
        for later in ('F004', 'F005', 'climbing away', 'another approach unconfirmed'):
            self.assertNotIn(later, prompt)

    def test_retry_returns_the_stored_answer_without_a_second_model_call(self):
        s, _ = self.replay()
        self.act(s, 'jump', markerId='R-F003')
        adapter = MockAdapter([GO_AROUND_REPLY])
        body = dict(requestId='q', runId=s.run_id, viewRevision=s.view_revision, question='Why is TRN101 going around?')
        first = s.ask(dict(body), adapter, SETTINGS, run_turn)
        self.act(s, 'seek', cutoff=200)
        self.assertEqual(s.ask(dict(body), adapter, SETTINGS, run_turn), first)
        self.assertEqual(len(adapter.calls), 1)
        with self.assertRaises(ReplayConflict):
            s.ask(dict(body, question='Something else?'), adapter, SETTINGS, run_turn)

    def test_answer_arriving_after_a_seek_is_discarded(self):
        s, _ = self.replay()
        self.act(s, 'jump', markerId='R-F003')
        test = self

        class SeeksWhileAnswering(MockAdapter):
            def _generate(self, request, effective):
                test.act(s, 'seek', cutoff=60)
                return super()._generate(request, effective)

        with self.assertRaises(ReplayConflict):
            self.ask(s, SeeksWhileAnswering([GO_AROUND_REPLY]), request='late')
        self.assertEqual((s.memory_turns, s.memory_intents, s.pending), ([], [], None))
        self.assertNotIn('late', s._answers)
        view = s.view()
        self.assertEqual((view['cutoff'], view['assistantPending']), (60, False))

    def test_answer_for_a_previously_selected_aircraft_is_discarded(self):
        s, _ = self.replay()
        self.act(s, 'jump', markerId='R-F003')
        ticket, _ = s.begin_question(dict(requestId='q', runId=s.run_id, viewRevision=s.view_revision, question='Latest?'))
        with self.assertRaises(ReplayConflict):  # one question per view
            s.begin_question(dict(requestId='q2', runId=s.run_id, viewRevision=s.view_revision, question='Latest?'))
        self.act(s, 'select', aircraftId='A2')
        self.assertFalse(s.finish_question(ticket, dict(accepted=True)))
        self.assertEqual((s._answers, s.pending), ({}, None))
        # The new view can be asked about straight away.
        ticket, _ = s.begin_question(dict(requestId='q3', runId=s.run_id, viewRevision=s.view_revision, question='Latest?'))
        self.assertEqual((ticket['aircraftId'], ticket['flightInstance']), ('A2', 'TRN102'))

    def test_backward_seek_leaves_later_answers_out_of_the_context(self):
        s, _ = self.replay()
        self.act(s, 'jump', markerId='R-F004')
        adapter = MockAdapter([reply(claims=[claim('F004:movement_status', 'climbing away after go-around', 'current', 'F004')]),
                               reply(claims=[claim('F001:route', 'approach to Runway 09R', 'current', 'F001')]),
                               'not json'])
        self.assertTrue(self.ask(s, adapter)['accepted'])
        self.act(s, 'seek', cutoff=90)
        self.assertTrue(self.ask(s, adapter)['accepted'])
        earlier = self.prompt(adapter)
        self.assertIn('"previousAnswer": null', earlier)
        self.assertNotIn('"atReplayTime": 113', earlier)
        self.assertNotIn('F004', earlier)
        self.assertNotIn('climbing away', earlier)
        self.act(s, 'jump', markerId='R-F005')
        self.ask(s, adapter)
        self.assertIn('"atReplayTime": 113', self.prompt(adapter))  # the latest visible answer returns going forward

    def test_asking_pauses_playback_at_one_cutoff(self):
        s, now = self.replay()
        self.act(s, 'seek', cutoff=105)
        self.act(s, 'play')
        now[0] = 3
        adapter = MockAdapter([reply(claims=[claim('F003:movement_condition', GO_AROUND, 'current', 'F003')])])
        result = s.ask(dict(requestId='q', runId=s.run_id, viewRevision=s.view_revision, question='Latest?'),
                       adapter, SETTINGS, run_turn)
        now[0] = 50
        self.assertEqual((result['cutoff'], s.view()['cutoff'], s.view()['playing']), (108, 108, False))


class BluebirdHandoff(ReplayCase):
    def test_both_contacts_identity_and_the_authored_gap(self):
        s, _ = self.replay(BLUEBIRD_787)
        view = self.act(s, 'seek', cutoff=75)
        kinds = {r['sourceKind'] for r in view['reports']}
        self.assertEqual(kinds, {'airborne_observation'})  # no airport report inside the gap
        self.assertEqual({r['flightInstance'] for r in view['reports']}, {'TRN101', 'BLUEBIRD-TRAFFIC'})
        latest = view['selectedReports'][-1]
        self.assertEqual((view['selectedFlight'], latest['id'], latest['eventTime'], latest['ageSeconds']),
                         ('TRN101', 'BB-AIR0-10', 60, 15))
        self.assertEqual(HANDOFF - latest['eventTime'], 30)
        self.assertTrue(all(r['flightInstance'] == 'TRN101' for r in view['selectedReports']))
        scene = {a['aircraftId']: a for a in view['scene']}
        self.assertFalse(scene['A1']['visible'])  # no trajectory is drawn across the gap
        self.assertFalse(scene['A5']['visible'])
        self.assertNotIn('x', scene['A1'])
        traffic = self.act(s, 'select', aircraftId='A5')
        self.assertEqual({r['flightInstance'] for r in traffic['selectedReports']}, {'BLUEBIRD-TRAFFIC'})

    def test_airport_sequence_matches_the_original_787_replay_at_matched_cutoffs(self):
        for seed in (0, 17):
            handoff, _ = self.replay(BLUEBIRD_787, seed)
            original, _ = self.replay('fleet_b787_priority_landing', seed)
            airport = [m['time'] for m in original.markers if m['kind'] == 'received']
            self.assertEqual(len(airport), 6)
            for t in [0, 49.999] + airport + [original.end]:
                a = self.act(original, 'seek', cutoff=t)
                b = self.act(handoff, 'seek', cutoff=min(handoff.end, t + HANDOFF))
                def rows(view):
                    return [(r['id'], r['flightInstance'], r['message'], r['ageSeconds'], r['sinceReceiptSeconds'],
                             [(f['property'], f['value'], f['status']) for f in f_rows(r)])
                            for r in view['reports'] if r['sourceKind'] == 'airport_report']
                def f_rows(r):
                    return r['facts']
                self.assertEqual(rows(a), rows(b), (seed, t))
                self.assertEqual({k: v for k, v in a['scene'][0].items()}, {k: v for k, v in b['scene'][0].items()}, (seed, t))
        last = self.act(handoff, 'seek', cutoff=handoff.end)['selectedReports'][-1]
        self.assertEqual(last['facts'][0]['value'], 'hold: inspection underway; recovery requested; runway release unconfirmed')

    def test_handoff_scenario_is_the_drivers(self):
        s, _ = self.replay(BLUEBIRD_787)
        authored, _, _ = build_bluebird_inbound(17, BLUEBIRD_787)
        self.assertEqual({k: v for k, v in s.scenario().items() if k != 'scenarioId'},
                         {k: v for k, v in authored.items() if k != 'scenarioId'})


class Service(unittest.TestCase):
    AUTH = {'Authorization': 'Bearer test-token'}

    def serve(self, replies):
        import tempfile
        from pathlib import Path
        from fastapi.testclient import TestClient
        from backend.replay import replay_app
        self.replay = ReplaySession(17, clock=lambda: 0.)
        self.adapter = MockAdapter(replies)
        self.audit = Path(tempfile.mkdtemp()) / 'replay.jsonl'
        client = TestClient(replay_app(self.adapter, SETTINGS, self.replay, token='test-token', audit_path=self.audit))
        self.addCleanup(client.__exit__, None, None, None)
        return client.__enter__()

    def post(self, client, path, **body):
        return client.post(path, headers=self.AUTH, json=dict(runId=self.replay.run_id, **body))

    def test_token_bounds_and_read_only_health(self):
        client = self.serve([])
        self.assertEqual(client.get('/replay').status_code, 401)
        self.assertEqual(client.post('/replay/action', json={}).status_code, 401)
        self.assertEqual(client.post('/replay/action', headers=self.AUTH, content=b'x' * 20_000).status_code, 413)
        self.assertEqual(client.post('/replay/action', headers=self.AUTH, content=b'[').status_code, 422)
        health = client.get('/health', headers=self.AUTH).json()
        self.assertEqual((health['exercise'], health['readOnly'], health['scenarioHash']),
                         (LEAD_CASE, True, self.replay.scenario_hash))

    def test_seek_question_and_scene_share_one_cutoff(self):
        client = self.serve([GO_AROUND_REPLY])
        view = self.post(client, '/replay/action', actionId='a1', viewRevision=0, action='jump', markerId='R-F003').json()
        answer = self.post(client, '/replay/question', requestId='q1', viewRevision=view['viewRevision'],
                           question='Why is TRN101 going around?')
        self.assertEqual(answer.status_code, 200)
        self.assertTrue(answer.json()['accepted'])
        traffic = client.get('/traffic', headers=self.AUTH).json()
        self.assertEqual((traffic['serverTime'], answer.json()['cutoff'], traffic['clock']['state']), (105, 105, 'replay'))
        self.assertEqual(traffic['scenario']['scenarioId'], traffic['replay']['scenarioId'])
        self.assertEqual((traffic['training']['mode'], traffic['training']['revision'], traffic['training']['runId']),
                         ('replay', 0, self.replay.run_id))
        audit = json.loads(self.audit.read_text())
        self.assertEqual((audit['requestId'], audit['cutoff'], audit['scenarioHash']), ('q1', 105, self.replay.scenario_hash))
        retry = self.post(client, '/replay/question', requestId='q1', viewRevision=view['viewRevision'],
                          question='Why is TRN101 going around?')
        self.assertEqual((retry.json(), len(self.adapter.calls)), (answer.json(), 1))

    def test_conflicts_and_invalid_requests(self):
        client = self.serve([])
        self.assertEqual(self.post(client, '/replay/action', actionId='a', viewRevision=9, action='pause').status_code, 409)
        self.assertEqual(self.post(client, '/replay/action', actionId='b', viewRevision=0, action='release_runway').status_code, 422)
        self.assertEqual(self.post(client, '/replay/action', actionId='c', viewRevision=0, action='seek', cutoff=-1).status_code, 422)
        self.assertEqual(client.post('/replay/action', headers=self.AUTH,
                                     json=dict(runId='other', actionId='d', viewRevision=0, action='pause')).status_code, 409)
        self.assertEqual(self.post(client, '/replay/question', requestId='q', viewRevision=3, question='Latest?').status_code, 409)
        self.assertEqual(self.post(client, '/replay/observation', actionId='o', aircraftId='A2', kind='k', value='v',
                                   confidence=.5, captureTime=50).status_code, 422)
        self.replay.verify_unchanged()

    def test_replay_without_a_model_still_serves_the_view(self):
        from fastapi.testclient import TestClient
        from backend.replay import replay_app
        self.replay = ReplaySession(17, clock=lambda: 0.)
        client = TestClient(replay_app(None, None, self.replay, token='test-token'))
        self.addCleanup(client.__exit__, None, None, None)
        client = client.__enter__()
        self.assertEqual(client.get('/health', headers=self.AUTH).json()['assistant'], False)
        view = self.post(client, '/replay/action', actionId='a', viewRevision=0, action='seek', cutoff=105)
        self.assertEqual([r['id'] for r in view.json()['reports']], ['F001', 'F002', 'F003'])
        self.assertEqual(self.post(client, '/replay/question', requestId='q', viewRevision=1, question='Latest?').status_code, 503)
        self.assertFalse(self.replay.view()['assistantPending'])


class StandBCameraSession(ReplayCase):
    SESSION = Path(__file__).resolve().parents[1] / 'outputs/checkpoint2-run/stand-b-session-observations.json'

    def stand(self, arm):
        return ReplaySession(17, 'stand_clearance', clock=lambda: 0., camera_session=self.SESSION, camera_arm=arm)

    def test_camera_sees_the_stand_clear_before_the_removal_report_and_release(self):
        s = self.stand('rgb_depth')
        self.count = 0
        view = self.act(s, 'seek', cutoff=92)
        latest = view['cameraObservations'][-1]
        self.assertEqual((latest['captureTime'], latest['visibleVehicle'], latest['onStandB']), (92, 'present', False))
        self.assertEqual(latest['sourceKind'], 'camera_observation')
        self.assertNotIn('S007', [r['id'] for r in view['reports']])  # removal report arrives at 95 s
        released = [r for r in self.act(s, 'seek', cutoff=149)['reports'] if 'released' in r['facts'][0]['value']]
        self.assertEqual(released, [])  # a clear camera view never stands in for the release report
        self.assertTrue(any('released' in r['facts'][0]['value'] for r in self.act(s, 'seek', cutoff=150)['reports']))
        s.verify_unchanged()

    def test_rgb_arm_has_no_location_and_tracking_loss_has_none_either(self):
        rgb = self.stand('rgb')
        self.count = 0
        view = self.act(rgb, 'seek', cutoff=60)
        self.assertEqual(len(view['cameraObservations']), 61)
        self.assertFalse(any('apronPositionMetres' in o for o in view['cameraObservations']))
        depth = self.stand('rgb_depth')
        self.count = 0
        lost = [o for o in self.act(depth, 'seek', cutoff=60)['cameraObservations'] if not o['trackingValid']]
        self.assertEqual(len(lost), 5)
        self.assertFalse(any('apronPositionMetres' in o for o in lost))
        occluded = next(o for o in depth.view()['cameraObservations'] if o['captureTime'] == 47)
        self.assertEqual(occluded['visibleVehicle'], 'not_detected')

    def test_backward_seek_hides_later_observations_and_runs_are_bound(self):
        s = self.stand('rgb_depth')
        self.count = 0
        self.act(s, 'seek', cutoff=200)
        back = self.act(s, 'seek', cutoff=30)
        self.assertEqual(max(o['captureTime'] for o in back['cameraObservations']), 30)
        self.assertTrue(all(o['runId'] == s.run_id for o in back['cameraObservations']))

    def test_card_wording_follows_the_latest_observation_at_the_cutoff(self):
        depth, rgb = self.stand('rgb_depth'), self.stand('rgb')
        self.count = 0
        for s in (depth, rgb):
            self.act(s, 'select', aircraftId='A3')
        card = lambda s, t: self.act(s, 'seek', cutoff=t)['cameraLatest']
        self.assertEqual(card(depth, 40)['text'], 'Fuel-transfer vehicle seen on Stand B')
        self.assertEqual(card(depth, 92)['text'], 'Fuel-transfer vehicle seen off Stand B')
        self.assertIn('est. position x 46 m, z 60 m', card(depth, 92)['meta'])
        self.assertEqual(card(depth, 47)['text'], 'Fuel-transfer vehicle not detected (not proof it has gone)')
        self.assertEqual(card(depth, 57)['text'], 'Fuel-transfer vehicle seen; position unknown (tracking lost)')
        self.assertEqual(card(rgb, 92)['text'], 'Fuel-transfer vehicle seen in view')
        self.assertIn('position not available in this arm', card(rgb, 92)['meta'])
        self.assertIn('cannot release the stand', card(rgb, 92)['warning'])
        self.assertEqual(card(depth, 92.6)['meta'].split(' · ')[:2], ['Captured 01:32', '1 s old'])
        other = next(a['id'] for a in depth._world['aircraft'] if a['id'] != 'A3')
        self.assertFalse(self.act(depth, 'select', aircraftId=other)['cameraLatest']['present'])
        plain = ReplaySession(17, LEAD_CASE, clock=lambda: 0.)
        self.assertEqual(plain.view()['cameraLatest']['present'], False)

    def test_session_is_only_for_stand_b_qualified_and_one_arm(self):
        import json, tempfile
        with self.assertRaises(ValueError):
            ReplaySession(17, LEAD_CASE, camera_session=self.SESSION, camera_arm='rgb')
        with self.assertRaises(ValueError):
            self.stand('depth')
        body = json.loads(self.SESSION.read_text())
        body['qualified'] = False
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as handle:
            json.dump(body, handle)
        with self.assertRaises(ValueError):
            ReplaySession(17, 'stand_clearance', camera_session=handle.name, camera_arm='rgb')
        plain = ReplaySession(17, 'stand_clearance', clock=lambda: 0.)
        self.assertEqual((plain.observations, plain.camera_arm), ([], None))



if __name__ == '__main__':
    unittest.main()
