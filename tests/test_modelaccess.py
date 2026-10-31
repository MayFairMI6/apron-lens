"""Shared inference-contract checks with a scripted adapter; no paid calls, no model weights."""
import unittest

from modelaccess.contract import (FinishReason, ImageInput, InvalidRequest, Operation, ProviderReply,
                                  Request, SchemaMode, Settings, UnsupportedCapability, Usage)
from modelaccess.local_backbone import LocalBackboneAdapter
from modelaccess.contract import ModelAccessError
from backbone import expected_manifest
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


class FakeEngine:
    def __init__(self, manifest, output_tokens=3):
        self.manifest, self.output_tokens, self.calls = manifest, output_tokens, []
        self.runtime = dict(device='cpu', dtype='float32', attn_implementation='eager', backbone='test')

    def generate(self, prompt, image, max_new_tokens=512):
        self.calls.append(('generate', max_new_tokens))
        return '{"a":1}', 12, min(self.output_tokens, max_new_tokens)

    def score_labels(self, prompt, image, labels):
        return {'Yes': -0.1, 'No': -2.3}, 9


class LocalBackbone(unittest.TestCase):
    MODEL = 'qwen2.5-vl-3b'

    def adapter(self, engine=None, **runtime):
        runtime = runtime or dict(profile='cpu-float32')
        engine = engine or FakeEngine(expected_manifest(self.MODEL))
        made = []

        def factory(name, **values):
            made.append((name, values))
            return engine
        adapter = LocalBackboneAdapter(self.MODEL, engine_factory=factory, **runtime)
        return adapter, made

    def test_runtime_must_be_explicit(self):
        with self.assertRaises(InvalidRequest):
            LocalBackboneAdapter(self.MODEL)
        with self.assertRaises(InvalidRequest):
            LocalBackboneAdapter(self.MODEL, device='mps')
        with self.assertRaises(InvalidRequest):
            LocalBackboneAdapter(self.MODEL, profile='apronlens-v2-mps', device='cpu')
        with self.assertRaises(InvalidRequest):
            LocalBackboneAdapter(self.MODEL, device='auto', dtype='float16', attn_implementation='eager')

    def test_profile_is_passed_to_the_backbone(self):
        adapter, made = self.adapter(profile='apronlens-v2-mps')
        adapter.load()
        self.assertEqual(made, [(self.MODEL, dict(device='mps', dtype='float16', attn_implementation='eager'))])
        self.assertIn(Operation.SCORE_LABELS, adapter.capabilities.operations)

    def test_generate_and_score_through_the_engine(self):
        adapter, _ = self.adapter()
        result = adapter.generate(request(model=adapter.served_model, max_output_tokens=50, temperature=0.7))
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.ignored_settings, ('temperature',))  # greedy engine
        self.assertEqual(result.metadata['engineRuntime']['dtype'], 'float32')
        scores = adapter.score_labels('Yes or No?', ('Yes', 'No'), Settings(adapter.served_model, 1))
        self.assertEqual(scores, {'Yes': -0.1, 'No': -2.3})

    def test_output_cap_reached_is_a_length_stop(self):
        adapter, _ = self.adapter(engine=FakeEngine(expected_manifest(self.MODEL), output_tokens=5))
        result = adapter.generate(request(model=adapter.served_model, max_output_tokens=5))
        self.assertEqual(result.finish_reason, FinishReason.LENGTH)

    def test_wrong_engine_revision_is_refused(self):
        adapter, _ = self.adapter(engine=FakeEngine(dict(expected_manifest(self.MODEL), revision='0' * 40)))
        with self.assertRaises(ModelAccessError):
            adapter.load()


class Repair(unittest.TestCase):
    def test_single_policy_reports_raw_validity(self):
        self.assertEqual(parse_json_output('{"a":1}'), ({'a': 1}, True, (), None))
        value, raw_valid, repairs, error = parse_json_output('```json\n{"a":1}\n```')
        self.assertEqual((value, raw_valid, repairs, error), ({'a': 1}, False, ('strip_code_fence',), None))
        self.assertEqual(parse_json_output('Sure! {"a":1}')[3], 'invalid_json')
        self.assertEqual(REPAIR_POLICY_VERSION, 'json-repair-v1')


if __name__ == '__main__':
    unittest.main()
