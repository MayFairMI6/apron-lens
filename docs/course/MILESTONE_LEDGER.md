# AirfieldLens milestone ledger

The active planning decision is to implement a fog visual profile and one bounded,
report-led low-visibility demonstration in the **current Checkpoint 1**. There is
no established technical reason to make these wait for the visual-evidence study.
The reconsideration also recommends a **bounded scored fog lesson for CURRENT as
the next increment**, subject to its own rubric and learner-flow acceptance. It
is not part of the current F01/F02 delivery or acceptance claim. The demonstration's received
reports supply a distinct assessment of partial cancellation and unconfirmed
departure authority; no visual-evidence research dependency remains. A
weather-driven queue model belongs in M2 development; a controlled comparison
across airport layouts and demand belongs in M3 evaluation. These are separate
decisions, not a single weather feature assigned wholesale to a later milestone.

At the review baseline all five units below were unimplemented. F01/F02 are now
implemented, accepted in the native simulator, recorded and included in the
published 27:48 Drive video, with the reviewed evidence linked below. The
implementation is also committed and pushed as `c81812167361a73ceca8d944ffc3510bac1335ae`;
PR #22 remains open and unmerged. F03 is planned and unbuilt.
Placement, implementation, acceptance and publication are separate statuses in
this ledger.
The reusable reviewer instructions are in [MILESTONE_LEDGER_AGENT.md](MILESTONE_LEDGER_AGENT.md).

## Review basis and constraints

Review baseline: 2 November 2026, branch `codex/checkpoint1-controller-training`,
commit `8a96417538c3024abd75a5b3e5abe5dfe266f73c`, initially clean working tree.
The reviewer read the current course documents, actual environment/session/lesson
code and relevant tests. This review did not execute Unity, rerun the local model,
inspect the app or independently validate the published video.

The latest user steering asks why fog cannot be done now, welcomes justified scope
changes, and asks for a persistent decision process rather than automatic M2
deferral. The supplied assignment requires a smartphone app, a video identifying
each member before their contribution, and an achievement/reflection of at most
one page covering functionality, teamwork, future checkpoints, coordination,
meetings and decision-making. It supplies no video duration limit. No imminent
deadline or measured implementation estimate has been established. Neither may be
invented to justify placement.

The current recorded product has three scored lessons, a live report-grounded
local assistant, and clear/rain/snow/dusk presentation controlled by the external
clock. The review baseline publication was 24:18. The current published edit is
27:48 with Person 1's approved speech edit preserved; Person 2 is pending.
The assignment-status document has been updated
to distinguish this publication from the archived 8:27 capture and to preserve
the user's added teamwork text in the editable reflection. That current document
still needs final content and one-page-layout review; do not replace it with the
older blank local template. Physical-phone execution remains unverified;
the user's instruction to use the simulator for now remains in force. The reviewer
does not silently waive the smartphone requirement or make device work a new gate
for a visual supplement.

The original M2 visual-evidence research remains a distinct commitment. It asks
whether images and viewpoint add reliable information, with separate development,
freeze and evaluation. A report-led fog example cannot satisfy that question.
New work must not silently crowd it out or rewrite the frozen M1 results. If the
combined M2 workload becomes too large, reduce or reschedule the new additions
with a recorded tradeoff before displacing the original study.

Evidence: [current checkpoint](CHECKPOINT1_CURRENT.md),
[assignment status](CHECKPOINT1_ASSIGNMENT_STATUS.md),
[implementation docket](IMPLEMENTATION_DOCKET.md),
[scenario register](TRAINING_SCENARIO_REGISTER.md),
[original AR milestones](../AR_SCOPE.md),
[repository workflow](../../AGENTS.md).

## Active placement decisions

`CURRENT` means the still-open Checkpoint 1 product/presentation, not a rerun of
the frozen M1 research. `Defer` means no milestone commitment until a named trigger.
`Reject` means exclude the described scope unless the reason changes. Placement
and delivery status are tracked separately.

