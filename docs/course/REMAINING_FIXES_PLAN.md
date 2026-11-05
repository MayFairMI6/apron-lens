# Remaining assistant and scenery fixes

The owner authorizes this bounded current-iteration work after ML-048. Preserve
all previous results, the deployed typed reviewer, weights and recorded video
unless a separately verified remedy requires a change. No new foundation-model
training or graph database is required.

1. Build an isolated typed-review candidate with explicit learner-unit checks,
   exact source-text references and independently derived overall verdicts.
   Review every learner unit, including additions following a correct answer.
   Separate criterion coverage from support for claims actually made. Exact text
   matching does not prove faithful interpretation; unit checks remain fallible.
2. Use exposed historical cases only for development. Freeze the candidate,
   labels and at least 24 fresh paired questions before final evaluation: 12 valid
   and 12 unsafe/omitted/contradictory/uncertain responses. Independently inspect
   every judgment, including unsupported clauses hidden inside a broad span.
   Require no newly accepted false credit, no higher total false credit, valid
   acceptance at least 10/12 and not below baseline, and no reduction in review
   yield. These are descriptive pilot gates, not statistical generalization.
   Allow at most two documented development revisions before a stop decision.
   If development fails, retain its outputs and do not spend the fresh test set.
3. Extend recovery testing to fixed repeated actual-model cycles; distinguish a
   blocked request, process crash and initialization failure. Record replacement
   readiness, process ownership, successful requests, parent/resource observations
   and warnings. Python termination can corrupt IPC or strand synchronization
   resources, so never reuse a dead worker's connection. Test transport blocking
   as well as generation blocking. Do not infer indefinite stability.
4. Audit wide-airport rendered evidence against the saved mapped geography.
   Fix only a demonstrated mismatch, using reference, implementation and separate
   Astra visual review. The original reported camera may remain unknown. Decide
   video impact from visible corrections and spoken claims; no automatic recut.
5. Adopt a reviewer only after the paired gate and a native typed-flow check.
   Publish code, real outputs, rejected attempts and exact limits. Update #59–62
   and the ledger without duplicating completion counts. Preserve the current
   video and script when the verified behavior they demonstrate still holds.

## Research basis

FActScore decomposes factual statements into atomic facts for support assessment:
https://aclanthology.org/2023.emnlp-main.741/ . Its precision framing motivates
checking added claims; it does not establish that a learner covered a question.

ALCE separates answer correctness and citation quality:
https://aclanthology.org/2023.emnlp-main.398/ . Apply that distinction here: a valid
report ID or exact quotation does not certify the judgment attached to it. Measure
coverage, false credit, valid answers rejected and unavailable reviews separately.

Python's multiprocessing documentation warns about termination while using pipes,
queues and shared synchronization resources:
https://docs.python.org/3.12/library/multiprocessing.html . Isolate process ownership,
discard failed IPC, and report resource cleanup observations explicitly.

These are design influences, not replications or evidence that this application
already implements a published method. Existing frozen results remain unchanged.

## Execution status

The bounded pass is complete; see [the outcome and preserved failures](../../outputs/remaining-fixes/RESULTS.md).
Worker reliability is accepted within tested bounds. The two-revision development
cycle failed and the candidate is rejected; production typed review remains v2,
and the fresh paired evaluation was not consumed. The wide audit found no
justified geometry patch; the original reported view remains unidentified. The
finished narrated video is preserved and updated in Drive. Publication status is
recorded separately in the milestone ledger and GitHub.
