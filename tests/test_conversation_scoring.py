"""Scoring harness and development family labels: no model, no network."""
import copy
import json
import unittest
from pathlib import Path

from backend.conversation.scoring import (baseline_proposal, load_families, score_turn, summarize,
                                          validate_families)
from backend.conversation.server import load_scenarios
from backend.conversation.validate import validate_proposal

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ROOT / 'data/conversation_dev/families.json'
A2_R1 = {'aircraftId': 'A2', 'flightInstance': 'F2-R1'}


def result(accepted=True, referent=A2_R1, claims=(), **proposal):
    p = dict(status='answer', explanationChanged=None, unknowns=[], observations=[])
    p.update(proposal)
    return dict(accepted=accepted, referent=referent if accepted else None, rawModelOutput=json.dumps(p),
                display=dict(claims=[{'fact_id': f} for f in claims]))


class Labels(unittest.TestCase):
    def setUp(self):
        self.scenarios = load_scenarios()
        self.families = load_families(FAMILIES)

    def test_development_labels_hold_for_their_scenarios(self):
        validate_families(self.families, self.scenarios)
        self.assertEqual(self.families['split'], 'development')

    def test_a_citation_not_yet_received_is_a_broken_label(self):
        broken = copy.deepcopy(self.families)
        late = next(f for f in broken['families'] if f['id'] == 'F3-late-report')
        late['turns'][1]['cutoff'] = 30  # V04 is received at 34 s
        with self.assertRaises(ValueError):
            validate_families(broken, self.scenarios)


class TurnScores(unittest.TestCase):
    def test_correct_answer(self):
        expect = dict(status=['answer'], referent=A2_R1, mustCite=['V04:baggage_status'], explanationChanged=True)
        scores = score_turn(expect, result(claims=['V04:baggage_status'], explanationChanged=True))
        self.assertTrue(scores['correct'])
        self.assertIsNone(scores['unknowns'])

    def test_wrong_referent_and_denied_change(self):
        expect = dict(status=['answer'], referent=A2_R1, explanationChanged=True)
        scores = score_turn(expect, result(referent={'aircraftId': 'A2', 'flightInstance': 'F2-R2'}, explanationChanged=False))
        self.assertEqual((scores['referent'], scores['changed'], scores['correct']), (False, False, False))

    def test_withheld_is_never_correct(self):
        self.assertFalse(score_turn(dict(status=['answer']), result(accepted=False))['correct'])

    def test_clarification_expected(self):
        expect = dict(status=['clarify'], referent=None)
        self.assertTrue(score_turn(expect, result(referent=None, status='clarify'))['correct'])
        self.assertFalse(score_turn(expect, result(status='answer'))['correct'])

    def test_observations_visible_and_hidden(self):
        visible = dict(status=['answer'], referent=A2_R1, observations={'fuel_vehicle': 'connected'})
        seen = [{'kind': 'fuel_vehicle', 'aircraftId': 'A2', 'value': 'connected', 'captureTime': 24}]
        self.assertTrue(score_turn(visible, result(observations=seen))['observations'])
        self.assertFalse(score_turn(visible, result())['observations'])
        hidden = dict(status=['answer'], referent=A2_R1, observations={'fuel_vehicle': None})
        self.assertFalse(score_turn(hidden, result(observations=seen))['observations'])
        self.assertTrue(score_turn(hidden, result())['observations'])

    def test_summary_counts_only_labelled_criteria(self):
        rows = [dict(family='F', scores=dict(valid=True, status=True, referent=True, cites=None, changed=False,
                                             unknowns=None, observations=None, correct=False))]
        summary = summarize(rows)
        self.assertEqual((summary['all']['turns'], summary['all']['correct']), (1, 0))
        self.assertEqual((summary['F']['changed'], summary['F']['cites']), ([0, 1], [0, 0]))


class Baseline(unittest.TestCase):
    def test_conflicting_reports_are_cited_with_their_status_and_validate(self):
        data = load_scenarios()['V4-conflicting-reports-dev-04']
        proposal = baseline_proposal(data, 15, ('A1', 'F1-R1'))
        self.assertEqual([(c['fact_id'], c['status']) for c in proposal['claims']],
                         [('X01:stand', 'conflicting'), ('X02:stand', 'conflicting')])
        self.assertTrue(validate_proposal(proposal, data, 15)['accepted'])

    def test_follow_up_flags_the_change(self):
        data = load_scenarios()['V4-conflicting-reports-dev-04']
        self.assertTrue(baseline_proposal(data, 25, ('A1', 'F1-R1'), previous_cutoff=15)['explanationChanged'])


if __name__ == '__main__':
    unittest.main()
