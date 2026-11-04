# Qwen learner-interpretation experiment, version 1

The user approved testing the existing local Qwen approach on 4 November 2026.
This is a separate experimental architecture, not an amendment to historical
R11 results or activation in the app. The original R11 contract and all old
records remain immutable. The milestone ledger records placement in CURRENT.

This first phase tests extraction only. It produces no grade, credit, source
support verdict or learner-facing answer. The model receives only the exact
learner answer and mechanically derived exact text units. No report, question,
rubric proposition, reference annotation, expected status or hidden test data
enters the extraction prompt. A question-dependent fragment may remain unresolved;
the extractor may not supply its missing meaning from an expected answer.

The model is Qwen/Qwen3.5-9B, revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, loaded from the existing local artifact
through the shared backbone. The profile is `apronlens-v2-mps`: MPS, float16,
eager attention, greedy decoding, thinking disabled by the frozen registry.
Initial output capacity is 1,000 tokens. No weight training, network API, model
fallback, constrained-decoding substitution or prompt retry occurs. Actual model
artifact hashes, package versions, template settings, source hashes, prompt,
raw output, usage, latency and observed terminal token are retained. A returned
EOS token establishes completion; short output alone does not. Incomplete or
malformed output remains a recorded failure and is never repaired silently.

An isolated process owns the model. Startup has the existing 300-second limit;
each generation has a 55-second killable deadline. A timed-out request is not
retried and a recovered answer does not replace it. No other model owner may
run concurrently. These are extraction-stage observations, not proof that a
future combined interpretation/report-verification pipeline meets the whole
55/60/90-second budgets. Those budgets remain whole-request requirements at
integration; assigning each stage another 55 seconds is prohibited.

The versioned candidate defines a compact schema for atomic claims, exact text
references, actor/relation/value, polarity, epistemic and temporal status,
attribution, correction links and unresolved text. The parser binds references
to original text, rejects invented or ambiguously bound spans, malformed links,
unknown fields and uncovered text. Mechanical coverage does not prove that all
meanings or conjuncts were extracted. Schema validity is reported separately from
independently reviewed semantic fidelity. Rejecting every difficult answer is
not successful extraction. An interpretation with valid quotes can still be wrong.

The initial six controls are already-exposed answers, selected and annotated
independently before inference. References stay outside the prompt and parser.
They include ambiguous identity, retraction, readiness/clearance distinctions,
an omitted related point, unsupported compound claims and a valid correction.
All six outputs, including failures, must be reviewed. No initial pass authorizes
credit or claims generalization. Additional exposed contrasts and all prior
development cases remain available for development; they are not held out.

Later grading requires a separately frozen implementation and verification plan:
each interpreted claim must retain exact learner evidence; reports must be
receipt-eligible, episode-correct and appropriate to current versus historical
claims; uncertainty must remain distinct from denial or omission; every extra
assertion and attribution must be checked. Extraction, support checking and
aggregation errors must be recorded separately. No extracted frame receives
credit merely because its quotation exists or because a source contains a
correct answer. Raw learner text remains available for independent comparison.

The four assessment statuses, gold conventions, final quotation requirements,
1,200-character input limit, five ordered acceptance gates and frozen baseline
remain unchanged. A final candidate must pass full exposed qualification,
independent review, a correctly registered fresh comparison, isolated runtime
and native acceptance, then publication/readback before promotion.

The unread `fresh-v3` was authored under R11's pinned-classifier contract. It is
ineligible for this changed architecture under that contract's own rule, and
remains sealed with provenance intact. It is not a failed run and will not be
silently reused. Replacement authoring or evaluation requires the independent
eligibility/placement step recorded in the ledger after exposed qualification.
This phase does not authorize automatic reserve replacement. Existing videos,
results, production review behavior and course submissions remain unchanged.
