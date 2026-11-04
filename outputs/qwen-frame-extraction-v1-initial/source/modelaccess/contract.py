"""Narrow inference contract shared by ApronLens and the GenAI project.

The contract packages requests and reports what actually happened. It owns no
prompts, memory, validation, datasets, budgets or conversation state; each
consuming project keeps those itself.

Rules enforced here for every adapter:
- A missing capability raises UnsupportedCapability. Nothing is emulated and
  nothing falls back to another model or provider.
- Settings the provider ignores are reported, never silently dropped.
- The model the provider says it served must equal the configured model or an
  explicitly accepted snapshot; otherwise the result is marked as failed.
- A length stop with no visible output is a failure, not an empty answer.
- Values that change results (model, output cap, image size) have no defaults.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from modelaccess import __version__


class Operation(str, Enum):
    GENERATE = 'generate'
    SCORE_LABELS = 'score_labels'


class SchemaMode(str, Enum):
    STRICT = 'strict'        # provider enforces a JSON schema
    JSON_MODE = 'json_mode'  # provider promises JSON, not a schema
    NONE = 'none'            # plain text only


class FinishReason(str, Enum):
    STOP = 'stop'
    LENGTH = 'length'
    SAFETY = 'safety'
    REFUSAL = 'refusal'
    CANCELLED = 'cancelled'
    ERROR = 'error'
    OTHER = 'other'


class ModelAccessError(Exception):
    """Base error for contract violations."""


class UnsupportedCapability(ModelAccessError):
    """The adapter cannot perform the requested operation or setting."""


class InvalidRequest(ModelAccessError):
    """The request is missing a value that would otherwise be defaulted."""


@dataclass(frozen=True)
class Capabilities:
    operations: frozenset
    image_input: bool
    video_input: bool
    schema_mode: SchemaMode
    max_images: int
    reasoning_efforts: tuple = ()
    temperature: bool = True
    # 'verified' means checked against official documentation or a recorded
    # probe; unverified declarations must be confirmed before formal use.
    verified: bool = False
    source: str = ''


@dataclass(frozen=True)
class Settings:
    model: str
    max_output_tokens: int
    temperature: float | None = None
    reasoning_effort: str | None = None
    image_max_side: int | None = None
    # Dated snapshots the provider may report for this alias. Must be listed
    # explicitly; anything else is a model mismatch.
    accepted_returned_models: tuple = ()


@dataclass(frozen=True)
class ImageInput:
    data: bytes
    media_type: str
    capture_time: float | None = None


@dataclass(frozen=True)
class Request:
    request_id: str
    messages: tuple  # ((role, text), ...)
    settings: Settings
    images: tuple = ()
    schema: dict | None = None


@dataclass
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    image_tokens: int | None = None
    cached_input_tokens: int | None = None

    @property
    def complete(self) -> bool:
        return self.input_tokens is not None and self.output_tokens is not None


@dataclass
class Result:
    request_id: str
    provider: str
    configured_model: str
    returned_model: str | None
    text: str
    finish_reason: FinishReason
    raw_finish_reason: str | None
    usage: Usage
    latency_seconds: float
    effective_settings: dict
    ignored_settings: tuple
    library_version: str = __version__
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class ProviderReply:
    """What a concrete adapter returns before contract checks are applied."""
    text: str
    returned_model: str | None
    raw_finish_reason: str | None
    finish_reason: FinishReason
    usage: Usage
    metadata: dict = field(default_factory=dict)


class Adapter(ABC):
    provider: str = 'unknown'

    def __init__(self, capabilities: Capabilities):
        self.capabilities = capabilities

    # ---- public operations -------------------------------------------------
    def generate(self, request: Request) -> Result:
        self.require(Operation.GENERATE)
        self._check_inputs(request)
        effective, ignored = self.resolve_settings(request.settings)
        start = time.monotonic()
        try:
            reply = self._generate(request, effective)
        except ModelAccessError:
            raise
        except Exception as exc:  # transport/provider failure is reported, not hidden
            return Result(request.request_id, self.provider, request.settings.model, None, '',
                          FinishReason.ERROR, None, Usage(), time.monotonic() - start,
                          effective, ignored, error='provider_error:' + type(exc).__name__)
        result = Result(request.request_id, self.provider, request.settings.model,
                        reply.returned_model, reply.text, reply.finish_reason,
                        reply.raw_finish_reason, reply.usage, time.monotonic() - start,
                        effective, ignored, metadata=dict(reply.metadata))
        result.error = self.contract_error(request.settings, result)
        return result

    def score_labels(self, prompt: str, labels: tuple, settings: Settings, image: ImageInput | None = None):
        """Return {label: log-probability}. Only adapters declaring this may run it."""
        self.require(Operation.SCORE_LABELS)
        if image is not None:
            self._check_images((image,), settings)
        return self._score_labels(prompt, tuple(labels), settings, image)

    # ---- contract checks ---------------------------------------------------
    def require(self, operation: Operation):
        if operation not in self.capabilities.operations:
            raise UnsupportedCapability(f'{self.provider} does not support {operation.value}')

    def _check_images(self, images, settings):
        if not self.capabilities.image_input:
            raise UnsupportedCapability(f'{self.provider} does not accept images')
        if len(images) > self.capabilities.max_images:
            raise UnsupportedCapability(f'{self.provider} accepts at most {self.capabilities.max_images} images')
        if settings.image_max_side is None:
            raise InvalidRequest('image_max_side must be set explicitly when images are sent')

    def _check_inputs(self, request: Request):
        if not request.request_id:
            raise InvalidRequest('request_id is required')
        if request.settings.max_output_tokens <= 0:
            raise InvalidRequest('max_output_tokens must be positive')
        if request.images:
            self._check_images(request.images, request.settings)
        if request.schema is not None and self.capabilities.schema_mode is SchemaMode.NONE:
            raise UnsupportedCapability(f'{self.provider} cannot accept an output schema')

    def resolve_settings(self, settings: Settings):
        effective = {'model': settings.model, 'max_output_tokens': settings.max_output_tokens,
                     'image_max_side': settings.image_max_side}
        ignored = []
        if settings.temperature is not None:
            if self.capabilities.temperature:
                effective['temperature'] = settings.temperature
            else:
                ignored.append('temperature')
        if settings.reasoning_effort is not None:
            if settings.reasoning_effort not in self.capabilities.reasoning_efforts:
                raise UnsupportedCapability(
                    f'{self.provider} does not offer reasoning_effort={settings.reasoning_effort!r}')
            effective['reasoning_effort'] = self.map_effort(settings.reasoning_effort)
            effective['reasoning_effort_requested'] = settings.reasoning_effort
        return effective, tuple(ignored)

    def map_effort(self, effort: str) -> str:
        """Providers whose effort names differ override this; both values are logged."""
        return effort

    @staticmethod
    def contract_error(settings: Settings, result: Result) -> str | None:
        allowed = {settings.model, *settings.accepted_returned_models}
        if result.returned_model is None:
            return 'returned_model_missing'
        if result.returned_model not in allowed:
            return 'model_mismatch'
        if result.finish_reason is FinishReason.LENGTH and not result.text.strip():
            return 'empty_output_length'
        if result.finish_reason in (FinishReason.SAFETY, FinishReason.REFUSAL, FinishReason.ERROR):
            return 'finish_' + result.finish_reason.value
        return None

    # ---- implemented by concrete adapters ------------------------------------
    @abstractmethod
    def _generate(self, request: Request, effective: dict) -> ProviderReply: ...

    def _score_labels(self, prompt, labels, settings, image):
        raise UnsupportedCapability(f'{self.provider} does not support score_labels')
