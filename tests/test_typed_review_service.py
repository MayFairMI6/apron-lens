"""Distinct classification lifecycle and audit; no generation/EOS emulation."""
import json
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from backend.typed_review_service import (ReviewRequest, ReviewOutcome,
    IsolatedReviewService, generate_semantic_review)
from backend.training_assessment import ReviewContext
from tests.test_typed_relation_review import payload, FakeScorer
from experiments.typed_relation_review.candidate import evaluate

class Worker:
    def load(self): pass
    def warmup(self, settings): return {'operation': 'classification', 'ready': True}
    def review(self, request):
        if request.request_id == 'hang': time.sleep(8)
        p = request.payload
        review = evaluate(p, FakeScorer(), time.monotonic()+5)
        return ReviewOutcome(request.request_id, request.fingerprint, 'completed', review,
                             'pinned-model', 'revision', 'test-policy', .01, {'pairs': []})

class TypedReviewServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = IsolatedReviewService(Worker, 'pinned-model', model_revision='revision',
            policy_version='test-policy',
            audit_path=Path(self.tmp.name)/'worker.jsonl',generation_timeout=.3,
            startup_timeout=5,cleanup_timeout=.2)
        self.service.warmup(None)
        self.request = ReviewRequest('normal', 'fingerprint', payload())
    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()
    def test_actual_classification_completion_no_generation_claim(self):
        result=self.service.review(self.request)
        self.assertTrue(result.ok)
        self.assertFalse(hasattr(result, 'finish_reason'))
        self.assertFalse(hasattr(result, 'usage'))
        self.assertEqual(result.completion,'completed')
    def test_identity_revision_and_source_validation(self):
        result=Worker().review(self.request)
        for bad in (replace(result, fingerprint='stale'),replace(result,model_revision='wrong'),
                    replace(result,request_id='wrong'),replace(result,completion='stop'),
                    replace(result,policy_version=''),replace(result,audit=[]),
                    replace(result,elapsed_seconds=-1),replace(result,error='failed')):
            with self.assertRaises(ValueError): self.service._validate_result(bad,self.request)
        result.review['points'][0]['evidenceIds']=['future']
        with self.assertRaises(ValueError):self.service._validate_result(result,self.request)
    def test_deadline_stops_owner_and_allows_explicit_retry(self):
        old=self.service._process.pid
        result=self.service.review(replace(self.request,request_id='hang'))
        self.assertFalse(result.ok)
        self.assertEqual(result.completion,'timed_out')
        self.assertIsNone(result.review)
        limit=time.monotonic()+5
        while self.service.status!='ready' and time.monotonic()<limit:time.sleep(.03)
        self.assertEqual(self.service.status,'ready')
        self.assertNotEqual(self.service._process.pid,old)
        self.assertTrue(self.service.review(self.request).ok)
    def test_context_and_classification_audit(self):
        context=ReviewContext('run',2,'check-3','action','fingerprint',json.dumps(payload()))
        path=Path(self.tmp.name)/'review.jsonl'
        review,error=generate_semantic_review(self.service,None,context,path)
        self.assertIsNone(error)
        self.assertEqual(review['verdict'],'supported')
        record=json.loads(path.read_text())
        self.assertTrue(record['contractAccepted'])
        self.assertEqual(record['classificationOutcome']['completion'],'completed')
        self.assertEqual(record['payload']['learnerResponse'],payload()['learnerResponse'])

if __name__=='__main__':unittest.main()

class TypedReviewIntegrationTests(unittest.TestCase):
    def test_route_uses_separate_owner_and_readiness_preserves_input(self):
        from fastapi.testclient import TestClient
        from unittest.mock import Mock
        from backend.training import training_app
        from modelaccess.mock import MockAdapter
        from modelaccess.contract import Settings
        from tests.test_training_assessment import TypedAssessmentTests, valid_review
        session,_=TypedAssessmentTests().checkpoint()
        service=Mock(status='ready')
        service.review.side_effect=lambda request: ReviewOutcome(request.request_id,request.fingerprint,
            'completed',valid_review(request.payload),'model','revision','test-policy',.01,{'pairs':[]})
        ordinary=MockAdapter([])
        with tempfile.TemporaryDirectory() as tmp:
            app=training_app(ordinary,Settings('mock',50),session,token='test-token',
                             audit_path=Path(tmp)/'audit.jsonl',typed_review_service=service)
            headers={'Authorization':'Bearer test-token'}
            with TestClient(app) as client:
                service.status='recovering'
                self.assertEqual(client.get('/health',headers=headers).json()['typedReviewStatus'],'recovering')
                self.assertEqual(client.get('/training',headers=headers).json()['typedReviewStatus'],'recovering')
                self.assertEqual(client.post('/conversation',headers=headers,json={}).status_code,503)
                body=TypedAssessmentTests().body(session,'I need to check the reports.')
                response=client.post('/training/response',headers=headers,json=body)
                self.assertEqual(response.status_code,429)
                self.assertEqual(session.review_status,'idle')
                service.status='ready'
                ordinary.status='recovering'
                self.assertEqual(client.post('/training/response',headers=headers,json=body).status_code,429)
                self.assertEqual(service.review.call_count,0)
                ordinary.status='ready'
                response=client.post('/training/response',headers=headers,json=body)
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(service.review.call_count,1)
                duplicate=client.post('/training/response',headers=headers,json=body)
                self.assertEqual(duplicate.status_code,200)
                self.assertEqual(service.review.call_count,1)
            service.close.assert_called_once()

class TypedClassificationConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_and_late_result_preserve_text_and_allow_retry(self):
        import asyncio
        import threading
        import httpx
        from backend.training import training_app
        from modelaccess.mock import MockAdapter
        from modelaccess.contract import Settings
        from tests.test_training_assessment import TypedAssessmentTests, valid_review
        session,_=TypedAssessmentTests().checkpoint()
        class GatedService:
            status='ready'
            def __init__(self):
                self.entered=threading.Event();self.release=threading.Event();self.calls=0
            def warmup(self,settings):return []
            def close(self):self.release.set()
            def review(self,request):
                self.calls+=1;self.entered.set()
                if not self.release.wait(3):raise RuntimeError('test gate expired')
                return ReviewOutcome(request.request_id,request.fingerprint,'completed',
                    valid_review(request.payload),'model','revision','test-policy',.1,{})
        service=GatedService()
        with tempfile.TemporaryDirectory() as tmp:
            app=training_app(MockAdapter([]),Settings('mock',50),session,token='test-token',
                             audit_path=Path(tmp)/'audit.jsonl',typed_review_service=service)
            app.state.review_timeout_seconds=.06
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',
                        headers={'Authorization':'Bearer test-token'}) as client:
                    body=TypedAssessmentTests().body(session,'Original learner text')
                    task=asyncio.create_task(client.post('/training/response',json=body))
                    try:
                        self.assertTrue(await asyncio.to_thread(service.entered.wait,2))
                        result=await task
                        self.assertEqual(result.json()['reviewStatus'],'failed')
                        self.assertEqual(result.json()['responseText'],'Original learner text')
                        self.assertTrue(app.state.busy.locked())
                        retry=TypedAssessmentTests().body(session,'Original learner text','retry')
                        self.assertEqual((await client.post('/training/response',json=retry)).status_code,429)
                    finally:
                        service.release.set()
                        await asyncio.gather(*list(app.state.assessment_tasks))
                    self.assertFalse(app.state.busy.locked())
                    self.assertIsNone(session.state()['feedback'])
                    retry=TypedAssessmentTests().body(session,'Original learner text','retry-after')
                    result=await client.post('/training/response',json=retry)
                    self.assertEqual(result.json()['phase'],'feedback')
                    self.assertEqual(service.calls,2)

class ReviewAdmissionRaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_peer_recovery_between_readiness_check_and_lock_rejects_without_mutation(self):
        import httpx
        from unittest.mock import Mock
        from backend.training import training_app
        from backend.conversation.server import ConversationRequest
        from fastapi import HTTPException
        from modelaccess.mock import MockAdapter
        from modelaccess.contract import Settings
        from tests.test_training_assessment import TypedAssessmentTests
        session,_=TypedAssessmentTests().checkpoint()
        ordinary=MockAdapter([]);ordinary.status='ready'
        service=Mock(status='ready')
        with tempfile.TemporaryDirectory() as tmp:
            app=training_app(ordinary,Settings('mock',50),session,token='test-token',
                audit_path=Path(tmp)/'audit.jsonl',typed_review_service=service)
            class FlipOnAcquire:
                def locked(self):return real.locked()
                async def acquire(self):
                    await real.acquire();service.status='recovering';return True
                def release(self):real.release()
                async def __aenter__(self):await self.acquire();return self
                async def __aexit__(self,*args):self.release()
            async with app.router.lifespan_context(app):
                real=app.state.busy
                app.state.busy=FlipOnAcquire()
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',
                        headers={'Authorization':'Bearer test-token'}) as client:
                    before=session.state()
                    body=TypedAssessmentTests().body(session,'Saved locally')
                    response=await client.post('/training/response',json=body)
                    self.assertEqual(response.status_code,429)
                    self.assertEqual(session.state(),before)
                    self.assertFalse(real.locked());service.review.assert_not_called()
                    health=(await client.get('/health')).json()
                    self.assertEqual(health['status'],'recovering')
                    self.assertEqual(health['ordinaryStatus'],'ready')
                service.status='ready'
                endpoint=next(r.endpoint for r in app.routes if getattr(r,'path','')=='/conversation')
                body=ConversationRequest(requestId='r',turnId='t',sessionId='s',scenarioId=session.scenario['scenarioId'],
                    aircraftId='A1',flightInstance='TRN101',checkpoint=60,expectedRevision=0,question='What is reported?')
                with self.assertRaises(HTTPException) as caught:await endpoint(body)
                self.assertEqual(caught.exception.status_code,429)
                self.assertEqual(ordinary.calls,[]);self.assertFalse(real.locked())
