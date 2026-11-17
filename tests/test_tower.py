"""Tower scenario and query-program contract: same evidence rules, tower vocabulary."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.evidence import expected_selection
from backend.reasoning import context_for
from backend.query_parser import TOPICS,keyword_parse,parse,read_program
from backend.server import create_app
T='T1-tower-clearances-01'
def claims(c):return {(x['fact_id'],x['status']) for x in expected_selection(c)['claims']}

class TowerScenarioTests(unittest.TestCase):
 def test_amended_taxi_clearance_replaces_original(self):
  self.assertEqual(claims(context_for(T,'A1',5,'current',['taxi_clearance'])),{('T01:taxi_clearance','current')})
  self.assertEqual(claims(context_for(T,'A1',12,'current',['taxi_clearance'])),{('T03:taxi_clearance','current')})
  self.assertIn(('T01:taxi_clearance','superseded'),claims(context_for(T,'A1',12,'change',['taxi_clearance'])))
 def test_late_readback_and_takeoff_appear_only_on_arrival(self):
  self.assertEqual(expected_selection(context_for(T,'A1',18,'current',['readback']))['unknown_properties'],['readback'])
  self.assertEqual(claims(context_for(T,'A1',19,'current',['readback'])),{('T04:readback','current')})
  self.assertEqual(expected_selection(context_for(T,'A1',49,'current',['takeoff_clearance']))['unknown_properties'],['takeoff_clearance'])
  self.assertEqual(claims(context_for(T,'A1',50,'current',['takeoff_clearance'])),{('T08:takeoff_clearance','current')})
 def test_wrong_aircraft_readback_is_flagged_not_borrowed(self):
  # EZY123 read back EZY132's clearance: two different readbacks conflict, so there is no current value,
  # and EZY132 (the similar call sign) never gets a readback from it.
  self.assertEqual(expected_selection(context_for(T,'A1',23,'current',['readback']))['unknown_properties'],['readback'])
  self.assertEqual(claims(context_for(T,'A1',23,'change',['readback'])),{('T04:readback','conflicting'),('T06:readback','conflicting')})
  self.assertEqual(expected_selection(context_for(T,'A2',60,'current',['readback']))['unknown_properties'],['readback'])
 def test_tower_topics_are_valid_fields(self):
  for domain,topics in TOPICS.items():context_for(T,'A1',30,'current',list(topics)[:2])

class ProgramTests(unittest.TestCase):
 def test_reader_accepts_grammar_only(self):
  self.assertEqual(read_program('current(baggage_status)')[0],{'queryType':'current','properties':['baggage_status']})
  self.assertEqual(read_program('`change(stand, route)`')[0]['properties'],['route','stand'])
  self.assertEqual(read_program('latest()')[0],{'queryType':'latest','properties':[]})
  for text,why in (('rm -rf /','not_in_grammar'),('current()','missing_topic'),('latest(stand, route)','latest_takes_one_topic'),
                   ('current(taxi_clearance)','unknown_topic'),('change(stand, stand)','repeated_topic'),('','not_in_grammar')):
   self.assertEqual(read_program(text),(None,why),text)
  self.assertEqual(read_program('current(taxi_clearance)','tower')[0]['properties'],['taxi_clearance'])
 def test_tower_keyword_baseline(self):
  self.assertEqual({k:v for k,v in keyword_parse('Is it cleared to line up and take off?','tower').items() if k!='version'},
                   {'queryType':'current','properties':['lineup_clearance','takeoff_clearance']})

class TowerEngine:
 manifest={'model_id':'test-double','revision':'test-only'};device='test'
 def __init__(self):self.prompts=[]
 def score_labels(self,prompt,image,labels):
  self.prompts.append(prompt)
  if labels==('A','B','C'):return {'A':-3.,'B':-.1,'C':-3.},50
  return {l:(-.1 if l=='A' else -5.) for l in labels},40  # A = taxi_clearance in the tower list
class TowerServiceTests(unittest.TestCase):
 def test_service_parses_with_tower_topics(self):
  engine=TowerEngine()
  with tempfile.TemporaryDirectory() as tmp,patch('backend.server.AUDIT_PATH',Path(tmp)/'audit.jsonl'):
   with TestClient(create_app(engine,'t')) as client:
    r=client.post('/reason',json=dict(requestId='t',scenarioId=T,aircraftId='A1',checkpoint=12,question='What taxi route now?'),
                  headers={'Authorization':'Bearer t'}).json()
  self.assertEqual((r['queryType'],r['properties'],r['evidenceIds']),('current',['taxi_clearance'],['T03']))
  self.assertIn('taxi clearance',engine.prompts[1])
class SandboxTests(unittest.TestCase):
 def test_hostile_code_is_rejected(self):
  from backend.evidence import load_scenario
  from backend.program_answer import run_code
  d=load_scenario('M1-stand-coordination-01')
  for code,why in (('import os','forbidden_statement'),('open("/etc/passwd")','forbidden_name'),('x=().__class__','forbidden_attribute'),
                   ('getattr(len,"x")','forbidden_name'),('while True:\n    pass','runtime_error'),('answer = {','syntax_error')):
   self.assertEqual(run_code(code,d,'A2',20),(None,why),code)
  good='mine=[r for r in reports if r["flight"]==flight]\nlast=max(r["arrived"] for r in mine)\nanswer={"fact_ids":[r["fact_id"] for r in mine if r["arrived"]==last],"unknown":[]}'
  self.assertEqual(run_code(good,d,'A2',20),({'fact_ids':['E06:movement_status'],'unknown':[]},None))

class FakeAll:
 manifest={'model_id':'test-double','revision':'test-only'};device='test';dtype='test'
 def score_labels(self,prompt,image,labels):
  if labels==('A','B','C'):return {'A':-3.,'B':-.1,'C':-3.},50
  return {l:(-.1 if l=='B' else -5.) for l in labels},40
 def generate(self,prompt,image):
  if prompt.endswith('Query:'):return 'current(baggage_status)',60,6
  if 'Write Python' in prompt:return '```python\nanswer={"fact_ids":["E03:baggage_status"],"unknown":[]}\n```',300,20
  return '```json\n{"fact_ids":["E03:baggage_status"],"unknown":[]}\n```',300,20
class EvaluationPipelineTests(unittest.TestCase):
 def test_four_methods_scored_on_answers(self):
  import json
  from backend.direct_answer import read_answer
  self.assertEqual(read_answer('{"fact_ids":["b","a","a"]}'),({'fact_ids':['a','b'],'unknown':[]},None))
  self.assertEqual(read_answer('not json')[1],'not_json');self.assertEqual(read_answer('[1]')[1],'wrong_shape')
  import runpy
  module=runpy.run_path('scripts/evaluate_query_parsing.py')
  with tempfile.TemporaryDirectory() as tmp,patch('backend.engine.load_engine',return_value=FakeAll()):
   module['run']('apron','dev','qwen2.5-vl-3b',tmp)
   summary=json.loads(Path(tmp,'summary.json').read_text())
   rows=[json.loads(l) for l in Path(tmp,'results.jsonl').read_text().splitlines()]
  qd07=next(r for r in rows if r['id']=='QD07')  # "Is the baggage done?" -> current baggage_status
  self.assertEqual(qd07['answers']['gold'],{'fact_ids':['E03:baggage_status'],'unknown':[]})
  for k in ('direct','pal','choice','generated'):self.assertEqual(qd07['answers'][k],qd07['answers']['gold'],k)
  self.assertEqual(set(summary['answerScore']),{'direct','pal','choice','generated','keyword'})
  self.assertEqual(summary['answerScore']['keyword']['exact'],36)  # keyword rules were written on dev
if __name__=='__main__':unittest.main()
