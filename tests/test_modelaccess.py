"""Shared inference-contract checks with a scripted adapter; no paid calls, no model weights."""
import unittest

from modelaccess.contract import (FinishReason, ImageInput, InvalidRequest, Operation, ProviderReply,
                                  Request, SchemaMode, Settings, UnsupportedCapability, Usage)
from modelaccess.local_qwen import LocalQwenAdapter
from modelaccess.mock import MockAdapter, mock_capabilities
from modelaccess.repair import REPAIR_POLICY_VERSION, parse_json_output


def request(**settings):
    values = dict(model='model-x', max_output_tokens=200)
    values.update(settings)
    return Request('r1', (('user', 'hello'),), Settings(**values))


class Contract(unittest.TestCase):
    def test_label_scoring_is_never_emulated(self):
        adapter = MockAdapter(['{}'])
        with self.assertRaises(UnsupportedCapability):
            adapter.score_labels('Yes or No?', ('Yes', 'No'), Settings('model-x', 1))

    def test_ignored_settings_are_reported(self):
        adapter = MockAdapter(['ok'], mock_capabilities(temperature=False))
        result = adapter.generate(request(temperature=0.2))
        self.assertEqual(result.ignored_settings, ('temperature',))
        self.assertNotIn('temperature', result.effective_settings)

    def test_unknown_reasoning_effort_is_refused(self):
        with self.assertRaises(UnsupportedCapability):
            MockAdapter(['ok']).generate(request(reasoning_effort='max'))

    def test_returned_model_mismatch_fails(self):
        reply = ProviderReply('ok', 'model-y', 'stop', FinishReason.STOP, Usage(1, 1))
        result = MockAdapter([reply]).generate(request())
        self.assertEqual(result.error, 'model_mismatch')
        snapshot = ProviderReply('ok', 'model-x-2026-10-01', 'stop', FinishReason.STOP, Usage(1, 1))
        accepted = MockAdapter([snapshot]).generate(request(accepted_returned_models=('model-x-2026-10-01',)))
        self.assertTrue(accepted.ok)

    def test_length_stop_with_empty_text_is_a_failure(self):
        reply = ProviderReply('  ', 'model-x', 'max_tokens', FinishReason.LENGTH, Usage(10, 200, 200))
        self.assertEqual(MockAdapter([reply]).generate(request()).error, 'empty_output_length')

    def test_provider_exception_is_reported_not_hidden(self):
        result = MockAdapter([TimeoutError('slow')]).generate(request())
        self.assertEqual(result.error, 'provider_error:TimeoutError')
        self.assertFalse(result.ok)

    def test_schema_on_plain_text_adapter_is_refused(self):
        adapter = MockAdapter(['ok'], mock_capabilities(schema_mode=SchemaMode.NONE))
        with self.assertRaises(UnsupportedCapability):
            adapter.generate(Request('r1', (('user', 'x'),), Settings('model-x', 10), schema={'type': 'object'}))

    def test_images_require_explicit_resize_policy(self):
        image = ImageInput(b'png', 'image/png')
        with self.assertRaises(InvalidRequest):
            MockAdapter(['ok']).generate(Request('r1', (('user', 'x'),), Settings('model-x', 10), images=(image,)))
        no_images = MockAdapter(['ok'], mock_capabilities(image_input=False))
        with self.assertRaises(UnsupportedCapability):
            no_images.generate(Request('r1', (('user', 'x'),), Settings('model-x', 10, image_max_side=672), images=(image,)))


class LocalQwenSettings(unittest.TestCase):
    def test_device_and_dtype_must_be_explicit(self):
        with self.assertRaises(InvalidRequest):
            LocalQwenAdapter('models/x', 'Qwen/Qwen2.5-VL-3B-Instruct', 'rev', 'auto', 'float16', 'eager')
        with self.assertRaises(InvalidRequest):
            LocalQwenAdapter('models/x', 'Qwen/Qwen2.5-VL-3B-Instruct', 'rev', 'mps', 'half', 'eager')
        adapter = LocalQwenAdapter('models/x', 'Qwen/Qwen2.5-VL-3B-Instruct', 'rev', 'cpu', 'float32', 'eager')
        self.assertIn(Operation.SCORE_LABELS, adapter.capabilities.operations)
        self.assertEqual(adapter.run_metadata()['dtype'], 'float32')


class Repair(unittest.TestCase):
    def test_single_policy_reports_raw_validity(self):
        self.assertEqual(parse_json_output('{"a":1}'), ({'a': 1}, True, (), None))
        value, raw_valid, repairs, error = parse_json_output('```json\n{"a":1}\n```')
        self.assertEqual((value, raw_valid, repairs, error), ({'a': 1}, False, ('strip_code_fence',), None))
        self.assertEqual(parse_json_output('Sure! {"a":1}')[3], 'invalid_json')
        self.assertEqual(REPAIR_POLICY_VERSION, 'json-repair-v1')


if __name__ == '__main__':
    unittest.main()
