"""Offline fixtures verify retry control; they are never demonstration answers."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from backend.training_adapter import TrainingAdapter
from backend.training_turn import run_turn
from backend.conversation.state import SessionState
from modelaccess.local_backbone import LocalBackboneAdapter
from modelaccess.contract import ProviderReply,FinishReason,Usage,Settings
from scripts.history_evaluation import new_cases

class HistoryRecoveryTests(unittest.TestCase):
    def execute(self,ids):
        with tempfile.TemporaryDirectory() as folder:
            audit=Path(folder)/'selector.jsonl'
            adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=audit)
            calls=[];iterator=iter(ids)
            def generate(owner,request,effective):
                calls.append(request)
                raw=json.dumps(dict(aircraftId='K1',flightInstance='ST204',fact_ids=[next(iterator)],unknowns=[]))
                return ProviderReply(raw,request.settings.model,'stop',FinishReason.STOP,Usage(100,20))
            ep=new_cases()[1];turn=dict(requestId='history',turnId='history',expectedRevision=0,cutoff=39,aircraftId='K1',flightInstance='ST204',question='For ST204, which stand immediately preceded E4?')
            # The bounded grammar covers preceding, not every synonym.
            turn['question']='For ST204, name the stand immediately preceding E4.'
            with patch.object(LocalBackboneAdapter,'_generate',generate):
                result=run_turn(SessionState('history-test'),ep['world'],turn,adapter,Settings(adapter.served_model,256,image_max_side=672))
            rows=[json.loads(s) for s in audit.read_text().splitlines()]
            return result,calls,rows
    def test_actual_second_selection_supplies_history_not_code(self):
        result,calls,rows=self.execute(['S2:stand','S1:stand'])
        self.assertTrue(result['accepted'],result['errors']);self.assertEqual(len(calls),2)
        self.assertEqual(result['display']['claims'][0]['fact_id'],'S1:stand')
        self.assertEqual(rows[0]['completenessError'],'historical_fact_missing')
        self.assertIsNone(rows[1]['completenessError'])
        self.assertTrue(calls[1].messages[0][1].startswith(calls[0].messages[0][1]))
        self.assertNotIn('S3:stand',calls[1].messages[0][1])
        self.assertEqual(result['inputTokens'],200);self.assertEqual(result['outputTokens'],40)
    def test_repeated_current_answer_is_withheld_after_two_calls(self):
        result,calls,rows=self.execute(['S2:stand','S2:stand'])
        self.assertFalse(result['accepted']);self.assertEqual(len(calls),2)
        self.assertEqual(result['errors'],['historical_fact_missing_after_retry'])
        self.assertEqual(rows[-1]['completenessError'],'historical_fact_missing')
    def test_invented_historical_id_not_repaired(self):
        result,calls,rows=self.execute(['S2:stand','invented:stand'])
        self.assertFalse(result['accepted']);self.assertEqual(len(calls),2)
