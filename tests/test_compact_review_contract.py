"""Synthetic offline checks; v2 guards use synthetic topics, with no model accuracy claim.

No model calls or evaluation labels. Citation acceptance is not entailment.
"""
import json
import unittest
from unittest.mock import patch

from experiments.typed_review_repair.candidate import expand_review as expand, prompt_for, coverage_prompt, parse_coverage
from experiments.typed_review_repair.coverage import facets_for
from backend.training_assessment import TYPED_QUESTIONS, RUBRICS
from experiments.typed_claim_review.candidate import units_for


def payload_for(text='The parcel is at the depot. Delivery time is unknown.'):
    return {
        'episodeId': 'synthetic-episode', 'checkpointId': 'synthetic-check',
        'cutoff': 10, 'question': 'Where is the parcel and when will it arrive?',
        'learnerResponse': text,
        'criteria': [
            {'id': 'location', 'expected': 'Identify depot and unknown delivery time.', 'evidenceIds': ['R1']},
            {'id': 'grounding', 'expected': 'Check every asserted claim.', 'evidenceIds': ['R1']},
        ],
        'reports': [{'id': 'R1', 'episodeId': 'synthetic-episode', 'receiptTime': 10,
                     'message': 'Parcel is at the depot. Delivery time is unknown.'}],
    }


def answer_for(payload, status='met', refs=None, checks=None):
    units = units_for(payload['learnerResponse'])
    return json.dumps({'points': [{'id': 'location', 'status': status,
                                  'units': refs if refs is not None else [u['id'] for u in units],
                                  'reason': 'The location and unknown time are stated.'}],
                       'checks': checks if checks is not None else [[u['id'], 'supported'] for u in units]})


def synthetic_facets(payload):
    return [{'id': 'location.1', 'criterion': 'location', 'topic': 'Location stated by learner'},
            {'id': 'location.2', 'criterion': 'location', 'topic': 'Delivery time stated by learner'}]


def coverage_for(payload):
    ids = [u['id'] for u in units_for(payload['learnerResponse'])]
    return [['location.1', [ids[0]]], ['location.2', [ids[-1]]]]


def expand_review(text, payload, coverage=None):
    return expand(text, payload, coverage_for(payload) if coverage is None else coverage)


