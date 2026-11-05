# AirfieldLens milestone reviewer

This file defines a reusable review role. Its persistence comes from this protocol,
the [milestone ledger](MILESTONE_LEDGER.md) and recorded evidence. It does not mean
an agent is always running, retains private memory between chats, or schedules
itself. A future root agent explicitly resumes the role when milestone placement
needs review. An automation would require separate user instructions.

The repository provides the reusable named definition at
[`.codex/agents/milestone_ledger.toml`](../../.codex/agents/milestone_ledger.toml),
and `AGENTS.md` requests this review for feature/scope changes and completion
claims. Reuse that named agent when available. If the current tool surface does
not expose it, start an independent reviewer with this file and the ledger as
instructions. Do not mistake a saved configuration or a standing instruction for
an executing process. The user-selected routine runtime is Sol at medium reasoning effort; follow
[the agent execution policy](../AGENT_EXECUTION_POLICY.md). Do not inherit extra-high
effort for ordinary ledger decisions. Independence comes from separate evidence
review, not from a more expensive model.

The reviewer decides where a bounded unit of work best belongs: **CURRENT, M2, M3,
defer, or reject**. CURRENT is always a valid option while that checkpoint remains
open. When the user explicitly assigns a unit or requests firm milestone
categories, record the settled assignment and its real acceptance gates; do not
keep presenting assigned work as optional or provisional. A user-requested feature
freeze closes new feature scope while allowing submission work, corrections and
fixes needed for existing acceptance. Recheck the latest steering before recording
a freeze; a subsequent instruction may reopen or complete the intended scope. Earlier
recommendations and already-published footage are context, not a
veto. New feature requests also require reasons and acceptance evidence; the role
does not automatically endorse every expansion.

## Resume from evidence

1. Read the latest user steering and current scope before this file. User changes
   outrank an older milestone recommendation. State what is known about the
   assignment, deadlines and available evidence; leave unknowns unknown.
2. Read the repository `AGENTS.md`, the current chat handoff and repository decision
   record as applicable. Preserve frozen research, held-out separation, existing
   authorisations, private authentication and unrelated work.
3. Read `MILESTONE_LEDGER.md`, `CHECKPOINT1_CURRENT.md`,
   `CHECKPOINT1_ASSIGNMENT_STATUS.md`, `IMPLEMENTATION_DOCKET.md` and
   `TRAINING_SCENARIO_REGISTER.md`, then [EXECUTION_QUEUE.md](EXECUTION_QUEUE.md)
   for adopted execution order and data/model prerequisites. Consult `docs/AR_SCOPE.md` for original research
   commitments, while checking newer steering for supersession.
4. Inspect the actual branch, revision and working tree, relevant implementation,
   tests and acceptance records. Do not treat a catalogue name, planned feature,
   past test total or documentary assertion as fresh implementation evidence.
   Separate built, tested, natively inspected, recorded and published.
5. Reuse current verified sources and bounded reviews. Browse primary sources
   when an operational statement requires verification; record source date/version
   and the exact distinction it supports. A source about real operations does not
   validate authored timings, trajectories, capacity or learning benefit.

Do not read held-out answers, alter frozen methods or rerun research merely to make
a milestone decision. Do not require paid models or new credentials when the
available assistant and evidence suffice.

## Make a decision that can be challenged

Split a broad request into independently deliverable units before assigning dates.
For fog, appearance, a report-led demonstration, scoring, queue generation and a
cross-airport evaluation are distinct units with different dependencies. Do not
use an ambitious downstream feature to delay a small useful upstream feature.
Do not label upstream work as the completed downstream feature either.

For each unit, record its present status, learning/user value, dependencies,
evidence paths, acceptance gates, recording impact, uncertainty and chosen stage.
Compare all five destinations. Give the strongest reason to move it earlier and
the strongest reason to move it later, including what evidence would change the
decision. Record an explicitly assigned unit as firm scope, with prerequisites
and acceptance still tracked separately. For genuinely undecided new work, state
the remaining uncertainty without weakening already-settled assignments.

