"""experiments/answer_methods: tower rules, strict query reader, keyword baseline, sandbox and pipeline."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from backend.evidence import build_context,expected_selection
from experiments.answer_methods import evaluate
from experiments.answer_methods.direct import read_answer
from experiments.answer_methods.pal import run_code
from experiments.answer_methods.parser import keyword_parse,read_program
from experiments.answer_methods.scenarios import TOWER_ID,load
def ctx(aircraft,t,kind,props):return build_context(load(TOWER_ID),aircraft,t,kind,props)
def claims(c):return {(x['fact_id'],x['status']) for x in expected_selection(c)['claims']}
def unknown(c):return expected_selection(c)['unknown_properties']

class TowerScenarioTests(unittest.TestCase):
 def test_amended_taxi_clearance_replaces_original(self):
  self.assertEqual(claims(ctx('A1',5,'current',['taxi_clearance'])),{('T01:taxi_clearance','current')})
  self.assertEqual(claims(ctx('A1',12,'current',['taxi_clearance'])),{('T03:taxi_clearance','current')})
  self.assertIn(('T01:taxi_clearance','superseded'),claims(ctx('A1',12,'change',['taxi_clearance'])))
 def test_late_reports_appear_only_on_arrival(self):
  self.assertEqual(unknown(ctx('A1',18,'current',['readback'])),['readback'])
  self.assertEqual(claims(ctx('A1',19,'current',['readback'])),{('T04:readback','current')})
  self.assertEqual(unknown(ctx('A1',49,'current',['takeoff_clearance'])),['takeoff_clearance'])
  self.assertEqual(claims(ctx('A1',50,'current',['takeoff_clearance'])),{('T08:takeoff_clearance','current')})
 def test_wrong_aircraft_readback_is_flagged_not_borrowed(self):
  # EZY123 read back EZY132's clearance: two different readbacks conflict, and EZY132 never gets one.
  self.assertEqual(unknown(ctx('A1',23,'current',['readback'])),['readback'])
  self.assertEqual(claims(ctx('A1',23,'change',['readback'])),{('T04:readback','conflicting'),('T06:readback','conflicting')})
  self.assertEqual(unknown(ctx('A2',60,'current',['readback'])),['readback'])

class ReaderTests(unittest.TestCase):
 def test_query_reader_accepts_grammar_only(self):
  self.assertEqual(read_program('current(baggage_status)')[0],{'queryType':'current','properties':['baggage_status']})
  self.assertEqual(read_program('`change(stand, route)`')[0]['properties'],['route','stand'])
  self.assertEqual(read_program('latest()')[0],{'queryType':'latest','properties':[]})
  for text,why in (('rm -rf /','not_in_grammar'),('current()','missing_topic'),('latest(stand, route)','latest_takes_one_topic'),
                   ('current(taxi_clearance)','unknown_topic'),('change(stand, stand)','repeated_topic'),('','not_in_grammar')):
   self.assertEqual(read_program(text),(None,why),text)
  self.assertEqual(read_program('current(taxi_clearance)','tower')[0]['properties'],['taxi_clearance'])
 def test_answer_reader_and_keywords(self):
  self.assertEqual(read_answer('{"fact_ids":["b","a","a"]}'),({'fact_ids':['a','b'],'unknown':[]},None))
  self.assertEqual(read_answer('not json')[1],'not_json');self.assertEqual(read_answer('[1]')[1],'wrong_shape')
  self.assertEqual({k:v for k,v in keyword_parse('Is it cleared to line up and take off?','tower').items() if k!='version'},
                   {'queryType':'current','properties':['lineup_clearance','takeoff_clearance']})

class SandboxTests(unittest.TestCase):
 def test_hostile_code_is_rejected_and_good_code_runs(self):
  d=load('M1-stand-coordination-01')
  for code,why in (('import os','forbidden_statement'),('open("/etc/passwd")','forbidden_name'),('x=().__class__','forbidden_attribute'),
                   ('getattr(len,"x")','forbidden_name'),('while True:\n    pass','runtime_error'),('answer = {','syntax_error')):
   self.assertEqual(run_code(code,d,'A2',20),(None,why),code)
  good='mine=[r for r in reports if r["flight"]==flight]\nlast=max(r["arrived"] for r in mine)\nanswer={"fact_ids":[r["fact_id"] for r in mine if r["arrived"]==last],"unknown":[]}'
  self.assertEqual(run_code(good,d,'A2',20),({'fact_ids':['E06:movement_status'],'unknown':[]},None))

class FakeEngine:
 manifest={'model_id':'test-double','revision':'test-only'};device='test'
 def score_labels(self,prompt,image,labels):
  if labels==('A','B','C'):return {'A':-3.,'B':-.1,'C':-3.},50
  return {l:(-.1 if l=='B' else -5.) for l in labels},40
 def generate(self,prompt,image):
  if prompt.endswith('Query:'):return 'current(baggage_status)',60,6
  if 'Write Python' in prompt:return '```python\nanswer={"fact_ids":["E03:baggage_status"],"unknown":[]}\n```',300,20
  return '```json\n{"fact_ids":["E03:baggage_status"],"unknown":[]}\n```',300,20
class PipelineTests(unittest.TestCase):
 def test_five_methods_scored_on_answers(self):
  runtime=dict(device='cpu',dtype='float16',attn_implementation='eager')
  with tempfile.TemporaryDirectory() as tmp,patch.object(evaluate,'load_engine',return_value=FakeEngine()),patch('builtins.print'):
   evaluate.run('apron','dev','qwen2.5-vl-3b',tmp,runtime)
   summary=json.loads(Path(tmp,'summary.json').read_text())
   rows=[json.loads(l) for l in Path(tmp,'results.jsonl').read_text().splitlines()]
  qd07=next(r for r in rows if r['id']=='QD07')  # "Is the baggage done?" -> current baggage_status
  self.assertEqual(qd07['answers']['gold'],{'fact_ids':['E03:baggage_status'],'unknown':[]})
  for k in ('direct','pal','choice','generated'):self.assertEqual(qd07['answers'][k],qd07['answers']['gold'],k)
  self.assertEqual(set(summary['answerScore']),{'direct','pal','choice','generated','keyword'})
  self.assertEqual(summary['answerScore']['keyword']['exact'],36)  # keyword rules were written on dev
  self.assertEqual(summary['runtime'],runtime)
 def test_frozen_datasets_match_their_hashes(self):
  for name in ('apron','tower'):
   for split in ('dev','test'):evaluate.load(name,split)
if __name__=='__main__':unittest.main()
