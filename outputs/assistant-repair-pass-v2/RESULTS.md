# Bounded assistant repair pass

This pass follows published base `8c2c0f0cf162e4a29224d0ed686bbd7efd9dd982`.
It preserves earlier results and the finished narrated video. The four-track
[plan](../../docs/course/ASSISTANT_REPAIR_PLAN.md) distinguishes runtime fixes,
ordinary selection, typed meaning, and citation mechanics. No weights were trained.

## Typed meaning and citations: candidate rejected

The initial compact candidate delivered six structurally accepted reviews but
only four exact judgments. It incorrectly credited an omitted hold and false
stand occupancy. The sole permitted revision separated report-blind learner
coverage from report-based judgment. It delivered three exact reviews out of
six, withheld three, and accepted only one of three fully valid responses.
This fails the development gate. No fresh typed evaluation was run and no
candidate was deployed. The authored fresh pilot is unused, not an evaluated
benchmark. Production `backend/training_assessment.py` remains unchanged.

Candidate-only checks derive literal quotations from learner references, preserve
multi-unit spans, reject invalid/future/cross-run evidence before inference, and
use declared report bundles. Eighteen contract tests pass. These checks do not
establish semantic truth or constitute a deployed citation remedy; mechanically
valid references did not prevent incorrect learner interpretation. Independent
[meaning review](../../docs/course/TYPED_MEANING_REPAIR_REVIEW.md) and
[citation review](../../docs/course/CITATION_REPAIR_REVIEW.md) retain all failures.
Both development folders preserve source snapshots and raw replies. The
predeclared two-version limit ends this experiment; #60 and #61 remain open.

## Runtime: bounded stopping and recovery remedy

The training wrapper rejects reported non-STOP, empty, mismatched, malformed or
nonserializable results. It preserves well-formed raw output, usage and reported
termination. A runtime ERROR retires the failed owner and prepares a replacement
for a subsequent request without replaying the failed request. Cleanup runs even
when audit writing fails. Worker/server/client budgets remain55/60/90seconds.

Seventeen targeted completion/worker tests passed in both local runtimes. The
[real-model probe](../runtime-error-recovery-20261103-r2/summary.json) produced
actual replies before and after an injected runtime error, stopped PID7256 before
starting7291, and closed the final owner. The failed first harness attempt is
also retained. This is an injected-error recovery test, not observed natural-error
frequency. Its image warmup executed but answered `B.`, not the requested text;
that is not instruction-accuracy evidence. A semaphore cleanup warning remains.
The shared engine infers STOP from length, so these checks do not certify EOS.
See the [independent runtime review](../../docs/course/RUNTIME_FAILURE_REPAIR.md).

The probe locked an adapter before the later history guard. Its exact source is
reconstructed in `source/runtime-probe-adapter.py` and verified against the probe
hash. Worker/result sources remain identical to the probe. Final integrated
adapter behavior has separate ordinary/regression tests; do not equate those
source versions. `source-manifest.json` records the final integration snapshot.

## Ordinary history: separate measured correction

The fixed diagnostic initially passed11/12. The failure identified the right
flight but returned current standE4 instead of the stand precedingE4. A narrow
history-coverage check requests one further model answer using the same reports
and cutoff; it never inserts a previous fact itself. A second inadequate answer
is withheld. The fixed diagnostic then passed12/12. These exposed questions are
regression evidence, not fresh generalization evidence.

The guard recognizes literal stand/TOBT anchors and an unambiguous flight. It
checks presence of earlier superseded information, not whether every wording
was interpreted or the selected predecessor is always immediately previous.
The primary prompt remainsv8; retry policy isv4. The separate frozen comparison
uses four new fictional worlds and12questions, baseline then repair, with gold
excluded from model inputs. Both arms use the same model/runtime. Its recorded
gate and independent review govern adoption; no tuning follows fresh results.

## Preservation and verification

`preservation.json` verifies309 previously committed output files unchanged by
Git-normalized hashes, unchanged production typed reviewer, and unchanged video
SHA256 `5d7a20600a32c9211ef16ab9fcb5dd891366b4badb4c7f0888af728f62af3af1`.
The existing Drive video remains intact. No native UI/scenery or media is edited.
No broad model-accuracy, zero-timeout, professional-training or whole-assignment
completion claim follows from this pass. GitHub publication is recorded separately after remote readback.

## Final checks

All **395 tests pass** (77.860 seconds), frozen research integrity passes for
160 records, and the backbone boundary check passes. Logs are retained beside
this report. The source-frozen fresh ordinary pilot completed all 12 pairs:
baseline12/12 and repair12/12, with no new failure and no delivered identity or
source-support failure. This tie supports bounded integration, not superiority.
The [independent ordinary review](../../docs/course/ORDINARY_HISTORY_REPAIR_REVIEW.md)
inspects expanded answers and raw attempts separately.

The CPU-only automated suite overlapped the later repaired-arm run. Actual model
runs were sequential, but timings are descriptive, not a controlled speed
comparison. The outer pilot lock omitted the scorer/comparison-runner hashes;
arm locks include the scorer and the final source manifest retains both. No
original lock is rewritten. The guard's fresh pilot success does not establish
a retry benefit when the model's first selection was already correct.

Independent review accepted the bounded ordinary integration: all 24 fresh raw
selections and expanded answers were inspected. Both arms used 12 attempts and
returned identical corresponding raw selections. The exposed regression used
13 attempts: the incorrect current-stand selection was detected, and the model's
second answer supplied the earlier stand. No scripted answer was inserted.