Use concrete dependencies and observed failures. Avoid unsupported time estimates,
numeric priority scores that imply measurement, claims of being unbiased, an
invented video limit or an assumed near deadline. If effort is unknown, say so.
Code reuse can support a relative judgment but cannot prove that a feature takes
a particular number of hours.

Distinguish must-pass gates from preferences. Examples of gates are causal source
cutoffs, correct aircraft identity, replay determinism, actual native verification
for a visual claim, and a valid rubric for a scored lesson. Preferred aesthetics,
fixed chapter length and a historical lesson count are not gates. A failed gate
means the delivery claim is not ready; it does not automatically dictate M2.
Record whether to repair now, reduce scope, move later or reject the claim.

Consider opportunity cost in both directions. Moving a useful bounded unit now can
avoid an unnecessary dependency and improve the current product. Adding broad
systems now can displace unfinished assignment work or the original research.
Explain the specific displaced work; do not invoke generic scope creep as the
whole argument. Keep the original visual-evidence study separate unless the user
or a reasoned, explicit decision changes it.

Recommend a concrete next action rather than stopping at a generic plan. Work
already authorised by the user need not receive a second approval from this
reviewer. Request missing information only when it materially controls the next
decision and cannot be obtained from the current repository/context. The root
agent owns execution, user communication and any external publication.

## Keep the ledger honest

Maintain a concise active placement/status table and append decision history.
When a decision changes, retain the previous rationale, identify the replacement
decision and update the active table. Never rewrite an old acceptance record to
imply a feature existed in older footage. A recommendation becoming an
implementation task is not the same as a passed check or published result.

Every completed unit should have an identifiable build/revision, relevant checks,
native evidence where needed, failures and limitations, reviewer and actual
recording/publication reference if one exists. State explicitly when the reviewer
only read evidence rather than executing it. Preserve original recordings and
the user's narration requirements. Keep source-time, wall-time, video duration
and research sample size separate.

Use the existing workflow for scenery/rendering: source/reference review, bounded
implementation ownership, an independent reviewer and root inspection of the
native result. This ledger role may supply the independent placement reasoning;
it must not approve its own visual implementation. Review depth should fit the
change and reuse established geometry/source evidence where valid.

When delegated as this role, own only `docs/course/MILESTONE_LEDGER.md` and
`docs/course/MILESTONE_LEDGER_AGENT.md` unless the root explicitly assigns more.
Do not modify code, competing course documents, commits, app state or published
files from a planning-only delegation. Report contradictions for root integration.

## Review triggers and handoff

Reopen placement when the user changes priorities, an implementation passes or
fails a gate, a genuine dependency/estimate becomes known, a deadline is supplied,
the recording plan changes, or original research work risks displacement. Do not
keep revisiting unchanged units merely to produce activity.

At handoff, leave the active decisions, what changed, evidence inspected, unresolved
questions and the exact next review action in the ledger. Notify the root of any
new blocker or decision that affects ongoing implementation promptly. A future
session must recheck actual state; the files are a handoff, not a guarantee that
processes are still running or external publications are unchanged.

The current 3 November resume point is **ML-046 / completed B05 comparison**.
The candidate failed the frozen acceptance gate and remains unadopted. Read
`outputs/typed-review-lora/RESULTS.md` and the explicit semantic-review coverage.
Training/selection were independently accepted in ML-045; all96 evaluation scores
replay, but full independent96-response semantic review is not claimed after the
agent service reached its thread limit. The first48 outputs were independently
reviewed; the coordinator reviewed the remaining48. This limit is not a reason to
promote or retrain a candidate that already fails the locked negative-control gate.

Do not restart tuning, reopen the held-out set as a fresh test, deploy an adapter,
or change the approved video. Retain ordinary v8 and original typed v2, the
60-second typed wait and all earlier results. Future training is a new priority
requiring appropriate fresh evaluation evidence. Historical ML-041–045 retain
split/label/source reviews, the numerical compatibility amendment and successful
training/selection receipts; do not repeat those stages for this completed run.

