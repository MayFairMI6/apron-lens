"""Killable typed-review service; classification is not token generation.

The ordinary assistant keeps its own unchanged generation adapter. This owner
uses its lifecycle and deadlines but validates a distinct classification reply.
"""
from dataclasses import asdict, dataclass
import json
import math
import time
from pathlib import Path
from backend.training_worker import IsolatedTrainingAdapter
from backend.training_assessment import validate_review

@dataclass(frozen=True)
class ReviewRequest:
    request_id: str
    fingerprint: str
    payload: dict

@dataclass
class ReviewOutcome:
    request_id: str
    fingerprint: str
    completion: str
    review: dict | None
    model_id: str
    model_revision: str
    policy_version: str
    elapsed_seconds: float
    audit: dict
    error: str | None = None

    @property
    def ok(self):
        return self.completion == 'completed' and self.error is None

class IsolatedReviewService(IsolatedTrainingAdapter):
    """Operation-specific validation; never manufactures EOS or token usage."""
    def __init__(self, factory, served_model, *, model_revision, policy_version, **kwargs):
        super().__init__(factory, served_model, **kwargs)
        self.model_revision = model_revision
        self.policy_version = policy_version

    def _validate_result(self, value, request):
        if not isinstance(value, ReviewOutcome):
            raise ValueError('Invalid classification outcome')
        json.dumps(asdict(value), allow_nan=False)
        if value.request_id != request.request_id or value.fingerprint != request.fingerprint:
            raise ValueError('Classification context mismatch')
        if value.model_id != self.served_model or value.model_revision != self.model_revision:
            raise ValueError('Classification model mismatch')
        if value.completion not in ('completed', 'failed', 'timed_out'):
            raise ValueError('Invalid classification completion')
        if (value.policy_version != self.policy_version or not isinstance(value.audit, dict)
                or type(value.elapsed_seconds) not in (int, float)
                or not math.isfinite(value.elapsed_seconds) or value.elapsed_seconds < 0
                or (value.completion == 'completed' and value.error is not None)
                or (value.completion != 'completed' and not isinstance(value.error, str))):
            raise ValueError('Invalid classification metadata')
        if value.ok:
            validate_review(json.dumps(value.review), request.payload)
        elif value.review is not None:
            raise ValueError('Failed classification must not expose a review')
        return value

    def _runtime_failed(self, value):
        return not value.ok

    def _failure(self, request, error, started):
        return ReviewOutcome(request.request_id, request.fingerprint,
            'timed_out' if 'Timeout' in error else 'failed', None,
            self.served_model, '', '', time.monotonic()-started,
            {'workerStatus': self.status}, error)


def generate_semantic_review(service, settings, context, audit_path):
    """Preserve actual classification evidence; failure never substitutes feedback."""
    payload = json.loads(context.payload_json)
    request = ReviewRequest('typed-'+context.run_id+'-'+context.action_id,
                            context.fingerprint, payload)
    started = time.monotonic()
    outcome = None
    accepted = None
    error = None
    try:
        outcome = service.review(request)
        if not outcome.ok:
            raise ValueError(outcome.error or 'classification unavailable')
        accepted = validate_review(json.dumps(outcome.review), payload)
    except Exception as exc:
        error = type(exc).__name__+': '+str(exc)
    finally:
        if audit_path:
            path = Path(audit_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a') as stream:
                stream.write(json.dumps(dict(recordVersion=2, event='typed_review_classification',
                    runId=context.run_id, revision=context.revision,
                    checkpointId=context.checkpoint_id, actionId=context.action_id,
                    fingerprint=context.fingerprint, payload=payload,
                    classificationOutcome=None if outcome is None else asdict(outcome),
                    elapsedSeconds=time.monotonic()-started,
                    contractAccepted=accepted is not None, error=error,
                    recordedAt=time.time()), ensure_ascii=False)+'\n')
    return accepted, error
