# Discriminative typed-feedback experiment

The user authorized a different approach to the remaining typed-answer and
citation errors, preserving earlier results and the final narrated video. This
new experiment follows `f36380688213ca90cfc65f34876ae9d474d8e2b2`; it does not
replace or reinterpret any previous run. **The candidate is not deployed.**

Instead of asking the assistant to generate a review, a pinned natural-language
inference classifier compares learner statements with authored rubric propositions,
and received reports with learner assertions. Code assembles statuses, literal
quotation spans and eligible report references. The classifier generates no
citation IDs or prose. Its scores are fallible, uncalibrated model judgments,
not a proof of correctness. No model weights were trained.

The model is `cross-encoder/nli-deberta-v3-small`, revision
`fa2804872c3b4bd748f38c0185cc85775361e735`, Apache-2.0. The
[publisher's model card](https://huggingface.co/cross-encoder/nli-deberta-v3-small)
specifies contradiction/entailment/neutral labels and SNLI/MultiNLI training.
Those general-domain benchmarks do not validate aviation assessment. Local model
and tokenizer file hashes are retained in `model-provenance.json`; weights are
not committed to the repository. Evaluation used CPU and a fixed 0.8 threshold.

| Development version | Structurally delivered | Exact reviews | Valid answers reviewed exactly | Gate |
|---|---:|---:|---:|---|
| Whole-response NLI v1 | 6/6 | 1/6 | 0/3 | Fail |
| Topic-scoped sentence NLI v2 | 6/6 | 5/6 | 2/3 | Fail |

Both versions used the same six exposed development cases with unchanged labels.
Each source snapshot and decision policy was saved before its model calls. These
are development observations, not an independent benchmark or a paired comparison
against production. The fresh 24-case draft remains unused and unvalidated.

V1 falsely treated unrelated text as contradicting other criteria and failed
valid waiting, service and explicit-unknown answers. V2 scopes comparisons to
neutral topics, preserves all learner sentences for grounding, and adds a bounded
authored present-occupancy exclusion for the waiting-for-stand criterion. It uses
identity-only context for an unambiguous explicit learner flight, with separate
audit metadata; quoted learner text is not rewritten. It preserves negation,
blocks conflicting relevant judgments, uses shorter received-report groups, and
unions the actual supporting source IDs when grounding is fully met. These rules
are bounded authored assumptions, not general language understanding.

V2 correctly handles the waiting-for answer, omitted hold, wrong occupancy,
unsupported fire addition, and explicit unknown-clearance answer in this set.
The remaining failure is a fully valid response:

> The late baggage batch is delaying TRN102. Fuel is complete, but that does not mean baggage loading is complete.

The model scores the baggage-delay sentence as contradicting the fuel-versus-
baggage scope proposition, while the relevant fuel sentence supports it. The
conflict guard therefore returns uncertain separation. Its report-to-sentence
check also returns uncertain grounding. The learner receives partial support
instead of the expected fully supported review. This is still incorrect feedback,
not a successful safe rejection. All raw pair inputs, probabilities, references,
quotations, comments and timings are preserved in the two development folders.

The v2 per-answer measured CPU time was 0.029–0.141 seconds after model loading.
That is a six-case local measurement, not end-to-end service/device latency.
Deadline checks reject late output between batches but cannot forcibly interrupt
an active CPU kernel. No native typed-flow validation or new production model
ownership integration was attempted because the development gate failed.

The fixed plan allowed an initial version and one revision. Both are complete,
so this experiment stops before fresh evaluation or promotion. Production
`backend/training_assessment.py`, the previously accepted runtime/history fixes,
and the final video remain unchanged. Typed semantic and citation limitations
#60/#61 remain open. Eligibility, exact quotation and deterministic formatting
can be mechanically checked; they do not establish a correct semantic judgment.

The [plan](../../experiments/typed_nli_review/PLAN.md),
[independent review](../../docs/course/TYPED_NLI_REVIEW.md) and ML-051 in the
[milestone ledger](../../docs/course/MILESTONE_LEDGER.md) record the boundaries.
Final checks and preservation receipts accompany this report. Publication is
recorded separately after remote readback.

Final verification: **411 tests pass** (42.391 seconds), frozen integrity for
160 records passes, and backbone boundaries pass. The initial file-by-file audit
matched all 386 earlier output files; the final tracked-output and production-code
diffs are empty. The final video checksum remains
`5d7a20600a32c9211ef16ab9fcb5dd891366b4badb4c7f0888af728f62af3af1`.
Independent review inspected all 102 NLI pairs across both versions and replayed
all twelve saved reviews without inference; no observed false credit in these
six cases changes the failed valid-answer acceptance gate.
