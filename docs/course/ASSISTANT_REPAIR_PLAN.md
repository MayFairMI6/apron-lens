# Assistant repair plan

The owner reopens the remaining typed-feedback, citation and model-failure issues
in the current iteration. Preserve every earlier result and the finished narrated
video. This is a new bounded repair pass after ML-049, not a change to the earlier
failed experiments or their conclusions. ML-050 records the acceptance rules.

| Fix | Concrete problem | Implementation route | Acceptance |
|---|---|---|---|
| Typed meaning (#60) | Crediting omitted information, confusing waiting with occupancy, ignoring invented additions. | Separate a report-blind reading of the learner's words from report-based correctness review; require actual learner evidence for credit and inspect every clause. | Pass exposed development first, then a frozen 24-case paired pilot with 12 valid and 12 other responses; no newly accepted false credit, total false credit no higher than production, valid acceptance at least 10/12 and at least production, yield at least production. Independently review every result. |
| Quotations and sources (#61) | Invented quotations, wrong report scope, invalid JSON, misleading source associations. | Derive literal quotations from checked text references and attach only authored reference bundles after checking run/cutoff. Explicitly treat them as comparison evidence, not proof that unsupported statements occurred. | Malformed, stale, future and cross-run inputs fail before inference. Test multiple learner spans and unsupported additions. Review citation relevance separately from ID validity. No weakening of evidence checks to raise acceptance. |
| Model stopping/runtime failures (#62) | Nonterminal/truncated output can look successful; a reported runtime error can leave a broken owner marked ready. | Training-only completion guard; preserve true returned stop/error/usage fields; stop failed owner and warm a replacement without replaying the request. Audit malformed-result and cleanup failures. | Spawned-process regressions plus a fixed actual-model recovery probe. Unchanged 55-second worker and 60-second server budgets. Successful replies after recovery, no overlapping owners, preserved input/visible failure. No claim of eliminating all device faults. |
| Other ordinary-assistant errors | Wrong flight, missed readiness uncertainty, history/current confusion, unsupported explanations. | Keep v8 fixed initially. Run varied questions with explicit expected components and eligible source scope; repair only a reproduced defect. | Audit every actual reply, rejected answer and retry. No scripted answers, silent source changes or broad accuracy claim from a small diagnostic. |

Root owns integration and actual-model execution. Separate agents own runtime
implementation, independent typed-meaning review, and independent citation review;
the milestone reviewer adjudicates each outcome. Model calls run sequentially to
avoid resource contention. A code fix can be accepted independently of a failed
semantic experiment; no issue is closed merely because work was attempted.

The new semantic cycle permits an initial candidate and one documented revision.
The initial compact-format candidate returned six structurally accepted reviews
but only four exact judgments: it still credited the omitted fog hold and wrongly
accepted false stand occupancy. Its new citations are mechanically eligible, but
that did not make the judgments true. Preserve these results. The remaining
revision must address evidence leakage/answer completion rather than repeat the
same prompt. If it fails, stop this cycle and retain the failure analysis; do not
consume or tune against a fresh test set.

Only a candidate that passes the paired pilot, latency checks and native typed-flow
compatibility may replace production. The video, its existing claims and historical
scores remain untouched. Weight training, a new renderer and the video-memory
project are outside this pass.

## Execution outcome

The typed candidate used both allowed development versions. The second delivered
three exact reviews out of six and accepted only one of three fully valid answers;
it is rejected. The authored fresh typed pilot remains unused. Quotations and
source eligibility have stronger candidate-only checks, but the failed semantic
gate prevents deploying those changes as a replacement reviewer. See
[TYPED_MEANING_REPAIR_REVIEW.md](TYPED_MEANING_REPAIR_REVIEW.md) and
[CITATION_REPAIR_REVIEW.md](CITATION_REPAIR_REVIEW.md).

Runtime hardening passed its spawned-process tests and a real-model recovery
probe; the remaining cleanup warning and reported-STOP limitation are retained.
The ordinary diagnostic reproduced a current-versus-previous stand error. Its
narrow retry guard passed all twelve exposed regressions and proceeds to the
frozen paired twelve-question pilot. Final acceptance and publication are recorded
in [the pass report](../../outputs/assistant-repair-pass-v2/RESULTS.md) and ML-050;
this plan is not itself evidence of completion.
