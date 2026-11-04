"""Two predeclared interpretation tasks inside one isolated-worker request.

No retry, report checking, production activation or semantic certification.
"""
from dataclasses import asdict, replace
from pathlib import Path
import hashlib
import json
import os
import time

from modelaccess.contract import Request, FinishReason, Usage
from .runtime import FrameAdapter
from . import two_pass_candidate as candidate


class TwoPassFrameAdapter(FrameAdapter):
    candidate_api = candidate

    def __init__(self, *, audit_path, audit_context=None):
        super().__init__()
        self.audit_path = Path(audit_path)
        self.audit_context = dict(audit_context or {})

    def _audit(self, event, **values):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = dict(event=event, recordedAt=time.time(), candidateModule=self.candidate_api.__name__,
                      frozenContext=self.audit_context, **values)
        with self.audit_path.open('a') as stream:
            stream.write(json.dumps(record, allow_nan=False, default=str) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def warmup(self, settings):
        # Do not dispatch the interpretation pipeline for the readiness probe.
        result = self.generate(Request('two-pass-startup',
            (('user', 'Reply with the word ready.'),),
            replace(settings, max_output_tokens=16)))
        if not result.ok or result.finish_reason != FinishReason.STOP or not result.metadata.get('observedEOS'):
            raise RuntimeError('Two-pass warmup did not finish with observed EOS')
        return dict(runtime=result.metadata, usage=asdict(result.usage),
                    finishReason=result.finish_reason.value)

    def review(self, request):
        if request.images or len(request.messages) != 1 or request.messages[0][0] != 'user':
            raise ValueError('Two-pass diagnostic accepts one learner-only message')
        if request.settings.max_output_tokens != 1000:
            raise ValueError('Two-pass aggregate output capacity must be 1000')
        learner = request.messages[0][1]
        api = self.candidate_api
        started = time.monotonic()
        selection = None
        final = None
        stages = []
        error = None
        identity = dict(requestId=request.request_id,
                        learnerSHA256=hashlib.sha256(learner.encode()).hexdigest())
        for stage in ('selection', 'annotation'):
            prompt = (api.selection_prompt(learner) if stage == 'selection'
                      else api.annotation_prompt(learner, selection))
            stage_request = replace(request, request_id=request.request_id + '-' + stage,
                messages=(('user', prompt),),
                settings=replace(request.settings, max_output_tokens=500))
            self._audit('stage_started', **identity, stage=stage,
                        prompt=prompt, maxOutputTokens=500,
                        elapsedSeconds=time.monotonic()-started)
            result = self.generate(stage_request)
            # Persist raw output BEFORE parsing or starting another model call.
            self._audit('stage_raw_result', **identity, stage=stage,
                        result=asdict(result), elapsedSeconds=time.monotonic()-started)
            parsed = None
            try:
                if not result.ok or result.finish_reason != FinishReason.STOP or not result.metadata.get('observedEOS'):
                    raise ValueError(result.error or 'stage_missing_observed_EOS')
                if type(result.usage.output_tokens) is not int or not 0 <= result.usage.output_tokens <= 500:
                    raise ValueError('stage_output_usage_unknown_or_over_cap')
                if stage == 'selection':
                    parsed = api.parse_selection(result.text, learner)
                    selection = parsed
                else:
                    parsed = api.parse_annotation(result.text, learner, selection)
                    final = parsed
            except (ValueError, TypeError, KeyError) as exc:
                error = stage + ':' + type(exc).__name__ + ':' + str(exc)
            stages.append(dict(stage=stage, result=asdict(result), parsed=parsed, error=error))
            self._audit('stage_validated', **identity, stage=stage, parsed=parsed,
                        error=error, elapsedSeconds=time.monotonic()-started)
            if error:
                break
        def total(field):
            values = [entry['result']['usage'][field] for entry in stages]
            return sum(values) if all(isinstance(v, int) for v in values) else None
        elapsed = time.monotonic()-started
        combined = replace(result, request_id=request.request_id, error=error or result.error,
            usage=Usage(total('input_tokens'), total('output_tokens'),
                        total('reasoning_tokens'), total('image_tokens'), total('cached_input_tokens')),
            latency_seconds=elapsed,
            effective_settings={**result.effective_settings, 'max_output_tokens': 1000,
                                'per_stage_max_output_tokens': [500, 500]},
            metadata={**result.metadata, 'version': api.VERSION, 'candidateModule': api.__name__,
                      'stages': stages, 'selection': selection, 'parsed': final,
                      'observedEOS': len(stages) == 2 and all(
                          s['result']['metadata'].get('observedEOS') for s in stages),
                      'fidelityVerified': False, 'reportCheckAllowed': False,
                      'semanticCompletenessVerified': False,
                      'aggregateBudgetSeconds': 55, 'retries': 0})
        self._audit('request_completed', **identity, elapsedSeconds=elapsed,
                    error=combined.error, usage=asdict(combined.usage),
                    structurallyValid=final is not None)
        return combined
