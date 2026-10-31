"""Hosted-model access for ApronLens runs: adapter choice and budget enforcement.

Every hosted call goes through BudgetedAdapter, which reserves a conservative
maximum in the ledger before the call (input estimated high, all of it at the
uncached rate, plus the full output cap) and reconciles it with the provider's
reported usage afterwards. A reservation the ledger refuses raises before any
network call, so nothing is spent past the total, purpose or session limit.

estimate_run prices a run without calling any model: a capturing adapter
records each request the run would send, and the sum of their maximum
reservations is reported. Scripts show this figure and require an explicit
confirmation before a paid run.
"""
import datetime as dt
import math
import uuid
from pathlib import Path

from modelaccess.contract import FinishReason, ModelAccessError, ProviderReply, Usage
from modelaccess.mock import MockAdapter
from backend.conversation.ledger import Ledger, RateTable

ROOT = Path(__file__).resolve().parents[2]
RATES_PATH = ROOT / 'config/hosted-models.json'
LEDGER_PATH = ROOT / 'work/api-ledger.sqlite'
HOSTED_PROVIDERS = ('anthropic', 'openai')
CHARS_PER_TOKEN_FLOOR = 2       # real prompts run near 4 characters per token; 2 over-reserves
IMAGE_TOKEN_BOUND = 3000        # per image at image_max_side 672, well above provider counts
TOKEN_OVERHEAD = 200            # message framing


def max_input_tokens(request):
    text = sum(len(content) for _, content in request.messages)
    return math.ceil(text / CHARS_PER_TOKEN_FLOOR) + IMAGE_TOKEN_BOUND * len(request.images) + TOKEN_OVERHEAD


def make_adapter(provider, model=None, profile=None):
    """Return (adapter, configured model name)."""
    if provider == 'local':
        from modelaccess.local_backbone import LocalBackboneAdapter
        adapter = LocalBackboneAdapter(model, profile=profile)
        return adapter, adapter.served_model
    if provider == 'anthropic':
        from modelaccess.anthropic_api import AnthropicAdapter
        return AnthropicAdapter(), model
    if provider == 'openai':
        from modelaccess.openai_api import OpenAIAdapter
        return OpenAIAdapter(), model
    raise ValueError(f'Unknown provider {provider}')


class BudgetedAdapter:
    """Wraps a hosted adapter so each call is reserved and reconciled in the ledger."""

    def __init__(self, adapter, ledger, rates, purpose, session_id=None, today=None):
        self.adapter, self.ledger, self.rates = adapter, ledger, rates
        self.purpose, self.session_id = purpose, session_id
        self.today = today or dt.date.today()
        self.provider, self.capabilities = adapter.provider, adapter.capabilities
        # The ledger deduplicates by (request ID, attempt) across all runs, and scripts reuse
        # fixed request IDs, so reservation IDs are prefixed with a run ID unique to this adapter.
        self.run_id = f'{session_id or "run"}:{uuid.uuid4().hex}'
        self.attempts = {}

    def generate(self, request):
        model = request.settings.model
        reserve = self.rates.max_cost_micro(model, self.today, max_input_tokens(request),
                                            request.settings.max_output_tokens)
        attempt = self.attempts[request.request_id] = self.attempts.get(request.request_id, 0) + 1
        reservation = self.ledger.reserve(f'{self.run_id}:{request.request_id}', attempt, self.purpose, model, reserve,
                                          session_id=self.session_id)
        try:
            result = self.adapter.generate(request)
        except ModelAccessError:
            # Contract checks run before anything is sent, so nothing can be billed.
            # Transport and provider failures do not raise: they return a failed result
            # with incomplete usage, and the full reservation is kept below.
            self.ledger.reconcile(reservation, 0)
            raise
        usage = result.usage
        if usage.complete:
            self.ledger.reconcile(reservation, self.rates.actual_cost_micro(
                model, self.today, dict(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                                        cached_input_tokens=usage.cached_input_tokens or 0)))
        else:
            self.ledger.reconcile(reservation, None)
        result.metadata['reservedMicroUsd'] = reserve
        return result


def open_ledger(path=LEDGER_PATH, session_limit=None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return Ledger(path, session_limit=session_limit)


class _Capture(MockAdapter):
    """Records requests and answers each with empty text; never calls a model."""

    def __init__(self, provider_capabilities):
        super().__init__([], provider_capabilities)

    def _generate(self, request, effective):
        self.calls.append((request, effective))
        return ProviderReply(text='', returned_model=request.settings.model, raw_finish_reason='stop',
                             finish_reason=FinishReason.STOP, usage=Usage(0, 0, 0, 0, 0))


def estimate_run(run, capabilities, rates, model, today=None):
    """Call run(adapter) with a capturing adapter and return (requests, max reservation in USD).

    The run sees empty replies, so later prompts can be slightly shorter than in
    a real run (no stored previous answers); the per-request bound covers that.
    """
    capture = _Capture(capabilities)
    run(capture)
    today = today or dt.date.today()
    total = sum(rates.max_cost_micro(model, today, max_input_tokens(request), request.settings.max_output_tokens)
                for request, _ in capture.calls)
    return len(capture.calls), total / 1_000_000


def load_rates(path=RATES_PATH):
    return RateTable.load(path)


def prepare(provider, model, profile, run, *, estimate_only, confirm_spend, max_spend, session_id,
            purpose='screening'):
    """Return (adapter or None, configured model) for a script run.

    run(adapter, model) performs the run. For a hosted provider the run is first
    priced with estimate_run; it starts only with confirm_spend, within max_spend,
    and through a BudgetedAdapter whose ledger session limit is max_spend.
    """
    if provider == 'local' and not profile:
        raise SystemExit('--profile is required for the local provider, e.g. --profile apronlens-v2-mps')
    adapter, served = make_adapter(provider, model, profile)
    if provider == 'local':
        if estimate_only:
            print('Local models make no paid calls.')
            return None, served
        adapter.load()
        return adapter, served
    rates = load_rates()
    count, usd = estimate_run(lambda capture: run(capture, served), adapter.capabilities, rates, served)
    print(f'{provider} {served}: {count} requests, maximum reservation ${usd:.2f} '
          '(all input at the uncached rate, full output cap; actual cost is lower).', flush=True)
    if estimate_only:
        return None, served
    if not confirm_spend:
        raise SystemExit('This run makes paid calls. After approval, rerun with --confirm-spend.')
    if usd > max_spend:
        raise SystemExit(f'Maximum reservation ${usd:.2f} exceeds --max-spend ${max_spend:.2f}.')
    return BudgetedAdapter(adapter, open_ledger(session_limit=max_spend), rates, purpose, session_id), served


def add_arguments(parser, default_model):
    parser.add_argument('--provider', default='local', choices=('local',) + HOSTED_PROVIDERS)
    parser.add_argument('--model', default=default_model)
    parser.add_argument('--profile', help='Runtime profile from backbone/models.json (local provider)')
    parser.add_argument('--reasoning-effort', help='Hosted providers only, e.g. low or medium')
    parser.add_argument('--estimate-only', action='store_true', help='Price the run without calling any model')
    parser.add_argument('--confirm-spend', action='store_true', help='Required for a paid hosted run')
    parser.add_argument('--max-spend', type=float, default=5.0, help='USD cap for this run (ledger session limit)')
