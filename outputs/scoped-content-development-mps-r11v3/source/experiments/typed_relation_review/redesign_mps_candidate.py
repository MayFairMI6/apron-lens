"""Explicit pinned MPS runtime for the isolated structural R11 experiment."""
from . import redesign as core
from modelaccess.nli import PairClassifier,MODEL_ID,MODEL_REVISION,LABELS
VERSION=core.VERSION+'-anli-large-mps'
THRESHOLD=core.THRESHOLD
DEADLINE_SECONDS=core.DEADLINE_SECONDS
QUOTE_CONTRACT=core.QUOTE_CONTRACT
evaluate=core.evaluate

class NLIEngine(PairClassifier):
    def __init__(self,model_dir=MODEL_ID,batch_size=8):
        super().__init__(model_dir,batch_size,device='mps')
