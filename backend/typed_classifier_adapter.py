"""Process-local typed policy and generic classifier, loaded only when activated."""
import time
from backend.typed_review_service import ReviewOutcome
from modelaccess.nli import PairClassifier, MODEL_ID, MODEL_REVISION

class TypedClassifierAdapter:
    served_model = MODEL_ID
    provider = 'local-pair-classifier'

    def load(self):
        # Policy graduation is an explicit acceptance step; never import an
        # experiment as a fallback if the accepted backend module is absent.
        from backend import typed_review_policy
        self.policy = typed_review_policy
        self.engine = PairClassifier(device='mps')

    def warmup(self, settings):
        started = time.monotonic()
        self.engine.records = []
        self.engine.score([dict(premise='The route is blocked.',
                                hypothesis='There is an obstruction on the route.')], started+55)
        return dict(operation='pair_classification', modelId=MODEL_ID,
                    modelRevision=MODEL_REVISION, policyVersion=self.policy.VERSION,
                    completed=True, elapsedSeconds=time.monotonic()-started,runtime=self.engine.runtime)

    def review(self, request):
        started=time.monotonic()
        self.engine.records=[]
        self.engine.planned_pairs=[]
        self.engine.semantic_rule_audit=[]
        self.engine.typed_state_audit=[]
        review=None
        error=None
        completion='completed'
        try:
            review=self.policy.evaluate(request.payload,self.engine,started+55)
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
            completion='timed_out' if isinstance(exc,TimeoutError) else 'failed'
        return ReviewOutcome(request.request_id,request.fingerprint,completion,review,
            MODEL_ID,MODEL_REVISION,self.policy.VERSION,time.monotonic()-started,
            dict(runtime=self.engine.runtime,pairs=self.engine.records,plannedPairs=self.engine.planned_pairs,
                 semanticRules=self.engine.semantic_rule_audit,
                 typedStates=self.engine.typed_state_audit),error)
