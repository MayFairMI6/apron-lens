import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.traffic import make_scenario
from backend.role_demo import RoleView,ROLE_PORTS,world_hash,demo_app,START_TIME
from backend.evidence import validate_scenario
from modelaccess.mock import MockAdapter
from modelaccess.contract import Settings

class SharedRoleTests(unittest.TestCase):
    def test_roles_share_identical_world_and_independent_presentation(self):
        canonical,slots=make_scenario(1,'surface_conflict',role='ramp')
        views=[RoleView(canonical,slots,r) for r in ROLE_PORTS]
        for v in views:
            validate_scenario(v.scenario)
            self.assertEqual(world_hash(v.scenario),world_hash(canonical))
            self.assertEqual(v.scenario['trainingRole'],v.role)
        self.assertEqual(len({v.scenario['scenarioId'] for v in views}),3)
        self.assertEqual(len({v.scenario['assistantQuestions'][0] for v in views}),3)
    def test_reset_is_authenticated_changes_context_and_preserves_world(self):
        now=[100.];canonical,slots=make_scenario(1,'surface_conflict',role='ramp')
        v=RoleView(canonical,slots,'controller_awareness',clock=lambda:now[0])
        with tempfile.TemporaryDirectory() as folder,patch('backend.role_demo.ROOT',Path(folder)):
            app=demo_app(MockAdapter([]),Settings('mock-model',256,image_max_side=672),v)
            with TestClient(app) as client:
                self.assertEqual(client.post('/demo/reset').status_code,401)
                old=v.scenario['scenarioId'];now[0]+=20
                result=client.post('/demo/reset',headers={'Authorization':'Bearer '+app.state.token})
                self.assertEqual(result.status_code,200)
                self.assertNotEqual(old,v.scenario['scenarioId'])
                self.assertEqual(v.snapshot()['serverTime'],START_TIME)
                self.assertEqual(app.state.scenarios[v.scenario['scenarioId']],v.scenario)
                self.assertEqual(world_hash(v.scenario),world_hash(canonical))
