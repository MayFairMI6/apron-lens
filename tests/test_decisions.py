"""Contract tests: no baseline leakage or silent repair of model decisions."""
import json,unittest
from unittest.mock import patch
from backend.decisions import select_claims
from backend.evidence import build_context
from backend.reasoning import validate_answer

class Scores:
 def __init__(self,values):self.values=iter(values)
 def score_labels(self,prompt,image,labels):
  yes=next(self.values)
  return {'Yes':-.1 if yes else -6.,'No':-6. if yes else -.1},12

def context(events,query='current',properties=None):
 data={'scenarioId':'unit','duration':100,'aircraft':[{'id':'A','flightInstance':'F'}],'events':events}
 return build_context(data,'A',30,query,properties or ['route'])

def event(eid,value,supersedes=()):
 return {'id':eid,'aircraftId':'A','flightInstance':'F','source':'unit',
 'eventTime':1 if eid=='old' else 2,'receiptTime':1 if eid=='old' else 2,
 'facts':[{'property':'route','value':value,'supersedes':list(supersedes)}]}

class DecisionContractTests(unittest.TestCase):
 def test_empty_evidence_is_structural_unknown_no_model_or_baseline(self):
  with patch('backend.evidence.expected_selection',side_effect=AssertionError('baseline leak')):
   raw,trace=select_claims(Scores([]),context([]))
  self.assertEqual(json.loads(raw),{'claims':[],'unknown_properties':['route']})
  self.assertEqual(trace['forwardPasses'],0)
 def test_wrong_model_decision_is_retained_and_withheld_not_repaired(self):
  c=context([event('old','east'),event('new','west',['old:route'])])
  # Deliberately select superseded as current, reject the real current record.
  with patch('backend.evidence.expected_selection',side_effect=AssertionError('baseline leak')):
   raw,_=select_claims(Scores([True,True,False,True]),c)
  parsed=json.loads(raw)
  self.assertEqual(parsed['claims'][0]['fact_id'],'old:route')
  self.assertEqual(parsed['claims'][0]['status'],'superseded')
  self.assertEqual(validate_answer(raw,c)['resultStatus'],'withheld')
 def test_history_retains_superseded_and_source_without_asking_generator(self):
  c=context([event('old','east'),event('new','west',['old:route'])],'change')
  raw,_=select_claims(Scores([True,False,True,True]),c)
  parsed=json.loads(raw)
  self.assertEqual([r['fact_id'] for r in parsed['claims']],['old:route','new:route'])
  self.assertEqual(parsed['claims'][0]['evidence_ids'],['old'])
  self.assertEqual(parsed['unknown_properties'],[])
 def test_missing_flag_and_claim_share_the_same_model_decision(self):
  raw,_=select_claims(Scores([True,False]),context([event('old','east')]))
  self.assertEqual(json.loads(raw),{'claims':[],'unknown_properties':['route']})

if __name__=='__main__':unittest.main()
