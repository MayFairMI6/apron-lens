"""Variant dispatch and shared deadline checks using fake inference only."""
from dataclasses import replace
from functools import partial
import json
from pathlib import Path
import tempfile
import unittest

from backend.training_worker import IsolatedTrainingAdapter
from modelaccess.contract import Request, Settings
from experiments.typed_qwen_frames import discourse_candidate, two_pass_candidate
from tests.test_typed_qwen_two_pass_runtime import FakeTwoPass, LEARNER, ANNOTATION


class FakeDiscourse(FakeTwoPass):
    candidate_api = discourse_candidate

    def generate(self, request):
        result = super().generate(request)
        if request.request_id == 'two-pass-startup' or self.mode != 'success':
            return result
        if request.request_id.endswith('-selection'):
            text = json.dumps({'repairs': [], 'unresolved': []})
        else:
            wire = json.loads(ANNOTATION)
            wire['repairAssignments'] = []
            text = json.dumps(wire)
        return replace(result, text=text)


class DiscourseRuntimeTests(unittest.TestCase):
    def test_explicit_variant_does_not_change_default_or_treat_empty_map_as_fallback(self):
        self.assertIs(FakeTwoPass.candidate_api, two_pass_candidate)
        self.assertIs(FakeDiscourse.candidate_api, discourse_candidate)
        with tempfile.TemporaryDirectory() as tmp:
            adapter = FakeDiscourse(audit_path=Path(tmp)/'stages.jsonl')
            result = adapter.review(Request('plain', (('user', LEARNER),), Settings('fake', 1000)))
            self.assertTrue(result.ok)
            self.assertEqual(len(adapter.calls), 2)
            self.assertEqual(result.metadata['version'], discourse_candidate.VERSION)
            self.assertEqual(result.metadata['candidateModule'], discourse_candidate.__name__)
            self.assertFalse(result.metadata['reportCheckAllowed'])
            self.assertIsNotNone(result.metadata['parsed'])
            self.assertIn('repairAssignments', result.metadata['parsed']['wireFrames'])

    def test_variant_keeps_same_aggregate_kill_and_preserves_map_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'stages.jsonl'
            owner = IsolatedTrainingAdapter(partial(FakeDiscourse, audit_path=str(path),
                delays=(0.2, 0.8)), 'fake', audit_path=Path(tmp)/'worker.jsonl',
                generation_timeout=0.5, startup_timeout=10, cleanup_timeout=0.2)
            try:
                settings = Settings('fake', 1000)
                owner.warmup(settings)
                result = owner.review(Request('deadline', (('user', LEARNER),), settings))
                self.assertFalse(result.ok)
                self.assertIn('TimeoutError', result.error)
            finally:
                owner.close()
            raw = [json.loads(l) for l in path.read_text().splitlines()]
            returned = [e for e in raw if e['event'] == 'stage_raw_result']
            self.assertEqual(len(returned), 1)
            self.assertEqual(returned[0]['candidateModule'], discourse_candidate.__name__)
            self.assertEqual(json.loads(returned[0]['result']['text']), {'repairs': [], 'unresolved': []})


if __name__ == '__main__':
    unittest.main()
