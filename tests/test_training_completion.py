import unittest
from dataclasses import replace
from backend.training_result import checked_training_result
from modelaccess.contract import FinishReason, Request, Result, Settings, Usage

class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.request=Request('request',(('user','question'),),Settings('model',20))
        self.result=Result('request','test','model','model','{"complete":true}',FinishReason.STOP,'eos',Usage(5,7),.1,{},())
    def test_every_non_stop_reason_fails_even_with_valid_json(self):
        for reason in FinishReason:
            if reason==FinishReason.STOP:continue
            with self.subTest(reason=reason):
                raw=replace(self.result,finish_reason=reason,raw_finish_reason=reason.value)
                result=checked_training_result(raw,self.request)
                self.assertFalse(result.ok);self.assertEqual(result.finish_reason,reason)
                self.assertEqual(result.text,raw.text);self.assertEqual(result.usage.output_tokens,7)
    def test_complete_result_passes_but_empty_and_wrong_identity_do_not(self):
        self.assertIs(checked_training_result(self.result,self.request),self.result)
        for kwargs in ({'text':'  '},{'returned_model':'other'},{'request_id':'stale'}):
            self.assertFalse(checked_training_result(replace(self.result,**kwargs),self.request).ok)
    def test_malformed_result_is_rejected_before_delivery(self):
        for fields in ({'text':None},{'finish_reason':'bogus'},{'usage':{}},
                       {'metadata':None},{'metadata':{'bad':{1,2}}},
                       {'latency_seconds':float('nan')}):
            with self.subTest(fields=fields):
                with self.assertRaises(RuntimeError):
                    checked_training_result(replace(self.result,**fields),self.request)

    def test_existing_runtime_error_and_unknown_usage_are_preserved(self):
        raw=replace(self.result,finish_reason=FinishReason.ERROR,error='provider_error:RuntimeError',usage=Usage())
        result=checked_training_result(raw,self.request)
        self.assertEqual(result.error,raw.error);self.assertIsNone(result.usage.output_tokens)