class CompactReviewContractTests(unittest.TestCase):
    def setUp(self):
        patcher = patch('experiments.typed_review_repair.candidate.facets_for', synthetic_facets)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_literal_quote_and_authored_bundle(self):
        payload = payload_for()
        result = expand_review(answer_for(payload), payload)
        for point in result['points']:
            self.assertIn(point['learnerQuote'], payload['learnerResponse'])
            self.assertLessEqual(len(point['learnerQuote']), 160)
            self.assertEqual(point['evidenceIds'], ['R1'])

    def test_future_authored_reference_rejected(self):
        payload = payload_for()
        payload['reports'][0]['receiptTime'] = 11
        with self.assertRaises(ValueError):
            expand_review(answer_for(payload), payload)

    def test_other_episode_authored_reference_rejected(self):
        payload = payload_for()
        payload['reports'][0]['episodeId'] = 'another-episode'
        with self.assertRaises(ValueError):
            expand_review(answer_for(payload), payload)

    def test_missing_authored_reference_rejected(self):
        payload = payload_for()
        payload['reports'] = []
        with self.assertRaises(ValueError):
            expand_review(answer_for(payload), payload)

    def test_omitted_unit_check_rejected(self):
        payload = payload_for()
        with self.assertRaises(ValueError):
            expand_review(answer_for(payload, checks=[['U1', 'supported']]), payload)

    def test_unknown_unit_reference_rejected(self):
        payload = payload_for()
        with self.assertRaises(ValueError):
            expand_review(answer_for(payload, refs=['U999']), payload)

    def test_missing_criterion_requires_empty_quote(self):
        payload = payload_for()
        result = expand_review(answer_for(payload, status='missing', refs=[]), payload)
        self.assertEqual(result['points'][0]['learnerQuote'], '')
        with self.assertRaises(ValueError):
            expand_review(answer_for(payload, status='missing', refs=['U1']), payload)

    def test_unrelated_unsupported_extra_is_not_hidden_by_met_core(self):
        payload = payload_for('The parcel is at the depot and delivery time is unknown. A dragon destroyed the truck.')
        result = expand_review(answer_for(payload, refs=['U1'],
                               checks=[['U1', 'supported'], ['U2', 'unsupported']]), payload,
                               [['location.1', ['U1']], ['location.2', ['U1']]])
        self.assertEqual(result['points'][0]['status'], 'met')
        self.assertEqual(result['points'][-1]['status'], 'contradicted')
        self.assertEqual(result['points'][-1]['learnerQuote'], 'A dragon destroyed the truck.')
        self.assertEqual(result['verdict'], 'needs_review')

    def test_long_units_remain_literal_and_bounded(self):
        for text in ('word ' * 100, 'x' * 400):
            for unit in units_for(text):
                self.assertLessEqual(len(unit['text']), 160)
                self.assertEqual(unit['text'], text[unit['start']:unit['end']])

    def test_prompt_rejects_future_and_other_episode_reports_before_inference(self):
        for episode, time in [('synthetic-episode', 11), ('another', 1)]:
            payload = payload_for()
            payload['reports'].append({'id': 'UNAVAILABLE', 'episodeId': episode,
                                       'receiptTime': time, 'message': 'unavailable sentinel'})
            for operation in (coverage_prompt, lambda p: prompt_for(p, coverage_for(p))):
                with self.assertRaises(ValueError):
                    operation(payload)

    def test_duplicate_ids_and_missing_bundles_rejected_before_inference(self):
        for change in ('duplicate', 'missing', 'empty'):
            payload = payload_for()
            if change == 'duplicate':
                payload['reports'].append(dict(payload['reports'][0]))
            elif change == 'missing':
                payload['criteria'][0]['evidenceIds'] = ['ABSENT']
            else:
                payload['criteria'][0]['evidenceIds'] = []
            with self.assertRaises(ValueError):
                coverage_prompt(payload)

    def test_multi_unit_support_uses_full_exact_contiguous_span(self):
        payload = payload_for()
        result = expand_review(answer_for(payload, refs=['U1', 'U2']), payload)
        self.assertEqual(result['points'][0]['learnerQuote'], payload['learnerResponse'])
        self.assertEqual(set(result['points'][0]),
                         {'criterionId', 'status', 'comment', 'evidenceIds', 'learnerQuote'})

    def test_multi_unit_span_over_160_is_withheld(self):
        payload = payload_for('The parcel is at the depot. ' + 'Delivery ' * 18 + 'is unknown.')
        with self.assertRaisesRegex(ValueError, 'span too wide'):
            expand_review(answer_for(payload), payload)

    def test_empty_coverage_blocks_met(self):
        payload = payload_for()
        with self.assertRaisesRegex(ValueError, 'blind coverage'):
            expand_review(answer_for(payload), payload,
                          [['location.1', ['U1']], ['location.2', []]])

    def test_wrong_claim_can_be_contradicted_with_missing_other_facet(self):
        payload = payload_for('The parcel is at the moon.')
        result = expand_review(answer_for(payload, status='contradicted', refs=['U1'],
                               checks=[['U1', 'unsupported']]), payload,
                               [['location.1', ['U1']], ['location.2', []]])
        self.assertEqual(result['points'][0]['status'], 'contradicted')
        self.assertEqual(result['verdict'], 'needs_review')

    def test_coverage_parser_rejects_unknown_duplicate_missing_or_reordered_rows(self):
        payload = payload_for()
        invalid = [[], [['location.2', []], ['location.1', []]],
                   [['location.1', ['U999']], ['location.2', []]],
                   [['location.1', ['U1', 'U1']], ['location.2', []]]]
        for rows in invalid:
            with self.assertRaises(ValueError):
                parse_coverage(json.dumps(rows), payload)

    def test_blind_prompt_omits_reports_and_expected_answers(self):
        payload = payload_for()
        payload['criteria'][0]['expected'] = 'EXPECTED_ANSWER_SENTINEL'
        payload['reports'][0]['message'] = 'REPORT_ANSWER_SENTINEL'
        prompt = coverage_prompt(payload)
        self.assertNotIn('EXPECTED_ANSWER_SENTINEL', prompt)
        self.assertNotIn('REPORT_ANSWER_SENTINEL', prompt)
        data = json.loads(prompt.split('\n', 1)[1])
        self.assertEqual(set(data), {'topics', 'units', 'learnerResponse'})

    def test_every_live_question_has_matching_neutral_facets(self):
        for exercise, questions in TYPED_QUESTIONS.items():
            for index, question in enumerate(questions):
                payload = {'question': question,
                           'criteria': [{'id': cid} for cid, _, _ in RUBRICS[exercise][index]]}
                rows = facets_for(payload)
                self.assertEqual({f['criterion'] for f in rows}, {c['id'] for c in payload['criteria']})
                self.assertTrue(all('stated by the learner' in f['topic'] or 'learner' in f['topic'] for f in rows))


if __name__ == '__main__':
    unittest.main()