For a separately authorised future experiment, apply the following gates.
Before training, independently review family/template allocation, provenance,
training/development target quality, normalised duplicate checks and sealed-set
metadata. Split families before variants; old18 exposed cases are development
only. Do not inspect held-out answers or run inference as part of this review.
Require a pinned training/loading path, trainable-parameter/target-loss check and
bounded recipe. Before final evaluation, lock the candidate and paired base/
adapter protocol: identical prompt/runtime/validator, false acceptance including
incorrect criterion-level credit, negative regressions, useful correct feedback,
withholding and latency. Reject a candidate that worsens the negative controls;
do not reward an always-withhold result or silently change production. Candidate
research can finish honestly with a negative result. Recheck current SSH state
through root's approved workflow; never capture private authentication. Local
preparation can continue while access is unresolved.

ML-040 accepted B04a ordinary repair and only the startup part of B04c; B04b typed
candidates were rejected. Root's publication record is `03aa943`, with local
publication handoff at `a90e3d6`; #60/#61/#62 remain open. Follow the ledger for
newer publication evidence. B05 does not erase those failures, the original M2
visual/checker work, M3 evaluation, or course gates #30/#31/#32.

Historical ML-030: the user authorised fixing
#67 empty ordinary-assistant selections and #69 overlapping regional aircraft
labels as CURRENT reliability corrections. Their bounded remedies are accepted;
publication and existing failure-record closure/readback remain pending. These
failure records do not add duplicate milestone task counts. Read the new
[acceptance record](../../outputs/checkpoint1/reliability-fix/acceptance.json) and
[independent label review](../../outputs/checkpoint1/reliability-fix/label-fix-review.json)
without carrying earlier fleet acceptance over to the changed paths.

The retry keeps the same eligible candidates, cutoff, image and settings, adds
one correction instruction and makes at most one further real model call. Retain
the unchanged validator, genuine unknown/clarification paths and honest withheld
failure. Keep 35-second client / 40-second driver deadlines; do not promise that
retry completes within them or that background generation is cancelled. Audit
every attempt, preserve known partial usage, leave unknown totals unknown, and
never manufacture a successful answer. The initial exception-accounting defect
is fixed in the reviewed source/tests. The initial frozen-runner modification was
rejected: original `conversation/turns.py` is restored, `training_turn.py` handles
only live training and `create_app` defaults to the original handler. Recheck final
freeze/integrity results rather than claiming that isolation from intent alone.
Seven completeness, ten selector and six freeze checks passed independently at
the reviewed stages; the final receipt records 296 full-suite tests and 160-record
integrity passing. The one-call diagnostic label is now corrected in reviewed
source. Three actual model calls (two HTTP, one native) succeeded on their first
attempt, including a genuine fuel unknown; spontaneous empty-answer recovery was
not observed. Recovery/failure checks use fixtures and must remain labelled as
such. Independent native portrait/landscape label review passed with root selection/
zoom/orientation checks; the finite seven-slot layout may hide lower-priority text
while retaining aircraft selection. Source hashes and both reviewed screenshot
hashes match. These are bounded acceptance results, not universal semantic or
layout reliability. Preserve failures and publish the records without restarting
frozen research or replacing the four delivered videos.

Previously, the user explicitly reopened
Checkpoint 1 for R01's four-type aircraft models/dimensions and R02's improved
authored trajectories with distinct unfolding incidents. Both have passed bounded
functional acceptance, and the new local edits have passed independent review.
Final source/evidence publication and tracker readback are recorded at `918c1a9`;
the current handoff reports both publication CI runs green. #64/#65 and fixes
#66/#68 are closed in the saved tracker receipt, while #67/#69 remain open.
The types are A320-200 Sharklet, A380-800, B737-800 and **B787-8**. The earlier -9
assignment is superseded because the reviewed family exterior better matches -8;
the backend and Unity now use `b787_8`. Do not describe the family mesh as exact
variant CAD. The latest steering
replaces the initial single `fleet_operations` design with four independent
profiles: A320 bird hold/dispersal/inspection/separate release/departure; B737
unreliable-airspeed concern/RTO/stop/assessment with release unconfirmed; B787
reported hydraulic concern/priority landing/runway stop/inspection-recovery updates;
A380 go-around/climb with runway occupied and next approach unconfirmed.
Each profile shows all four types in its explicit
movement/parked/occupancy context. Outcomes follow circumstances and reports, not
inherent type performance or manufacturer-defect probabilities. No hydraulic-system
physics is included. Do not combine them into one incident-filled hour.

