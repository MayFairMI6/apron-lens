"""Importable test-only fault injector; never used by the training launcher."""
from backend.training_adapter import TrainingAdapter
from modelaccess.contract import FinishReason, Result, Usage


class RuntimeProbeAdapter(TrainingAdapter):
    def review(self, request):
        if request.request_id == 'injected-runtime-error':
            return Result(request.request_id, self.provider, request.settings.model,
                          self.served_model, 'injected partial output', FinishReason.ERROR,
                          'injected_provider_exception', Usage(), 0., {}, (),
                          error='provider_error:InjectedRuntimeError')
        return super().review(request)

