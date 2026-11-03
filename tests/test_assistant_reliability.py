"""Recovery preserves evidence, fails closed and gates startup readiness."""
import json,tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.training import training_app
from backend.training_assessment_candidate import generate_review
from backend.training_session import TrainingSession
from modelaccess.contract import Settings,ProviderReply,FinishReason,Usage
from modelaccess.mock import MockAdapter
from tests.test_training_assessment import valid_review

class SequenceAdapter(MockAdapter):
 def __init__(self,outputs):super().__init__([]);self.outputs=iter(outputs)
 def _generate(self,request,effective):
  self.calls.append((request,effective));value=next(self.outputs)
  if isinstance(value,Exception):raise value
  return ProviderReply(value,request.settings.model,'stop',FinishReason.STOP,Usage(20,30))

class ReliabilityTests(unittest.TestCase):
 def test_reference_guard_preserves_explicit_switches_and_relative_questions(self):
  from backend.training_adapter import reference_error
  candidates=[dict(aircraftId='A',flightInstance='AB123'),dict(aircraftId='B',flightInstance='CD456')]
  wrong=dict(referent=dict(aircraftId='B',flightInstance='CD456'))
  prefix='\nMemory: '+json.dumps(dict(currentReferent=dict(aircraftId='A',flightInstance='AB123')))+'\nQuestion: '
  self.assertEqual(reference_error(wrong,prefix+'Compare its E4 stand with the new one.',candidates),'followup_reference_mismatch')
  for q in ['Correction: I mean CD456. What is its stand?','What is its next rotation?','Which aircraft is at E4?', 'I mean the aircraft at E4. What is its stand?', 'Switch to B. What is its stand?']:
   self.assertIsNone(reference_error(wrong,prefix+q,candidates))
  self.assertIsNone(reference_error({'referent':None},prefix+'Where is it?',candidates))
 def test_warmup_exception_is_audited_and_blocks_startup(self):
  from backend.training_adapter import TrainingAdapter
  with tempfile.TemporaryDirectory() as d:
   a=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=Path(d)/'prompts')
   def fail(request):raise RuntimeError('failed')
   a.review=fail
   with self.assertRaises(RuntimeError):a.warmup(Settings(a.served_model,768,image_max_side=672))
   rows=[json.loads(x) for x in (Path(d)/'startup-inference.jsonl').read_text().splitlines()]
   self.assertEqual(len(rows),1);self.assertFalse(rows[0]['ok']);self.assertEqual(rows[0]['error'],'RuntimeError')
 def test_indexed_passages_expand_only_exact_learner_text(self):
  from backend.training_assessment_candidate import quote_choices,expand_review_quotes,validate_review
  c,p=self.context();choices=quote_choices(p['learnerResponse']);review=valid_review(p)
  for point in review['points']:point['learnerQuote']=next(iter(choices))
  expanded=validate_review(expand_review_quotes(json.dumps(review),p),p)
  self.assertTrue(all(x['learnerQuote'] in p['learnerResponse'] for x in expanded['points']))
  review['points'][0]['learnerQuote']='Q9999'
  with self.assertRaises(ValueError):expand_review_quotes(json.dumps(review),p)
  self.assertTrue(all(len(v)<=160 for v in quote_choices('x'*600).values()))
 def test_indexed_quotes_do_not_repair_invalid_report_citations(self):
  from backend.training_assessment_candidate import expand_review_quotes,validate_review
  c,p=self.context();r=valid_review(p)
  for point in r['points']:point['learnerQuote']='Q1'
  r['points'][0]['evidenceIds']=['future-report']
  with self.assertRaises(ValueError):validate_review(expand_review_quotes(json.dumps(r),p),p)
 def context(self):
  s=TrainingSession(17,'fog_restrictions');s.phase='checkpoint';s.active_probe=0;s.source_time=s.probes[0]['at']
  c,_=s.prepare_response(dict(actionId='r',runId=s.run_id,revision=s.revision,checkpointId='check-1',responseText='Low visibility procedures are active. TRN101 remains held.'))
  return c,json.loads(c.payload_json)
 def test_invalid_quote_retry_preserves_payload_and_attempts(self):
  c,p=self.context();good=valid_review(p);bad=json.loads(json.dumps(good));bad['points'][0]['learnerQuote']='words never submitted'
  a=SequenceAdapter([json.dumps(bad),json.dumps(good)])
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'audit';review,error=generate_review(a,Settings('mock-model',768),c,path)
   rows=[json.loads(l) for l in path.read_text().splitlines()]
  self.assertEqual(review,good);self.assertIsNone(error);self.assertEqual(len(rows),2)
  self.assertFalse(rows[0]['contractAccepted']);self.assertTrue(rows[1]['contractAccepted'])
  for request,_ in a.calls:self.assertEqual(json.loads(request.messages[0][1].split('Practice input JSON:\n')[1]),p)
 def test_second_invalid_citation_stays_withheld(self):
  c,p=self.context();bad=valid_review(p);bad['points'][0]['evidenceIds']=['unreceived']
  a=SequenceAdapter([json.dumps(bad)]*2)
  review,error=generate_review(a,Settings('mock-model',768),c,None)
  self.assertIsNone(review);self.assertIn('outside criterion',error);self.assertEqual(len(a.calls),2)
 def test_provider_failure_not_retried(self):
  c,_=self.context();a=SequenceAdapter([RuntimeError('unavailable')])
  review,error=generate_review(a,Settings('mock-model',768),c,None)
  self.assertIsNone(review);self.assertEqual(len(a.calls),1)
 def test_warmup_gates_readiness_without_advancing_source_clock(self):
  now=[0.];s=TrainingSession(17,'surface_conflict',mode='continuous',clock=lambda:now[0]);a=SequenceAdapter([])
  def warm(settings):now[0]=70.;return [{'path':'text'}]
  a.warmup=warm
  with TestClient(training_app(a,Settings('mock-model',768),s,token='test')) as client:
   self.assertEqual(s.state()['sourceTime'],0);self.assertEqual(s.last_wall,70)
   now[0]=71.;self.assertEqual(s.state()['sourceTime'],1)
   self.assertEqual(client.get('/health',headers={'Authorization':'Bearer test'}).status_code,200)
 def test_failed_warmup_does_not_announce_ready(self):
  a=SequenceAdapter([])
  def fail(settings):raise RuntimeError('startup inference failed')
  a.warmup=fail
  with self.assertRaisesRegex(RuntimeError,'startup inference failed'):
   with TestClient(training_app(a,Settings('mock-model',768),TrainingSession(17,'surface_conflict'),token='test')):pass
if __name__=='__main__':unittest.main()
