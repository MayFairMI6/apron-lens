"""OpenAI Responses API adapter (official `openai` SDK, imported only when used).

- reasoning_effort maps to `reasoning.effort`; reasoning tokens are billed as output
  and reported separately when the provider returns them.
- Temperature is reported as ignored: reasoning models do not take sampling settings.
- Images are sent at the shared image_max_side with detail "high", so small props
  are not downsampled further by the provider.
- SDK retries are off (max_retries=0); retries are separate budgeted attempts.
Capabilities are unverified until a recorded probe confirms them.
"""
from modelaccess.contract import (Adapter, Capabilities, FinishReason, Operation, ProviderReply, SchemaMode,
                                  Usage)
from modelaccess.images import prepare_png

OPENAI_CAPABILITIES = Capabilities(
    operations=frozenset({Operation.GENERATE}), image_input=True, video_input=False, schema_mode=SchemaMode.NONE,
    max_images=4, reasoning_efforts=('none', 'low', 'medium', 'high', 'xhigh', 'max'), temperature=False,
    verified=False, source='https://developers.openai.com/api/docs/models')

_INCOMPLETE = {'max_output_tokens': FinishReason.LENGTH, 'content_filter': FinishReason.SAFETY}


class OpenAIAdapter(Adapter):
    provider = 'openai'

    def __init__(self, client=None, capabilities=OPENAI_CAPABILITIES):
        super().__init__(capabilities)
        self._client = client

    @property
    def client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(max_retries=0)
        return self._client

    def _generate(self, request, effective):
        items = [{'role': role, 'content': [{'type': 'input_text' if role == 'user' else 'output_text', 'text': text}]}
                 for role, text in request.messages]
        if request.images:  # images go before the text of the first user message
            first = next(i for i in items if i['role'] == 'user')
            first['content'][:0] = [{'type': 'input_image', 'detail': 'high', 'image_url':
                                     'data:image/png;base64,' + prepare_png(image, request.settings.image_max_side)[0]}
                                    for image in request.images]
        kwargs = dict(model=request.settings.model, input=items, max_output_tokens=request.settings.max_output_tokens)
        if 'reasoning_effort' in effective:
            kwargs['reasoning'] = {'effort': effective['reasoning_effort']}
        response = self.client.responses.create(**kwargs)
        refused = any(part.type == 'refusal' for item in response.output if item.type == 'message'
                      for part in item.content)
        if response.status == 'completed':
            finish, raw = (FinishReason.REFUSAL, 'refusal') if refused else (FinishReason.STOP, 'completed')
        elif response.status == 'incomplete':
            raw = getattr(response.incomplete_details, 'reason', None)
            finish = _INCOMPLETE.get(raw, FinishReason.OTHER)
        else:
            raw = response.status
            finish = {'failed': FinishReason.ERROR, 'cancelled': FinishReason.CANCELLED}.get(raw, FinishReason.OTHER)
        usage = response.usage
        cached = getattr(getattr(usage, 'input_tokens_details', None), 'cached_tokens', None) or 0
        reasoning = getattr(getattr(usage, 'output_tokens_details', None), 'reasoning_tokens', None)
        return ProviderReply(text=response.output_text or '', returned_model=response.model, raw_finish_reason=raw,
                             finish_reason=finish, usage=Usage(usage.input_tokens, usage.output_tokens, reasoning, None,
                                                               cached),
                             metadata={'responseId': response.id})
