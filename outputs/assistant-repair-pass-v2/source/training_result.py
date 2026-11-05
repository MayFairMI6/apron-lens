"""Training-only completion checks; frozen shared inference contract is unchanged."""
import json
from dataclasses import asdict, replace
from modelaccess.contract import FinishReason, Result, Usage


def checked_training_result(result, request):
    if not isinstance(result, Result):
        raise RuntimeError('Worker returned an invalid result type')
    if (not isinstance(result.finish_reason, FinishReason)
            or not isinstance(result.text, str)
            or not isinstance(result.metadata, dict)
            or not isinstance(result.usage, Usage)):
        raise RuntimeError('Worker returned malformed result fields')
    try:
        json.dumps(asdict(result), allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError('Worker returned a non-serializable result') from exc
    error = result.error
    if result.request_id != request.request_id:
        error = 'training_result_request_mismatch'
    elif result.finish_reason != FinishReason.STOP:
        error = error or 'training_incomplete_' + result.finish_reason.value
    elif result.returned_model not in {request.settings.model, *request.settings.accepted_returned_models}:
        error = error or 'training_result_model_mismatch'
    elif not result.text.strip():
        error = error or 'training_empty_output'
    if error == result.error:
        return result
    # Preserve raw text, actual termination and usage for the audit. Callers must
    # not display this as an answer: Result.ok is false. No synthetic completion.
    return replace(result, error=error,
                   metadata={**result.metadata, 'trainingCompletionRejected': True})
