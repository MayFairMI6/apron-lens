import contextlib
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from experiments.typed_qwen_frames.runtime import FrameAdapter
from modelaccess.contract import FinishReason, Request, Settings


class Tokens:
    def __init__(self, ids): self.ids = ids
    def __getitem__(self, key): return self
    def cpu(self): return self
    def tolist(self): return self.ids


class QwenFrameTerminationTests(unittest.TestCase):
    def generate(self, ids, cap=4, eos=(7, 9)):
        adapter = FrameAdapter()
        engine = SimpleNamespace(
            _inputs=Mock(return_value={'input_ids': SimpleNamespace(shape=(1, 12))}),
            torch=SimpleNamespace(inference_mode=contextlib.nullcontext,
                                  mps=SimpleNamespace(synchronize=Mock())),
            model=SimpleNamespace(generate=Mock(return_value=Tokens(ids)),
                                  generation_config=SimpleNamespace(eos_token_id=list(eos))),
            processor=SimpleNamespace(batch_decode=Mock(return_value=['{}'])), runtime={})
        adapter._engine = engine
        request = Request('test', (('user', 'input'),), Settings(adapter.served_model, cap))
        return adapter._generate(request, {})

    def test_short_non_eos_output_is_not_reported_as_successful_completion(self):
        reply = self.generate([3, 4])
        self.assertEqual(reply.finish_reason, FinishReason.OTHER)
        self.assertFalse(reply.metadata['observedEOS'])

    def test_token_limit_without_eos_is_length_failure(self):
        reply = self.generate([1, 2, 3, 4])
        self.assertEqual(reply.finish_reason, FinishReason.LENGTH)

    def test_actual_eos_at_capacity_is_still_verified_completion(self):
        reply = self.generate([1, 2, 3, 9])
        self.assertEqual(reply.finish_reason, FinishReason.STOP)
        self.assertTrue(reply.metadata['observedEOS'])
        self.assertEqual(reply.metadata['terminalTokenId'], 9)
        self.assertEqual(reply.usage.output_tokens, 4)

    def test_empty_output_without_eos_is_unverified(self):
        self.assertEqual(self.generate([]).finish_reason, FinishReason.OTHER)


if __name__ == '__main__':
    unittest.main()
