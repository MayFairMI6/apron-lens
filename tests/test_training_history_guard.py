import copy
import json
import unittest
from backend.training_history_guard import history_error, HISTORY_ERROR


class HistoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.ref = dict(aircraftId='K1', flightInstance='RP810')
        self.facts = [dict(fact_id='S1:stand', property='stand', value='D12', status='superseded', eventTime=3, receiptTime=8),
                      dict(fact_id='S2:stand', property='stand', value='E4', status='current', eventTime=21, receiptTime=38),
                      dict(fact_id='T1:tobt', property='tobt', value='14:10', status='superseded', eventTime=4, receiptTime=9),
                      dict(fact_id='T2:tobt', property='tobt', value='14:25', status='current', eventTime=22, receiptTime=39)]
        self.candidates = [dict(**self.ref, facts=self.facts),
                           dict(aircraftId='K2', flightInstance='RP811', facts=[])]

    def check(self, question, ids=('S2:stand',), ref=None, candidates=None, memory=True):
        proposal = dict(referent=ref or self.ref, claims=[dict(fact_id=i) for i in ids])
        prompt = '\nMemory: '+json.dumps(dict(currentReferent=self.ref) if memory else {})+'\nFlights: []\nQuestion: '+question
        original = copy.deepcopy((proposal, candidates or self.candidates))
        result = history_error(proposal, prompt, candidates or self.candidates)
        self.assertEqual(original, (proposal, candidates or self.candidates))
        return result

    def test_observed_same_aircraft_history_not_current(self):
        q = 'For that same aircraft, name the stand immediately preceding E4. Do not switch to an aircraft currently at E4.'
        self.assertEqual(self.check(q), HISTORY_ERROR)
        self.assertIsNone(self.check(q, ('S1:stand',)))

    def test_time_history_and_explicit_identity(self):
        q = 'For RP810, what TOBT was reported prior to 14:25?'
        self.assertEqual(self.check(q, ('T2:tobt',), memory=False), HISTORY_ERROR)
        self.assertIsNone(self.check(q, ('T1:tobt',), memory=False))

    def test_legitimate_current_and_general_before_are_unchanged(self):
        for q in ['What is its current stand?', 'What is its stand before departure?',
                  'What is its target off-block time before departure?',
                  'Compare its stand before E4 with its current stand.',
                  'How has its stand changed from before E4?']:
            with self.subTest(q=q): self.assertIsNone(self.check(q))

    def test_literal_quoted_values_and_boundaries(self):
        self.assertEqual(self.check('What was its stand before "E4"?'), HISTORY_ERROR)
        self.assertEqual(self.check("What was its stand before stand ‘E4’?"), HISTORY_ERROR)
        for q in ['What was its stand before E40?', 'What was its TOBT before 14:250?', 'What was its TOBT before 14:25:00?', 'What was its stand before E4-A?']:
            self.assertIsNone(self.check(q))

    def test_no_prior_no_guard_and_future_report_not_prior(self):
        cs=copy.deepcopy(self.candidates);cs[0]['facts']=[self.facts[1]]
        self.assertIsNone(self.check('What was its stand before E4?', candidates=cs))
        cs=copy.deepcopy(self.candidates);cs[0]['facts'][0]['receiptTime']=50
        self.assertIsNone(self.check('What was its stand before E4?', candidates=cs))

    def test_wrong_flight_and_ambiguous_references_not_resolved(self):
        self.assertIsNone(self.check('What was its stand before E4?', ref=dict(aircraftId='K2',flightInstance='RP811')))
        self.assertIsNone(self.check('For RP810 or RP811, what stand preceded E4?'))
        self.assertIsNone(self.check('What was the stand before E4?', memory=False))
        self.assertIsNone(self.check('What was its stand before E4?', memory=False))
        self.assertIsNone(self.check('For the other aircraft, what was its stand before E4?'))

    def test_multiple_properties_and_repeated_anchor_skip(self):
        self.assertIsNone(self.check('What were its stand and TOBT before E4?'))
        cs=copy.deepcopy(self.candidates);cs[0]['facts'].append(dict(self.facts[1],fact_id='S3:stand'))
        self.assertIsNone(self.check('What was its stand before E4?', candidates=cs))

    def test_same_property_required_and_any_history_not_injected(self):
        self.assertEqual(self.check('What was its stand before E4?', ('T1:tobt',)), HISTORY_ERROR)
        self.assertIsNone(self.check('What was its stand before E4?', ('S1:stand','S2:stand')))
        cs=copy.deepcopy(self.candidates);cs[0]['facts'][0]['status']='conflicting'
        self.assertIsNone(self.check('What was its stand before E4?', candidates=cs))


if __name__ == '__main__': unittest.main()
