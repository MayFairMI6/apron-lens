"""No model/decoder involved: exact protocol and accounting controls only."""
import unittest

from experiments.typed_qwen_frames.reasoning_protocol import (
    ProtocolError, THINK_START_ID as OPEN, THINK_END_ID as CLOSE, split_generated,
)

EOS = 999


class ProtocolTests(unittest.TestCase):
    def test_off_full_suffix_and_eos_accounted(self):
        self.assertEqual(split_generated([1, 2, EOS], False, [EOS]),
                         dict(finalTokenIds=[1, 2], reasoningTokenCount=0,
                              finalTokenCount=3, totalGeneratedTokens=3))

    def test_on_exact_suffix_close_and_eos_accounted(self):
        self.assertEqual(split_generated([1, 2, CLOSE, 3, 4, EOS], True, [EOS]),
                         dict(finalTokenIds=[3, 4], reasoningTokenCount=3,
                              finalTokenCount=3, totalGeneratedTokens=6))

    def test_empty_generated_reasoning_allowed_not_empty_final(self):
        out = split_generated([CLOSE, 1, EOS], True, [EOS])
        self.assertEqual(out['reasoningTokenCount'], 1)
        for ids, arm in [([CLOSE, EOS], True), ([EOS], False)]:
            with self.assertRaises(ProtocolError):
                split_generated(ids, arm, [EOS])

    def test_eos_at_frozen_cap_both_arms(self):
        for ids, arm in [([1] * 999 + [EOS], False), ([1] * 997 + [CLOSE, 2, EOS], True)]:
            result = split_generated(ids, arm, [EOS])
            self.assertEqual(result['totalGeneratedTokens'], 1000)
            self.assertEqual(result['reasoningTokenCount'] + result['finalTokenCount'], 1000)

    def test_over_cap_and_no_budget_increase(self):
        for ids, cap in [([1] * 1000 + [EOS], 1000), ([1, 2, EOS], 2), ([1, EOS], 1001),
                         ([1, EOS], 0), ([1, EOS], -1), ([1, EOS], True), ([1, EOS], 2.0)]:
            with self.assertRaises(ProtocolError):
                split_generated(ids, False, [EOS], cap)
        self.assertEqual(split_generated([1, EOS], False, [EOS], 2)['finalTokenCount'], 2)

    def test_missing_or_earlier_eos_rejects_without_suffix_recovery(self):
        for ids, arm in [([], False), ([1, 2], False), ([1, CLOSE, 2], True),
                         ([EOS, 1, EOS], False), ([EOS, CLOSE, 1, EOS], True),
                         ([1, 998, 2, EOS], False)]:
            with self.assertRaises(ProtocolError):
                split_generated(ids, arm, [EOS, 998])

    def test_on_missing_close_and_multiple_closes(self):
        for ids in [[1, 2, EOS], [CLOSE, 1, CLOSE, 2, EOS], [CLOSE, CLOSE, 1, EOS]]:
            with self.assertRaises(ProtocolError):
                split_generated(ids, True, [EOS])

    def test_no_generated_open_in_either_arm_anywhere(self):
        for arm in [False, True]:
            for ids in [[OPEN, CLOSE, 1, EOS], [1, CLOSE, OPEN, EOS], [1, OPEN, EOS]]:
                with self.assertRaises(ProtocolError):
                    split_generated(ids, arm, [EOS])

    def test_off_close_forbidden(self):
        for ids in [[CLOSE, 1, EOS], [1, CLOSE, EOS]]:
            with self.assertRaises(ProtocolError):
                split_generated(ids, False, [EOS])

    def test_strict_token_and_arm_types(self):
        for ids in [None, '1,999', [True, EOS], [-1, EOS], [1.0, EOS], [None, EOS]]:
            with self.assertRaises(ProtocolError):
                split_generated(ids, False, [EOS])
        for arm in [0, 1, 'true', None]:
            with self.assertRaises(ProtocolError):
                split_generated([1, EOS], arm, [EOS])

    def test_effective_eos_configuration_validation(self):
        for eos in [[], None, EOS, [True], [-1], [1.0], [CLOSE], [OPEN, EOS]]:
            with self.assertRaises(ProtocolError):
                split_generated([1, EOS], False, eos)
        self.assertEqual(split_generated([1, 998], False, {998, EOS})['finalTokenIds'], [1])

    def test_input_not_mutated_even_failure(self):
        ids = [1, CLOSE, 2, EOS]
        saved = list(ids)
        split_generated(ids, True, [EOS])
        self.assertEqual(ids, saved)
        with self.assertRaises(ProtocolError):
            split_generated(ids, False, [EOS])
        self.assertEqual(ids, saved)
        self.assertEqual(split_generated(tuple([1, EOS]), False, (EOS,))['finalTokenIds'], [1])

    def test_nonempty_token_suffix_not_claimed_nonempty_decoded_text(self):
        # Token 1 could decode to whitespace; caller separately checks decoded
        # final text and v6 parsing. The helper cannot infer token meanings.
        self.assertEqual(split_generated([CLOSE, 1, EOS], True, [EOS])['finalTokenIds'], [1])


if __name__ == '__main__':
    unittest.main()
