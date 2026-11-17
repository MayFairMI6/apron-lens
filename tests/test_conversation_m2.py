"""M2 camera arms: prompt block, checked camera answers, retry, scoring, and freeze 1 left untouched."""
import ast
import json
import unittest
from pathlib import Path

from modelaccess.contract import Settings
from modelaccess.mock import MockAdapter
from backend.conversation import camera as camera_evidence
from backend.conversation.scoring_m2 import first_attempt_view, score_turn_m2
from backend.conversation.state import SessionState
from backend.conversation.turns import build_prompt
from backend.conversation.turns_m2 import build_prompt_m2, camera_config, run_turn_m2, validate_m2, allowed_for
from backend.stand_clearance_lesson import build_stand_clearance_lesson

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / 'outputs/checkpoint2-run/stand-b-session-observations.json'
T3 = ('A3', 'TRN103')
MC = 'movement_condition'


def reply(claims=(), camera=(), referent=T3, status='answer', explanation=None):
    return dict(status=status, referent=None if referent is None else dict(aircraftId=referent[0], flightInstance=referent[1]),
                claims=list(claims), unknowns=[], explanationChanged=explanation, changesNotDiscussed=[],
                memoryUpdate=None, rationale='', observations=[], camera=list(camera))


def claim(fact_id, value, status='current'):
    return dict(fact_id=fact_id, value=value, status=status, evidence_ids=[fact_id.split(':')[0]])


