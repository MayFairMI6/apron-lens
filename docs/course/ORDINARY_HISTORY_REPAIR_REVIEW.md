# Ordinary history repair: independent fresh-pilot plan

The existing twelve-question diagnostic reported 11/12 exact passes. The reported
failure selected the current E4 stand when asked for the stand immediately
preceding E4. This pilot addresses that bounded selection problem. It does not
claim a general natural-language interpretation remedy, and no answers or gold
labels are inserted into the candidate guard.

The independent reviewer authored and froze
`experiments/ordinary_history_repair/fresh-v1.json` before model calls. SHA-256:
`e9dabbe824032f06893e3db0f5522a81cc8fde01848733a94fb412ae4eb1915a`.
It uses the world/case structure and `score_answer` contract from
`scripts/history_evaluation.py`, with top-level `episodes` and evaluation-only
`metadata`. This reviewer made no model or GPU calls, read no old LoRA held-out
labels, changed no typed pilot, and changed no learner UI, video or production
code. Inputs/gold must remain frozen after exposure.

The twelve questions comprise four new fictional worlds, each with three turns:

| Episode | First turn | Second turn | Third turn |
|---|---|---|---|
| stand_before | Current stand; “Before departure” is context, not report history | Immediate predecessor before literal H6 | Explicit correction from NQ641 to NQ752 |
| stand_preceding | Earlier and replacement stands | Immediate predecessor preceding literal M17 | Explicit correction from AZ471 to AZ582 |
| estimate_prior | Current off-block estimate | Estimate immediately prior to literal 09:50 | Explicit correction from KD314 to KD425 |
| estimate_before | Earlier and revised off-block estimates | Estimate immediately before literal 18:35 | Explicit correction from LM207 to LM318 |

There are four history questions, two change questions and six current questions,
four of which correct the selected flight. New flight identities, values and
wording distinguish the pilot from the old diagnostic; it remains a small,
authored same-family test. The history phrasing intentionally fits the bounded
guard's declared literal `before`, `preceding` and `prior to` report-value scope.
No broad synonym or unconstrained history-understanding claim is justified.

Each world has two received assignments/estimates for K1. Its third change has
already occurred by event time 48 but is not received until 80; every question is
at receipt cutoff 50–52. K3 has the same current anchor value as K1, creating a
wrong-flight distractor. K2 has a distinct received value for the correction turn.
History gold requires the immediately preceding K1 fact, while allowing the
anchor as optional context. Returning only the anchor fails required coverage.
Current gold allows only the specified flight's current fact. Change gold
requires both the superseded and replacement facts.

The “Before departure” case asks only the current reported stand. That property
is explicitly supported and is not a claim about departure readiness or
permission. It provides one bounded check that the word “before” alone does not
force historical selection. No ambiguous readiness or unsupported property is
introduced.

Before inference, `validate_keys` passed all twelve cases. A deterministic
scorer sanity check constructed exact authored outputs and obtained 12/12
passes; substituting the anchor for the predecessor failed each of the four
history questions. These are checks of the file and gold contract, not model
results. At freeze time no fresh inference outcome was available; completed results follow below.

The model receives the question, world-derived received facts, and normal
conversation state only. `mode`, `required`, `allowed`, `unknowns` and top-level
`metadata` are evaluation labels and must never enter its input. Preserve the
frozen file/hash with the runner's source hashes and both arm configurations
before inference. Run baseline and repaired arms with separate new sessions per
episode, the same settings and report worlds, and all three turns in order.
Retain the existing bounded retry behavior and audit every attempt, including
withheld first attempts; do not discard failures or regenerate a favorable answer.

The predeclared gate is:

- The repaired arm passes all twelve old diagnostic regressions.
- On this fresh paired pilot, repaired exact passes are at least baseline exact
  passes, with no case newly failing in the repaired arm.
- No wrong-flight or future citation is delivered; inspect all raw claims,
  referents, values, statuses, evidence IDs and unknowns for both arms.
- Audit every raw output and report accepted yield, exact results, retries,
  latency and any withheld response separately. A guard-induced withholding is
  not an exact success.

Passing this gate permits a bounded integration recommendation only. It does
not demonstrate superiority if both arms tie, certify general history reasoning,
or close unrelated semantic/citation limitations. If the gate fails, preserve
these inputs and actual outputs as exposed evidence; do not tune against this
fresh pilot and continue calling it independent.

## Completed independent evidence review