| Unit | Delivery status at review | Active decision | Why this placement | Owner / next action |
|---|---|---|---|---|
| F01 — fog visual profile | Implemented; native acceptance/capture passed; edited video published to Drive; source pushed as `c818121` | CURRENT | Extends an existing external-clock presentation path; it does not require a detector, scoring or queue generation. | Delivered for this increment; preserve evidence and review future changes. |
| F02 — bounded report-led fog demonstration | `fog_visibility` implemented; source-hour native/model acceptance/capture passed; edited video published to Drive; source pushed as `c818121` | CURRENT | A distinct, source-supported information task uses the available assistant and standalone demo machinery. | Delivered for this increment; preserve unscored status. |
| F03 — scored fog lesson | Planned next increment; not built or accepted | CURRENT, conditional on separate assessment acceptance | The demonstrated report sequence now supports a distinct test of partial cancellation and authority; the existing assessment machinery can support a bounded new lesson. | After this F01/F02 increment, author the short lesson/rubric, preserve the demo, and verify targets, evidence cutoffs, feedback and complete native learner flow. |
| Q01 — weather-driven arrival/departure queues | Not built or accepted | M2 development, conditional on defined scope | Introduces a new demand/capacity/reservation system beyond scripted movement and visual weather. | Specify one illustrative queue task and invariants, then review cost against the original M2 study. |
| A01 — airport-size/demand comparisons | Not built or accepted | M3 evaluation, conditional on a stable task | A meaningful comparison needs a shared task and controlled variation, rather than several attractive maps. | Define the comparison after the task/driver stabilises; defer extra airport reconstruction until needed. |

## Alternatives considered

The reasons below express judgment from the inspected code and learning objective.
They are not measured engineering estimates or an assurance of impartiality.

| Unit | CURRENT | M2 | M3 | Defer | Reject |
|---|---|---|---|---|---|
| F01 | **Selected.** Existing weather interpolation, validation and restoration are reusable. | Reasonable if native readability, material compatibility or clock restoration fails; otherwise an unnecessary dependency on research. | Too late for this bounded presentation improvement unless a new rendering architecture is deliberately selected. | Appropriate only while a concrete renderer/verification blocker is unresolved. | Reject calibrated-visibility or operational claims from a cosmetic effect; retain the visual profile. |
| F02 | **Selected.** Report timing and changed restrictions already match the assistant's evidence model. | Reasonable if the selected-flight report representation cannot faithfully express the task without wider changes. | Little benefit from waiting for integrated evaluation before building the bounded case. | Appropriate if primary-source interpretation or actual model/UI failures leave its lesson misleading. | Reject inferred clearances or claims of visual recognition; retain a source-limited report task. |
| F03 | **Selected on reconsideration.** The report sequence supplies a distinct, bounded assessment; verify its independent rubric and learner flow now. | Strong alternative if current assignment work takes precedence or learner-flow integration proves broader than the bounded design; no remaining prerequisite inherently requires M2. | Consider only if the assessment is expanded to depend on later visual evidence or comparative evaluation. | Appropriate if questions merely repeat an existing hold/release lesson without testing partial cancellation or authority. | Reject unvalidated competence claims or a decorative score; retain a properly defined fog lesson. |
| Q01 | Possible only after an explicit, bounded design is implemented and passes reservation/clock checks. Existing fog support alone does not establish readiness. | **Selected.** Build one authored restriction-to-backlog/recovery task and retain the original visual study. | Appropriate for the integrated stress test or if new driver work would displace the original M2 commitment. | Appropriate if no learning decision requires generated queues or capacity assumptions cannot be stated honestly. | Reject operational-capacity claims without calibration and weather automatically issuing clearances; illustrative queues remain viable. |
| A01 | A labelled static contrast could be shown now, but would not complete a controlled size/demand comparison. | A small development prototype is reasonable if it is needed to validate Q01 or an obstruction task. | **Selected.** Compare a stable task with physical layout and traffic demand varied separately. | Appropriate if one setting answers the research/learning question or suitable layouts are unavailable. | Reject shrinking Heathrow/aircraft and naming the result a different real airport, or treating aircraft count as learning quality. |

