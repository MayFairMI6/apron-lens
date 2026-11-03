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