class M2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world, _, _ = build_stand_clearance_lesson(17)
        cls.records = {arm: camera_evidence.load_session(SESSION, arm, cls.world['scenarioId']) for arm in ('rgb', 'rgb_depth')}

    def cam(self, arm, form='tracked'):
        return camera_config(arm, form, self.records.get(arm, []))

    def prompt(self, arm, cutoff, form='tracked', selection=T3):
        return build_prompt_m2(self.world, cutoff, selection, selection, [], {}, 'Is Stand B clear?', (), self.cam(arm, form))

    def candidates(self, text):
        return json.JSONDecoder().raw_decode(text.split('Candidate flights and received facts: ', 1)[1])[0]

    def test_arms_differ_only_in_camera_evidence(self):
        off, rgb, depth = (self.prompt(a, 92) for a in ('off', 'rgb', 'rgb_depth'))
        self.assertIn('No camera observations are available', off)
        self.assertNotIn('"camera": {', off)
        latest = lambda text: self.candidates(text)[0]['camera']['latest']
        self.assertEqual((latest(rgb)['finding'], latest(rgb)['place']), ('seen', 'unknown'))
        self.assertNotIn('estimatedPositionMetres', latest(rgb))
        self.assertEqual(latest(depth)['place'], 'off_stand_b')
        strip = lambda text: [{k: v for k, v in c.items() if k != 'camera'} for c in self.candidates(text)]
        self.assertEqual(strip(off), strip(rgb))
        self.assertEqual(strip(rgb), strip(depth))

    def test_v6_prompt_is_unchanged_and_contained(self):
        v6 = build_prompt(self.world, 92, T3, T3, [], {}, 'Is Stand B clear?')
        self.assertIn('Every reply has all ten keys.', v6)
        self.assertNotIn('camera', v6.split('Candidate flights')[0])
        self.assertIn('Every reply has all eleven keys.', self.prompt('off', 92))

    def test_nothing_after_the_cutoff_is_listed(self):
        block = self.candidates(self.prompt('rgb_depth', 91.5))[0]['camera']
        self.assertEqual(block['latest']['captureTime'], 91.0)
        self.assertEqual(block['history']['placeChanges'], [])
        frame = self.candidates(self.prompt('rgb_depth', 120, form='frame'))[0]['camera']
        self.assertNotIn('history', frame)

    def test_camera_only_for_the_flight_it_is_about(self):
        other = self.candidates(self.prompt('rgb_depth', 92, selection=('A1', 'TRN101')))
        self.assertTrue(all('camera' not in c for c in other))

    def test_camera_entries_must_copy_a_listed_observation(self):
        allowed = allowed_for(self.cam('rgb_depth'), 92)
        ok = reply([claim(f'S006:{MC}', 'hold: Stand B clearance check pending')],
                   [dict(captureId='cam-t092-rgb_depth', finding='seen', place='off_stand_b')])
        checked = validate_m2(ok, self.world, 92, None, allowed)
        self.assertTrue(checked['accepted'], checked['errors'])
        self.assertIn('not a report and cannot release', checked['display']['answer'])
        wrong_place = json.loads(json.dumps(ok)); wrong_place['camera'][0]['place'] = 'on_stand_b'
        self.assertEqual(validate_m2(wrong_place, self.world, 92, None, allowed)['errors'], ['camera_value_mismatch'])
        unlisted = json.loads(json.dumps(ok)); unlisted['camera'][0]['captureId'] = 'cam-t150-rgb_depth'
        self.assertEqual(validate_m2(unlisted, self.world, 92, None, allowed)['errors'], ['camera_outside_listed'])
        rgb_place = reply(camera=[dict(captureId='cam-t092-rgb', finding='seen', place='off_stand_b')])
        self.assertEqual(validate_m2(rgb_place, self.world, 92, None, allowed_for(self.cam('rgb'), 92))['errors'],
                         ['camera_value_mismatch'])
        no_key = {k: v for k, v in ok.items() if k != 'camera'}
        self.assertEqual(validate_m2(no_key, self.world, 92, None, allowed)['errors'], ['schema'])

    def test_one_validator_guided_retry_keeps_both_attempts(self):
        bad = reply([claim(f'S008:{MC}', 'released')])
        good = reply([claim(f'S006:{MC}', 'hold: Stand B clearance check pending')])
        turn = dict(requestId='r1', turnId='r1', expectedRevision=0, aircraftId='A3', flightInstance='TRN103',
                    cutoff=92, question='Can TRN103 go to Stand B?')
        adapter = MockAdapter([json.dumps(bad), json.dumps(good)])
        result = run_turn_m2(SessionState('s1'), self.world, turn, adapter, Settings(model='mock', max_output_tokens=512), self.cam('rgb'))
        self.assertEqual(result['attempts'], 2)
        self.assertFalse(result['firstAttempt']['accepted'])
        self.assertTrue(result['accepted'])
        self.assertIn('claim_outside_eligible_evidence', adapter.calls[1][0].messages[0][1])
        expect = dict(status=['answer'], referent=dict(aircraftId='A3', flightInstance='TRN103'),
                      authority=[f'S006:{MC}'])
        by_id = {r['captureId']: r for r in self.records['rgb']}
        self.assertTrue(score_turn_m2(expect, result, by_id)['correct'])
        self.assertFalse(score_turn_m2(expect, first_attempt_view(result), by_id)['correct'])
        once = run_turn_m2(SessionState('s2'), self.world, dict(turn, requestId='r2', turnId='r2'),
                           MockAdapter([json.dumps(bad)]), Settings(model='mock', max_output_tokens=512), self.cam('rgb'), retry=False)
        self.assertEqual((once['attempts'], once['accepted']), (1, False))

    def test_camera_labels_are_capture_times(self):
        turn = dict(requestId='r3', turnId='r3', expectedRevision=0, aircraftId='A3', flightInstance='TRN103',
                    cutoff=92, question='Is Stand B clear?')
        answer = reply([claim(f'S006:{MC}', 'hold: Stand B clearance check pending')],
                       [dict(captureId='cam-t092-rgb_depth', finding='seen', place='off_stand_b')])
        result = run_turn_m2(SessionState('s3'), self.world, turn, MockAdapter([json.dumps(answer)]),
                             Settings(model='mock', max_output_tokens=512), self.cam('rgb_depth'))
        by_id = {r['captureId']: r for r in self.records['rgb_depth']}
        scores = score_turn_m2(dict(status=['answer'], cameraMustCite=[92.0], cameraCiteOnly=[92.0]), result, by_id)
        self.assertTrue(scores['cameraCites'] and scores['cameraPrecise'])
        self.assertFalse(score_turn_m2(dict(status=['answer'], cameraCiteOnly=[]), result, by_id)['cameraPrecise'])

    def test_request_path_reads_no_labels_or_masks(self):
        for name in ('backend/conversation/camera.py', 'backend/conversation/turns_m2.py'):
            tree = ast.parse((ROOT / name).read_text())
            imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertFalse({'backend.conversation.scoring', 'backend.conversation.scoring_m2',
                              'backend.conversation.visual_truth'} & imported, name)
            code = ast.unparse(tree)
            self.assertNotIn("['visibleBoxes']", code)
            self.assertNotIn('.mask', code)


if __name__ == '__main__':
    unittest.main()
