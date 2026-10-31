"""Visual observation evidence on the authored development scenario (no evaluation gold)."""
import json
import unittest
from pathlib import Path

from backend.conversation import visual_truth
from backend.conversation.context import changed_facts, snapshot
from backend.conversation.identity import next_rotation, rotation_at, validate_rotations
from backend.conversation.observations import VISUAL_KINDS, relate
from backend.conversation.validate import validate_proposal
from backend.evidence import validate_scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / 'unity/SurfaceSafetyCoach/Assets/Resources/visual_dev_01.json'
REQUEST_PATH = ['context.py', 'state.py', 'validate.py', 'observations.py', 'identity.py', 'guards.py', 'ledger.py',
                'turns.py', 'server.py']


def load():
    return json.loads(SCENARIO.read_text())


def obs(kind, value, t, aircraft='A2'):
    return {'kind': kind, 'aircraftId': aircraft, 'value': value, 'captureTime': t}


def proposal(observations, claims=()):
    return dict(status='answer', referent={'aircraftId': 'A2', 'flightInstance': 'F2-R1'}, claims=list(claims),
                unknowns=[], explanationChanged=None, changesNotDiscussed=[], memoryUpdate=None, rationale='',
                observations=list(observations))


class Separation(unittest.TestCase):
    def test_scenario_is_valid_and_props_are_well_formed(self):
        data = load()
        validate_scenario(data)
        validate_rotations(data)
        for prop in data['visualProps']:
            self.assertEqual(prop['states'][0]['t'], 0)
            self.assertTrue(all(s['value'] in VISUAL_KINDS[prop['kind']]['values'] for s in prop['states']))

    def test_snapshot_carries_no_visual_ground_truth(self):
        text = json.dumps(snapshot(load(), 'A2', 'F2-R1', 24), default=str)
        for leaked in ('visualProps', 'fuel_vehicle', 'cargo_door', 'connected', '"P1"'):
            self.assertNotIn(leaked, text)

    def test_request_path_never_reads_visual_truth(self):
        base = ROOT / 'backend/conversation'
        for name in REQUEST_PATH:
            source = (base / name).read_text()
            self.assertNotIn('visual_truth', source, name)
            self.assertNotIn('visualProps', source, name)


class Relations(unittest.TestCase):
    def setUp(self):
        self.data = load()

    def related(self, kind, value, capture, cutoff):
        return relate(obs(kind, value, capture), snapshot(self.data, 'A2', 'F2-R1', cutoff))

    def test_view_conflicts_with_report_without_changing_it(self):
        snap = snapshot(self.data, 'A2', 'F2-R1', 24)
        result = relate(obs('fuel_vehicle', 'connected', 24), snap)
        self.assertEqual((result['relation'], result['evidenceIds']), ('conflicts', ['V03']))
        self.assertEqual(snap['factsById']['V03:fuel_status']['status'], 'current')

    def test_view_ahead_of_late_report(self):
        self.assertEqual(self.related('cargo_door', 'closed', 31, 31)['relation'], 'no_report_yet')
        later = self.related('cargo_door', 'closed', 36, 36)
        self.assertEqual((later['relation'], later['evidenceIds']), ('consistent', ['V04']))

    def test_report_about_a_later_moment_is_not_a_conflict(self):
        self.assertEqual(self.related('fuel_vehicle', 'connected', 18, 24)['relation'], 'report_describes_later_time')

    def test_consistent_after_vehicle_departs(self):
        self.assertEqual(self.related('fuel_vehicle', 'departed', 31, 31)['relation'], 'consistent')

    def test_observation_after_cutoff_is_refused(self):
        with self.assertRaises(ValueError):
            self.related('fuel_vehicle', 'connected', 30, 24)


