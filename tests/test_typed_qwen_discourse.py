"""Mechanical mapping and assignment constraints, never semantic acceptance."""
import copy
import json
import unittest

from experiments.typed_qwen_frames.discourse_candidate import (
    FrameError, selection_prompt, parse_selection, annotation_prompt, parse_annotation,
)


TEXT = 'BOT7 — no, sorry, BOT8 — moved the chair.'
REPAIR = ['r1', ['u1'], 'BOT7', 'no, sorry', 'BOT8', 'fragment']
CLAIMS = [['c1', ['u1'], 'BOT7', 'withdrawn', None],
          ['c2', ['u1'], 'BOT8 moved the chair.', 'active', 'c1']]


def select(learner=TEXT, repairs=None, unresolved=None):
    return parse_selection(json.dumps(dict(repairs=repairs if repairs is not None else [REPAIR],
                                          unresolved=unresolved or [])), learner)


def annotate(selected=None, learner=TEXT, claims=None, assignments=None, unresolved=None):
    return parse_annotation(json.dumps(dict(claims=claims if claims is not None else CLAIMS,
        unresolved=unresolved or [], repairAssignments=assignments if assignments is not None else
        [['r1', 'c1', 'c2', None]])), learner, selected or select())


class DiscourseTests(unittest.TestCase):
    def test_exact_mapping_offsets_and_false_flags(self):
        out = select()
        for key in ('oldSpan', 'cueSpan', 'newSpan'):
            span = out['repairs'][0][key]
            self.assertEqual(TEXT[span['start']:span['end']], span['text'])
        self.assertFalse(out['allClauseCoverageRequired'])
        self.assertFalse(out['fidelityVerified'])
        self.assertFalse(out['reportCheckAllowed'])

    def test_empty_map_valid_without_all_unit_coverage(self):
        out = select('A. B.', repairs=[])
        self.assertEqual(out['repairs'], [])
        self.assertEqual(len(out['units']), 2)
        self.assertFalse(out['semanticCompletenessVerified'])

    def test_exact_fields_no_paraphrase_or_incidental_word_binding(self):
        for replacement in ['BOT9', 'bot7', 'OT7']:
            row = copy.deepcopy(REPAIR)
            row[2] = replacement
            with self.assertRaises(FrameError):
                select(repairs=[row])

    def test_repeated_actual_mentions_reject_ambiguity(self):
        with self.assertRaises(FrameError):
            select(TEXT + ' BOT7.', repairs=[['r1', ['u1', 'u2'], 'BOT7', 'no, sorry', 'BOT8', 'fragment']])

    def test_scope_and_stage_a_width_types(self):
        for row in [REPAIR[:-1], REPAIR + [None], {}, ['r1', ['u1'], 'BOT7', 'no, sorry', 'BOT8', 'active']]:
            with self.assertRaises(FrameError):
                select(repairs=[row])

    def test_map_ids_unique_and_source_offsets_ordered_not_unit_starts(self):
        with self.assertRaises(FrameError):
            select(repairs=[REPAIR, REPAIR])
        reverse = ['r1', ['u1'], 'BOT8', 'no, sorry', 'BOT7', 'fragment']
        with self.assertRaises(FrameError):
            select(repairs=[reverse])

    def test_full_final_root_and_map_notes_preserved(self):
        note = [['u1'], 'Cue scope remains ambiguous']
        selected = select(unresolved=[note])
        out = annotate(selected)
        self.assertEqual(out['wireFrames']['repairAssignments'], [['r1', 'c1', 'c2', None]])
        self.assertEqual(out['repairMapWire'], selected['wireFrames'])
        self.assertEqual(out['selectionUnresolvedAudit'], selected['unresolved'])
        self.assertEqual(out['repairMapSHA256'], selected['mapSHA256'])
        self.assertFalse(out['fidelityVerified'])
        self.assertFalse(out['reportCheckAllowed'])

    def test_rejected_map_not_forced_into_claims(self):
        out = annotate(claims=[['c1', ['u1'], TEXT, 'ambiguous', None]],
                       assignments=[['r1', None, None, 'Map reading is not supported by the original.']])
        self.assertEqual(out['repairAssignments'][0]['disposition'], 'unresolved')
        self.assertFalse(out['repairAssignments'][0]['semanticAcceptanceVerified'])

    def test_assignment_missing_duplicate_extra_partial_rejected(self):
        for rows in [[], [['r1', 'c1', 'c2', None]] * 2, [['r9', 'c1', 'c2', None]],
                     [['r1', None, 'c2', 'reason']], [['r1', 'c1', None, 'reason']],
                     [['r1', None, None, None]], [['r1', 'c1', 'c2', 'reason']]]:
            with self.assertRaises(FrameError):
                annotate(assignments=rows)

    def test_assignment_requires_withdrawal_and_link(self):
        for rows in [[['c1', ['u1'], 'BOT7', 'active', None], ['c2', ['u1'], 'BOT8 moved', 'active', None]],
                     [['c1', ['u1'], 'BOT7', 'withdrawn', None], ['c2', ['u1'], 'BOT8 moved', 'active', None]]]:
            with self.assertRaises(FrameError):
                annotate(claims=rows)

    def test_correction_chain_replacement_may_later_be_withdrawn(self):
        learner = 'At 14:00, correction 15:00, correction 16:00.'
        selected = select(learner, repairs=[
            ['r1', ['u1'], '14:00', 'correction 15:00', '15:00', 'complete_assertion'],
            ['r2', ['u1'], '15:00', 'correction 16:00', '16:00', 'complete_assertion']])
        out = annotate(selected, learner, claims=[
            ['c1', ['u1'], 'At 14:00', 'withdrawn', None],
            ['c2', ['u1'], 'At 15:00', 'withdrawn', 'c1'],
            ['c3', ['u1'], 'At 16:00', 'active', 'c2']], assignments=[
            ['r1', 'c1', 'c2', None], ['r2', 'c2', 'c3', None]])
        self.assertEqual(out['frames']['claims'][1]['lifecycle'], 'withdrawn')

    def test_assigned_evidence_contains_original_mentions(self):
        learner = 'BOT7 was named. No, sorry, BOT8 moved.'
        selected = select(learner, repairs=[['r1', ['u1', 'u2'], 'BOT7', 'No, sorry', 'BOT8', 'complete_assertion']])
        with self.assertRaises(FrameError):
            annotate(selected, learner, claims=[['c1', ['u2'], 'BOT7', 'withdrawn', None],
                                                 ['c2', ['u2'], 'BOT8 moved', 'active', 'c1']],
                     unresolved=[[['u1'], 'context']])

    def test_final_coverage_includes_nonrepair_claims(self):
        learner = TEXT + ' The lamp is on.'
        selected = select(learner)
        with self.assertRaises(FrameError):
            annotate(selected, learner)
        rows = CLAIMS + [['c3', ['u2'], 'The lamp is on.', 'active', None]]
        self.assertEqual(len(annotate(selected, learner, claims=rows)['frames']['claims']), 3)

    def test_no_stage_a_id_constraint_on_full_claims(self):
        selected = select('A. B.', repairs=[])
        out = annotate(selected, 'A. B.', claims=[['c5', ['u1'], 'A.', 'active', None],
                                                   ['c9', ['u2'], 'B.', 'active', None]], assignments=[])
        self.assertEqual(len(out['frames']['claims']), 2)

    def test_map_wire_input_version_provenance(self):
        for key, value in [('version', 'bad'), ('inputSHA256', 'bad'), ('mapSHA256', 'bad')]:
            selected = select()
            selected[key] = value
            with self.assertRaises(FrameError):
                annotation_prompt(TEXT, selected)
        selected = select()
        selected['wireFrames']['unresolved'].append([['u1'], 'injected'])
        with self.assertRaises(FrameError):
            annotation_prompt(TEXT, selected)

    def test_map_rejection_still_unverified_not_automatic_fidelity(self):
        out = annotate(claims=[['c1', ['u1'], 'A fabricated fire occurred.', 'active', None]],
                       assignments=[['r1', None, None, 'Map not used']])
        self.assertFalse(out['fidelityVerified'])
        self.assertFalse(out['reportCheckAllowed'])

    def test_strict_json_and_list_bounds(self):
        for raw in ['{}', '```json\n{}\n```', '{"repairs":[],"repairs":[],"unresolved":[]}',
                    '{"repairs":NaN,"unresolved":[]}']:
            with self.assertRaises(FrameError):
                parse_selection(raw, TEXT)
        with self.assertRaises(FrameError):
            select(repairs=[], unresolved=[[['u1'], 'note']] * 25)
        with self.assertRaises(FrameError):
            annotate(assignments=[['r1', 'c1', 'c2']])

    def test_input_bound_and_prompt_original_context(self):
        prompt = annotation_prompt(TEXT, select())
        self.assertIn('UNTRUSTED_REPAIR_MAP=', prompt)
        self.assertIn('BOT7', prompt)
        select('a' * 1200, repairs=[])
        with self.assertRaises(FrameError):
            selection_prompt('a' * 1201)


if __name__ == '__main__':
    unittest.main()
