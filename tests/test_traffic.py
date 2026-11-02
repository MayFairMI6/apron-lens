"""External exercise timing, evidence consistency and authentication, without a model load."""
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.evidence import validate_scenario, received_facts
from backend.traffic import PROFILES, ROLES, DURATION, TrafficDriver, make_scenario, traffic_app
from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter

class TrafficTests(unittest.TestCase):
    def test_all_profiles_produce_valid_evidence_and_ordered_routes(self):
        for profile in PROFILES:
            for seed in (1,42,987):
                data,slots=make_scenario(seed,profile)
                validate_scenario(data)
                for a in data['aircraft']:
                    times=[w['t'] for w in a['waypoints']]
                    self.assertEqual(times,sorted(set(times)))
                    self.assertEqual(times[-1],DURATION)
                self.assertTrue(all(e['eventTime']<=e['receiptTime']<=DURATION for e in data['events']))
                self.assertTrue(all(a['end']<b['start'] for a,b in zip(slots,slots[1:])))
                self.assertTrue(all(4<=slot['speedMetresPerSecond']<=6 for slot in slots))
                for slot in slots:
                    event=next(e for e in data['events'] if e['aircraftId']==slot['aircraftId'] and e['facts'][0]['value']=='taxiing' and abs(e['eventTime']-slot['taxiStart'])<.001)
                    self.assertGreater(event['eventTime'],slot['start']+32.5)
    def test_every_role_and_exercise_has_valid_identity_and_evidence(self):
        for role in ROLES:
            for exercise in PROFILES:
                data,_=make_scenario(42,exercise,role=role)
                validate_scenario(data)
                self.assertEqual(data['trainingRole'],role)
                self.assertEqual(len(data['assistantQuestions']),2)
                self.assertTrue(data['trainingObjective'])
    def test_controller_default_focuses_on_traffic_not_service_completion(self):
        d=TrafficDriver(7)
        self.assertEqual(d.exercise,'surface_conflict')
        self.assertEqual(d.role,'controller_awareness')
        props={f['property'] for e in d.scenario['events'] for f in e['facts']}
        self.assertNotIn('fuel_status',props);self.assertNotIn('baggage_status',props)
        self.assertTrue({'route','movement_status','movement_condition'}<=props)
        self.assertEqual(d.scenario['assistantQuestionLabels'],['Traffic update','Reported hold'])
    def test_pilot_default_has_its_own_briefing_and_session_identity(self):
        pilot=TrafficDriver(7,role='pilot_awareness')
        controller=TrafficDriver(7,exercise=pilot.exercise)
        self.assertEqual(pilot.exercise,'late_departure')
        self.assertIn('Pilot',pilot.snapshot()['exerciseTitle'])
        self.assertEqual(pilot.scenario['assistantQuestionLabels'][0],'Route briefing')
        self.assertNotEqual(pilot.scenario['scenarioId'],controller.scenario['scenarioId'])

    def test_seed_reproducibility_and_variation(self):
        self.assertEqual(make_scenario(10),make_scenario(10))
        self.assertNotEqual(make_scenario(10)[1],make_scenario(11)[1])
    def test_driver_advances_without_client_play_and_caps_at_end(self):
        now=[100.0];d=TrafficDriver(7,'late_baggage',clock=lambda:now[0])
        now[0]+=12.5;self.assertEqual(d.snapshot()['serverTime'],12.5)
        now[0]+=5000;self.assertEqual(d.snapshot()['serverTime'],3600)
    def test_conflict_then_explicit_correction(self):
        data,_=make_scenario(7,'conflicting_stand')
        stands=[e for e in data['events'] if e['aircraftId']=='A2' and e['facts'][0]['property']=='stand']
        self.assertNotIn('supersedes',stands[1]['facts'][0])
        self.assertEqual(set(stands[-1]['facts'][0]['supersedes']),{e['id']+':stand' for e in stands[:-1]})
        self.assertNotIn(stands[-1]['id'],[f['event_id'] for f in received_facts(data,17)])
    def test_authenticated_snapshot_and_same_conversation_scenario(self):
        d=TrafficDriver(7,'late_baggage')
        with tempfile.TemporaryDirectory() as folder:
            app=traffic_app(MockAdapter([]),Settings('mock-model',256,image_max_side=672),d,Path(folder)/'audit.jsonl')
            with TestClient(app) as client:
                self.assertEqual(client.get('/traffic').status_code,401)
                response=client.get('/traffic',headers={'Authorization':'Bearer '+app.state.token})
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json()['scenario'],app.state.scenarios[d.scenario['scenarioId']])

if __name__=='__main__':unittest.main()
