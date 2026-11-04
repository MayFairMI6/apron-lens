"""Real spawned processes, fake inference: lifecycle evidence, not model accuracy."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from modelaccess.contract import Settings, Request, Result, FinishReason, Usage
from backend.training_worker import IsolatedTrainingAdapter

class FakeModel:
    def load(self): pass
    def warmup(self, settings): return [{'ok':True}]
    def generate(self, request):
        if request.request_id=='hang': time.sleep(30)
        if request.request_id=='crash': os._exit(7)
        if request.request_id=='runtime-error':
            return Result(request.request_id,'local-backbone','fake','fake','partial',FinishReason.ERROR,'provider_exception',Usage(),.01,{},(),error='provider_error:RuntimeError')
        result = Result(request.request_id,'local-backbone',request.settings.model,request.settings.model,
                      'actual worker response',FinishReason.STOP,'stop',Usage(2,3),.01,{},())
        if request.request_id=='malformed-text': return replace(result,text=None)
        if request.request_id=='malformed-finish': return replace(result,finish_reason='bogus')
        if request.request_id=='unserializable': return replace(result,metadata={'bad':{1,2}})
        if request.request_id=='unpicklable': return replace(result,metadata={'bad':lambda:None})
        return result
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
    def test_reported_runtime_error_restarts_owner_without_replaying_request(self):
        self.adapter.warmup(self.settings);old=self.adapter._process.pid
        result=self.adapter.generate(self.request('runtime-error'))
        self.assertFalse(result.ok);self.ready()
        self.assertNotEqual(old,self.adapter._process.pid)
        self.assertTrue(self.adapter.generate(self.request('success')).ok)
        events=[json.loads(line) for line in self.path.read_text().splitlines()]
        failed=[e for e in events if e['event']=='worker_runtime_failure']
        self.assertEqual(len(failed),1)
        self.assertEqual(failed[0]['modelResult']['text'],'partial')
        self.assertEqual(failed[0]['modelResult']['error'],'provider_error:RuntimeError')

    def test_malformed_and_unserializable_results_replace_owner(self):
        self.adapter.warmup(self.settings)
        for fault in ('malformed-text','malformed-finish','unserializable','unpicklable'):
            with self.subTest(fault=fault):
                old=self.adapter._process.pid
                reply=self.adapter.review(self.request(fault))
                self.assertFalse(reply.ok);self.assertEqual(reply.text,'')
                self.ready();self.assertNotEqual(old,self.adapter._process.pid)
                self.assertTrue(self.adapter.review(self.request('success')).ok)

    def test_failed_process_creation_releases_connections(self):
        with patch('backend.training_worker.subprocess.Popen',side_effect=OSError('spawn failed')):
            with self.assertRaisesRegex(OSError,'spawn failed'):
                self.adapter.warmup(self.settings)
        self.assertIsNone(self.adapter._process);self.assertIsNone(self.adapter._connection)
        self.assertEqual(self.adapter.status,'failed')
        self.adapter.warmup(self.settings)
        self.assertTrue(self.adapter.review(self.request('success')).ok)

    def test_audit_failure_releases_owner_and_does_not_announce_ready(self):
        self.adapter.warmup(self.settings);process=self.adapter._process
        with patch.object(self.adapter,'_record',side_effect=OSError('disk failure')):
            reply=self.adapter.review(self.request('success'))
        self.assertFalse(reply.ok);self.assertFalse(process.is_alive())
        self.assertIsNone(self.adapter._process);self.assertIsNone(self.adapter._connection)
        self.assertEqual(self.adapter.status,'failed')
        self.assertFalse(self.adapter._lock.locked())

    def test_recovery_audit_failure_stops_replacement_owner(self):
        self.adapter.warmup(self.settings)
        original=self.adapter._record
        def record(event,**values):
            if event in ('worker_ready','worker_recovery_failed','worker_stopped'):
                raise OSError('disk failure during replacement startup')
            return original(event,**values)
        with patch.object(self.adapter,'_record',side_effect=record):
            self.assertFalse(self.adapter.generate(self.request('crash')).ok)
            # Stop-audit failure prevents automatic recovery; explicitly exercise
            # a queued recovery against the failed audit destination.
            self.adapter._recover()
        self.assertIsNone(self.adapter._process);self.assertIsNone(self.adapter._connection)
        self.assertEqual(self.adapter.status,'failed')
        self.assertFalse(self.adapter._lock.locked())

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
