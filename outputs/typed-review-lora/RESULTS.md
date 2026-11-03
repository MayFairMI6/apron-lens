# Typed-review LoRA pilot: retain the current app model

The trained adapter failed the predefined acceptance rule. It improved response
validity, acceptance of fully correct answers and average latency, but increased
incorrect credit from **3 to 4 of 48 negative criteria**, introducing one newly
accepted error. The candidate is preserved for research and is **not adopted**.
Further tuning is not needed for this iteration.

The comparison used the same pinned Qwen3.5-9B model and NF4 runtime, with the
adapter disabled or enabled. Both arms received the same learner response,
received reports and rubric, with greedy generation, a 900-token limit and the
unchanged production validator. There were 48 cases per arm, 96 actual responses,
no retries and no missing or duplicate pairs. Every stored score replayed exactly.
All responses stopped at EOS; there were no inference exceptions. These findings
concern typed practice feedback, not the ordinary conversational assistant.

| Measure | Base | Trained adapter |
|---|---:|---:|
| Responses passing the structural validator |32/48|44/48|
| Valid responses with every criterion status correct |26/48|33/48|
| Fully correct learner answers accepted as supported |9/16|16/16|
| Incorrect credit on negative criteria, after validation |3/48|4/48|
| Newly accepted incorrect-credit cases relative to base |—|1|
| Mean generation latency |14.82s|10.65s|
| Median generation latency |15.75s|10.45s|
|95th-percentile generation latency |17.12s|12.47s|
| Output tokens, all 48 answers |12,807|8,446|

Rejected responses remain failures in the validity and exact-status measures.
Their claims are not delivered as accepted feedback, so they receive no accepted
false-credit count. This distinction matters: the adapter can fix formatting while
allowing an underlying semantic mistake through. Both arms used 36,906 input tokens.
Lower output length contributes to the latency difference; this is not an isolated
measurement of inference-engine speed.

The family-level result is uneven. Route-authority exact-status success improved
from 15/24 to 24/24. Tug-dispatch exact-status success fell from 11/24 to 9/24, while
accepted incorrect credit rose from 3 to 4. The primary regression is
`dispatch_conflict-0-unsupported_extra`: reports establish a tug reassignment and
an unconfirmed replacement, but the learner adds that AX210 completed pushback.
Both models' raw answers overlook that unsupported addition. The base response
fails the exact-quotation contract; the adapter produces a structurally valid
`supported` answer, allowing the error through. Thus this is a newly accepted
error, not proof that only the adapter generated the underlying false judgment.

Other adapter failures in the dispatch family include treating an omitted fact
as a contradiction, wrongly rejecting a correct tug-assignment statement, and
producing a verdict inconsistent with its own criterion statuses. Cleaner JSON
and generic fluent feedback do not establish better semantic review.

Training used 144 authored examples from six families, 48 validation examples from
two other families and 48 test examples from two further families. Four substituted
episodes per pattern are correlated. The old 18 exposed cases were development
material only. The model trained 1,966,080 language-attention LoRA parameters for
72 optimizer steps. Validation completion-token losses at steps 24/48/72 were
0.08236425/0.00545529/0.00849797; the fixed minimum-loss rule selected checkpoint 48.
The selected adapter and executable source hashes were independently checked
before final evaluation. Test grading labels were used for scoring, not supplied
as target answers to generation. The rubric remains an intended model input.

This is a small authored supplied-report pilot with two held-out families, shared
output/error structures and generic target feedback. It does not establish
real-world performance, independent temporal retrieval, visual reasoning or
learner training efficacy. Results from this NF4 runtime are not silently compared
with older unquantized Mac measurements. Further training against these observed
test failures would make these cases development material; a new independent
claim would require fresh evaluation evidence.

The independent reviewer checked all training/validation labels, checkpoint
selection and the first 48 actual evaluation responses. The coordinator reviewed
the remaining 48 responses, including all distinct role-normalised feedback texts.
The attempted independent continuation/replacement was blocked by the agent
service's thread limit. Consequently, full independent 96-response semantic review
is **not claimed**. The preserved automatic gate and concrete regression suffice
to reject this candidate; deployment approval is not sought. See
`semantic-review.json` for coverage and case-level findings.

Training job 571259 completed successfully in 13:46; evaluation 571262 completed in
20:52. Earlier environment and gradient failures remain preserved, including the
reviewed pre-training scale correction. The approved app, video, production
prompts and model weights remain unchanged. All 232 previously tracked evidence
files match their pre-B05 Git blob hashes. The current semantic-error issue remains
open. Finish this iteration with the measured negative result rather than another
tuning cycle.

Reproduction evidence: `training-receipt.json`, `training-steps.jsonl`,
`selection-lock.json`, `selection-review.json`, `evaluation-v1/records.jsonl`,
`evaluation-v1/summary.json`, `evaluation-v1/runtime.json`, `evaluation-audit.json`,
`prior-results-preservation.json`, and the exact `data-v2.tar.gz`. The locked
training/evaluation code and protocol are in `experiments/typed_review_lora`.
The selected adapter and the other two checkpoints are preserved locally under
`work/typed-review-lora/remote/run-v1` and on GAIVI; model binaries are not deployed
or included in the source commit.
