"""Experimental text-only Qwen owner with observed terminal-token metadata.

No shared backbone, production adapter, weights or registry is changed.
"""
from modelaccess.local_backbone import LocalBackboneAdapter
from modelaccess.contract import Request, ProviderReply, FinishReason, Usage
from dataclasses import replace


class FrameAdapter(LocalBackboneAdapter):
    def __init__(self):
        super().__init__('qwen3.5-9b', profile='apronlens-v2-mps')

    def _generate(self, request, effective):
        if request.images or len(request.messages) != 1 or request.messages[0][0] != 'user':
            raise ValueError('Frame diagnostic accepts one text-only user message')
        engine = self.load()
        inputs = engine._inputs(request.messages[0][1], None)
        with engine.torch.inference_mode():
            output = engine.model.generate(**inputs,
                max_new_tokens=request.settings.max_output_tokens, do_sample=False)
        engine.torch.mps.synchronize()
        count = int(inputs['input_ids'].shape[1])
        ids = output[0, count:].cpu().tolist()
        eos = engine.model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos or [])
        terminal = ids[-1] if ids else None
        stopped = terminal in eos
        finish = (FinishReason.STOP if stopped else FinishReason.LENGTH
                  if len(ids) >= request.settings.max_output_tokens else FinishReason.OTHER)
        text = engine.processor.batch_decode(output[:, count:], skip_special_tokens=True)[0]
        return ProviderReply(text, self.served_model,
            'observed_eos' if stopped else 'max_new_tokens' if finish == FinishReason.LENGTH else 'unverified_termination',
            finish, Usage(count, len(ids), 0, None, 0),
            metadata={**self.run_metadata(), 'terminalTokenId': terminal,
                      'eosTokenIds': eos, 'observedEOS': stopped})

    def review(self, request):
        return self.generate(request)

    def warmup(self, settings):
        result = self.review(Request('frames-startup', (('user', 'Reply with the word ready.'),),
                                     replace(settings, max_output_tokens=16)))
        if not result.ok or result.finish_reason != FinishReason.STOP:
            raise RuntimeError('Frame model warmup did not finish with observed EOS')
        return dict(runtime=result.metadata, usage=vars(result.usage),
                    finishReason=result.finish_reason.value)
