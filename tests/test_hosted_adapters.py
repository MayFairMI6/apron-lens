"""Hosted adapters and budget enforcement with fake SDK clients: no network, no keys, no spend."""
import base64
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from PIL import Image

from modelaccess.anthropic_api import AnthropicAdapter
from modelaccess.contract import FinishReason, ImageInput, Request, Settings, UnsupportedCapability
from modelaccess.openai_api import OpenAIAdapter
from backend.conversation.hosted import BudgetedAdapter, estimate_run, load_rates, max_input_tokens, prepare
from backend.conversation.ledger import MICRO, BudgetExceeded, Ledger


def png(width=1344, height=1008):
    stream = io.BytesIO()
    Image.new('RGB', (width, height), (30, 40, 50)).save(stream, format='PNG')
    return stream.getvalue()


def decoded_size(b64):
    return Image.open(io.BytesIO(base64.b64decode(b64))).size


class Recorder:
    def __init__(self, response):
        self.response, self.calls = response, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def claude_reply(text='{"ok": true}', stop='end_turn', model='claude-sonnet-5-5', usage=(1000, 200), **extra):
    response = NS(content=[NS(type='thinking', thinking=''), NS(type='text', text=text)], stop_reason=stop,
                  model=model, usage=NS(input_tokens=usage[0], output_tokens=usage[1], cache_read_input_tokens=0),
                  stop_details=extra.get('stop_details'))
    response._request_id = 'req_test'
    return response


def openai_reply(text='{"ok": true}', status='completed', model='gpt-6.1-terra', parts=('output_text',),
                 incomplete=None):
    return NS(id='resp_test', status=status, model=model, output_text=text,
              incomplete_details=NS(reason=incomplete) if incomplete else None,
              output=[NS(type='message', content=[NS(type=p) for p in parts])],
              usage=NS(input_tokens=900, output_tokens=150, input_tokens_details=NS(cached_tokens=100),
                       output_tokens_details=NS(reasoning_tokens=40)))


def request(model, images=0, effort=None, temperature=None, max_output=4000):
    return Request('r1', (('user', 'Which stand?'),),
                   Settings(model, max_output, temperature=temperature, reasoning_effort=effort, image_max_side=672),
                   tuple(ImageInput(png(), 'image/png', 24) for _ in range(images)))


class Anthropic(unittest.TestCase):
    def adapter(self, response):
        recorder = Recorder(response)
        return AnthropicAdapter(client=NS(messages=recorder)), recorder

    def test_request_shape_and_text(self):
        adapter, recorder = self.adapter(claude_reply())
        result = adapter.generate(request('claude-sonnet-5-5', images=1, effort='low', temperature=0.0))
        sent = recorder.calls[0]
        self.assertEqual((sent['model'], sent['max_tokens'], sent['output_config']), ('claude-sonnet-5-5', 4000, {'effort': 'low'}))
        self.assertNotIn('thinking', sent)
        self.assertNotIn('temperature', sent)
        image, text = sent['messages'][0]['content']
        self.assertEqual((image['type'], image['source']['media_type']), ('image', 'image/png'))
        self.assertEqual(decoded_size(image['source']['data']), (672, 504))
        self.assertEqual(text, {'type': 'text', 'text': 'Which stand?'})
        self.assertTrue(result.ok)
        self.assertEqual(result.text, '{"ok": true}')  # thinking blocks are not answer text
        self.assertEqual(result.ignored_settings, ('temperature',))
        self.assertEqual((result.usage.input_tokens, result.usage.output_tokens), (1000, 200))

    def test_refusal_and_empty_length_are_failures(self):
        adapter, _ = self.adapter(claude_reply(text='', stop='refusal', stop_details=NS(category='cyber')))
        result = adapter.generate(request('claude-sonnet-5-5'))
        self.assertEqual((result.finish_reason, result.error), (FinishReason.REFUSAL, 'finish_refusal'))
        self.assertEqual(result.metadata['refusalCategory'], 'cyber')
        adapter, _ = self.adapter(claude_reply(text='', stop='max_tokens'))
        self.assertEqual(adapter.generate(request('claude-sonnet-5-5')).error, 'empty_output_length')

    def test_served_model_must_match(self):
        adapter, _ = self.adapter(claude_reply(model='claude-opus-4-8'))
        self.assertEqual(adapter.generate(request('claude-sonnet-5-5')).error, 'model_mismatch')


