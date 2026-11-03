# Assistant reliability update

This iteration ships ordinary-assistant reference/coverage corrections and model
startup preparation. The typed-review candidates were rejected: they improved
some quotation failures but produced incorrect semantic judgments. The original
typed reviewer is restored byte-for-byte, with its original 60-second server
limit and unchanged 90-second native client limit. Remaining typed errors are
not represented as fixed.

Earlier results remain measurements of their original software. No old score,
model response, frozen v5/v6 adapter, research record or video is replaced. The
new ordinary-assistant prompt is v8; model weights and pinned runtime are unchanged.
These are bounded reliability corrections, not professional training validation.

The ordinary assistant makes flight continuity and full-question coverage
explicit. A guard checks unqualified pronoun follow-ups against the established
conversational referent. It does not select or fabricate report facts. One real
model retry uses the same reports and cutoff; an unresolved mismatch is withheld.
Explicit flight/aircraft references, descriptive corrections, relative references
and valid clarification remain available. This narrow guard is not a complete
natural-language reference resolver.

The training service exercises text and image inference during startup, before
HTTP readiness. Startup work does not advance scenario time. Its synthetic
requests, usage, outputs and failures are logged separately from learner answers.
This moves first-inference preparation out of a learner request. It does not
provide a hard inference-time guarantee or terminate an indefinitely stuck worker.
The existing lock, stale-response rejection and visible timeout behavior remain.

## Development evidence

The first v7 attempt did not fix the known stand-reference failure. Its interrupted
17-response run (16 passed), hash-verified adapter, runner and actual prompts are
retained. The v8 evaluation contains 24 known regression questions, then 24 newly
worded/renamed questions for each of frozen v5 and v8. V8 passed all 24 regressions;
both versions passed all 24 new probes. Those probes reuse four report families;
they are not independent held-out scenarios or evidence of broad superiority.
The fixed execution order is not a controlled speed comparison.

The initial v8 guard was independently reviewed and narrowed to preserve
clarifications and descriptive switches. Exact evaluated source is retained as
adapter-v8.py.txt. Saved-output replay checks the final guard against every v8
turn; this is not new inference. Final live checks are separate. The initial lock
omitted the turn handler and typed fixture hashes; later recording is labelled
supplemental provenance, not retroactively pre-locked. Startup logging and clock
refinements remain distinguishable from that initial inference run.

A retry-only typed trial recovered one quotation failure in 72.9 seconds but
still failed another case twice. It remains intact. A second candidate supplied
exact learner passages and allowed passage-ID selection before expansion through
the unchanged validator. Its complete 18-case development run includes every
checkpoint plus partial and incorrect responses. It produced accepted semantic
errors despite valid source/quotation structure, so it was rejected. Do not count
withholding as a correct semantic answer, or infer correctness from the schema.
Actual ID use, attempted recoveries and failures are reported in the evidence.
A temporary 80-second server budget used during investigation is not deployed.

The rejected candidate remains explicitly separate in
backend/training_assessment_candidate.py; the service imports only the restored
backend/training_assessment.py. The exact executed candidate and runner are also
archived. A later passage-ID collision-priority correction is distinguished from
the executed source and checked by expansion replay. No further prompt tuning or
weight training was undertaken to erase the failures.

See [the new evidence](../../outputs/assistant-reliability/) and its summary for
counts, timings, remaining failures and native verification. These are authored
development checks; targeted native checks are not four new complete lesson runs.

## Reproduction and preservation

Run `.venv-candidates/bin/python -m scripts.evaluate_assistant_reliability` for
the ordinary-development battery, or
`.venv-candidates/bin/python -m scripts.evaluate_indexed_reviews` for the rejected
typed candidate. Both refuse existing output/lock files. A new experiment needs
a new output version; do not delete published files to rerun it. The archived
runners record exactly what produced the historical trials.

Recompute the report with
`.venv-candidates/bin/python -m scripts.report_assistant_reliability` and replay
saved ordinary selections with
`.venv-candidates/bin/python -m scripts.replay_assistant_reliability`.

The approved video remains unchanged: learner interface, scenarios and demonstrated
flow are unchanged. No new scene, video chapter, weight training or visual-reasoning
validation claim is introduced. Member participation, reflection and smartphone
course acceptance remain separate submission requirements.