| Unit | Strongest reason to move earlier | Strongest reason to move later |
|---|---|---|
| F01 | It makes the user's requested condition visible using an already demonstrated mechanism. | Native fog obscures the interface/selection or cannot render consistently with the existing materials and camera views. |
| F02 | It adds a concrete information distinction now and uses the available assistant without waiting for vision research. | Faithful handling requires unplanned cross-flight or airport-wide evidence changes, or real answers cannot be shown accurately. |
| F03 | The working report sequence establishes a distinct objective, and scoring adds learner decisions and feedback using existing infrastructure without waiting for vision research. | The demonstration already covers the domain; scoring adds another implementation/native check cycle while required participation, device evidence and reflection review remain incomplete. |
| Q01 | The user prioritises generated traffic, and a limited driver is ready with convincing reservation, report-cutoff and clock-equivalence evidence. | Driver complexity or calibration needs would consume the original M2 visual-evidence work; move the queue extension before changing that study. |
| A01 | A reusable, validated task and sourced or explicitly fictional layouts already exist, making the comparison a small extension. | Layout, demand, reporting delay and task difficulty change together, so results would be uninterpretable; fix the design first. |

Implementation effort and native capture/edit time remain **unknown**. Code reuse
supports the relative dependency judgments above, not a promise that a feature is
quick. Published footage creates real editing work, but it is not a prohibition
on adding current work. The absence of a video limit also does not mean every
feature needs a long chapter.

Verified development state: `fog_visibility` has one parked aircraft on the mapped
T3 apron, ordinary question cutoffs at 650, 2450 and 3050 source seconds, and
separate reports for LVP cancellation and safeguarding cancellation. Appearance
improves by source time 2200 while restrictions remain reported. The
[independent fog source/code review](../../outputs/checkpoint1/fog-independent-review.json)
records no blocking source, clock, restoration or renderer-code finding, 16
independently executed targeted backend tests and review of the 46 actual Metal
pixel/weather checks.

The consolidated [fog acceptance](../../outputs/checkpoint1/fog-acceptance.json)
records 249 backend tests, 175 Unity checks, a native build and run
`ddf9cb22710cd0584d41` reaching 3600 source seconds/debrief in 214.948 seconds of
wall time. Its three actual accepted Qwen3.5-9B answers at 650, 2450 and 3050 had
latencies of 11.140, 12.472 and 11.749 seconds. The root inspected dense/clearing
fog, correct restrictions, landscape/upright portrait, Sources scrolling and
fog-to-clear restoration. Upside-down portrait remains intentionally disabled.
A separate native reconnect inspection shows the same 29:50 clock in two
disconnected captures, then 33:35 after resumption; its fog view stayed fixed
while disconnected. The initial editor-callback failure and correction are
preserved. No native request failed in the accepted run.

This milestone reviewer read that acceptance record, independently matched all
eight recorded source hashes to current files, confirmed all eight referenced
screenshots exist, and checked each saved answer against the latest eligible A1
restriction in the deterministic seed-17 scenario at its actual cutoff. All three
matched the correct fact ID, value, current status and source. The reviewer did
not independently operate or visually inspect the native app. These checks
support F01/F02 acceptance and the captured report task, not a model benchmark,
scored lesson or physical-device run.

