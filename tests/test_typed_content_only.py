"""Uniform baseline contract checks; no model calls or GPU initialization."""
import copy
import time
import unittest
from tests.test_typed_redesign import fixture,Scores
from experiments.typed_relation_review.content_only import evaluate,THRESHOLD


class ContentOnlyTests(unittest.TestCase):
    def review(self,p=None,scorer=None):return evaluate(p or fixture(),scorer or Scores(),time.monotonic()+20)

    def test_uniform_bare_content_no_question_or_meta_probe_anywhere(self):
        p=fixture();scorer=Scores();result=self.review(p,scorer)
        self.assertEqual(result['verdict'],'supported')
        self.assertEqual(THRESHOLD,.8)
        for row in scorer.records:
            self.assertNotIn(p['question'],row['premise'])
            self.assertNotIn('Question',row['premise'])
            self.assertNotIn('ultimately asserts',row['hypothesis'])
            self.assertNotIn('PRIVATE_EXPECTED',row['premise'])
        primary=[r for r in scorer.records if r['kind']=='bare_criterion']
        self.assertTrue(all(r['premise']==p['learnerResponse'] for r in primary))
        self.assertEqual(len(scorer.records),len(scorer.planned_pairs))

    def test_neutral_is_conservative_uncertain_neither_missing_nor_contradicted(self):
        scorer=Scores(lambda row:'neutral' if row['kind'] in ('bare_criterion','bare_grounding') else None)
        result=self.review(fixture('The state is not clear.'),scorer)
        self.assertTrue(all(p['status']=='uncertain' for p in result['points']))
        self.assertTrue(all(p['learnerQuotes']==[] for p in result['points']))

    def test_snippet_does_not_override_whole_answer(self):
        scorer=Scores(lambda row:'neutral' if row['kind']=='bare_criterion' else None)
        result=self.review(fixture('TRN102 is held. Correction: I cannot identify the aircraft.'),scorer)
        self.assertTrue(all(p['status']=='uncertain' for p in result['points'][:-1]))
        self.assertFalse(any(r['kind']=='bare_quote_witness' for r in scorer.records))

    def test_full_original_and_each_sentence_are_mandatory(self):
        p=fixture('TRN102 is held. A vehicle blocks its route. An engine caught fire.')
        scorer=Scores(lambda row:'contradiction' if row['kind'] in ('bare_grounding','bare_grounding_quote') and row['hypothesis']==p['learnerResponse'] else None)
        result=self.review(p,scorer)
        self.assertEqual(result['points'][-1]['status'],'contradicted')
        hypotheses=[r['hypothesis'] for r in scorer.records if r['kind']=='bare_grounding']
        self.assertIn(p['learnerResponse'],hypotheses)
        self.assertIn('An engine caught fire.',hypotheses)

    def test_current_only_source_attribution_without_historical_rescue(self):
        p=fixture();old=copy.deepcopy(p['reports'][0]);old.update(id='OLD',eventTime=1,receiptTime=2,message='Old incorrect state.',facts=[dict(property='movement_condition',value='old')])
        p['reports'].append(old);p['reports'][0]['facts'][0]['supersedes']=['OLD:movement_condition']
        scorer=Scores();self.review(p,scorer)
        ground=[r for r in scorer.records if r['kind']=='bare_grounding']
        self.assertTrue(all('OLD' not in r['reportIds'] for r in ground))
        self.assertTrue(all('ground-control' in r['premise'] for r in ground))

    def test_relevant_multi_quote_projection_and_no_metadata_status_controls(self):
        result=self.review()
        for point in result['points']:
            self.assertLessEqual(len(point['learnerQuotes']),3)
            self.assertEqual(point['learnerQuote'],point['learnerQuotes'][0])
            self.assertTrue(all(len(q)<=160 and q in fixture()['learnerResponse'] for q in point['learnerQuotes']))

    def test_invalid_inputs_and_elapsed_deadline_do_not_call_model(self):
        p=fixture();p['cutoff']=float('nan');scorer=Scores()
        with self.assertRaises(ValueError):self.review(p,scorer)
        self.assertEqual(scorer.calls,0)
        with self.assertRaises(TimeoutError):evaluate(fixture(),Scores(),time.monotonic()-1)


if __name__=='__main__':unittest.main()
