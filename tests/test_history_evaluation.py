import copy
import json
import unittest
from scripts.history_evaluation import new_cases,validate_keys,score_answer
from backend.conversation.context import snapshot

class HistoryScoringTests(unittest.TestCase):
    def setUp(self):
        self.ep=new_cases()[0];self.world=self.ep['world'];self.case=self.ep['cases'][2]
    def answer(self,case=None,ids=None):
        c=case or self.case;facts=snapshot(self.world,c['aircraftId'],c['flight'],c['cutoff'])['factsById']
        p=dict(status='answer',referent=dict(aircraftId=c['aircraftId'],flightInstance=c['flight']),unknowns=c['unknowns'],claims=[])
        for fid in c['required'] if ids is None else ids:
            f=facts[fid];p['claims'].append(dict(fact_id=fid,value=f['value'],status=f['status'],evidence_ids=[f['event_id']]))
        return p
    def grade(self,p,c=None):return score_answer(dict(accepted=True,rawModelOutput=json.dumps(p)),self.world,c or self.case)
    def test_labels_and_all_authored_reference_answers(self):
        eps=new_cases();validate_keys(eps);self.assertEqual(sum(len(e['cases']) for e in eps),24)
        for ep in eps:
            self.world=ep['world']
            for c in ep['cases']:self.assertTrue(self.grade(self.answer(c),c)['passed'])
    def test_correct_labelled_change_history_passes(self):self.assertTrue(self.grade(self.answer())['passed'])
    def test_old_claim_masquerading_as_current_fails(self):
        p=self.answer();p['claims'][0]['status']='current';self.assertFalse(self.grade(p)['passed'])
    def test_current_question_does_not_accept_old_history(self):
        c=dict(self.case,mode='current',required=[self.case['required'][1]],allowed=[self.case['required'][1]])
        self.assertFalse(self.grade(self.answer(),c)['passed'])
    def test_change_requires_before_and_after(self):
        for i in (0,1):
            p=self.answer();p['claims'].pop(i);self.assertFalse(self.grade(p)['passed'])
    def test_wrong_identity_and_citation_fail(self):
        p=self.answer();p['referent']['flightInstance']='WX522';self.assertFalse(self.grade(p)['passed'])
        p=self.answer();p['claims'][0]['evidence_ids']=['invented'];self.assertFalse(self.grade(p)['passed'])
    def test_future_and_invented_facts_fail(self):
        for fid in ('W3:movement_condition','nonexistent'):
            p=self.answer();p['claims'].append(dict(fact_id=fid,value='hold: route inspection',status='current',evidence_ids=['W3']))
            self.assertFalse(self.grade(p)['passed'])
    def test_irrelevant_older_history_fails(self):
        c=self.ep['cases'][4];p=self.answer(c,ids=['W1:movement_condition',*c['required']])
        self.assertFalse(self.grade(p,c)['passed'])
    def test_history_question_requires_the_requested_past_fact(self):
        c=self.ep['cases'][3];self.assertTrue(self.grade(self.answer(c),c)['passed'])
        self.assertFalse(self.grade(self.answer(c,ids=['W2:movement_condition']),c)['passed'])
    def test_missing_or_extra_unknown_is_not_success(self):
        c=self.ep['cases'][5];p=self.answer(c);p['unknowns']=[];self.assertFalse(self.grade(p,c)['passed'])
        p=self.answer();p['unknowns']=['overall_readiness'];self.assertFalse(self.grade(p)['passed'])
    def test_duplicate_and_malformed_claims_fail_safely(self):
        p=self.answer();p['claims'].append(copy.deepcopy(p['claims'][0]));self.assertFalse(self.grade(p)['passed'])
        p=self.answer();p['claims'][0]['fact_id']=['bad'];self.assertFalse(self.grade(p)['passed'])
    def test_withheld_answer_cannot_pass(self):
        r=score_answer(dict(accepted=False,rawModelOutput=json.dumps(self.answer())),self.world,self.case)
        self.assertFalse(r['passed'])

class HistoricalDiagnosticTests(unittest.TestCase):
    def test_diagnostic_corrects_only_new_score_and_preserves_original(self):
        import hashlib
        from pathlib import Path
        from scripts.evaluate_history_questions import diagnostic_old_answers
        p=Path('outputs/prompt-revision/v6-run.json');before=hashlib.sha256(p.read_bytes()).hexdigest()
        d=diagnostic_old_answers()
        self.assertEqual(len(d['records']),2)
        self.assertTrue(all(not r['originalScore']['passed'] and r['diagnosticScore']['passed'] for r in d['records']))
        self.assertEqual(before,hashlib.sha256(p.read_bytes()).hexdigest())

class HistoryReportTests(unittest.TestCase):
    def test_failure_and_unknown_usage_are_not_hidden(self):
        from scripts.report_history_questions import summarize
        rows=[dict(version=v,episode='sample',case=dict(mode='change'),result=dict(requestId=v,latencySeconds=41),score=dict(passed=v=='v6',accepted=True)) for v in ('v5','v6')]
        calls=[dict(requestId=v,usage=dict(input_tokens=None,output_tokens=7)) for v in ('v5','v6')]
        s=summarize(dict(records=rows),calls)
        self.assertEqual(s['v5']['passed'],0)
        self.assertEqual(s['v5']['accepted'],1)
        self.assertEqual(s['v5']['byMode']['change'],dict(passed=0,total=1))
        self.assertIsNone(s['v5']['usage']['input_tokens'])
        self.assertEqual(s['v5']['over40Seconds'],1)
