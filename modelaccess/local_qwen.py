"""Local Qwen2.5-VL adapter with explicit device, dtype and attention settings.

Third-party model weights (Qwen/Qwen2.5-VL-3B-Instruct) and frameworks are not
part of this library. This adapter only packages calls to them.

Unlike backend/server.py (frozen for the V2 evaluation), nothing here is
auto-selected: MPS fp16, CUDA bf16 and CPU fp32 can flip near-zero label
margins, so each run must state its device and dtype and record them. If the
requested device is unavailable the adapter fails rather than falling back.

Dependencies (torch, transformers) are imported lazily and are not pinned by
this library; each consuming project's own lock file decides their versions.
"""
from modelaccess.contract import (Adapter, Capabilities, FinishReason, InvalidRequest,
                                  ModelAccessError, Operation, ProviderReply, SchemaMode, Usage)

DEVICES = ('mps', 'cuda', 'cpu')
DTYPES = ('float16', 'bfloat16', 'float32')

LOCAL_QWEN_CAPABILITIES = Capabilities(
    operations=frozenset({Operation.GENERATE, Operation.SCORE_LABELS}),
    image_input=True, video_input=False, schema_mode=SchemaMode.NONE, max_images=1,
    reasoning_efforts=(), temperature=True, verified=True,
    source='Local Transformers runtime; label scoring reads next-token log-probabilities.')


class LocalQwenAdapter(Adapter):
    provider = 'local-qwen'

    def __init__(self, model_path, model_id, revision, device, dtype, attn_implementation):
        super().__init__(LOCAL_QWEN_CAPABILITIES)
        if device not in DEVICES:
            raise InvalidRequest(f'device must be one of {DEVICES}')
        if dtype not in DTYPES:
            raise InvalidRequest(f'dtype must be one of {DTYPES}')
        if not attn_implementation:
            raise InvalidRequest('attn_implementation must be set explicitly')
        if not revision:
            raise InvalidRequest('a pinned model revision is required')
        self.model_path, self.model_id, self.revision = model_path, model_id, revision
        self.device, self.dtype_name, self.attn_implementation = device, dtype, attn_implementation
        self.served_model = f'{model_id}@{revision}'
        self._model = self._processor = self._torch = None

    def run_metadata(self):
        meta = dict(device=self.device, dtype=self.dtype_name, attn_implementation=self.attn_implementation,
                    model=self.served_model)
        if self._torch is not None:
            import transformers
            meta.update(torch=self._torch.__version__, transformers=transformers.__version__)
        return meta

    def load(self):
        if self._model is not None:
            return
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        available = {'cpu': True, 'mps': torch.backends.mps.is_available(), 'cuda': torch.cuda.is_available()}
        if not available[self.device]:
            raise ModelAccessError(f'requested device {self.device} is unavailable; no fallback is applied')
        self._torch = torch
        self._dtype = getattr(torch, self.dtype_name)
        self._processor = AutoProcessor.from_pretrained(self.model_path, local_files_only=True, use_fast=False)
        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path, dtype=self._dtype, attn_implementation=self.attn_implementation,
            local_files_only=True).to(self.device).eval()

    def _inputs(self, prompt, image, image_max_side):
        self.load()
        pil = None
        if image is not None:
            import io
            from PIL import Image
            pil = Image.open(io.BytesIO(image.data)).convert('RGB')
            pil.thumbnail((image_max_side, image_max_side))
        content = ([{'type': 'image'}] if pil is not None else []) + [{'type': 'text', 'text': prompt}]
        text = self._processor.apply_chat_template([{'role': 'user', 'content': content}],
                                                   tokenize=False, add_generation_prompt=True)
        inputs = self._processor(text=[text], images=[pil] if pil is not None else None,
                                 return_tensors='pt').to(self.device)
        if 'pixel_values' in inputs:
            inputs['pixel_values'] = inputs['pixel_values'].to(self._dtype)
        return inputs

    def _generate(self, request, effective):
        if len(request.messages) != 1 or request.messages[0][0] != 'user':
            raise InvalidRequest('local Qwen adapter accepts exactly one user message')
        image = request.images[0] if request.images else None
        inputs = self._inputs(request.messages[0][1], image, request.settings.image_max_side)
        sample = request.settings.temperature not in (None, 0)
        kwargs = dict(max_new_tokens=request.settings.max_output_tokens, do_sample=sample)
        if sample:
            kwargs['temperature'] = request.settings.temperature
        with self._torch.inference_mode():
            output = self._model.generate(**inputs, **kwargs)
        count = inputs['input_ids'].shape[1]
        produced = int(output.shape[1] - count)
        text = self._processor.batch_decode(output[:, count:], skip_special_tokens=True)[0]
        finish = FinishReason.LENGTH if produced >= request.settings.max_output_tokens else FinishReason.STOP
        return ProviderReply(text=text, returned_model=self.served_model, raw_finish_reason=finish.value,
                             finish_reason=finish, usage=Usage(int(count), produced, 0, None, 0),
                             metadata=self.run_metadata())

    def _score_labels(self, prompt, labels, settings, image):
        inputs = self._inputs(prompt, image, settings.image_max_side)
        token_ids = {label: self._processor.tokenizer.encode(label, add_special_tokens=False) for label in labels}
        if any(len(ids) != 1 for ids in token_ids.values()):
            raise InvalidRequest('decision labels must each be one token')
        with self._torch.inference_mode():
            logits = self._model(**inputs, logits_to_keep=1, use_cache=False).logits[0, -1].float()
            scores = self._torch.log_softmax(logits, dim=-1)
        return {label: float(scores[ids[0]].item()) for label, ids in token_ids.items()}
