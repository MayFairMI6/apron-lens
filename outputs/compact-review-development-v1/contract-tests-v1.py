"""Synthetic offline checks; known gaps are explicit expected failures, not fixes.

No model calls or evaluation labels. Citation acceptance is not entailment.
"""
import json
import unittest

from experiments.typed_review_repair.candidate import expand_review, prompt_for
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


class CompactReviewContractTests(unittest.TestCase):
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
        payload = payload_for('The parcel is at the depot. A dragon destroyed the truck.')
        result = expand_review(answer_for(payload, refs=['U1'],
                               checks=[['U1', 'supported'], ['U2', 'unsupported']]), payload)
        self.assertEqual(result['points'][0]['status'], 'met')
        self.assertEqual(result['points'][-1]['status'], 'contradicted')
        self.assertEqual(result['points'][-1]['learnerQuote'], 'A dragon destroyed the truck.')
        self.assertEqual(result['verdict'], 'needs_review')

    def test_long_units_remain_literal_and_bounded(self):
        for text in ('word ' * 100, 'x' * 400):
            for unit in units_for(text):
                self.assertLessEqual(len(unit['text']), 160)
                self.assertEqual(unit['text'], text[unit['start']:unit['end']])

    @unittest.expectedFailure
    def test_prompt_excludes_future_and_other_episode_reports(self):
        payload = payload_for()
        payload['reports'] += [
            {'id': 'FUTURE', 'episodeId': payload['episodeId'], 'receiptTime': 11, 'message': 'future sentinel'},
            {'id': 'OTHER', 'episodeId': 'another', 'receiptTime': 1, 'message': 'other episode sentinel'},
        ]
        data = json.loads(prompt_for(payload).split('Input JSON:\n', 1)[1])
        self.assertEqual([r['id'] for r in data['receivedReports']], ['R1'])

    @unittest.expectedFailure
    def test_multi_unit_support_retains_every_reference_for_audit(self):
        payload = payload_for()
        result = expand_review(answer_for(payload, refs=['U1', 'U2']), payload)
        # A future sidecar or explicit quote-array contract must preserve this
        # mapping; silently selecting U1 loses the unknown-time support.
        self.assertEqual(result['points'][0].get('learnerUnitIds'), ['U1', 'U2'])


if __name__ == '__main__':
    unittest.main()