class Validator(unittest.TestCase):
    def setUp(self):
        self.data = load()

    def test_accepted_observation_is_labelled_and_reports_unchanged(self):
        claim = {'fact_id': 'V03:fuel_status', 'value': 'complete', 'status': 'current', 'evidence_ids': ['V03']}
        result = validate_proposal(proposal([obs('fuel_vehicle', 'connected', 24)], [claim]), self.data, 24,
                                   image_capture_time=24)
        self.assertTrue(result['accepted'], result['errors'])
        self.assertIn('not verified', result['display']['answer'])
        self.assertIn('conflicts with report V03', result['display']['answer'])
        self.assertEqual(result['observations'][0]['relation'], 'conflicts')

    def test_observation_needs_an_image_and_its_capture_time(self):
        p = proposal([obs('fuel_vehicle', 'connected', 24)])
        self.assertIn('observation_without_image', validate_proposal(p, self.data, 24)['errors'])
        self.assertIn('observation_capture_time_mismatch',
                      validate_proposal(p, self.data, 26, image_capture_time=25)['errors'])
        self.assertIn('image_after_cutoff', validate_proposal(p, self.data, 24, image_capture_time=30)['errors'])

    def test_observation_must_concern_the_referent(self):
        p = proposal([obs('fuel_vehicle', 'connected', 24, aircraft='A1')])
        self.assertIn('observation_outside_referent',
                      validate_proposal(p, self.data, 24, image_capture_time=24)['errors'])

    def test_unknown_visual_kind_is_a_schema_error(self):
        p = proposal([{'kind': 'chocks', 'aircraftId': 'A2', 'value': 'on', 'captureTime': 24}])
        self.assertIn('observation_schema', validate_proposal(p, self.data, 24, image_capture_time=24)['errors'])


class EvaluationTruth(unittest.TestCase):
    def test_scoring_uses_authored_state_at_capture_time(self):
        data = load()
        self.assertEqual(visual_truth.score_observation(data, 'F2-R1', obs('fuel_vehicle', 'connected', 24)),
                         (True, 'connected'))
        self.assertEqual(visual_truth.score_observation(data, 'F2-R1', obs('fuel_vehicle', 'connected', 31)),
                         (False, 'departed'))
        self.assertEqual(visual_truth.score_observation(data, 'F2-R1', obs('cargo_door', 'open', 27.9)),
                         (True, 'open'))


class UniformLiveryScenario(unittest.TestCase):
    """visual_dev_02: three aircraft in one livery, told apart only by position, motion and props."""

    def setUp(self):
        self.data = json.loads((SCENARIO.parent / 'visual_dev_02.json').read_text())

    def test_scenario_is_valid(self):
        validate_scenario(self.data)
        validate_rotations(self.data)
        self.assertEqual(self.data['livery'], 'uniform')
        self.assertEqual(len(self.data['aircraft']), 3)
        for prop in self.data['visualProps']:
            self.assertEqual(prop['states'][0]['t'], 0)
            self.assertTrue(all(s['value'] in VISUAL_KINDS[prop['kind']]['values'] for s in prop['states']))

    def test_props_belong_to_different_aircraft(self):
        self.assertEqual(visual_truth.prop_value(self.data, 'A1', 'F1-R1', 'fuel_vehicle', 25), 'connected')
        self.assertEqual(visual_truth.prop_value(self.data, 'A1', 'F1-R1', 'fuel_vehicle', 26), 'departed')
        self.assertEqual(visual_truth.prop_value(self.data, 'A2', 'F2-R1', 'cargo_door', 31), 'open')
        self.assertIsNone(visual_truth.prop_value(self.data, 'A2', 'F2-R1', 'fuel_vehicle', 20))
        self.assertIsNone(visual_truth.prop_value(self.data, 'A3', 'F3-R1', 'cargo_door', 20))


class RotationScenario(unittest.TestCase):
    """visual_dev_03: A2 flies F2-R1 until 45 s, then F2-R2; F2-R2's off-block time is revised by a late report."""

    def setUp(self):
        self.data = json.loads((SCENARIO.parent / 'visual_dev_03.json').read_text())

    def test_scenario_and_rotations_are_valid(self):
        validate_scenario(self.data)
        validate_rotations(self.data)
        self.assertEqual(next_rotation(self.data, 'A2', 'F2-R1')['flightInstance'], 'F2-R2')
        self.assertEqual(rotation_at(self.data, 'A2', 30)['flightInstance'], 'F2-R1')
        self.assertEqual(rotation_at(self.data, 'A2', 45)['flightInstance'], 'F2-R2')

    def test_late_revision_reaches_the_next_rotation_at_36_s(self):
        before = snapshot(self.data, 'A2', 'F2-R2', 30)
        after = snapshot(self.data, 'A2', 'F2-R2', 40)
        self.assertEqual([(f['fact_id'], f['status']) for f in before['facts']], [('R04:tobt', 'current')])
        self.assertEqual(changed_facts(before, after), ['R04:tobt', 'R05:tobt'])


if __name__ == '__main__':
    unittest.main()
