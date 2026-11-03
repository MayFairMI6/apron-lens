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
an executing process. The definition inherits the default model; this role does
not need a model change to establish independence.

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

The current 3 November resume point is publication of accepted F03/T01 plus C01
in Checkpoint 1. Start from [EXECUTION_QUEUE.md](EXECUTION_QUEUE.md) and ML-021.
Exact v2 is restored; the full native typed fog run and separate positioned
original-lesson/Next checks have passed limited functional review. C01's bounded
contract/evidence work is complete. Current feature scope is frozen. ML-022 records
the 30:33.5 video published to Drive; source/shared-document/ZIP publication remains
pending. C02–C04 stay in M2/M3. The user
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
increment with the bounded acceptance and known limitations now recorded; current
feature scope is frozen. F01/F02 and
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
in history. The next action is source/shared-document/ZIP publication, not another
feature or repeated native run.
The companion correctness record is aligned with the final native artifact.
Preserve that coverage without reopening passed functional checks or removing
the unresolved semantic/device limitations.

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
