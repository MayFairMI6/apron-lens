"""Deterministic owner-lock readiness races; spawned fake inference only."""
import tempfile
import threading
import unittest
from pathlib import Path

from backend.training_worker import IsolatedTrainingAdapter
from modelaccess.contract import Request, Settings
from tests.test_training_worker import FakeModel


class WorkerReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.release_audit = threading.Event()
        self.audit_entered = threading.Event()
        self.threads = []
        self.thread_errors = []
        self.settings = Settings('fake', 10)
        self.adapter = IsolatedTrainingAdapter(FakeModel, 'fake',
            audit_path=Path(self.tmp.name)/'worker.jsonl',
            generation_timeout=.15, startup_timeout=5, cleanup_timeout=.2)

    def tearDown(self):
        self.release_audit.set()
        for thread in self.threads:
            thread.join(5)
        self.adapter.close()
        self.tmp.cleanup()

    def request(self, name='success'):
        return Request(name, (('user', 'question'),), self.settings)

    def block_audit(self, wanted):
        original = self.adapter._record
        def record(event, **values):
            if event == wanted:
                self.audit_entered.set()
                if not self.release_audit.wait(5):
                    raise RuntimeError('Test did not release blocked audit')
            return original(event, **values)
        self.adapter._record = record

    def background(self, fn):
        def run():
            try:
                fn()
            except Exception as exc:
                self.thread_errors.append(exc)
        thread = threading.Thread(target=run)
        self.threads.append(thread)
        thread.start()
        return thread

    def assert_ready_call(self):
        self.assertEqual(self.adapter.status, 'ready')
        self.assertFalse(self.adapter._lock.locked())
        self.assertTrue(self.adapter.generate(self.request()).ok)

    def test_warmup_does_not_publish_ready_before_owner_lock_release(self):
        self.block_audit('worker_ready')
        thread = self.background(lambda: self.adapter.warmup(self.settings))
        self.assertTrue(self.audit_entered.wait(5))
        self.assertTrue(self.adapter._lock.locked())
        self.assertNotEqual(self.adapter.status, 'ready')
        self.release_audit.set()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.thread_errors, [])
        self.assert_ready_call()

    def test_recovery_does_not_publish_ready_before_owner_lock_release(self):
        self.adapter.warmup(self.settings)
        self.block_audit('worker_ready')
        self.assertFalse(self.adapter.generate(self.request('crash')).ok)
        self.assertTrue(self.audit_entered.wait(5))
        self.assertTrue(self.adapter._lock.locked())
        self.assertNotEqual(self.adapter.status, 'ready')
        unavailable = self.adapter.generate(self.request())
        self.assertFalse(unavailable.ok)
        self.assertEqual(unavailable.metadata['workerStatus'], self.adapter.status)
        self.release_audit.set()
        self.adapter._recovery.join(5)
        self.assertFalse(self.adapter._recovery.is_alive())
        self.assert_ready_call()

    def test_busy_call_does_not_mask_failed_or_closed_states(self):
        self.adapter.warmup(self.settings)
        self.block_audit('worker_request_complete')
        results = []
        thread = self.background(lambda: results.append(self.adapter.generate(self.request())))
        self.assertTrue(self.audit_entered.wait(5))
        self.assertTrue(self.adapter._lock.locked())
        self.assertNotEqual(self.adapter.status, 'ready')
        self.assertFalse(self.adapter.generate(self.request()).ok)
        self.release_audit.set()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertTrue(results[0].ok)
        self.assert_ready_call()
        self.adapter.status = 'failed'
        with self.adapter._lock:
            self.assertEqual(self.adapter.status, 'failed')
        self.adapter.close()
        self.assertEqual(self.adapter.status, 'closed')
        self.assertFalse(self.adapter.generate(self.request()).ok)


if __name__ == '__main__':
    unittest.main()
