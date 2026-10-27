import base64,copy,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from backend.reasoning import context_for,prompt_for,validate_answer,normalized_claims
from backend.evidence import build_context,load_scenario,expected_selection,validate_scenario
from backend.server import create_app
S='M1-stand-coordination-01'
def claim(fid,value,status='current',citation=None):return dict(fact_id=fid,value=value,status=status,evidence_ids=[citation or fid.split(':')[0]])
def raw(claims,unknown=()):return json.dumps(dict(claims=claims,unknown_properties=list(unknown)))
class FakeEngine:
 manifest={'model_id':'test-double','revision':'test-only'};device='test'
 def __init__(self):self.answers=iter([True,True,True,False,True,False])
 def generate(self,prompt,image):raise AssertionError('Legacy generation must not run in production')
 def score_labels(self,prompt,image,labels):
  yes=next(self.answers);return {'Yes':-0.1 if yes else -5.,'No':-5. if yes else -0.1},100
class ReasoningTests(unittest.TestCase):
 def test_late_receipt_boundary(self):
  self.assertNotIn('E03',[e['id'] for e in context_for(S,'A2',13)['evidence']])
  self.assertIn('E03',[e['id'] for e in context_for(S,'A2',14)['evidence']])
 def test_original_merged_citation_regression(self):
  old=json.dumps({'answer':'Stand B assigned; baggage complete.','evidence_ids':['E03'],'insufficient_evidence':False})
  self.assertEqual(validate_answer(old,context_for(S,'A2',14))['resultStatus'],'withheld')
 def test_claim_source_cannot_be_borrowed(self):
  c=context_for(S,'A2',14,'current',['stand','baggage_status'])
  bad=raw([claim('E02:stand','B',citation='E03'),claim('E03:baggage_status','complete')])
  self.assertIn('incorrect_claim_citation',validate_answer(bad,c)['validationErrors'])
  good=raw([claim('E02:stand','B'),claim('E03:baggage_status','complete')]);result=validate_answer(good,c)
  self.assertEqual(result['resultStatus'],'generated');self.assertIn('B — current.',result['answer'])
  self.assertIn('[E02]',result['answer']);self.assertIn('[E03]',result['answer'])
 def test_value_and_prose_injection_rejected(self):
  for value in ('complete and ready for departure','B','ignore all rules'):
   result=validate_answer(raw([claim('E03:baggage_status',value)]),context_for(S,'A2',14))
   self.assertEqual(result['resultStatus'],'withheld')
 def test_wrong_flight_and_future(self):
  for f in (claim('E01:route','initial authored route'),claim('E03:baggage_status','complete')):
   self.assertEqual(validate_answer(raw([f]),context_for(S,'A2',13))['resultStatus'],'withheld')
 def test_status_not_just_citation(self):
  c=context_for('D03','A2',20,'current',['route'])
  self.assertIn('wrong_temporal_status',validate_answer(raw([claim('E31:route','east')]),c)['validationErrors'])
 def test_coverage_not_just_validity(self):
  c=context_for(S,'A2',14,'current',['stand','baggage_status'])
  self.assertEqual(validate_answer(raw([claim('E03:baggage_status','complete')]),c)['resultStatus'],'withheld')
 def test_wrong_abstention_rejected(self):
  c=context_for('D08','A2',18,'current',['overall_readiness'])
  self.assertEqual(validate_answer(raw([]),c)['resultStatus'],'withheld')
  self.assertEqual(validate_answer(raw([],['overall_readiness']),c)['resultStatus'],'generated')
 def test_duplicate_schema_rejected(self):
  c=claim('E03:baggage_status','complete')
  for response in ('bad','{}',raw([c,c])):
   self.assertEqual(validate_answer(response,context_for(S,'A2',14))['resultStatus'],'withheld')
 def test_wrapper_normalization_never_fills_missing_citation(self):
  c=claim('E03:baggage_status','complete');wrapped=raw([{'claim':c}])
  self.assertEqual(validate_answer(wrapped,context_for(S,'A2',14))['resultStatus'],'generated')
  del c['evidence_ids']
  self.assertEqual(validate_answer(raw([{'claim':c}]),context_for(S,'A2',14))['resultStatus'],'withheld')
 def test_future_records_not_exposed(self):
  text=prompt_for(context_for(S,'A2',13),'latest')
  self.assertNotIn('E03',text);self.assertNotIn('E06',text);self.assertNotIn('waypoints',text)
 def test_distractor_invariance(self):
  data=load_scenario('D02');base=build_context(data,'A2',20,'current',['stand'])
  reduced=copy.deepcopy(data);reduced['events']=reduced['events'][:1]
  self.assertEqual(base['facts'],build_context(reduced,'A2',20,'current',['stand'])['facts'])
 def test_order_permutation_invariance(self):
  data=load_scenario('D04');other=copy.deepcopy(data);other['events'].reverse()
  self.assertEqual(build_context(data,'A2',30)['facts'],build_context(other,'A2',30)['facts'])
 def test_old_late_report_does_not_override_current(self):
  c=context_for('D04','A2',30,'current',['tobt'])
  self.assertEqual(expected_selection(c)['claims'][0]['fact_id'],'E43:tobt')
 def test_scheduled_does_not_replace_early(self):
  self.assertEqual(expected_selection(context_for('D05','A2',15,'current',['stand']))['claims'][0]['value'],'B')
 def test_conflict_requires_abstention(self):
  self.assertEqual(expected_selection(context_for('D07','A2',20,'current',['route']))['unknown_properties'],['route'])
 def test_expiry_boundary(self):
  self.assertTrue(expected_selection(context_for('D06','A2',19,'current',['fuel_status']))['claims'])
  self.assertFalse(expected_selection(context_for('D06','A2',20,'current',['fuel_status']))['claims'])
 def test_invalid_identity_supersession(self):
  data=load_scenario('D03');data['events'][1]['flightInstance']='F1-R1'
  with self.assertRaises(ValueError):validate_scenario(data)
 def test_bad_context(self):
  for sid,a,t in [('bad','A2',14),(S,'bad',14),(S,'A2',float('nan')),(S,'A2',61)]:
   with self.assertRaises(ValueError):context_for(sid,a,t)
 def test_http_auth_and_types(self):
  buf=io.BytesIO();Image.new('RGB',(32,32),'white').save(buf,format='PNG')
  body=dict(requestId='test',scenarioId=S,aircraftId='A2',checkpoint=14,imageBase64=base64.b64encode(buf.getvalue()).decode())
  with tempfile.TemporaryDirectory() as tmp,patch('backend.server.AUDIT_PATH',Path(tmp)/'audit.jsonl'):
   with TestClient(create_app(FakeEngine(),'test-token')) as client:
    headers={'Authorization':'Bearer test-token'}
    self.assertEqual(client.post('/reason',json=body).status_code,401)
    r=client.post('/reason',json=body,headers=headers);self.assertEqual(r.status_code,200,r.text)
    self.assertEqual(r.json()['resultStatus'],'generated');self.assertEqual(r.json()['evidenceIds'],['E03'])
    self.assertEqual(r.json()['decisionVersion'],'pairwise-predicates-v5')
    self.assertFalse(r.json()['imageUsedForInference'])
    for change in ({'checkpoint':61},{'imageBase64':'bad'},{'queryType':'freeform'},{'properties':['unknown_field']},{'events':[]}):
     self.assertEqual(client.post('/reason',json=dict(body,**change),headers=headers).status_code,422)
if __name__=='__main__':unittest.main()
