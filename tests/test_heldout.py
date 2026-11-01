"""Held-out set tooling: location and hash checks, the label checker and the runner's refusals. No model."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from backend.conversation.guards import HeldoutLocationError, heldout_record, load_heldout_set

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'unity/SurfaceSafetyCoach/Assets/Resources/visual_dev_05.json'


def write_set(folder, image=True):
    """A one-family held-out set built from a development scenario under a new ID."""
    folder = Path(folder)
    (folder / 'scenarios').mkdir()
    scenario = dict(json.loads(BASE.read_text()), scenarioId='H-test')
    (folder / 'scenarios/h_test.json').write_text(json.dumps(scenario))
    turn = dict(cutoff=20, selected=dict(aircraftId='A1', flightInstance='F1-R1'), question='Which stand?',
                expect=dict(status=['answer'], referent=dict(aircraftId='A1', flightInstance='F1-R1')),
                textOnly=dict(question='Which stand is A1 on?'))
    if image:
        turn['image'] = 'heldout/H-test-20s.png'
    families = dict(version='conversation-heldout-test', split='heldout', set='final',
                    families=[dict(id='H1', type='no-change', tests='test', scenario='H-test',
                                   turns=[turn, dict(turn, cutoff=30)])])
    if image:
        families['families'][0]['turns'][1]['image'] = 'heldout/H-test-30s.png'
    (folder / 'families.json').write_text(json.dumps(families))
    (folder / 'renders.json').write_text(json.dumps([dict(scenarioFile='scenarios/h_test.json', times=[20, 30])]))
    return folder / 'families.json', folder / 'scenarios'


def check(families, scenarios, *extra):
    return subprocess.run([sys.executable, 'scripts/check_heldout.py', '--families', str(families),
                           '--scenarios', str(scenarios), *extra], cwd=ROOT, capture_output=True, text=True)


class HeldoutSet(unittest.TestCase):
    def test_matching_set_loads_and_any_change_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            families, scenarios = write_set(folder)
            record = Path(folder) / 'record.json'
            record.write_text(json.dumps(heldout_record(families, scenarios)))
            loaded, by_id = load_heldout_set(families, scenarios, record)
            self.assertEqual((loaded['split'], list(by_id)), ('heldout', ['H-test']))
            (scenarios / 'extra.json').write_text('{}')
            with self.assertRaisesRegex(HeldoutLocationError, 'extra.json'):
                load_heldout_set(families, scenarios, record)
            (scenarios / 'extra.json').unlink()
            families.write_text(families.read_text().replace('Which stand?', 'Which gate?'))
            with self.assertRaisesRegex(HeldoutLocationError, 'committed hash'):
                load_heldout_set(families, scenarios, record)

    def test_record_path_follows_the_set(self):
        from backend.conversation.guards import heldout_record_path
        self.assertEqual(heldout_record_path({'set': 'final'}).name, 'heldout-final.json')
        with self.assertRaises(HeldoutLocationError):
            heldout_record_path({'set': 'development'})

    def test_set_inside_the_repository_is_refused(self):
        (ROOT / 'work').mkdir(exist_ok=True)  # ignored by git, so absent on a fresh checkout
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as folder:
            families, scenarios = write_set(folder)
            record = Path(folder) / 'record.json'
            record.write_text(json.dumps(heldout_record(families, scenarios)))
            with self.assertRaises(HeldoutLocationError):
                load_heldout_set(families, scenarios, record)
            self.assertIn('must be outside the repository', check(families, scenarios).stdout)

    def test_checker_passes_a_valid_set_and_prints_only_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            families, scenarios = write_set(folder)
            out = check(families, scenarios)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            self.assertIn('"imageShare": 1.0', out.stdout)
            self.assertNotIn('Which stand?', out.stdout)

    def test_checker_reports_broken_labels_and_images(self):
        with tempfile.TemporaryDirectory() as folder:
            families, scenarios = write_set(folder)
            data = json.loads(families.read_text())
            first, second = data['families'][0]['turns']
            first['image'] = 'heldout/H-test-21s.png'           # name doesn't match the cutoff
            second['expect']['mustCite'] = ['Z99:stand']        # never received
            second['expect']['observations'] = {'fuel_vehicle': 'parked'}  # not a value
            families.write_text(json.dumps(data))
            out = check(families, scenarios)
            self.assertNotEqual(out.returncode, 0)
            for text in ('image must be named heldout/H-test-20s.png', 'invalid observation label', 'Z99:stand'):
                self.assertIn(text, out.stdout)

    def test_checker_reports_scenario_rule_violations(self):
        with tempfile.TemporaryDirectory() as folder:
            families, scenarios = write_set(folder)
            path = scenarios / 'h_test.json'
            data = json.loads(path.read_text())
            data['visualProps'][0]['states'][0]['t'] = 5        # states must start at 0
            data['events'][1]['receiptTime'] = data['events'][1]['eventTime'] - 1
            path.write_text(json.dumps(data))
            out = check(families, scenarios)
            self.assertIn('h_test.json', out.stdout)
            self.assertNotEqual(out.returncode, 0)

    def test_checker_mirrors_unitys_trajectory_and_board_rules(self):
        for change, text in ((lambda d: d['aircraft'][0].__setitem__('waypoints', d['aircraft'][0]['waypoints'][:1]),
                              'at least two waypoints'),
                             (lambda d: d['aircraft'][0]['waypoints'][-1].__setitem__('t', d['duration'] + 1),
                              'within 0..duration'),
                             (lambda d: d['occluders'][0].__setitem__('x', d['targetWidth']), 'position on the board')):
            with self.subTest(text), tempfile.TemporaryDirectory() as folder:
                families, scenarios = write_set(folder)
                path = scenarios / 'h_test.json'
                data = json.loads(path.read_text())
                change(data)
                path.write_text(json.dumps(data))
                out = check(families, scenarios)
                self.assertNotEqual(out.returncode, 0)
                self.assertIn(text, out.stdout)

    def test_checker_enforces_set_rules_types_and_running_clocks(self):
        with tempfile.TemporaryDirectory() as folder:
            families, scenarios = write_set(folder)
            data = json.loads(families.read_text())
            data['set'] = 'm1'                                   # m1: no images, every turn textOnly
            family = data['families'][0]
            family['type'] = 'tracking'                          # not a listed type
            del family['turns'][0]['textOnly']
            family['turns'][1]['lastSeen'] = 25                  # visual_dev_05's clock pauses
            families.write_text(json.dumps(data))
            out = check(families, scenarios).stdout
            for text in ('type must be one of', 'every m1 turn needs textOnly', 'the m1 set has no images',
                         'clockWhileUntracked'):
                self.assertIn(text, out)

    def test_runner_refuses_a_heldout_set_without_its_scenarios(self):
        with tempfile.TemporaryDirectory() as folder:
            families, _ = write_set(folder)
            out = subprocess.run([sys.executable, 'scripts/run_conversation_families.py', '--baseline',
                                  '--families', str(families)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(out.returncode, 0)
            self.assertIn('needs --scenarios', out.stderr)


if __name__ == '__main__':
    unittest.main()
