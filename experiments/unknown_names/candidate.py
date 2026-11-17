"""DEVELOPMENT CANDIDATE: selector prompt v9 wording for unknown property names.

Not the live prompt. The live TrainingAdapter stays on training-evidence-selector-v8.
The candidate adds two sentences and changes nothing else: same model, same
single retry, same validator. Written after seeing the `airport_landing_release`
and `engine_condition` failures, so results on those cases are development
results, not a held-out measurement.
"""
from backend.training_adapter import TrainingAdapter, selector_context

CANDIDATE_PROMPT_VERSION = 'training-evidence-selector-v9-candidate-unknown-names'
ANCHOR = 'Check every requested property separately before returning. '
ADDED = ('Every unknowns entry must be one of the names listed in that flight\'s missingProperties, copied exactly; '
         'never write a new name. When a selected current report itself says that something is unconfirmed, pending '
         'or not yet reported, that report is the answer: select it and do not add an unknown for that item. ')


class UnknownNamesCandidate(TrainingAdapter):
    prompt_version = CANDIDATE_PROMPT_VERSION

    def selector(self, base_prompt):
        prompt, candidates = selector_context(base_prompt, self.training_role)
        if prompt.count(ANCHOR) != 1:
            raise ValueError('Selector prompt changed; rebase the candidate')
        return prompt.replace(ANCHOR, ADDED + ANCHOR), candidates
