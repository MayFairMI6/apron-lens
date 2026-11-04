"""Real spawned processes, fake inference: lifecycle evidence, not model accuracy."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from modelaccess.contract import Settings, Request, Result, FinishReason, Usage
from backend.training_worker import IsolatedTrainingAdapter

class FakeModel:
    def load(self): pass
    def warmup(self, settings): return [{'ok':True}]
    def generate(self, request):
        if request.request_id=='hang': time.sleep(30)
        if request.request_id=='crash': os._exit(7)
        return Result(request.request_id,'local-backbone',request.settings.model,request.settings.model,
                      'actual worker response',FinishReason.STOP,'stop',Usage(2,3),.01,{},())
    review=generate

class BrokenStartup(FakeModel):
    def warmup(self, settings): raise RuntimeError('startup failure')

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'audit.jsonl'
        self.settings=Settings('fake',10)
        self.adapter=IsolatedTrainingAdapter(FakeModel,'fake',audit_path=self.path,
             generation_timeout=.15,startup_timeout=5,cleanup_timeout=.2)
    def tearDown(self): self.adapter.close();self.tmp.cleanup()
    def request(self, name): return Request(name,(('user','question'),),self.settings)
    def ready(self):
        deadline=time.monotonic()+5
        while self.adapter.status!='ready' and time.monotonic()<deadline: time.sleep(.02)
        self.assertEqual(self.adapter.status,'ready')
    def test_hang_and_crash_stop_old_owner_then_warm_replacement(self):
        self.adapter.warmup(self.settings)
        for fault in ('hang','crash','hang'):
            pid=self.adapter._process.pid;start=time.monotonic()
            reply=self.adapter.review(self.request(fault))
            self.assertFalse(reply.ok);self.assertEqual(reply.text,'')
            self.assertIsNone(reply.usage.output_tokens)
            self.assertLess(time.monotonic()-start,2)
            self.ready();self.assertNotEqual(self.adapter._process.pid,pid)
            self.assertTrue(self.adapter.generate(self.request('success')).ok)
        events=[json.loads(s) for s in self.path.read_text().splitlines()]
        owners=set()
        for event in events:
            if event['event']=='worker_started':
                self.assertFalse(owners);owners.add(event['pid'])
            if event['event']=='worker_stopped':owners.remove(event['pid'])
        self.assertEqual(len(owners),1)
    def test_unpicklable_factory_fails_closed_without_masking_start_error(self):
        self.adapter.factory=lambda:FakeModel()
        with self.assertRaises((AttributeError,TypeError)):self.adapter.warmup(self.settings)
        self.assertEqual(self.adapter.status,'failed');self.assertIsNone(self.adapter._process)

    @unittest.skipUnless(os.name=='posix','POSIX stop signal required')
    def test_stopped_worker_large_send_is_bounded_and_recoverable(self):
        import signal
        self.adapter.warmup(self.settings)
        os.kill(self.adapter._process.pid,signal.SIGSTOP)
        request=Request('large',(('user','x'*2_000_000),),self.settings)
        start=time.monotonic();reply=self.adapter.generate(request)
        self.assertFalse(reply.ok);self.assertLess(time.monotonic()-start,3)
        self.ready();self.assertTrue(self.adapter.generate(self.request('success')).ok)

    def test_failed_startup_does_not_announce_ready(self):
        self.adapter.factory=BrokenStartup
        with self.assertRaises(RuntimeError):self.adapter.warmup(self.settings)
        self.assertEqual(self.adapter.status,'failed');self.assertIsNone(self.adapter._process)
        self.assertFalse(self.adapter.generate(self.request('success')).ok)
    def test_close_cannot_restart_or_serve(self):
        self.adapter.warmup(self.settings);self.adapter.close()
        self.assertFalse(self.adapter.generate(self.request('success')).ok)
        self.assertEqual(self.adapter.status,'closed');self.assertIsNone(self.adapter._process)
    def test_close_during_generation_and_queued_recovery_stays_closed(self):
        import threading
        self.adapter.warmup(self.settings)
        thread=threading.Thread(target=lambda:self.adapter.generate(self.request('hang')))
        thread.start();time.sleep(.05);self.adapter.close();thread.join(3)
        self.assertFalse(thread.is_alive())
        self.adapter._recover()  # A previously queued recovery cannot revive status.
        self.assertEqual(self.adapter.status,'closed');self.assertIsNone(self.adapter._process)

    def test_replacement_startup_failure_remains_unavailable(self):
        self.adapter.warmup(self.settings);self.adapter.factory=BrokenStartup
        self.assertFalse(self.adapter.generate(self.request('crash')).ok)
        self.adapter._recovery.join(5)
        self.assertFalse(self.adapter._recovery.is_alive())
        self.assertEqual(self.adapter.status,'failed');self.assertIsNone(self.adapter._process)
        self.assertFalse(self.adapter.generate(self.request('success')).ok)

    def test_parallel_request_is_rejected_without_second_owner(self):
        import threading
        self.adapter.warmup(self.settings)
        thread=threading.Thread(target=lambda:self.adapter.generate(self.request('hang')))
        thread.start();time.sleep(.05)
        reply=self.adapter.generate(self.request('second'))
        self.assertFalse(reply.ok);self.assertEqual(reply.error,'model_worker_unavailable')
        thread.join(3);self.assertFalse(thread.is_alive());self.ready()

if __name__=='__main__':unittest.main()
