"""Anthropic Messages API adapter (official `anthropic` SDK, imported only when used).

Contract notes for current Claude models:
- Thinking is always on and cannot be disabled; depth is set only through
  output_config.effort, so reasoning_effort maps there and `thinking` is omitted.
  Thinking blocks are billed as output and are not returned as answer text.
- Sampling parameters are rejected by the API, so temperature is reported as ignored.
- Server-side refusal fallbacks are deliberately not enabled: the contract forbids
  serving a different model, so a refusal is reported as finish_refusal.
- SDK retries are off (max_retries=0). Each retry is a separate, separately budgeted
  attempt chosen by the caller.
Capabilities are unverified until a recorded probe confirms them.
"""
from modelaccess.contract import (Adapter, Capabilities, FinishReason, Operation, ProviderReply, SchemaMode,
                                  Usage)
from modelaccess.images import prepare_png

ANTHROPIC_CAPABILITIES = Capabilities(
    operations=frozenset({Operation.GENERATE}), image_input=True, video_input=False, schema_mode=SchemaMode.NONE,
    max_images=4, reasoning_efforts=('low', 'medium', 'high', 'xhigh', 'max'), temperature=False, verified=False,
    source='https://platform.claude.com/docs/en/models/overview')

_FINISH = {'end_turn': FinishReason.STOP, 'stop_sequence': FinishReason.STOP,
           'max_tokens': FinishReason.LENGTH, 'refusal': FinishReason.REFUSAL}


class AnthropicAdapter(Adapter):
    provider = 'anthropic'

    def __init__(self, client=None, capabilities=ANTHROPIC_CAPABILITIES):
        super().__init__(capabilities)
        self._client = client

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(max_retries=0)
        return self._client

    def _generate(self, request, effective):
        messages = [{'role': role, 'content': text} for role, text in request.messages]
        if request.images:  # images go before the text of the first user message
            first = next(m for m in messages if m['role'] == 'user')
            first['content'] = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png',
                                                             'data': prepare_png(image, request.settings.image_max_side)[0]}}
                                for image in request.images] + [{'type': 'text', 'text': first['content']}]
        kwargs = dict(model=request.settings.model, max_tokens=request.settings.max_output_tokens, messages=messages)
        if 'reasoning_effort' in effective:
            kwargs['output_config'] = {'effort': effective['reasoning_effort']}
        response = self.client.messages.create(**kwargs)
        text = ''.join(block.text for block in response.content if block.type == 'text')
        usage = response.usage
        metadata = {'requestId': getattr(response, '_request_id', None)}
        if response.stop_reason == 'refusal' and getattr(response, 'stop_details', None):
            metadata['refusalCategory'] = response.stop_details.category
        return ProviderReply(text=text, returned_model=response.model, raw_finish_reason=response.stop_reason,
                             finish_reason=_FINISH.get(response.stop_reason, FinishReason.OTHER),
                             usage=Usage(usage.input_tokens, usage.output_tokens, None, None,
                                         getattr(usage, 'cache_read_input_tokens', None) or 0),
                             metadata=metadata)
