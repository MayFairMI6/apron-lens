"""AR conditions in the turn handler: nothing selected (text-only) and lastSeen (tracking interruption)."""
import json
import unittest

from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter
from backend.conversation.state import SessionState
from backend.conversation.turns import REFERENT_RULE_VERSION, run_turn
from test_conversation import claim, proposal, two_rotation_scenario

SETTINGS = Settings('mock-model', 256, image_max_side=672)
A2_R1 = {'aircraftId': 'A2', 'flightInstance': 'F2-R1'}


def turn(n, revision, cutoff=35, selected=('A2', 'F2-R1'), **extra):
    request = dict(requestId=f'r{n}', turnId=f't{n}', expectedRevision=revision, cutoff=cutoff,
                   aircraftId=selected[0] if selected else None, flightInstance=selected[1] if selected else None,
                   question='Which stand is the aircraft on?')
    request.update(extra)
    return request


class TextOnly(unittest.TestCase):
    def test_nothing_selected_offers_every_flight(self):
        adapter = MockAdapter([json.dumps(proposal(status='clarify', referent=None))])
        result = run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, selected=None), adapter, SETTINGS)
        prompt = adapter.calls[0][0].messages[0][1]
        self.assertIn('Nothing is selected in the app', prompt)
        for flight in ('F1-R1', 'F2-R1', 'F2-R2'):
            self.assertIn(f'"flightInstance": "{flight}"', prompt)
        self.assertTrue(result['accepted'], result['errors'])
        self.assertIsNone(result['currentReferent'])
        self.assertFalse(result['selectionSent'])

    def test_an_accepted_answer_sets_the_referent_when_nothing_is_selected(self):
        data, session = two_rotation_scenario(), SessionState('s')
        adapter = MockAdapter([json.dumps(proposal(claims=[claim('E03:stand', 'D', 'current', 'E03')])),
                               json.dumps(proposal(claims=[claim('E03:stand', 'D', 'current', 'E03')]))])
        first = run_turn(session, data, turn(1, 0, selected=None), adapter, SETTINGS)
        self.assertTrue(first['accepted'], first['errors'])
        self.assertEqual(first['currentReferent'], A2_R1)
        self.assertEqual(REFERENT_RULE_VERSION, 'referent-rule-v3')
        run_turn(session, data, turn(2, 1, cutoff=36, selected=None, question='Has it changed?'), adapter, SETTINGS)
        self.assertIn('"currentReferent": {"aircraftId": "A2", "flightInstance": "F2-R1"}',
                      adapter.calls[1][0].messages[0][1])

    def test_a_selection_still_decides_the_referent(self):
        adapter = MockAdapter([json.dumps(proposal(status='clarify', referent=None))])
        result = run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0), adapter, SETTINGS)
        self.assertEqual(result['currentReferent'], A2_R1)
        self.assertIn('Selected in the app: aircraft A2, flight F2-R1', adapter.calls[0][0].messages[0][1])
        self.assertNotIn('"flightInstance": "F1-R1"', adapter.calls[0][0].messages[0][1])


class TrackingInterruption(unittest.TestCase):
    def test_last_seen_lists_what_changed_while_away(self):
        adapter = MockAdapter([json.dumps(proposal())])
        result = run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, cutoff=35, lastSeen=25),
                          adapter, SETTINGS)
        prompt = adapter.calls[0][0].messages[0][1]
        self.assertIn('out of the user\'s view from 25 s', prompt)
        candidates = json.loads(prompt.split('Candidate flights and received facts: ')[1].split('\nUser:')[0])
        away = {c['flightInstance']: c['changedWhileAway'] for c in candidates}
        # E03 (received at 30) supersedes E01, so both changed status while the board was out of view.
        self.assertEqual(away, {'F2-R1': ['E01:stand', 'E03:stand'], 'F2-R2': []})
        self.assertEqual(result['awayIntervals'], [25, 35])

    def test_back_in_view_excludes_reports_the_user_watched_arrive(self):
        adapter = MockAdapter([json.dumps(proposal())])
        run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, cutoff=40, lastSeen=10, backInView=25),
                 adapter, SETTINGS)
        prompt = adapter.calls[0][0].messages[0][1]
        self.assertIn('from 10 s to 25 s', prompt)
        candidates = json.loads(prompt.split('Candidate flights and received facts: ')[1].split('\nUser:')[0])
        # E03 arrives at 30, after the board came back into view at 25: watched, so not listed.
        self.assertEqual({c['flightInstance']: c['changedWhileAway'] for c in candidates}, {'F2-R1': [], 'F2-R2': []})
        with self.assertRaises(ValueError):
            run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, cutoff=40, lastSeen=10, backInView=45),
                     MockAdapter([]), SETTINGS)

    def test_separate_losses_keep_the_watched_time_between_them_out(self):
        adapter = MockAdapter([json.dumps(proposal())])
        # Out of view 0-4 and 31-40: E02 (5 s) and E03 (30 s) arrived while the board was in view.
        result = run_turn(SessionState('s'), two_rotation_scenario(),
                          turn(1, 0, cutoff=40, awayIntervals=[0, 4, 31, 40]), adapter, SETTINGS)
        prompt = adapter.calls[0][0].messages[0][1]
        self.assertIn('from 0 s to 4 s and from 31 s until now', prompt)
        candidates = json.loads(prompt.split('Candidate flights and received facts: ')[1].split('\nUser:')[0])
        self.assertEqual({c['flightInstance']: c['changedWhileAway'] for c in candidates}, {'F2-R1': [], 'F2-R2': []})
        self.assertEqual(result['awayIntervals'], [0, 4, 31, 40])
        merged = MockAdapter([json.dumps(proposal())])
        run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, cutoff=40, lastSeen=0), merged, SETTINGS)
        self.assertIn('"changedWhileAway": ["E01:stand", "E03:stand"]', merged.calls[0][0].messages[0][1])
        for bad in ([10, 5], [0, 20, 15, 30], [0, 4, 31]):
            with self.assertRaises(ValueError):
                run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, cutoff=40, awayIntervals=bad),
                         MockAdapter([]), SETTINGS)

    def test_without_last_seen_the_prompt_says_nothing_about_tracking(self):
        adapter = MockAdapter([json.dumps(proposal())])
        run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0), adapter, SETTINGS)
        self.assertNotIn('changedWhileAway', adapter.calls[0][0].messages[0][1])

    def test_last_seen_must_be_before_the_replay_time(self):
        with self.assertRaises(ValueError):
            run_turn(SessionState('s'), two_rotation_scenario(), turn(1, 0, cutoff=35, lastSeen=35),
                     MockAdapter([]), SETTINGS)


if __name__ == '__main__':
    unittest.main()
