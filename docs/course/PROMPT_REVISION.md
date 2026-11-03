# Readiness prompt revision

The user authorised a bounded prompt improvement after the current assistant's
comparison exposed an omitted readiness unknown. This is instruction tuning,
not model-weight training. The original v5 adapter is retained byte-for-byte in
`backend/training_adapter_v5.py`, and the earlier comparison runner explicitly
imports it. Original results in `outputs/assistant-comparison` remain unchanged.

Candidate v6 distinguishes the requested property from related progress. If a
question asks about overall readiness, an existing current readiness report must
be selected, including a negative report. If readiness is absent, that requested
property must be marked unknown even when a relevant service or hold-release fact
is also selected. Direct service, stand, route and estimate questions do not acquire
an unsolicited readiness unknown. No facts, sources, identities, answer expansion,
validator, model weights or retry rules are changed.

The pre-run lock in `outputs/prompt-revision/v6-run.lock.json` saves the source
hashes, all questions/expected values and adoption rule before model calls. The
18 previously observed questions are development regression material. Only after
all 18 pass does the runner expose the new evaluation: 24 fresh questions across
four six-turn episodes, each run through v5 and v6 with the same pinned model,
768-token limit, text-only input, seed 29 and report cutoffs. Fresh questions were
authored before this revision's calls; they are same-domain authored probes, not
independent-airport or professional validation. Both versions receive separate
normal history sessions; no selected aircraft is supplied.

The additional readiness episode inserts evaluation-only explicit ready and not-ready
reports, received at 200 and 220 seconds respectively. Before receipt the relevant
fact is unavailable. These reports do not enter the real app or original lessons.
This tests positive confirmation, negative status and absent knowledge rather than
rewarding indiscriminate abstention. Expected answers are used only after inference.

The adoption rule is fixed: all observed regression cases pass; v6 improves total
fresh task success over v5 without turning a v5 pass into a failure; every explicit-
readiness episode question passes. Fresh output will not be used to tune another
prompt. At most two development revisions are allowed before evaluation; a failed
fresh gate preserves the candidate/results but does not promote it. Passing source
validation alone is insufficient. The same scorer's existing limitations remain:
supported irrelevant additions and prose quality are not fully scored; citation
and support checks are relative to the expected flight; clarifications can be safe
but fail a full conversation task. Read outputs, not just totals.

The offline runner does not enforce native deadlines and its adapter infers stop
reason from token count. Actual model calls, raw selections, expanded/displayed
answers, usage, errors and timing are retained. Native/service verification is
separate from offline acceptance. No scripted answers or post-hoc answer filling
are introduced. Qualitative typed-assessment feedback is a separate path.

```sh
.venv-candidates/bin/python -m scripts.evaluate_prompt_revision --output outputs/prompt-revision/v6-run.json
```

Stop the local model service first to avoid a second allocation, then restore it.
Use a new path for every run; existing outputs or lock files cannot be overwritten.
`--validate-only` checks authored keys without inference. The new run is not a
replacement for the original v5 comparison or the frozen earlier research study.

During result inspection, v5's explicit-readiness change question selected both
the correctly labelled superseded ready report and the correct current not-ready
report. The inherited strict current-only scorer rejects this, although showing
history can be appropriate for that wording. Preserve the predeclared score, but
do not interpret that penalty as a factual error, false readiness claim or
proof of fresh-question semantic improvement. Independent review must separate
this scoring limitation from the known uncertainty omission. No labels or prompt
are changed after the fresh outputs are observed.

## Outcome and default

V6 passed all 18 observed regression turns, including the known uncertainty omission.
Fresh results tied at 23/24 under the predeclared strict scorer, with no paired
regressions. Both versions' only strict miss was the same accurately labelled
ready-to-not-ready history answer. This is a scorer/task-wording limitation, not
a demonstrated factual defect. No new-question advantage was established.

The locked adoption gate failed. V6 is published as a tested candidate in
`backend/training_adapter_v6.py`; the app default remains the byte-identical v5
adapter in `backend/training_adapter.py`. No v6 production/native promotion is
claimed. The service is restored using v5. The broad semantic limitation remains
open; fixing an observed question in a candidate does not close it.

The original executed runner is preserved in `outputs/prompt-revision/runner-at-run.py`.
After evaluation, the reproducible runner was routed to the explicit v6 module
so restoring the default to v5 cannot change which candidate it tests. The pre-run
lock's v6 adapter hash now maps to `backend/training_adapter_v6.py`, and its runner
hash maps to `runner-at-run.py`; all bytes are retained in the preservation manifest.
This routing change did not trigger another model run or alter any saved result.

One development revision was used. No second revision was tuned on the fresh
questions, no weights were trained, and no graph database was introduced. The
next research improvement would be a predeclared scorer that distinguishes a
current-status question from a change/history question, followed by a separate
unseen question set. That further experiment has not been started.