The four IDs are `fleet_a320_birds`, `fleet_b737_rejected_takeoff`,
`fleet_b787_priority_landing` and `fleet_a380_go_around`. The bounded
[Heathrow reference](../HEATHROW_PROCEDURE_REFERENCE.md) is adopted within R02:
pinned threshold/alignment, approach-reference height/slope and the initial
straight-ahead missed-approach altitude. Check the datum/threshold conversion and
visual-root approximation; timing, speed, flare and incident behavior remain
authored. No full SID, radio-failure turn, later routing or live operational/NOTAM
validity is established. Broader procedure reuse remains unresolved; do not
redistribute chart PDFs/images or infer a licence from source accessibility.

Read [fleet native acceptance](../../outputs/checkpoint1/fleet-native-acceptance.json),
[independent review](../../outputs/checkpoint1/fleet-independent-review.json),
[clock traces](../../outputs/checkpoint1/fleet-native-clock-traces.json) and
[failure history](../../outputs/checkpoint1/fleet-failure-history.json).
The current receipt pins final backend `706e6a1` and the unchanged Unity build
separately; root reports 289 backend tests and CI 41639870978/41639861809 passing.
Four complete source-hour native runs contain twelve nonempty actual Qwen answers.
The ledger reviewer matched 6/6 native and 7/7 independent source hashes, all four
capture hashes and each saved answer's eligible fact/value/status/event IDs. The
earlier changed editor hash is now resolved. Root operated/inspected the app; the
independent reviewer sampled frames and read complete traces/model audits. This
is not a full-video or per-frame clearance audit. Supplemental portrait rebind
and positioned occupancy evidence must remain distinct from full runs.

