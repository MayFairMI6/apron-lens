"""Scripted adapter for CI contract and state-transition tests. Makes no network calls."""
from modelaccess.contract import (Adapter, Capabilities, FinishReason, Operation,
                                  ProviderReply, SchemaMode, Usage)


def mock_capabilities(**overrides):
    values = dict(operations=frozenset({Operation.GENERATE}), image_input=True, video_input=False,
                  schema_mode=SchemaMode.STRICT, max_images=4, reasoning_efforts=('low', 'medium'),
                  temperature=True, verified=True, source='mock')
    values.update(overrides)
    return Capabilities(**values)


class MockAdapter(Adapter):
    provider = 'mock'

    def __init__(self, replies, capabilities=None):
        super().__init__(capabilities or mock_capabilities())
        self.replies = list(replies)
        self.calls = []

    def _generate(self, request, effective):
        self.calls.append((request, effective))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, ProviderReply):
            return reply
        return ProviderReply(text=reply, returned_model=request.settings.model, raw_finish_reason='stop',
                             finish_reason=FinishReason.STOP, usage=Usage(100, 20, 0, 0, 0))
