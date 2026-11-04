"""Matched template/protocol controls with fake tensors; no model loading."""
import contextlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from modelaccess.contract import Request, Settings, FinishReason
from experiments.typed_qwen_frames.reasoning_runtime import ReasoningFrameAdapter
from tests.test_typed_qwen_runtime import Tokens


class Batch(dict):
    def to(self, device):
        return self


class Processor:
    def __init__(self, final_text='{}'):
        self.calls = []
        self.decode_calls = []
        self.final_text = final_text
        self.tokenizer = SimpleNamespace(encode=lambda text, **_: [
            {'<think>': 248068, '</think>': 248069, '<|im_end|>': 248046}[text]])

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return repr(messages) + ('<think>\n' if kwargs['enable_thinking'] else '<think>\n\n</think>\n\n')

    def __call__(self, **kwargs):
        tokens = Tokens([101, 102, 103])
        tokens.shape = (1, 3)
        return Batch(input_ids=tokens)

    def batch_decode(self, batch, *, skip_special_tokens, clean_up_tokenization_spaces):
        self.decode_calls.append((skip_special_tokens, clean_up_tokenization_spaces))
        is_full_generation = any(t in (9, 248046, 248068, 248069) for t in batch[0])
        return ['RAW:'+repr(batch[0]) if is_full_generation else self.final_text]


class ReasoningRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def adapter(self, thinking, ids, final_text='{}'):
        adapter = ReasoningFrameAdapter(thinking=thinking,
            audit_path=Path(self.temp.name)/('on.jsonl' if thinking else 'off.jsonl'))
        processor = Processor(final_text)
        engine = SimpleNamespace(device='mps', template_kwargs={'enable_thinking': False},
            torch=SimpleNamespace(inference_mode=contextlib.nullcontext,
                                  mps=SimpleNamespace(synchronize=Mock())),
            model=SimpleNamespace(generate=Mock(return_value=Tokens(ids)),
                                  generation_config=SimpleNamespace(eos_token_id=[9])),
            processor=processor, runtime={})
        adapter._engine = engine
        request = Request('test', (('user', 'identical learner prompt'),),
                          Settings(adapter.served_model, 1000))
        return adapter, engine, request

    def test_only_template_flag_changes_and_raw_thoughts_are_not_final_evidence(self):
        off, off_engine, request = self.adapter(False, [42, 9])
        on, on_engine, _ = self.adapter(True, [7, 248069, 42, 9])
        a, b = off.generate(request), on.generate(request)
        self.assertTrue(a.ok)
        self.assertTrue(b.ok)
        self.assertEqual(a.text, b.text)
        self.assertEqual(a.usage.output_tokens, 2)
        self.assertEqual(b.usage.output_tokens, 4)
        self.assertEqual(b.usage.reasoning_tokens, 2)
        self.assertEqual(b.metadata['segments']['finalTokenCount'], 2)
        self.assertEqual(b.metadata['rawGeneratedTokenIds'], [7, 248069, 42, 9])
        self.assertEqual(b.metadata['rawDecodedText'], 'RAW:[7, 248069, 42, 9]')
        self.assertFalse(b.metadata['fidelityVerified'])
        self.assertFalse(b.metadata['reportCheckAllowed'])
        self.assertEqual(off_engine.template_kwargs, {'enable_thinking': False})
        self.assertEqual(on_engine.template_kwargs, {'enable_thinking': False})
        messages_a, kwargs_a = off_engine.processor.calls[0]
        messages_b, kwargs_b = on_engine.processor.calls[0]
        self.assertEqual(messages_a, messages_b)
        self.assertEqual({**kwargs_a, 'enable_thinking': True}, kwargs_b)
        self.assertEqual(off_engine.model.generate.call_args.kwargs['max_new_tokens'], 1000)
        self.assertEqual(on_engine.model.generate.call_args.kwargs['max_new_tokens'], 1000)
        self.assertEqual(on_engine.processor.decode_calls, [(False, False), (False, False)])
        events = [json.loads(s) for s in on.audit_path.read_text().splitlines()]
        self.assertEqual([e['event'] for e in events],
                         ['generation_started', 'input_prepared', 'generation_returned'])
        self.assertEqual(events[1]['inputTokenIds'], [101, 102, 103])
        self.assertEqual(events[1]['inputTokenIdsSHA256'], b.metadata['inputTokenIdsSHA256'])

    def test_observed_eos_does_not_hide_missing_thought_close(self):
        adapter, _, request = self.adapter(True, [42, 9])
        result = adapter.generate(request)
        self.assertFalse(result.ok)
        self.assertEqual(result.finish_reason, FinishReason.STOP)
        self.assertTrue(result.metadata['observedEOS'])
        self.assertIn('reasoning_protocol:', result.error)
        self.assertEqual(result.text, '')
        events = [json.loads(s) for s in adapter.audit_path.read_text().splitlines()]
        self.assertEqual(events[-1]['metadata']['rawGeneratedTokenIds'], [42, 9])

    def test_no_json_or_fence_repair(self):
        adapter, _, request = self.adapter(True, [7, 248069, 42, 9], '```json\n{}\n```')
        result = adapter.generate(request)
        self.assertEqual(result.text, '```json\n{}\n```')
        # The separate frozen JSON parser, not this transport, must reject it.

    def test_nonprotocol_special_token_survives_for_strict_parser_rejection(self):
        adapter, engine, request = self.adapter(True, [7, 248069, 555, 42, 9], '<other-special>{}')
        result = adapter.generate(request)
        self.assertEqual(result.text, '<other-special>{}')
        self.assertEqual(result.metadata['segments']['finalTokenIds'], [555, 42])
        self.assertEqual(engine.processor.decode_calls, [(False, False), (False, False)])
        from experiments.typed_qwen_frames.claims_v6_control import parse_frames, FrameError
        with self.assertRaises(FrameError):
            parse_frames(result.text, 'The cart is parked.')

    def test_decoded_whitespace_final_rejected_without_replacement(self):
        adapter, _, request = self.adapter(True, [7, 248069, 42, 9], '  \n')
        result = adapter.generate(request)
        self.assertFalse(result.ok)
        self.assertEqual(result.text, '  \n')
        self.assertEqual(result.metadata['protocolError'], 'empty_decoded_final')

    def test_excess_cap_rejected_before_generation(self):
        adapter, engine, _ = self.adapter(True, [7, 248069, 42, 9])
        request = Request('bad', (('user', 'input'),), Settings(adapter.served_model, 1001))
        result = adapter.generate(request)
        self.assertFalse(result.ok)
        engine.model.generate.assert_not_called()

    def test_chat_eos_is_passed_to_generation_without_mutating_base(self):
        for thinking, ids in ((False, [42, 248046]), (True, [7, 248069, 42, 248046])):
            adapter, engine, request = self.adapter(thinking, ids)
            result = adapter.generate(request)
            self.assertTrue(result.ok)
            self.assertEqual(result.finish_reason, FinishReason.STOP)
            self.assertEqual(result.metadata['terminalTokenId'], 248046)
            self.assertEqual(result.metadata['baseEosTokenIds'], [9])
            self.assertEqual(engine.model.generate.call_args.kwargs['eos_token_id'], [9, 248046])
            self.assertEqual(engine.model.generation_config.eos_token_id, [9])
            self.assertEqual(result.metadata['segments']['finalTokenIds'], [42])

    def test_post_chat_eos_content_is_rejected_not_stripped(self):
        adapter, _, request = self.adapter(False, [42, 248046, 198, 9])
        result = adapter.generate(request)
        self.assertFalse(result.ok)
        self.assertIsNotNone(result.metadata['protocolError'])
        self.assertEqual(result.metadata['rawGeneratedTokenIds'], [42, 248046, 198, 9])

    def test_both_warmups_receive_identical_1000_token_cap(self):
        for thinking, ids in ((False, [42, 9]), (True, [7, 248069, 42, 9])):
            adapter, engine, request = self.adapter(thinking, ids, 'ready')
            response = adapter.warmup(request.settings)
            self.assertEqual(response['warmupOutputCap'], 1000)
            self.assertEqual(engine.model.generate.call_args.kwargs['max_new_tokens'], 1000)


if __name__ == '__main__':
    unittest.main()
