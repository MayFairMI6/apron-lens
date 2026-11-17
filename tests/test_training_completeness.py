"""Training-only empty-answer recovery; model outputs are fixtures, not demo answers."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from modelaccess.contract import ProviderReply,FinishReason,Usage,Settings
from modelaccess.local_backbone import LocalBackboneAdapter
from backend.training_adapter import TrainingAdapter
from backend.training_turn import run_turn
from backend.conversation.state import SessionState
from test_conversation import two_rotation_scenario

class Completeness(unittest.TestCase):
    def selection(self, ids=(), unknowns=(), aircraft='A2', flight='F2-R1'):
        return json.dumps(dict(aircraftId=aircraft,flightInstance=flight,fact_ids=list(ids),unknowns=list(unknowns)))
    def execute(self, outputs):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.audit=Path(self.folder.name)/'audit.jsonl'
        self.adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=self.audit)
        self.session=SessionState('s')
        self.turn=dict(requestId='r',turnId='t',expectedRevision=0,cutoff=25,aircraftId='A2',flightInstance='F2-R1',question='Which stand?')
        self.requests=[]
        def generate(owner,request,effective):
            self.requests.append(request)
            value=outputs.pop(0)
            if isinstance(value,Exception): raise value
            return ProviderReply(text=value,returned_model=request.settings.model,finish_reason=FinishReason.STOP,
                raw_finish_reason='stop',usage=Usage(100,20,0,0,0))
        self.patch=patch.object(LocalBackboneAdapter,'_generate',generate);self.patch.start();self.addCleanup(self.patch.stop)
        self.settings=Settings(self.adapter.served_model,256,image_max_side=672)
        return run_turn(self.session,two_rotation_scenario(),self.turn,self.adapter,self.settings)
    def test_empty_then_grounded_answer_reuses_cutoff_and_audits_both(self):
        result=self.execute([self.selection(),self.selection(['E01:stand'])])
        self.assertTrue(result['accepted'],result['errors']);self.assertEqual(result['trainingAttemptCount'],2)
        self.assertEqual(result['inputTokens'],200);self.assertEqual(result['outputTokens'],40)
        first,second=[r.messages[0][1] for r in self.requests]
        self.assertTrue(second.startswith(first));self.assertNotIn('E03:stand',second)
        audits=[json.loads(x) for x in self.audit.read_text().splitlines()]
        self.assertEqual(audits[0]['completenessError'],'empty_answer');self.assertIsNone(audits[1]['completenessError'])
        repeat=run_turn(self.session,two_rotation_scenario(),self.turn,self.adapter,self.settings)
        self.assertTrue(repeat['accepted']);self.assertEqual(len(self.requests),2)
    def test_two_empty_outputs_fail_explicitly_without_third_call(self):
        r=self.execute([self.selection(),self.selection()])
        self.assertFalse(r['accepted']);self.assertEqual(r['errors'],['empty_answer_after_retry'])
        self.assertIn('open Sources',r['display']['answer']);self.assertEqual(len(self.requests),2)
        self.assertEqual(self.session.revision,1)
    def test_genuinely_missing_property_does_not_retry(self):
        r=self.execute([self.selection(unknowns=['fuel_status'])])
        self.assertTrue(r['accepted'],r['errors']);self.assertEqual(len(self.requests),1)
    def test_clarification_does_not_retry(self):
        r=self.execute([self.selection(aircraft=None,flight=None)])
        self.assertTrue(r['accepted']);self.assertEqual(len(self.requests),1)
    def test_retry_cannot_cite_future_report(self):
        r=self.execute([self.selection(),self.selection(['E03:stand'])])
        self.assertFalse(r['accepted']);self.assertIn('claim_outside_eligible_evidence',r['errors'])
    def test_retry_cannot_call_known_stand_unknown(self):
        r=self.execute([self.selection(),self.selection(unknowns=['stand'])])
        self.assertFalse(r['accepted']);self.assertIn('unknown_contradicts_current_fact',r['errors'])

    def test_second_call_exception_keeps_attempt_audit_and_partial_usage(self):
        r=self.execute([self.selection(),RuntimeError('unavailable')])
        self.assertFalse(r['accepted']);self.assertEqual(r['trainingAttemptCount'],2)
        self.assertIsNone(r['inputTokens']);self.assertEqual(r['trainingKnownInputTokens'],100)
        records=[json.loads(x) for x in self.audit.read_text().splitlines()]
        self.assertEqual(len(records),2);self.assertEqual(records[1]['providerErrorType'],'RuntimeError')

    def test_invented_unknown_name_gets_one_retry_with_the_same_evidence(self):
        r=self.execute([self.selection(['E01:stand'],['airport_landing_release']),self.selection(['E01:stand'],['fuel_status'])])
        self.assertTrue(r['accepted'],r['errors']);self.assertEqual(r['trainingAttemptCount'],2)
        first,second=[q.messages[0][1] for q in self.requests]
        self.assertTrue(second.startswith(first));self.assertIn('unknown_property_name',second)
        self.assertIn('The names ["airport_landing_release"] are not property names',second);self.assertNotIn('E03:stand',second)
        audits=[json.loads(x) for x in self.audit.read_text().splitlines()]
        self.assertEqual([a['completenessError'] for a in audits],['unknown_property_name',None])
        self.assertIn('airport_landing_release',audits[0]['rawSelectorOutput'])
    def test_two_invented_unknown_names_are_withheld_without_a_third_call(self):
        r=self.execute([self.selection(['E01:stand'],['landing_release']),self.selection(['E01:stand'],['release'])])
        self.assertFalse(r['accepted']);self.assertEqual(r['errors'],['unknowns_schema'])
        self.assertEqual((len(self.requests),r['trainingSelectionError']),(2,'unknown_property_name'))
    def test_withheld_unknown_name_answer_points_at_the_selected_received_report(self):
        r=self.execute([self.selection(['E01:stand'],['landing_release']),self.selection(['E01:stand'],['release'])])
        self.assertFalse(r['accepted']);self.assertEqual(r['display']['claims'],[])
        self.assertEqual(r['display']['selectedReportIds'],['E01'])
        self.assertIn('withheld',r['display']['answer']);self.assertIn('Relevant report: E01',r['display']['answer'])
    def test_withheld_pointer_never_names_a_report_received_after_the_cutoff(self):
        r=self.execute([self.selection(['E03:stand'],['release']),self.selection(['E03:stand'],['release'])])
        self.assertFalse(r['accepted']);self.assertNotIn('selectedReportIds',r['display']);self.assertNotIn('E03',r['display']['answer'])
    def test_prompt_candidate_adds_two_sentences_and_leaves_the_live_prompt_alone(self):
        from backend.training_adapter import selector_context,TRAINING_PROMPT_VERSION
        from experiments.unknown_names.candidate import UnknownNamesCandidate,ADDED
        self.execute([self.selection(['E01:stand'])])
        live=self.requests[0].messages[0][1]
        candidate=UnknownNamesCandidate('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=self.audit)
        base='x\nSelected in the app: aircraft A2, flight F2-R1.\nMemory: {}\nCandidate flights and received facts: []\nUser: q'
        self.assertEqual(candidate.selector(base)[0].replace(ADDED,''),selector_context(base)[0])
        self.assertNotIn(ADDED,live);self.assertEqual(TRAINING_PROMPT_VERSION,'training-evidence-selector-v8')
        self.assertEqual(TrainingAdapter.prompt_version,'training-evidence-selector-v8')