class OpenAI(unittest.TestCase):
    def adapter(self, response):
        recorder = Recorder(response)
        return OpenAIAdapter(client=NS(responses=recorder)), recorder

    def test_request_shape_and_usage(self):
        adapter, recorder = self.adapter(openai_reply())
        result = adapter.generate(request('gpt-6.1-terra', images=1, effort='low'))
        sent = recorder.calls[0]
        self.assertEqual((sent['model'], sent['max_output_tokens'], sent['reasoning']), ('gpt-6.1-terra', 4000, {'effort': 'low'}))
        image, text = sent['input'][0]['content']
        self.assertEqual((image['type'], image['detail']), ('input_image', 'high'))
        self.assertEqual(decoded_size(image['image_url'].split(',', 1)[1]), (672, 504))
        self.assertEqual(text, {'type': 'input_text', 'text': 'Which stand?'})
        self.assertTrue(result.ok)
        self.assertEqual((result.usage.cached_input_tokens, result.usage.reasoning_tokens), (100, 40))

    def test_incomplete_and_refusal(self):
        adapter, _ = self.adapter(openai_reply(text='', status='incomplete', incomplete='max_output_tokens'))
        self.assertEqual(adapter.generate(request('gpt-6.1-terra')).error, 'empty_output_length')
        adapter, _ = self.adapter(openai_reply(text='', parts=('refusal',)))
        self.assertEqual(adapter.generate(request('gpt-6.1-terra')).error, 'finish_refusal')


class Budget(unittest.TestCase):
    def setUp(self):
        self.rates = load_rates()
        self.path = Path(tempfile.mkdtemp()) / 'ledger.sqlite'

    def budgeted(self, response, session_limit=5.0):
        recorder = Recorder(response)
        ledger = Ledger(self.path, session_limit=session_limit)
        return BudgetedAdapter(AnthropicAdapter(client=NS(messages=recorder)), ledger, self.rates, 'screening',
                               session_id='s1'), recorder, ledger

    def test_reserve_then_reconcile_to_actual_cost(self):
        adapter, _, ledger = self.budgeted(claude_reply(usage=(1000, 200)))
        result = adapter.generate(request('claude-sonnet-5-5'))
        self.assertGreater(result.metadata['reservedMicroUsd'], 0)
        self.assertEqual(ledger.committed(), 1000 * 2 + 200 * 10)  # $2 / $10 per MTok, in micro-dollars

    def test_each_run_gets_its_own_reservation_for_reused_request_ids(self):
        first, _, ledger = self.budgeted(claude_reply(usage=(1000, 200)))
        second, recorder, _ = self.budgeted(claude_reply(usage=(1000, 200)))
        first.generate(request('claude-sonnet-5-5'))
        second.generate(request('claude-sonnet-5-5'))  # same request ID 'r1', a separate run
        self.assertEqual(ledger.committed(), 2 * (1000 * 2 + 200 * 10))
        tight, recorder, _ = self.budgeted(claude_reply(), session_limit=0.000001)
        with self.assertRaises(BudgetExceeded):  # a reused ID is still budget-checked
            tight.generate(request('claude-sonnet-5-5'))
        self.assertEqual(recorder.calls, [])

    def test_refused_reservation_never_calls_the_provider(self):
        adapter, recorder, _ = self.budgeted(claude_reply(), session_limit=0.000001)
        with self.assertRaises(BudgetExceeded):
            adapter.generate(request('claude-sonnet-5-5'))
        self.assertEqual(recorder.calls, [])

    def test_missing_usage_keeps_the_reservation(self):
        adapter, _, ledger = self.budgeted(ConnectionError('reset'))
        result = adapter.generate(request('claude-sonnet-5-5'))
        self.assertEqual(result.error, 'provider_error:ConnectionError')
        self.assertEqual(ledger.committed(), result.metadata['reservedMicroUsd'])

    def test_contract_error_before_sending_releases_the_reservation(self):
        adapter, recorder, ledger = self.budgeted(claude_reply())
        with self.assertRaises(UnsupportedCapability):
            adapter.generate(request('claude-sonnet-5-5', images=5))  # max_images is 4
        self.assertEqual((recorder.calls, ledger.committed()), ([], 0))

    def test_reservation_bounds_the_request(self):
        r = request('claude-sonnet-5-5', images=1)
        self.assertGreaterEqual(max_input_tokens(r), 3000 + len('Which stand?') // 2)

    def test_estimate_counts_requests_without_calling_a_model(self):
        def run(adapter):
            for _ in range(3):
                adapter.generate(request('claude-sonnet-5-5'))
        count, usd = estimate_run(run, AnthropicAdapter().capabilities, self.rates, 'claude-sonnet-5-5')
        one = self.rates.max_cost_micro('claude-sonnet-5-5', __import__('datetime').date.today(),
                                        max_input_tokens(request('claude-sonnet-5-5')), 4000)
        self.assertEqual((count, usd), (3, 3 * one / MICRO))

    def test_paid_run_needs_confirmation_and_a_cap(self):
        def run(adapter, model):
            adapter.generate(request(model))
        args = dict(estimate_only=False, max_spend=5.0, session_id='s')
        with self.assertRaises(SystemExit):
            prepare('anthropic', 'claude-sonnet-5-5', None, run, confirm_spend=False, **args)
        with self.assertRaises(SystemExit):
            prepare('anthropic', 'claude-sonnet-5-5', None, run, confirm_spend=True,
                    **dict(args, max_spend=0.0001))
        adapter, model = prepare('anthropic', 'claude-sonnet-5-5', None, run, confirm_spend=False,
                                 **dict(args, estimate_only=True))
        self.assertIsNone(adapter)


if __name__ == '__main__':
    unittest.main()