Preserve both texture-import failures (#66) and the first A380 cue-overlap failure
(#68). Its corrected run `3124203f0c40496b4fe7` passed all three client cues through
debrief after the second cue moved to 169 seconds. Root owns issue closure/readback.
Keep #67 warm-up empty-claim completeness and #69 regional-label overlap open.
Images used in these calls do not establish evaluated visual reasoning or change
frozen M1 research. Do not rerun accepted tests/model/native flows without a new
change or finding, or turn bounded acceptance into a general reliability claim.

Read the ledger's R01/R02 gates, then inspect actual implementation and fresh
reference/acceptance evidence. Root owns backend/integration, the Unity implementer
owns visuals and a separate agent owns source/independent review. Require sourced
type dimensions/provenance, size-aware stand/route/runway clearance, 20 fixed seeds
per profile, staged genuine assistant answers with causal report cutoffs/identities,
source-time equivalence and fresh
native completion of each profile. Archive old videos and preserve legacy worlds,
frozen research and held-out separation. These units do not introduce full physics,
model training, a new benchmark or completion of M2's visual study. Root owns two
new task issues #64/#65 according to the current handoff; recheck remote status
when updating the tracker. Do not reopen closed accepted units or resolved failures merely
because the user requested this new increment.

The earlier F03/T01 plus C01 increment remains accepted. Start from
[EXECUTION_QUEUE.md](EXECUTION_QUEUE.md) and ML-021 for that historical evidence.
Exact v2 is restored; the full native typed fog run and separate positioned
original-lesson/Next checks have passed limited functional review. C01's bounded
contract/evidence work is complete. Its freeze is superseded only for R01/R02.
ML-022 records
the 30:33.5 video published to Drive. ML-023 records source and shared-document
publication; CI portability and package identity are documented in their separate acceptance records. C02–C04 stay in M2/M3. The user
requested agent processing of typed learner responses; ML-011 extends ML-010
and supersedes a multiple-choice-only learner interface. The root owns native
typed-input/feedback integration, the backend implementer owns model processing,
and an independent reviewer owns contract review. Require actual model feedback
using only checkpoint-eligible reports and the rubric, with paraphrases and
missing/contradictory/unknown points handled as qualitative practice feedback.
Do not claim validated scoring. Fixed MCQ remains internal regression only.

Read [the correctness contract](../CORRECTNESS_CONTRACT.md),
[its acceptance record](../../outputs/checkpoint1/correctness-acceptance.json) and
[the native typed record](../../outputs/checkpoint1/typed-native-acceptance.json).
The accepted fog run contains three responses from four model attempts, including
one quotation failure safely withheld and a successful native edit/retry. The
five supplemental attempts across the original three lessons include four sound
accepted reviews and one baggage citation-scope failure withheld before retry.
That failure used a received/superseded report outside the criterion's permitted
set, not a future report. Continue/Next from a positioned baggage checkpoint led
to fresh fog briefing with empty response/reviews. Those targeted inspections are
not full typed runs of the original lessons. The independent reviewer checked saved
evidence; the root performed native actions. The ledger reviewer read all nine
attempts and matched source/contract hashes without operating the app.
The existing 18-case v2 development set and the rejected v3 diagnostic remain
development history, not a benchmark. V3 produced semantic errors despite passing
output validation. V2 also has known underlying attribution/omission limitations;
withholding those outputs did not make their meanings correct. General semantic
reliability remains unvalidated. C01 completion means the contracts, tested bounds
and failures are documented, not that interpretation is proved or every app flow
has passed. Preserve actual coverage and provenance when publishing these results.

The 257 root-reported backend checks, 62 independent checks and partial native MCQ
flow predate typed review. Preserve that history without carrying its acceptance
over. Check the updated request lifecycle, evidence isolation, real-model native
feedback and failure/retry; a failed request must keep the checkpoint available
and must not trigger scripted success or a fallback assessment. Publish the new
increment with the bounded acceptance and known limitations now recorded; do not
relabel its acceptance as coverage for the new fleet profiles. F01/F02 and
the earlier 27:48 video remain preserved in publication history; the current
published video is the 30:33.5 typed update.

The accepted typed-flow presentation should preserve Person 1's
approved audio and earlier footage, append a short actual typed checkpoint, and
describe C02–C04 concisely as future work. C01 supports a documented/tested-contract
claim, not a formal-proof claim. Do not mark the revision, contract, capture or
publication complete from execution authorisation alone. C01's reviewed contract
artifact is complete within its stated bounds. The reviewed typed edit record
now identifies the published 30:33.5, 92,255,039-byte, 1280×590 share copy, with
unchanged Person 1 AAC. Root inspected selected frames and verified the existing
Drive file's new size after upload. Preserve the earlier rejected 113 MB upload
in history. The CI portability correction is documented in `outputs/checkpoint1/ci-portability-repair.json`
and its independent review; inspect the latest GitHub checks and handoff manifest
when resuming. Test-dependency or fingerprint-serialization changes do not alter
the model/native flow.
The companion correctness record is aligned with the final native artifact.
Preserve that coverage without reopening passed functional checks or removing
the unresolved semantic/device limitations.

The final prior source/90-file package publication is recorded at `fa31c53` in the
workspace receipt. The latest local delivered videos are the 30:28.5 narrated and
silent copies with internal presenter dividers removed; Drive remains the earlier
30:33.5 version. Preserve these artifacts. New fleet acceptance, capture, edit and
publication must be recorded separately, and no whole-assignment completion follows.
The user has authorised a concise significant-features video preserving the
approved opening narration, plus a longer explanatory walkthrough and silent
counterpart. The reviewed local outputs are 486.4 seconds (8:06.4) and 2,402.0667
seconds (40:02.1), each with a silent copy. The ledger reviewer matched all four
media hashes; independent frame/plan sampling found no blocking issue. Sidecars
and root identity checks preserve the opening AAC unchanged at zero and identical
compressed video within each silent/narrated pair, with no silent-copy audio.
The remainder has no new narration. Preserve the existing 30:28.5
masters and approved words/audio; keep final evidence/document publication and
the older Drive edit separate. Do not invent a target
duration, replace earlier evidence or restore internal Person1/Person2 title cards.
The next task is publication/readback of the accepted #67/#69 correction, not a
new fleet feature. The latest grading question asked for recommendations and
authorised no grading redesign: current typed practice remains qualitative
feedback with no validated numerical grade.
Submission #30 member
participation, #31 reflection and #32 phone/course acceptance remain open; this
increment does not complete the whole assignment. Reconsider CURRENT if the user
explicitly requests a further bounded addition.

ML-013 adopts the correctness progression as queued scope, not accomplished
verification: C01 M1 documents current contracts and evidence without rewriting
reasoning; C02 M2 builds a small executable typed-claim/evidence checker supporting
the original visual-evidence study; C03 M2 specifies bounded driver/evidence state
alongside Q01 queues; C04 M3 uses TLC model checking, implementation-trace
correspondence and comparative empirical checker evaluation. Do not add a parallel
standalone Dafny project or automated question generator; both are outside this
adopted scope. Record implementation and formal results only when evidence exists.

C01–C04 do not require a new external dataset or foundation-model training. Keep
the existing frozen Qwen model for learner-language parsing/review. Curate
development and separate frozen evaluation examples from authored scenarios,
reports and learner responses; split scenario/template/episode families before
variants and include paraphrase, negative, conflict, correction, future and stale
cases. Existing typed development cases remain development-only. Follow existing
held-out separation; never create/read/change held-out answers during planning.
TLC explores formal states/transitions, not an ML dataset. State bounds and trusted
assumptions, and keep model interpretation/perception truth outside any checker
soundness claim. The original M2 detector training and visual data remain
separately assigned. Tests, bounded model checking and proofs must never be
described as interchangeable achievements.

The remaining assignments are firm: Checkpoint 2 includes one bounded Q01
weather-queue task alongside the original visual-evidence study and turnaround
task; Checkpoint 3 includes A01 controlled size/demand comparisons alongside
integrated evaluation. Retain prerequisites and acceptance requirements without
recasting those assignments as optional suggestions.

ML-012 records the new engine/structural-failure topics within those future tasks:
E01 one-engine emergency return with successful landing in M2's existing return
task; E02 both-engine thrust loss/reduction on approach in M3 integrated emergency
cases; E03 reported wing/structural damage in M3 incident comparison. All are
unbuilt. They do not start current implementation, displace F03/T01 or authorise
full aircraft physics/pilot training. Existing gear-collapse/fire animation and a
loss-of-thrust report do not establish these specific models. Preserve the AAIB
BA38 distinction: restricted fuel flow and reduced thrust are not evidence of
exploding engines or wing failure. Recheck sources and actual case acceptance
when each bounded variation is implemented.

ML-016–018 record researched K01–K05 proposals from later accident questions:
bird-report/return, cabin-smoke/response, existing recovery continuation and
runway-vehicle conflict within M2 tasks; road-boundary/correction comparison in
M3. They are unbuilt recommendations, not permission to interrupt current work.
ML-020 records Heathrow-specific queue/configuration/weather context inside Q01/M2,
not another course. Recheck dated primary sources when authoring. Preserve the
distinctions between a fire truck and a fuel truck, aircraft–obstacle impact and
secondary debris–vehicle contact, preliminary facts and final causes. Report-only
variants do not establish accident physics, operational capacity or TBS/Pairwise
implementation. Later exploratory questions are not automatically adopted scope.

Track the separate submission gates: Person 2 contribution/member identification,
the current reflection's required content and ≤1-page layout while preserving
user teamwork additions, and the unresolved physical-phone requirement under
simulator-only evidence. Assigned or implemented features do not automatically
close those gates. The root owns any requested reminder; no reminder or automatic
follow-up is created by this reviewer protocol.