The subsequently reviewed [fog edit record](../../outputs/checkpoint1/fog-demo-edit.json)
documents the published [27:48 recording](https://drive.google.com/file/d/1uHIweEFSlO4CRb8-VyNM7aZUd4mhsMhQ/view):
1668.4667 seconds, 104,760,296 bytes with Person 1 audio. The earlier video prefix
is preserved through 24:12.4667; the former final card is replaced by the fog
chapter and an updated next-work card. The recorded app excerpt uses native
capture seconds 8–214 with no source-time or report-text edits. The original and
output compressed Person 1 audio hashes match
`e7de3c293981e1c1190eb687ae2ef5f104cfc5ef26cc221c83704acaaa1efb98`.
The root reports completed upload and readback verification of the recording-plan
and scenario-register Google Docs. This reviewer read the edit record and checked
that local current/register documents now show the 27:48 video, built A14 demo and
unbuilt P04 scored extension; it did not independently fetch the Drive video.
Source publication is complete in
[`c81812167361a73ceca8d944ffc3510bac1335ae`](https://github.com/MayFairMI6/apron-lens/commit/c81812167361a73ceca8d944ffc3510bac1335ae)
on [`codex/checkpoint1-controller-training`](https://github.com/MayFairMI6/apron-lens/tree/codex/checkpoint1-controller-training).
This reviewer independently confirmed the local commit and matching remote branch
head using `git ls-remote`. The root reports that [PR #22](https://github.com/MayFairMI6/apron-lens/pull/22)
has updated metadata and the same head, and remains open/unmerged; no merge is
implied. This final publication-record update follows the implementation commit.

This evidence changes the F03 dependency judgment. Its distinctive assessment is
whether the learner keeps the remaining safeguarding restriction after LVP
cancellation, then keeps departure authority unknown after safeguarding ends.
An improving scene is insufficient evidence of either release. Unlike an
automatically answered demonstration, scoring records the learner's own decision
at a cutoff and can explain the specific mistaken inference. This is a proposed
assessment benefit, not a measured learning improvement.

The strongest counterargument is that F02 already presents the information, so a
fourth lesson adds assessment rather than another hazard category and requires
another integration, build and native learner check. The current assignment also
has unfinished participation/device/reflection items. Those costs are real, but
there is no measured effort estimate or known deadline showing they require M2,
and the user explicitly welcomes useful current scope changes. A narrowly scoped
lesson is therefore selected for CURRENT. Reopen the decision if the bounded
implementation exposes broader dependencies or the user changes priorities.

## Acceptance records to collect

These are must-pass gates for the stated delivery claims. The current status and
linked acceptance above establish which have passed; this checklist alone does
not. A preferred chapter length, number of extra
maps, aesthetic density, or a desire to keep exactly three lessons is a preference,
not a technical gate. The existing docket's 20-seed supplement check is retained
for a new scenario; a visual-only profile needs boundary and rendering checks,
not an invented statistical sample.

### F01 — fog visual profile

Keep appearance driven by external source time, including freeze/pause,
acceleration, reconnect and retry. Give fog its own validated profile. Confirm that
the same source time gives the same appearance and that returning to clear or
another condition restores the appropriate camera/lighting/fog state. Default
clear/legacy inputs must remain compatible. The environment alone must not create
reports, change answer keys, move aircraft or alter performance.

Inspect the actual native simulator in landscape and portrait, including overview,
close view, aircraft selection, reports and Sources. Fog must be perceptible without
making the teaching interface unusable. Check compatibility with the scene's
materials rather than assuming a global fog setting affects every object. Record
the build, source revision/hashes, profile/source-time windows, captures, failures
and reviewer. Do not label fog density as measured runway visual range.

Dependencies/evidence: [driver environment](../../backend/training_environment.py),
[session clock](../../backend/training_session.py),
[Unity weather](../../unity/SurfaceSafetyCoach/Assets/SurfaceSafety/Scripts/TrainingWeather.cs),
[environment tests](../../tests/test_training_environment.py),
[Unity weather checks](../../unity/SurfaceSafetyCoach/Assets/SurfaceSafety/Editor/WeatherVerification.cs),
[earlier weather acceptance](../../outputs/checkpoint1/weather-acceptance.json).
The earlier acceptance is a precedent, not acceptance of fog.

### F02 — report-led fog demonstration

Use one bounded case with its own run identity, ordinary assistant questions and
explicit event/receipt times. Its objective is to identify the reported operating
state and what remains restricted as updates arrive. A suitable sequence is
safeguarding requested/confirmed, procedures in force, procedures cancelled while
safeguarding remains, then separate safeguarding cancellation. A final update must
not imply an individual departure clearance unless that fact is separately
reported. The source explicitly distinguishes these stages; it does not validate
the app's timings. [Heathrow OSI052 v3.1, sections 3, 6–7 and 13](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASWeather_OSI_052_v3-1.pdf).

Keep all questions within the actual selected-flight evidence contract. If an
airport-wide condition affects a flight, make that applicability explicit in the
authored reports. Fog appearance alone must not activate/cancel restrictions or
become an observation claim. Include an improvement in appearance before the
received cancellation, or a delayed update, so report timing matters.

Verify deterministic worlds and causal report availability across at least 20
seeds, normal/demo equivalence at matched source times, stale-run/cutoff handling,
and the movement shown for affected traffic. Do not invent a queue generator for
this case. Capture actual local-model answers before and after relevant changes,
including the partial cancellation. Review both content and cited reports;
validator acceptance alone does not prove the intended answer was correct. Retain
failed/timeout requests. Complete a native run and inspect both orientations. Use
an unscored label, record provenance and update the published feature claims only
after the evidence exists.

Dependencies/evidence: [standalone demo builder](../../backend/runway_scenarios.py),
[training session](../../backend/training_session.py),
[demo tests](../../tests/test_runway_scenarios.py),
[session tests](../../tests/test_training_session.py), scenario-register P04,
and [earlier native demo acceptance](../../outputs/checkpoint1/runway-acceptance.json).
The source review confirms a useful distinction; new report design and model
acceptance remain work to do.

### F03 — scored fog lesson

Define the distinct objective, answer cutoffs, eligible evidence, defensible
distractors, deterministic key and explanatory feedback before declaring this a
lesson. Cover at least an active restriction, partial cancellation and remaining
unknown or separate release. Review whether this teaches more than the existing
hold/release pattern. Scoring must depend on reports available at the cutoff,
not on future messages or the weather animation.

Prefer a separately labelled short fog lesson with an explicitly authored compact
report/appearance timeline within the existing 210-second lesson contract. Preserve
the accepted one-hour demonstration and its actual question cutoffs. Three new
fixed-cutoff questions should test active restrictions despite improved appearance,
partial cancellation, and departure authority still unconfirmed after safeguarding
cancellation. Vary the correct-option position and use plausible, mutually
exclusive distractors. Retiming is illustrative; do not present it as real response
duration or as the same run shown in the demo.

Implement and verify briefing, checkpoint pause, answer submission, retry
idempotency, feedback, debrief and next-lesson routing. Check target aircraft and
later-report selection explicitly: current session code has exercise-specific
A2/A3 assumptions and a 210-second lesson end. Either fit the new lesson to that
contract deliberately or make a reviewed generalisation. Do not append questions
after the current lesson endpoint. Run the scenario's seeded/cutoff checks and a
complete native learner flow. If assistance is shown as part of this lesson,
verify that actual path too. These checks are manageable additional work, not a
reason that scoring is inherently impossible now.

The known incremental work is a short report/probe definition, scenario/target
routing, timing/evidence checks, correct- and incorrect-answer feedback, restart
and next-lesson regression, a native build/completion and accurate course/recording
claims. No new weather renderer, capacity model, external model or model change is
required by this scope. Its elapsed cost has not been measured. Actual accepted
demo answers cannot substitute for this new lesson's acceptance.

Dependencies/evidence: F02 report design, [lessons](../../backend/lessons.py),
[session](../../backend/training_session.py),
[lesson-flow tests](../../tests/test_training_session.py),
[existing lesson acceptance](../../outputs/checkpoint1/lesson-acceptance.json).
No fourth lesson or learner outcome is established by those existing records.

### Q01 — weather-driven queues

Define one task, an illustrative demand schedule, separate arrival/departure
queues, explicit operating-state reports, runway and stand reservations, and
recovery behavior. Keep schedule, revised estimate and actual movement distinct.
Every waiting reason needs a source and availability time. Public NATS material
supports the qualitative link between low visibility, spacing precautions and
possible delays; it does not calibrate this project's capacity or delay rates.
[NATS low-visibility explanation](https://nats.aero/blog/2025/10/low-visibility-procedures-what-you-need-to-know/).

Require no overlapping runway reservations or stand overbooking, continuous
movement without teleportation or off-route shortcuts, bounded accumulation,
and defined behavior on stale updates. The same seed and source time must yield
the same queues and eligible reports at 1× and 30×, including pending answers and
checkpoint pauses. Show where delayed arrivals are represented; do not imply an
operationally valid holding pattern from arbitrary aircraft placement. Measure
queue length, waiting and recovery separately from learner accuracy. Review
geometry and native readability before declaring the exercise delivered.

Dependencies/evidence: scenario-register P09; current
[lesson reservations](../../backend/lessons.py),
[flight cycle](../../backend/flight_cycle.py) and clock tests are reusable parts,
not an implemented capacity/demand scheduler. Q01 need not await a vision model,
but it must not consume the original M2 study without an explicit decision.

### A01 — airport-size/demand comparison

Define the comparison question and a stable task before producing more settings.
Vary traffic demand while holding task, reporting delays and layout fixed first;
then vary layout complexity separately. Use sourced layouts or clearly labelled
fictional airports. Preserve aircraft dimensions, turning envelopes, route widths
and reservation constraints; do not use uniform miniature scaling as an airport
size model. Verify comparable evidence availability and record confounds.

Use repeatable cases and native views, then report missed updates, unsupported
conclusions and task completion alongside latency/time. A claim about learner
benefit needs an appropriate learner study; a simulation comparison alone does
not establish it. More aircraft or more terminal geometry is not an outcome.

Dependencies/evidence: scenario-register airport-scale proposal, a stable Q01 or
another validated common task, [mapped-setting provenance](../../data/geography/README.md)
and [connected-setting acceptance](../../outputs/checkpoint1/connected-setting-acceptance.json).
The present Heathrow scene supplies one setting, not an airport-size comparison.

## Recording and assignment impact

| Unit | Recording impact if delivered | What the presentation may claim |
|---|---|---|
| F01 | Add a clearly identified fog supplement or integrate it with F02; preserve prior footage/audio and note the actual capture windows. | Fog presentation on the external clock, without calibrated visibility or weather-driven operations. |
| F02 | Add a distinct case chapter with real report/answer evidence and a matching Person 2 cue; retain failed requests in acceptance records. | A working report-led low-visibility demonstration, not a scored lesson or a vision result. |
| F03 | Show a representative checkpoint and debrief from the complete verified lesson; update lesson count consistently. | The implemented deterministic assessment, without a claim of professional competence or measured learning benefit. |
| Q01 | Capture the completed queue/recovery task only when its driver is verified. | Illustrative demand/capacity behavior under stated assumptions; no real Heathrow throughput validation. |
| A01 | Show controlled, comparable examples after the study design is fixed. | The particular settings/metrics tested; no universal claim that airport size determines difficulty. |

Any new edit must preserve Person 1's approved speech and archived recordings,
identify the contributing members as required, and avoid representing old footage
as a fresh run. Person 2 participation, physical-smartphone verification and final
review of the current reflection's coordination/meeting content and one-page layout
remain submission work. Preserve the user's teamwork additions in the editable
reflection. These requirements are not made complete
by adding fog. Record the actual extra editing burden; do not infer that 24:18 is
over an assignment limit that was never provided. The current edit is 27:48;
24:18 remains the historical pre-fog publication, not the current duration.

## Supersession history

Keep these entries. Add a new decision when placement changes; update the active
table and point the superseded entry to its replacement. Do not erase the reason
for a previous choice or retrofit a passed acceptance record.

| ID | Review / status | Decision and rationale | Supersedes / evidence |
|---|---|---|---|
| ML-001 | 2 November 2026; inherited recommendation, superseded in part by ML-002 | The existing docket/register grouped fog with later operational-weather work, proposed one queue task in M2 and size/demand comparisons in M3. | Captures the prior planning state in the reviewed baseline; it was not an assignment prohibition on current work. |
| ML-002 | 2 November 2026; active except F03 superseded by ML-005 | Split fog appearance, bounded report demonstration and scoring. Move F01/F02 to CURRENT. Keep F03 provisionally M2 with immediate reconsideration after F02. Retain Q01 M2 development and A01 M3 evaluation with their stated dependency/review gates. | Supersedes ML-001 only for blanket fog deferral. Basis: current user steering, existing clock/demo code, explicit lesson acceptance work, no verified deadline/video limit. |
| ML-003 | 2 November 2026; active process rule | Preserve the original M2 visual-evidence study as separate work. Assess any displacement explicitly; current product supplements do not reopen frozen M1 results. | Clarifies ML-002; grounded in the original milestone plan and current checkpoint scope. |
| ML-004 | 2 November 2026; progress status superseded by ML-006 | Root selected F01/F02 for current implementation. The reviewer inspected the new fog case/timeline and test assertions; native/model acceptance was pending at this entry. | Implements ML-002 without changing its placement or declaring delivery. Reusable agent configuration and the repository standing-review rule are now present. |
| ML-005 | 2 November 2026; active reconsideration | Recommend a bounded F03 scored fog lesson for CURRENT as the planned next increment, outside this F01/F02 delivery claim. The source-reviewed working report sequence now supports a distinct learner test of nested restrictions and unknown departure authority. Keep the one-hour demo unchanged; deliberately retime a short lesson and verify its independent rubric/flow. | Supersedes ML-002's provisional F03 M2 placement. Independent source/code review read; root reports actual native answers. Consolidated F01/F02 acceptance and all F03 acceptance remain pending. Counterargument: additional assessment/build cost with unfinished assignment work, recorded above. |
| ML-006 | 2 November 2026; F01/F02 accepted and captured, publication pending | Reviewed consolidated native acceptance: full source hour/debrief, three actual report-grounded answers, 249 backend/175 Unity checks, both supported orientations, restoration and reconnect inspection. Independently matched source hashes and response facts/cutoffs. | Supersedes ML-004's progress status and closes the F01/F02 acceptance pending at ML-005. Does not include F03, physical-smartphone evidence, a vision benchmark or edited-video publication. |
| ML-007 | 2 November 2026; F01/F02 edited and Drive-published, Git push pending | Reviewed the 27:48 edit record with unchanged prefix through 24:12.4667, actual native fog answers and matching Person 1 AAC hashes. Root reports successful upload to the existing Drive video and readback of updated shared planning/register documents. Local documents match A14 built and P04 CURRENT planned next. | Supersedes ML-006's video-publication pending status only. Git commit/push is the root's next action; F03 remains unbuilt and all outstanding assignment requirements remain. |
| ML-008 | 2 November 2026; F01/F02 source publication complete | Root committed/pushed implementation and ledger as [`c81812167361a73ceca8d944ffc3510bac1335ae`](https://github.com/MayFairMI6/apron-lens/commit/c81812167361a73ceca8d944ffc3510bac1335ae). Reviewer independently confirmed the local commit and identical remote branch head. Root reports updated PR #22 metadata; PR remains open and unmerged. | Closes ML-007's historical Git-publication pending status. F03 remains CURRENT planned next increment, unbuilt and not automatically executed as part of this delivery. No model or effort overrides were requested/applied. |

## Next review and exact resume point

The F01/F02 increment is delivered: native/report acceptance, Drive video and
source publication are complete; PR #22 remains open/unmerged. The root will
save this final publication record and handoff. The next product scope is F03,
reconsidered and moved to CURRENT as the planned next increment; it is not part of
this F01/F02 delivery and is not built or verified. Review its
implementation/assessment evidence when that increment is undertaken. Reopen placement for a concrete blocker, new
user steering, an actual deadline or an authorised scope change. Do not wait for
a calendar milestone when evidence already supports moving a unit earlier.
Before starting Q01, compare its
bounded design and real effort evidence with the original M2 workload. Before
A01, confirm the shared task and what the comparison can actually isolate.

Resume by reading the latest user request, this ledger and its reviewer protocol,
then inspect the actual checkout/diff and new acceptance files. Update each unit's
implementation, verification and recording status independently. The initial
reviewer wrote only this ledger and its protocol; it did not build, commit, push,
publish or send messages outside this agent collaboration. Implementation and
publication are the root agent's separate work.
