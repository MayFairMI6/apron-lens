"""Real isolated deadline and audit checks with fake inference, not model scores."""
from dataclasses import replace
from functools import partial
import json
from pathlib import Path
import tempfile
import time
import unittest

from backend.training_worker import IsolatedTrainingAdapter
from modelaccess.contract import Request, Settings, Result, Usage, FinishReason
from experiments.typed_qwen_frames.two_pass_runtime import TwoPassFrameAdapter


LEARNER = 'The cart is parked.'
SELECTION = json.dumps({'clauses': [['c1', ['u1'], LEARNER]], 'unresolved': []})
ANNOTATION = json.dumps({'claims': [['c1', ['u1'], LEARNER, 'active', None]], 'unresolved': []})


class FakeTwoPass(TwoPassFrameAdapter):
    def load(self):
        return None  # Worker startup must never load actual weights in this test.

    def __init__(self, *, audit_path, mode='success', delays=(0, 0)):
        super().__init__(audit_path=audit_path)
        self.mode, self.delays, self.calls = mode, delays, []

    def generate(self, request):
        self.calls.append(request)
        if request.request_id == 'two-pass-startup':
            text, count = 'ready', 1
        else:
            selection = request.request_id.endswith('-selection')
            if not selection:
                audit = [json.loads(s) for s in self.audit_path.read_text().splitlines()]
                if not any(e['event'] == 'stage_raw_result' and e['stage'] == 'selection' for e in audit):
                    raise AssertionError('Stage A was not durably recorded before Stage B')
            time.sleep(self.delays[0 if selection else 1])
            text, count = (SELECTION if selection else ANNOTATION), 30
            if self.mode == ('malformed_selection' if selection else 'malformed_annotation'):
                text = '{broken'
            if selection and self.mode == 'over_cap':
                count = 501
        stopped = self.mode != 'missing_eos'
        return Result(request.request_id, 'local-backbone', request.settings.model,
            request.settings.model, text, FinishReason.STOP, 'observed_eos',
            Usage(20, count, 0, 0, 0), 0.001,
            {'max_output_tokens': request.settings.max_output_tokens}, (),
            metadata={'observedEOS': stopped, 'terminalTokenId': 1 if stopped else 2})


class TwoPassRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'stages.jsonl'
        self.settings = Settings('fake', 1000)
        self.request = Request('control', (('user', LEARNER),), self.settings)

    def tearDown(self):
        self.temp.cleanup()

    def test_two_planned_calls_and_both_audits_never_grant_fidelity(self):
        adapter = FakeTwoPass(audit_path=self.path)
        result = adapter.review(self.request)
        self.assertTrue(result.ok)
        self.assertEqual([r.settings.max_output_tokens for r in adapter.calls], [500, 500])
        self.assertEqual(result.usage.output_tokens, 60)
        self.assertEqual(result.usage.input_tokens, 40)
        self.assertEqual(result.request_id, self.request.request_id)
        self.assertEqual(result.text, ANNOTATION)
        self.assertIsNotNone(result.metadata['parsed'])
        for flag in ('fidelityVerified', 'reportCheckAllowed', 'semanticCompletenessVerified'):
            self.assertIs(result.metadata[flag], False)
        events = [json.loads(s) for s in self.path.read_text().splitlines()]
        self.assertEqual([e['stage'] for e in events if e['event'] == 'stage_raw_result'],
                         ['selection', 'annotation'])

    def test_invalid_selection_never_calls_annotation_and_keeps_raw(self):
        for mode in ('malformed_selection', 'missing_eos', 'over_cap'):
            with self.subTest(mode=mode):
                adapter = FakeTwoPass(audit_path=self.path, mode=mode)
                result = adapter.review(self.request)
                self.assertFalse(result.ok)
                self.assertEqual(len(adapter.calls), 1)
                self.assertIsNone(result.metadata['parsed'])
                self.assertEqual(result.text, result.metadata['stages'][0]['result']['text'])

    def test_annotation_failure_is_not_replaced_by_successful_selection(self):
        adapter = FakeTwoPass(audit_path=self.path, mode='malformed_annotation')
        result = adapter.review(self.request)
        self.assertFalse(result.ok)
        self.assertEqual(len(adapter.calls), 2)
        self.assertEqual(result.text, '{broken')
        self.assertIsNotNone(result.metadata['selection'])
        self.assertIsNone(result.metadata['parsed'])

    def test_warmup_uses_one_ready_probe_not_interpretation(self):
        adapter = FakeTwoPass(audit_path=self.path)
        adapter.warmup(self.settings)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(adapter.calls[0].settings.max_output_tokens, 16)
        self.assertFalse(self.path.exists())

    def test_aggregate_deadline_kills_second_stage_and_preserves_first_raw(self):
        owner = IsolatedTrainingAdapter(partial(FakeTwoPass, audit_path=str(self.path),
                                               delays=(0.2, 0.8)), 'fake',
            audit_path=Path(self.temp.name)/'worker.jsonl', generation_timeout=0.5,
            startup_timeout=10, cleanup_timeout=0.2)
        try:
            owner.warmup(self.settings)
            started = time.monotonic()
            result = owner.review(self.request)
            elapsed = time.monotonic()-started
            self.assertFalse(result.ok)
            self.assertIn('TimeoutError', result.error)
            self.assertLess(elapsed, 2)
            self.assertIsNone(result.usage.output_tokens)
        finally:
            owner.close()
        events = [json.loads(s) for s in self.path.read_text().splitlines()]
        self.assertEqual([e['stage'] for e in events if e['event'] == 'stage_raw_result'], ['selection'])
        self.assertEqual([e['stage'] for e in events if e['event'] == 'stage_started'], ['selection', 'annotation'])
        self.assertFalse(any(e['event'] == 'request_completed' for e in events))

    def test_nonfrozen_output_capacity_is_rejected_without_inference(self):
        adapter = FakeTwoPass(audit_path=self.path)
        with self.assertRaises(ValueError):
            adapter.review(replace(self.request, settings=replace(self.settings, max_output_tokens=2000)))
        self.assertEqual(adapter.calls, [])


if __name__ == '__main__':
    unittest.main()
