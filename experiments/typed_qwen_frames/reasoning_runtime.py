"""Matched experimental thinking-template override; shared defaults stay intact."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import time

from modelaccess.contract import Request, ProviderReply, FinishReason, Usage
from .runtime import FrameAdapter
from .reasoning_protocol import split_generated, ProtocolError

EXPERIMENT_VERSION = 'qwen-reasoning-ablation-v1'


class ReasoningFrameAdapter(FrameAdapter):
    def __init__(self, *, thinking, audit_path, audit_context=None):
        if type(thinking) is not bool:
            raise ValueError('thinking must be an explicit boolean')
        super().__init__()
        self.thinking = thinking
        self.audit_path = Path(audit_path)
        self.audit_context = dict(audit_context or {})

    def _audit(self, event, **values):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open('a') as stream:
            stream.write(json.dumps(dict(event=event, recordedAt=time.time(),
                experimentVersion=EXPERIMENT_VERSION, thinkingEnabled=self.thinking,
                frozenContext=self.audit_context, **values), allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def _generate(self, request, effective):
        if request.images or len(request.messages) != 1 or request.messages[0][0] != 'user':
            raise ValueError('Ablation accepts one text-only user message')
        if type(request.settings.max_output_tokens) is not int or not 1 <= request.settings.max_output_tokens <= 1000:
            raise ValueError('Ablation cannot exceed 1000 generated tokens')
        engine = self.load()
        tokenizer = engine.processor.tokenizer
        for marker, expected in (('<think>', 248068), ('</think>', 248069)):
            if tokenizer.encode(marker, add_special_tokens=False) != [expected]:
                raise ValueError('Pinned thought token protocol does not match tokenizer')
        base_kwargs = dict(engine.template_kwargs)
        if base_kwargs.get('enable_thinking') is not False:
            raise ValueError('Unexpected base template profile')
        kwargs = {**base_kwargs, 'enable_thinking': self.thinking}
        content = [{'type': 'text', 'text': request.messages[0][1]}]
        rendered = engine.processor.apply_chat_template(
            [{'role': 'user', 'content': content}], tokenize=False,
            add_generation_prompt=True, **kwargs)
        rendered_hash = hashlib.sha256(rendered.encode()).hexdigest()
        self._audit('generation_started', requestId=request.request_id,
            renderedInput=rendered, renderedInputSHA256=rendered_hash,
            baseTemplateKwargs=base_kwargs, effectiveTemplateKwargs=kwargs,
            maxGeneratedTokens=request.settings.max_output_tokens)
        inputs = engine.processor(text=[rendered], images=None, return_tensors='pt').to(engine.device)
        input_ids = inputs['input_ids'][0].cpu().tolist()
        input_hash = hashlib.sha256(json.dumps(input_ids, separators=(',', ':')).encode()).hexdigest()
        self._audit('input_prepared', requestId=request.request_id,
                    inputTokenIds=input_ids, inputTokenIdsSHA256=input_hash,
                    inputTokenCount=len(input_ids), renderedInputSHA256=rendered_hash)
        with engine.torch.inference_mode():
            output = engine.model.generate(**inputs, max_new_tokens=request.settings.max_output_tokens,
                                          do_sample=False)
        engine.torch.mps.synchronize()
        count = int(inputs['input_ids'].shape[1])
        ids = output[0, count:].cpu().tolist()
        eos = engine.model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos or [])
        terminal = ids[-1] if ids else None
        stopped = terminal in eos
        finish = (FinishReason.STOP if stopped else FinishReason.LENGTH
                  if len(ids) >= request.settings.max_output_tokens else FinishReason.OTHER)
        raw = engine.processor.batch_decode([ids], skip_special_tokens=False,
                                           clean_up_tokenization_spaces=False)[0]
        segment = None
        error = None
        final_text = ''
        try:
            segment = split_generated(ids, thinking=self.thinking, eos_ids=eos,
                                      max_tokens=request.settings.max_output_tokens)
            final_text = engine.processor.batch_decode([segment['finalTokenIds']],
                skip_special_tokens=False, clean_up_tokenization_spaces=False)[0]
            if not final_text.strip():
                raise ProtocolError('empty_decoded_final')
        except ProtocolError as exc:
            error = str(exc)
        metadata = {**self.run_metadata(), 'experimentVersion': EXPERIMENT_VERSION,
            'thinkingEnabled': self.thinking, 'baseTemplateKwargs': base_kwargs,
            'effectiveTemplateKwargs': kwargs, 'renderedInputSHA256': rendered_hash,
            'inputTokenIdsSHA256': input_hash,
            'rawGeneratedTokenIds': ids, 'rawDecodedText': raw,
            'terminalTokenId': terminal, 'eosTokenIds': eos, 'observedEOS': stopped,
            'segments': segment, 'protocolError': error,
            'fidelityVerified': False, 'reportCheckAllowed': False}
        usage = Usage(count, len(ids), None if segment is None else segment['reasoningTokenCount'], 0, 0)
        self._audit('generation_returned', requestId=request.request_id,
                    finishReason=finish.value, finalText=final_text, usage=asdict(usage), metadata=metadata)
        return ProviderReply(final_text, self.served_model,
            'observed_eos' if stopped else 'max_new_tokens' if finish == FinishReason.LENGTH
            else 'unverified_termination', finish, usage, metadata=metadata)

    def generate(self, request):
        result = super().generate(request)
        if result.metadata.get('protocolError'):
            result = replace(result, error='reasoning_protocol:' + result.metadata['protocolError'])
        return replace(result, effective_settings={**result.effective_settings,
                       'enable_thinking': self.thinking, 'experiment_version': EXPERIMENT_VERSION})

    def warmup(self, settings):
        result = self.review(Request('reasoning-warmup', (('user', 'Reply with the word ready.'),),
                                     replace(settings, max_output_tokens=128)))
        if not result.ok or result.finish_reason != FinishReason.STOP:
            raise RuntimeError('Matched ablation warmup failed observed completion/protocol')
        return dict(runtime=result.metadata, usage=asdict(result.usage),
                    finishReason=result.finish_reason.value, warmupOutputCap=128)
