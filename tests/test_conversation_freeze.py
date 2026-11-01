"""Freeze record for the conversational method: no model, no network."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.conversation import freeze


class FreezeRecord(unittest.TestCase):
    def setUp(self):
        self.record = freeze.load()

    def test_record_names_the_current_versions_and_files(self):
        self.assertIsNotNone(self.record, 'config/conversation-freeze.json is missing')
        self.assertEqual(self.record['record'], freeze.RECORD_VERSION)
        self.assertEqual(self.record['versions'], freeze.versions())
        self.assertEqual(set(self.record['files']), set(freeze.FROZEN_FILES))

    def test_an_approved_record_matches_the_method(self):
        if self.record['status'] == 'approved':  # once approved, any change to a frozen file fails here
            self.assertEqual(freeze.mismatches(self.record), [])

    def test_a_changed_file_is_detected(self):
        changed = dict(self.record, files=dict(self.record['files'], **{freeze.FROZEN_FILES[0]: '0' * 64}))
        self.assertEqual(freeze.mismatches(changed), [freeze.FROZEN_FILES[0]])

    def test_formal_runs_need_an_approved_matching_record(self):
        path = Path(tempfile.mkdtemp()) / 'freeze.json'
        path.write_text(json.dumps(freeze.current_record()))
        with self.assertRaises(SystemExit):
            freeze.require_approved(path)  # proposed
        path.write_text(json.dumps(freeze.approve(freeze.current_record(), 'tester')))
        self.assertTrue(freeze.require_approved(path)['matches'])
        stale = freeze.approve(freeze.current_record(), 'tester')
        stale['files'][freeze.FROZEN_FILES[0]] = '0' * 64
        path.write_text(json.dumps(stale))
        with self.assertRaises(SystemExit):
            freeze.require_approved(path)

    def test_approval_needs_a_name(self):
        with self.assertRaises(ValueError):
            freeze.approve(freeze.current_record(), '')


if __name__ == '__main__':
    unittest.main()
