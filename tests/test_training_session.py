"""External time, causal assessment, live service guards and 60 seeded worlds."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.lessons import build_lesson, EXERCISES
from backend.training_session import TrainingSession, ActionConflict
from backend.training import training_app
from backend.evidence import validate_scenario, received_facts
from evidencekit import SourceRecord, check_references
from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter

class TrainingTests(unittest.TestCase):
    def session(self,exercise='surface_conflict',mode='lesson',seed=17):
        now=[0.];return TrainingSession(seed,exercise,mode,clock=lambda:now[0]),now
    def act(self,s,action,**kw):
        return s.action(dict(actionId=str(len(s.actions))+'-'+action,runId=s.run_id,revision=s.revision,action=action,**kw))

    def test_sixty_worlds_replayable_reserved_and_causal(self):
        for exercise in EXERCISES:
            for seed in range(20):
                world,slots,probes=build_lesson(seed,exercise)
                self.assertEqual((world,slots,probes),build_lesson(seed,exercise))
                validate_scenario(world)
                for a in world['aircraft']:
                    times=[p['t'] for p in a['waypoints']]
                    self.assertEqual(times,sorted(set(times)));self.assertEqual(times[-1],3600)
                self.assertTrue(all(a['end']<b['start'] for a,b in zip(slots,slots[1:])))
                for p in probes:
                    known={f['event_id'] for f in received_facts(world,p['at'])}
                    self.assertTrue(set(p['evidenceIds'])<=known)
                    self.assertEqual(len(p['choices']),4)

    def test_late_arrival_waits_for_physical_stand_and_received_release(self):
        world,slots,_=build_lesson(17,'late_arrival')
        outbound,inbound=slots[:2]
        self.assertEqual((outbound['aircraftId'],inbound['aircraftId']),('A2','A3'))
        self.assertLess(outbound['end'],inbound['start'])
        release=next(e for e in world['events'] if e['facts'][0]['value']=='Stand B available; exercise ground hold released')
        self.assertLess(release['receiptTime'],inbound['start'])
        a3=world['aircraft'][2]
        self.assertEqual(a3['waypoints'][0]['x'],.24)
        self.assertTrue(any(p['x']==.035 and p['z']==.04 for p in a3['waypoints']))

    def test_lesson_freezes_answers_once_and_debriefs_all_three(self):
        for exercise in EXERCISES:
            for seed in range(20):
                s,now=self.session(exercise,seed=seed);now[0]=100
                self.assertEqual(s.state()['sourceTime'],0)
                self.act(s,'ready')
                for i,p in enumerate(s.probes):
                    now[0]+=80;state=s.state()
                    self.assertEqual(state['sourceTime'],p['at']);self.assertEqual(state['phase'],'checkpoint')
                    self.assertNotIn('correct',state['checkpoint']);self.assertFalse(state['reviews'])
                    body=dict(actionId='answer'+str(i),runId=s.run_id,revision=s.revision,action='answer',checkpointId=p['id'],choice=p['correct'])
                    result=s.action(body);self.assertEqual(s.action(body),result)
                    changed=dict(body,choice=(p['correct']+1)%4)
                    with self.assertRaises(ActionConflict):s.action(changed)
                    self.assertTrue(result['feedback']['correct']);now[0]+=100
                    self.assertEqual(s.state()['sourceTime'],p['at'])
                    self.act(s,'continue')
                now[0]+=100;state=s.state()
                self.assertEqual((state['phase'],state['score'],len(state['reviews'])),('debrief',3,3))
                self.assertEqual(state['sourceTime'],210)

    def test_stale_actions_future_cutoffs_and_checkpoint_questions_rejected(self):
        s,now=self.session()
        with self.assertRaises(ActionConflict):s.begin_question(dict(scenarioId=s.scenario['scenarioId'],checkpoint=0))
        self.act(s,'ready')
        with self.assertRaises(ValueError):s.begin_question(dict(scenarioId=s.scenario['scenarioId'],checkpoint=2))
        with self.assertRaises(ActionConflict):s.action(dict(runId='old',actionId='1',revision=0,action='ready'))
        now[0]=61;s.state()
        with self.assertRaises(ActionConflict):s.begin_question(dict(scenarioId=s.scenario['scenarioId'],checkpoint=60))

    def test_demo_piecewise_integration_independent_of_poll_frequency(self):
        coarse,cn=self.session(mode='demo');fine,fn=self.session(mode='demo')
        for end in (1,2,15,45,100,180,300,500,700,900,1100,1400):
            while fn[0]<end:
                fn[0]=min(end,fn[0]+.1);fine.snapshot()
            cn[0]=end;coarse.snapshot()
            self.assertAlmostEqual(coarse.source_time,fine.source_time,places=5)
            self.assertEqual(coarse.phase,fine.phase)
        self.assertEqual(coarse.source_time,3600)

    def test_demo_slows_for_real_question_and_reading(self):
        s,now=self.session(mode='demo')
        now[0]=2;self.assertAlmostEqual(s.state()['sourceTime'],50+1/3)
        body=dict(scenarioId=s.scenario['scenarioId'],checkpoint=50,requestId='q1')
        ctx=s.begin_question(body)
        now[0]+=12;self.assertEqual(s.state()['rate'],1)
        self.assertTrue(s.end_question(body,ctx,True))
        now[0]+=9;self.assertEqual(s.state()['rate'],1)

    def test_demo_failure_is_recorded_and_gets_reading_time(self):
        s,now=self.session(mode='demo');now[0]=12
        state=s.state();self.assertEqual(state['demoCue']['status'],'pending')
        self.act(s,'demo_answer',cueId=state['demoCue']['id'],success=False)
        self.assertEqual(s.state()['demoCue']['status'],'failed')
        now[0]+=9;self.assertEqual(s.state()['rate'],1)

    def test_modes_share_identical_world_and_evidence_at_source_time(self):
        normal,n=self.session(mode='continuous');fast,f=self.session(mode='demo')
        a=copy.deepcopy(normal.scenario);b=copy.deepcopy(fast.scenario)
        a.pop('scenarioId');b.pop('scenarioId');self.assertEqual(a,b)
        for t in (24,60,104,120,180,210,900,1450,1550,2000,2100,2200,3599):
            self.assertEqual(received_facts(a,t),received_facts(b,t))

    def test_prediction_boundary_and_versioned_available_sources(self):
        s,now=self.session(mode='continuous');now[0]=24
        snap=s.snapshot()
        self.assertLessEqual(snap['clock']['nextBoundary'],28)
        self.assertTrue(all(r['version']==1 and r['kind']=='report' and r['available_time']<=24
                            and r['episode_id']==s.scenario['scenarioId'] for r in snap['sourceRecords']))
        self.assertNotIn('L010',{r['source_id'] for r in snap['sourceRecords']})

    def test_source_guard_rejects_future_other_episode_and_invalid_times(self):
        records=[SourceRecord('one','r1',1,5,'report'),SourceRecord('two','r2',1,2,'observation')]
        for refs in (['r1'],['r2']):
            with self.assertRaises(ValueError):check_references(refs,records,'one',3)
        self.assertEqual(check_references(['r1'],records,'one',5)[0],records[0])
        with self.assertRaises(ValueError):SourceRecord('one','r3',10,2,'report')

    def test_authenticated_service_and_phase_guard(self):
        s,now=self.session()
        with tempfile.TemporaryDirectory() as folder:
            app=training_app(MockAdapter([]),Settings('mock-model',256,image_max_side=672),s,token='test-token',audit_path=Path(folder)/'calls.jsonl')
            with TestClient(app) as c:
                headers={'Authorization':'Bearer test-token'}
                self.assertEqual(c.get('/training').status_code,401)
                snap=c.get('/traffic',headers=headers).json()
                self.assertEqual(snap['clock']['rate'],0)
                answer=c.post('/conversation',headers=headers,json=dict(scenarioId=s.scenario['scenarioId'],checkpoint=0))
                self.assertEqual(answer.status_code,409)
                action=dict(action='ready',runId=s.run_id,revision=s.revision,actionId='ready')
                self.assertEqual(c.post('/training/action',headers=headers,json=action).json()['phase'],'practice')
                now[0]=61;state=c.get('/training',headers=headers).json()
                self.assertEqual(state['phase'],'checkpoint');self.assertNotIn('correct',state['checkpoint'])

    def test_full_conversation_route_uses_the_training_world(self):
        s,now=self.session();self.act(s,'ready');now[0]=5
        stand=next(e for e in s.scenario['events'] if e['aircraftId']=='A2' and e['facts'][0]['property']=='stand')
        proposal=dict(status='answer',referent=dict(aircraftId='A2',flightInstance='TRN102'),
            claims=[dict(fact_id=stand['id']+':stand',value='B',status='current',evidence_ids=[stand['id']])],
            unknowns=[],explanationChanged=None,changesNotDiscussed=[],memoryUpdate=None,rationale='',observations=[])
        with tempfile.TemporaryDirectory() as folder:
            adapter=MockAdapter([json.dumps(proposal)])
            app=training_app(adapter,Settings('mock-model',256,image_max_side=672),s,token='test-token',audit_path=Path(folder)/'calls.jsonl')
            with TestClient(app) as c:
                body=dict(requestId='question',turnId='turn',sessionId='session',scenarioId=s.scenario['scenarioId'],
                    aircraftId='A2',flightInstance='TRN102',checkpoint=5,expectedRevision=0,question='Which stand?')
                response=c.post('/conversation',headers={'Authorization':'Bearer test-token'},json=body)
                self.assertEqual(response.status_code,200,response.text);self.assertTrue(response.json()['accepted'])
                self.assertFalse(s.assistant_pending)

    def test_old_response_context_and_retry_transition(self):
        s,now=self.session();self.act(s,'ready')
        body=dict(scenarioId=s.scenario['scenarioId'],checkpoint=0,requestId='pending')
        ctx=s.begin_question(body);now[0]=65;s.state()
        self.assertFalse(s.end_question(body,ctx,True))
        for p in s.probes:
            self.act(s,'answer',checkpointId=p['id'],choice=p['correct']);self.act(s,'continue')
            now[0]+=70;s.state()
        action=dict(runId=s.run_id,revision=s.revision,actionId='retry-id',action='retry')
        result=s.action(action)
        self.assertEqual(s.action(action),result)
        self.assertEqual(s.run_id,result['runId'])

if __name__=='__main__':unittest.main()
