"""Importable test-only model adapter; never used by the live training launcher."""
import os
import time
from backend.training_adapter import TrainingAdapter
class FaultProbeAdapter(TrainingAdapter):
    def review(self,request):
        if request.request_id=='forced-hang':time.sleep(120)
        if request.request_id=='forced-crash':os._exit(7)
        return super().review(request)
