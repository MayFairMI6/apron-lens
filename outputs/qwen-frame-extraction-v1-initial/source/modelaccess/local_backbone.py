"""Local adapter: the shared inference contract over a frozen backbone engine.

Weights, the model registry, revision checks and loading belong to the shared
backbone (backbone/). This adapter only maps the contract onto a backbone
engine created with an explicit runtime profile or explicit device, dtype and
attention values. It never chooses them and never falls back. Third-party
weights and frameworks are not part of either package.

The backbone engine decodes greedily, so a requested temperature is reported
as ignored rather than applied.
"""
from modelaccess.contract import (Adapter, Capabilities, FinishReason, InvalidRequest, ModelAccessError,
                                  Operation, ProviderReply, SchemaMode, Usage)

DEVICES = ('mps', 'cuda', 'cpu')
DTYPES = ('float16', 'bfloat16', 'float32')
ATTENTION = ('eager', 'sdpa')

LOCAL_BACKBONE_CAPABILITIES = Capabilities(
    operations=frozenset({Operation.GENERATE, Operation.SCORE_LABELS}),
    image_input=True, video_input=False, schema_mode=SchemaMode.NONE, max_images=1,
    reasoning_efforts=(), temperature=False, verified=True,
    source='Shared backbone engine; greedy decoding; label scoring reads next-token log-probabilities.')


class LocalBackboneAdapter(Adapter):
    provider = 'local-backbone'

    def __init__(self, model_name, *, profile=None, device=None, dtype=None, attn_implementation=None,
                 engine_factory=None):
        super().__init__(LOCAL_BACKBONE_CAPABILITIES)
        from backbone import expected_manifest, load_engine, runtime_profile
        explicit = (device, dtype, attn_implementation)
        if profile is not None:
            if any(v is not None for v in explicit):
                raise InvalidRequest('give a runtime profile or explicit runtime values, not both')
            runtime = runtime_profile(profile)
        elif any(v is None for v in explicit):
            raise InvalidRequest('a runtime profile or device, dtype and attn_implementation are required')
        else:
            runtime = dict(device=device, dtype=dtype, attn_implementation=attn_implementation)
        if runtime['device'] not in DEVICES or runtime['dtype'] not in DTYPES or runtime['attn_implementation'] not in ATTENTION:
            raise InvalidRequest(f'unsupported runtime {runtime}')
        self.model_name, self.profile, self.runtime = model_name, profile, runtime
        self.expected = expected_manifest(model_name)
        self.served_model = f"{self.expected['model_id']}@{self.expected['revision']}"
        self._factory = engine_factory or load_engine
        self._engine = None

    def load(self):
        if self._engine is None:
            engine = self._factory(self.model_name, **self.runtime)
            if engine.manifest != self.expected:
                raise ModelAccessError('loaded engine does not carry the pinned model revision')
            self._engine = engine
        return self._engine

    def run_metadata(self):
        meta = dict(model=self.served_model, modelName=self.model_name, runtimeProfile=self.profile, **self.runtime)
        if self._engine is not None:
            meta['engineRuntime'] = dict(getattr(self._engine, 'runtime', {}))
        return meta

    @staticmethod
    def _image(image, max_side):
        if image is None:
            return None
        import io
        from PIL import Image
        pil = Image.open(io.BytesIO(image.data)).convert('RGB')
        pil.thumbnail((max_side, max_side))
        return pil

    def _generate(self, request, effective):
        if len(request.messages) != 1 or request.messages[0][0] != 'user':
            raise InvalidRequest('the local backbone adapter accepts exactly one user message')
        engine = self.load()
        image = self._image(request.images[0] if request.images else None, request.settings.image_max_side)
        text, input_tokens, output_tokens = engine.generate(request.messages[0][1], image,
                                                            max_new_tokens=request.settings.max_output_tokens)
        finish = FinishReason.LENGTH if output_tokens >= request.settings.max_output_tokens else FinishReason.STOP
        return ProviderReply(text=text, returned_model=self.served_model, raw_finish_reason=finish.value,
                             finish_reason=finish, usage=Usage(input_tokens, output_tokens, 0, None, 0),
                             metadata=self.run_metadata())

    def _score_labels(self, prompt, labels, settings, image):
        engine = self.load()
        scores, _ = engine.score_labels(prompt, self._image(image, settings.image_max_side), labels)
        return scores
