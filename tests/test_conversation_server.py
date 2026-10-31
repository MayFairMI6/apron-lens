"""/conversation endpoint with a scripted model: no network, weights or paid calls."""
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter
from backend.conversation.server import create_app, load_scenarios
from test_conversation import claim, two_rotation_scenario

TOKEN = 'test-token'
AUTH = {'Authorization': 'Bearer ' + TOKEN}


def reply(**overrides):
    base = dict(status='answer', referent={'aircraftId': 'A2', 'flightInstance': 'F2-R1'}, claims=[],
                unknowns=[], explanationChanged=None, changesNotDiscussed=[], memoryUpdate=None,
                rationale='', observations=[])
    base.update(overrides)
    return json.dumps(base)


def png():
    stream = io.BytesIO()
    Image.new('RGB', (8, 8), (40, 60, 80)).save(stream, format='PNG')
    return base64.b64encode(stream.getvalue()).decode()


class Endpoint(unittest.TestCase):
    def serve(self, replies, scenarios=None):
        self.adapter = MockAdapter(replies)
        self.audit = Path(tempfile.mkdtemp()) / 'audit.jsonl'
        data = scenarios or {'conv-test': two_rotation_scenario()}
        client = TestClient(create_app(self.adapter, Settings('mock-model', 256, image_max_side=672),
                                       token=TOKEN, scenarios=data, audit_path=self.audit))
        self.addCleanup(client.__exit__, None, None, None)
        return client.__enter__()

    def ask(self, client, n, revision, checkpoint=25, aircraft='A2', flight='F2-R1', session='s1', **extra):
        body = dict(requestId=f'r{n}', turnId=f't{n}', sessionId=session, scenarioId='conv-test',
                    aircraftId=aircraft, flightInstance=flight, checkpoint=checkpoint,
                    expectedRevision=revision, question='Which stand is this one on?')
        body.update(extra)
        return client.post('/conversation', headers=AUTH, json=body)

    def prompt(self, index=-1):
        return self.adapter.calls[index][0].messages[0][1]

    def test_requires_token(self):
        client = self.serve([])
        self.assertEqual(client.get('/health').status_code, 401)
        self.assertEqual(client.post('/conversation', json={}).status_code, 401)

    def test_accepted_answer_is_rendered_and_audited_without_image_bytes(self):
        client = self.serve([reply(claims=[claim('E01:stand', 'B', 'current', 'E01')], rationale='From E01.')])
        result = self.ask(client, 1, 0, imageBase64=png(), imageCaptureTime=24).json()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['revision'], 1)
        self.assertIn('[E01]', result['display']['answer'])
        self.assertTrue(result['imageUsedForInference'])
        self.assertNotIn('prompt', result)
        audit = json.loads(self.audit.read_text())
        self.assertIn('Candidate flights', audit['prompt'])
        self.assertEqual(len(audit['imageSha256']), 64)
        self.assertNotIn(png(), self.audit.read_text())

    def test_retry_returns_stored_result_without_second_model_call(self):
        client = self.serve([reply(claims=[claim('E01:stand', 'B', 'current', 'E01')])])
        first = self.ask(client, 1, 0).json()
        again = self.ask(client, 1, 0).json()
        self.assertEqual(first, again)
        self.assertEqual(len(self.adapter.calls), 1)
        self.assertEqual(self.ask(client, 1, 0, turnId='other').status_code, 409)

    def test_stale_revision_is_refused_before_the_model_is_called(self):
        client = self.serve([reply()])
        self.assertEqual(self.ask(client, 1, 3).status_code, 409)
        self.assertEqual(self.adapter.calls, [])

    def test_prompt_holds_only_receipt_eligible_facts(self):
        client = self.serve([reply(), reply()])
        self.ask(client, 1, 0, checkpoint=25)
        self.assertNotIn('E03', self.prompt())
        self.ask(client, 2, 1, checkpoint=30)
        self.assertIn('E03', self.prompt())

    def test_correction_to_next_rotation_persists_while_the_aircraft_stays_selected(self):
        client = self.serve([
            reply(claims=[claim('E01:stand', 'B', 'current', 'E01')]),
            reply(referent={'aircraftId': 'A2', 'flightInstance': 'F2-R2'},
                  claims=[claim('E02:stand', 'C', 'current', 'E02')],
                  memoryUpdate={'kind': 'correction', 'aircraftId': 'A2', 'flightInstance': 'F2-R2'}),
            reply(referent={'aircraftId': 'A2', 'flightInstance': 'F2-R2'})])
        self.ask(client, 1, 0, checkpoint=25)
        second = self.ask(client, 2, 1, checkpoint=25, question='I mean its next rotation.').json()
        self.assertTrue(second['accepted'], second['errors'])
        self.assertEqual(second['currentReferent'], {'aircraftId': 'A2', 'flightInstance': 'F2-R2'})
        third = self.ask(client, 3, 2, checkpoint=26).json()  # the app still sends A2 / F2-R1
        self.assertEqual(third['currentReferent'], {'aircraftId': 'A2', 'flightInstance': 'F2-R2'})
        self.assertIn('"currentReferent": {"aircraftId": "A2", "flightInstance": "F2-R2"}', self.prompt())

    def test_selecting_another_aircraft_resets_the_referent(self):
        client = self.serve([
            reply(referent={'aircraftId': 'A2', 'flightInstance': 'F2-R2'},
                  memoryUpdate={'kind': 'correction', 'aircraftId': 'A2', 'flightInstance': 'F2-R2'}),
            reply(referent={'aircraftId': 'A1', 'flightInstance': 'F1-R1'})])
        self.ask(client, 1, 0)
        result = self.ask(client, 2, 1, aircraft='A1', flight='F1-R1').json()
        self.assertEqual(result['currentReferent'], {'aircraftId': 'A1', 'flightInstance': 'F1-R1'})

    def test_unsupported_claim_is_withheld(self):
        client = self.serve([reply(claims=[claim('E01:stand', 'Z', 'current', 'E01')])])
        result = self.ask(client, 1, 0).json()
        self.assertFalse(result['accepted'])
        self.assertIn('unsupported_value', result['errors'])
        self.assertEqual(result['display']['claims'], [])
        self.assertIsNone(result['referent'])

    def test_follow_up_must_cover_a_newly_received_change(self):
        client = self.serve([reply(claims=[claim('E01:stand', 'B', 'current', 'E01')]),
                             reply(claims=[claim('E01:stand', 'B', 'current', 'E01')], explanationChanged=False)])
        self.ask(client, 1, 0, checkpoint=25)
        result = self.ask(client, 2, 1, checkpoint=30).json()  # E03 supersedes E01, received at 30 s
        self.assertFalse(result['accepted'])
        self.assertIn('denies_change', result['errors'])

    def test_follow_up_prompt_carries_the_changes_the_validator_checks(self):
        client = self.serve([reply(claims=[claim('E01:stand', 'B', 'current', 'E01')]), reply(), reply()])
        self.ask(client, 1, 0, checkpoint=25)
        self.ask(client, 2, 1, checkpoint=26)
        self.assertIn('"changedSincePreviousAnswer": []', self.prompt())
        self.ask(client, 3, 2, checkpoint=30)  # E03 supersedes E01, received at 30 s
        self.assertIn('"changedSincePreviousAnswer": ["E01:stand", "E03:stand"]', self.prompt())

    def test_expiry_before_or_after_the_previous_answer_gives_different_prompts(self):
        prompts = []
        for expiry in (24, 27):
            data = two_rotation_scenario()
            data['events'][3]['facts'][0]['validUntil'] = expiry  # E04: A1's stand
            client = self.serve([reply(referent={'aircraftId': 'A1', 'flightInstance': 'F1-R1'}), reply()],
                                scenarios={'conv-test': data})
            self.ask(client, 1, 0, checkpoint=25, aircraft='A1', flight='F1-R1')
            self.ask(client, 2, 1, checkpoint=30, aircraft='A1', flight='F1-R1')
            prompts.append(self.prompt())
        self.assertIn('"changedSincePreviousAnswer": []', prompts[0])
        self.assertIn('"changedSincePreviousAnswer": ["E04:stand"]', prompts[1])

    def test_session_is_bound_to_its_scenario(self):
        other = dict(two_rotation_scenario(), scenarioId='conv-other')
        client = self.serve([reply(claims=[claim('E01:stand', 'B', 'current', 'E01')])],
                            scenarios={'conv-test': two_rotation_scenario(), 'conv-other': other})
        self.ask(client, 1, 0)
        self.assertEqual(self.ask(client, 1, 0, scenarioId='conv-other').status_code, 409)
        self.assertEqual(self.ask(client, 2, 1, scenarioId='conv-other').status_code, 409)
        self.assertEqual(len(self.adapter.calls), 1)

    def test_invalid_and_fenced_json(self):
        client = self.serve(['not json', '```json\n' + reply() + '\n```'])
        bad = self.ask(client, 1, 0).json()
        self.assertEqual(bad['errors'], ['invalid_json'])
        fenced = self.ask(client, 2, 1).json()
        self.assertTrue(fenced['accepted'])
        self.assertEqual((fenced['rawJsonValid'], fenced['repairs']), (False, ['strip_code_fence']))

    def test_model_failure_is_withheld_and_recorded(self):
        client = self.serve([RuntimeError('connection reset')])
        result = self.ask(client, 1, 0).json()
        self.assertEqual(result['errors'], ['model_error:provider_error:RuntimeError'])
        self.assertEqual(result['revision'], 1)

    def test_formal_session_rejects_backward_seek_and_mode_change(self):
        client = self.serve([reply(), reply()])
        self.ask(client, 1, 0, checkpoint=30, mode='formal')
        self.assertEqual(self.ask(client, 2, 1, checkpoint=20, mode='formal').status_code, 409)
        self.assertEqual(self.ask(client, 3, 1, checkpoint=40, mode='development').status_code, 409)

    def test_image_needs_a_capture_time_not_after_the_checkpoint(self):
        client = self.serve([])
        self.assertEqual(self.ask(client, 1, 0, imageBase64=png()).status_code, 422)
        self.assertEqual(self.ask(client, 2, 0, imageBase64=png(), imageCaptureTime=26).status_code, 422)
        self.assertEqual(self.ask(client, 3, 0, imageBase64='bm90IGFuIGltYWdl').status_code, 422)

    def test_unknown_scenario_and_flight_are_refused(self):
        client = self.serve([])
        self.assertEqual(self.ask(client, 1, 0, scenarioId='missing').status_code, 422)
        self.assertEqual(self.ask(client, 2, 0, flight='F1-R1').status_code, 422)

    def test_visual_observation_on_the_development_scenario(self):
        scenarios = load_scenarios()
        data = scenarios['V1-visual-observation-dev-01']
        client = self.serve([reply(observations=[{'kind': 'fuel_vehicle', 'aircraftId': 'A2', 'value': 'connected',
                                                  'captureTime': 24}])], scenarios={'conv-test': data})
        result = self.ask(client, 1, 0, checkpoint=24, imageBase64=png(), imageCaptureTime=24).json()
        self.assertTrue(result['accepted'], result['errors'])
        self.assertEqual(result['display']['observations'][0]['relation'], 'conflicts')


if __name__ == '__main__':
    unittest.main()