Both arms completed in `outputs/ordinary-history-comparison-v1/`. This reviewer
read all 24 expanded answers and all 24 raw selector attempts, replayed every
saved score against the frozen world/case, checked raw-to-expanded identity and
fact selection, and inspected cutoff eligibility in every audited prompt. All
replayed score dictionaries match the saved dictionaries. The frozen fixture
hash and all outer-lock source hashes still match current files at this review.

The exposed regression also passes 12/12. Its 13 raw selector attempts include a
real first-attempt `S2:stand`/E4 error for the preceding-E4 question, rejected with
`historical_fact_missing`; the bounded second attempt selects `S1:stand`/D12.
That is direct evidence of the guard/retry correcting the exposed symptom in
this run, rather than a merely intended fix. All twelve regression expanded
answers were independently read for identity, claims, statuses, citations and
unknowns.

Fresh paired results:

| Episode | Requested current/change result | Requested predecessor | Corrected-flight result | Baseline / repair |
|---|---|---|---|---|
| stand_before | NQ641: H6 current | NQ641: C21 superseded | NQ752: B9 current | 3/3 / 3/3 |
| stand_preceding | AZ471: L3 superseded → M17 current | AZ471: L3 superseded | AZ582: Q12 current | 3/3 / 3/3 |
| estimate_prior | KD314: 09:50 current | KD314: 09:15 superseded | KD425: 11:20 current | 3/3 / 3/3 |
| estimate_before | LM207: 18:05 superseded → 18:35 current | LM207: 18:05 superseded | LM318: 19:10 current | 3/3 / 3/3 |

Both arms deliver 12/12 accepted, exact answers. There are zero newly failing
cases, zero wrong-flight selections and zero future/unavailable citations in
either arm. Every selected value/status matches its fact, each evidence ID is
exactly that fact's report ID, and all requested corrections preserve the named
flight. The four historical questions select the predecessor, not the anchor.
Both comparison questions contain both required facts. The “Before departure”
question correctly selects the current stand. Every response has empty unknowns,
as expected for these questions. The future F1C–F4C reports are absent from every
candidate prompt, despite their earlier event times.

Every fresh answer succeeds on its first attempt with stop finish and no
completeness error. No fresh retry, withholding, inference exception or guard
rescue occurred. Corresponding first prompts and raw selector strings are
identical across arms. Therefore this fresh pilot supplies non-regression
observations, not fresh evidence that the guard corrected a model error or
improved exact accuracy. Both arms' text and image startup records report success.
Each arm's shutdown log retains a semaphore resource-tracker warning; these
results do not establish resource-cleanup completeness.

The predeclared gate passes: exposed regression 12/12, fresh baseline 12/12 and
repair 12/12, no newly failing case and no delivered identity/support failure.
Recommend accepting the bounded guard/retry integration on this evidence and its
offline checks. No broad semantic superiority, general history comprehension,
unrelated defect closure or milestone completion follows from that recommendation.

Methodology and remaining limits:

- The runner uses only the frozen world and question/cutoff in `run_turn`; gold
  and metadata remain outside model input. Episodes start with separate sessions,
  preserve their three-turn order and use identical model/profile/settings. Arms
  run sequentially, baseline first, and source hashes are checked after each arm.
  The baseline source differs by guard integration/policy/retry instructions and
  its necessary relocated role-file path; initial selector prompts are unchanged.
- The outer lock does not pin the comparison runner or scorer itself. Each arm's
  lock does pin `scripts/history_evaluation.py`; the review used the matching
  current scorer. Preserve the runner/source records as published provenance,
  without implying that the original outer lock contained those missing hashes.
- Baseline mean elapsed answer time is 5.098 seconds (4.518–5.557), repair mean
  5.920 seconds (5.200–7.074). These are descriptive only. Root reports its CPU
  test suite overlapped the latter repair arm, with no concurrent model run.
  Sequential order and that load difference preclude a controlled latency claim.
- The fresh “For this flight” history wording is outside the guard's explicit
  pronoun regex. It succeeds through the model in both arms. This is a valid
  frozen observation, not evidence that the guard recognizes that wording.
- Each pilot history question has only one eligible earlier same-property fact.
  The guard checks presence of some earlier superseded fact; it does not prove
  nearest-predecessor selection in a longer received chain. Ambiguous anchors,
  repeated values and unrecognized language remain outside this narrow guard.
- This is a twelve-question same-family authored pilot with no fresh failing
  baseline cases. Preserve it as exposed evaluation evidence; further tuning
  cannot keep treating it as an independent fresh test.

This final review changed only this document. It made no inference calls and
changed no implementation, frozen fixture, labels, UI or media. Root separately
reports a passing 395-test suite, 160-record integrity and boundary checks; this
reviewer did not rerun or independently audit those broader checks.
