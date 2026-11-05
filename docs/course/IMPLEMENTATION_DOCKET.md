# AirfieldLens implementation docket

The adopted [execution queue](EXECUTION_QUEUE.md) now includes C01 correctness
contracts and acceptance evidence in M1, C02 a bounded structured-evidence checker
and C03 a scenario-state specification in M2, and C04 formal model checking plus
comparative evaluation in M3. C01 is complete as a bounded contract/evidence record; C02–C04 are queued, not completed proofs.
Current typed practice remains a fallible qualitative prototype. C01–C04 require curated
development/evaluation cases and the existing model for language interpretation,
but no new external dataset or LLM training. The separately assigned M2 visual
study retains its own detector-training and image-data requirements.

The project owner approved **AirfieldLens** as the current title after reviewing
a voice-matched opening that replaces the spoken project name. Update the app
header, title cards and current submission materials consistently. Preserve the
original recording; document the synthetic opening sentence. Repository/package
identifiers and frozen research records retain their existing names.

The presentation uses distinct scenarios with time scaling within each. The
scenario clock describes simulated elapsed time; narration length and video
length are separate. The external driver owns movement, reports and visual
conditions. The original Checkpoint 1 core had three practice lessons. The fourth, `fog_restrictions`, is implemented for M1. Normal learner flow across all four lessons now uses typed responses and qualitative model feedback without a numerical score; bounded model/native checks and their failures are recorded.

## Scenario coverage correction

The rejected-takeoff review found a delivery gap: the older catalogue contains ten
report-led profiles, but at that audit the lesson service exposed only three scored
exercises. Later visual additions were not checked against a complete coverage
matrix. A catalogue entry, animation, recorded answer and practice lesson are
separate deliverables. The archived 16:18 video is not a comprehensive controller
scenario set.

The three runway cases identified by the earlier audit were implemented as independent
Checkpoint 1 demonstration profiles, together with the user's water-landing request.
They extend the external driver and use sourced Heathrow geography. Those four additions did not add
scored courses. Native capture and actual-answer verification are recorded separately
from the older video. The typed fog-restriction lesson now belongs to Checkpoint 1. Weather-driven queues,
visual-evidence research and a distinct turnaround task are assigned to Checkpoint 2.
Checkpoint 3 compares airport size/demand and evaluates the integrated experience.

| Scenario | Verified current coverage | Missing learning task / next step | Priority and stage |
|---|---|---|---|
| Rejected takeoff | Independent `rejected_takeoff` profile: roll, rejection, deceleration, runway stop and three model questions. | Follow takeoff roll → reported rejection → deceleration → stopped aircraft; distinguish aircraft status, runway occupancy/restriction and later inspection/release. Cause and damage stay unknown unless reported. | Implemented M1 demonstration; native acceptance recorded separately. |
| Occupied-runway go-around | Independent go-around profile; TRN101 climbs away while TRN102 occupies the mapped runway. | Show an arrival discontinuing its approach while the preceding aircraft has not vacated; identify both aircraft and the reported runway status. A go-around does not establish a collision or emergency. | Implemented M1 demonstration. |
| Runway incursion / stop-bar conflict | Independent vehicle runway-incursion profile; takeoff cancelled before roll, vehicle turns and withdraws. Specific red-stop-bar conflict still not implemented. | Add a bounded protected-boundary variation with received restriction/correction reports; distinguish an illuminated stop bar, a reported instruction and actual runway occupancy. | Incursion implemented M1; specific stop-bar variation assigned M2. |
| Water landing | Independent `water_landing` profile over actual Wraysbury Reservoir geometry; descent, water contact/spray, stopped aircraft, response reports. | Interpret reported emergency/location and missing evacuation confirmation; add the bounded location/response handover variation for integrated evaluation. | M1 illustration delivered; handover variation assigned M3. Aircraft-performance and flotation modelling remain outside the task. |
| Runway debris and inspection | Dropped bags on a stand and later inspections exist; no runway-debris exercise. | Track a reported debris location, inspection vehicle, recovery and explicit operational update. A clear-looking image cannot establish runway release. | Assigned M2 inspection/release branch using the RTO or route task. |
| Low visibility / fog | Fog presentation and the source-hour demonstration are native/model verified. The separate `fog_restrictions` practice lesson and typed review across all four lessons are implemented; the restored v2 backend suite passed 276 tests. | Three typed-response questions with qualitative report-grounded feedback distinguish active LVP/safeguarding, continuing safeguarding/hold after LVP cancellation, and unconfirmed departure clearance after safeguarding cancellation. | Assigned M1; bounded native typed prototype verified, with documented failures. |
| Wet or snow-contaminated surface / de-icing delay | Rain/snow particles exist; surface reports, clearance operations and de-icing dependencies do not. | Track received surface/inspection/service updates and what remains unconfirmed. Avoid inferring braking action or aircraft readiness from precipitation. | Assigned M2 weather and turnaround tasks. |
| Callsign/readback confusion; missing acknowledgement | Flight identity and source cutoffs exist; no dedicated communication-error lesson. | Match an instruction/correction to its addressee, recognise an unresolved acknowledgement, and avoid treating silence or a stale report as release. Start with report transcripts; live voice is not required. | Assigned M2 context-reasoning task. |
| Wildlife sighting versus reported bird strike | Animated flock and pre-departure hold; the reports explicitly say no strike is reported. | Introduce a separate reported/suspected strike and follow inspection/return updates without inventing damage or a causal link to another incident. | Assigned M2 report/inspection variation. |
| Disabled aircraft without fire; recovery/reopening | A disabled aircraft and closed runway are shown after the damaging landing; recovery and reopening remain pending. | Follow towing/recovery, runway vacancy, inspection and separate reopening; do not make every interruption a fire or crash. | Assigned M2 recovery/reopening continuation; partial coverage already present. |
| E01 — one-engine emergency return with a successful landing | The current emergency request/damaging landing does not provide a successful engine-out return branch. | Add the reported single-engine problem, requested return, confirmed successful landing and separate movement/recovery status. | Assigned M2 within the existing return task; not built. No engine-performance or pilot course. |
| Fuelling interruption / spill; turnaround handover | `fuel_delay` is a legacy report profile; the baggage lesson has fuel-completion facts. No dedicated interruption/spill task. | Identify outstanding service, a reported exclusion/restriction and handover needs; distinguish a fuel delay from a confirmed spill. | Assigned M2 turnaround handover. |
| Conflicting stand assignment / corrected report | `conflicting_stand` is legacy only. The current occupied-stand lesson concerns occupancy, not contradictory assignments. | Preserve the original and correcting sources and identify the currently supported assignment without changing aircraft identity or position. | Assigned M2 context-reasoning variation. |
| Departure sequencing delay | `late_departure` is legacy; the baggage lesson partly covers revised estimates and unconfirmed readiness. | Show a service-ready flight that remains held by a separate reported sequencing restriction. | Assigned M2 sequencing variation within the existing lesson. |
| Takeoff accident / runway excursion | `takeoff_accident` and `landing_accident` remain legacy labels. The current damaging landing stops on the runway; it is not an animated runway excursion. | Evaluate whether learners distinguish the existing rejected-takeoff/damaging-landing reports from accident or excursion claims; preserve unsupported outcomes as unknown. | Assigned M3 integrated report-comparison task using existing illustrations; no additional accident-physics course. |
| E02 — both-engine thrust loss/reduction on approach | The water case has a loss-of-thrust report; no separate both-engine approach-failure case is implemented. | Add a bounded reported propulsion emergency and confirmed outcome within integrated emergency evaluation. | Assigned M3; not built. Preserve unknown causes and avoid a generic total-engine-loss physics claim. |
| E03 — reported wing/structural damage | Gear-collapse/fire illustration exists; no wing-break or structural-damage case is implemented. | Separate reported damage location, extent, cause, flight status and inspection/outcome in an incident-comparison variation. | Assigned M3; not built. No structural-load or controllability model. |

The original three fixed-choice lessons—ground-route obstruction, occupied arrival stand and late
baggage—retain their delivery records and unchanged worlds. The fourth typed fog
lesson is implemented separately, with bounded native acceptance recorded. Normal takeoff/return, wildlife, dropped baggage, ground
contact, stand fire and damaging landing have visual demonstrations. Their existence
does not close the specific gaps above. This audit covers all ten legacy catalogue
IDs and the current demonstration builders (`lessons.py`, `flight_cycle.py`,
`baggage_incident.py`, `accident_scenarios.py`, `training_environment.py`, `fog_lesson.py`). It is a
prioritised coverage review, not an exhaustive aerodrome hazard assessment.

Each bounded variation has its own run identity and explicit timing within the
existing task family; do not stack another emergency onto the accident sequence. The normal-speed and
accelerated versions must expose the same reports at the same source time. For RTO,
use an illustrative bounded stop on the runway with no automatic fire; do not claim
a validated stopping-distance, aircraft-performance or pilot reject/continue model.
For a go-around, preserve a continuous approach-to-climb trajectory and distinct
identities for the arrival and runway occupant. Incursion cases need a defined
protected area and deliberately authored conflict geometry; other traffic remains
reserved. Learners identify affected movements and missing confirmation; the
assistant does not issue real clearances.
Questions about other affected flights need explicit received reports for each flight
and identity-preserving evidence selection. The current selected-flight assistant
must not infer a cross-flight restriction from scene geometry.

Before marking a supplement delivered: exercise at least 20 seeds per case; check
paths, turns, stopping/occupancy boundaries and report arrival; test cutoff and stale
answer behaviour; obtain real local-model answers before and after the relevant
update; preserve failed requests; run the case in the native iOS Simulator in both
orientations; and publish a distinct chapter with matching script and provenance.
If a case gains scoring, it also needs its own objective, fixed-cutoff questions,
deterministic rubric and end-to-end lesson test. Existing test totals cannot be
reused as acceptance for these unimplemented additions.

Evidence: [Heathrow rejected-takeoff investigation](https://assets.publishing.service.gov.uk/media/6221e05fe90e0710be03550f/Various_CAT_03-22.pdf),
[Heathrow runway-safety package](https://www.heathrow.com/company/team-heathrow/airside/useful-publications/runway-safety-awareness-package),
[Heathrow vehicle-incursion investigation](https://www.gov.uk/aaib-reports/aaib-investigation-to-airbus-a300b4-622r-f-d-aead),
[Heathrow go-around explanation](https://mediacentre.heathrow.com/pressrelease/detail/4150),
[Low Visibility Operations](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASWeather_OSI_052_v3-1.pdf),
[FOD management](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASGrOps_OSI_081-Airside-Cleanliness-and-FOD-Management_v-2.pdf),
[CAA occurrence examples](https://www.caa.co.uk/about-us/make-a-report-or-complaint/report-something/mor/the-mors-code/).
These sources establish relevant hazards and information distinctions. They do not
validate our animations, response times, learning outcomes or a ranking by prevalence.
See the Heathrow source notes for the specific evidence and limitations.

## Existing milestone work

| Milestone | Work | Acceptance condition | Current position |
|---|---|---|---|
| Immediate Checkpoint 1 extension | Remove the in-app 3–5-minute estimate and label the scenario clock explicitly. Return the viewer to Guided demonstration. | Native briefing has no fixed wall-time estimate; guided clock and 30× indicator remain visible. | Implemented; native build, 231 backend tests, 69 Unity checks and recorded visual checks passed. |
| Immediate Checkpoint 1 extension | Separate rain, snowfall and late-afternoon → dusk → night settings. Conditions and particles follow external source time, including pause/reconnection. Default clear daytime remains compatible. | Native rain/snow/dusk captures; timing/repeatability and legacy-input checks; readable interface in both orientations. | Implemented; native build, 231 backend tests, 69 Unity checks and recorded visual checks passed. |
| Immediate presentation update | Keep Person 1 audio, add Person 2 weather cues and a labelled environment supplement. Preserve previous recordings and source cutoffs. | Current Drive documents, video provenance, handoff and GitHub PR agree on implemented features. | Native clips captured and incorporated in the 16:18 edit; Person 1 audio preserved. Updated scripts, acceptance and shared handoff accompany the video. |
| Checkpoint 1 fog practice lesson | `fog_restrictions`: a separate 210-second practice world with three typed questions and qualitative report-grounded model feedback; preserve the source-hour fog demonstration. | Explicit criteria and cutoff eligibility; supported/partial/contradictory responses; retry, stale and duplicate guards; A1 targeting; native typing, hidden-question flow and debrief. No numerical score or semantic-truth guarantee. | Implemented; restored v2 passed 276 backend tests and 19 focused checks. One full native typed fog run and positioned original-lesson checks are recorded; feedback remains fallible. |
| Checkpoint 2 | Weather-driven queues with reported capacity restrictions, arrival/departure waiting, stand occupancy and explicit release. Keep visual weather separate from operational reports; surface-condition/de-icing extensions follow their defined task. | A bounded queue task, reproducible source-time outcomes, valid runway/stand reservations, explicit reasons for delay and separate clearance reports. | Assigned M2; not implemented. |
| Checkpoint 2 | Visual-evidence study under weather/light changes; compare with and without images and separate perception from report reasoning. Build a distinct turnaround handover task. | Questions that require visual evidence, frozen evaluation contract, perception-error analysis, and a separate turnaround objective with available reports and feedback. | Assigned M2; not implemented or evaluated. |
| Checkpoint 3 | Full 24-hour solar cycle and longer operating-day profile, including sunrise, as an integrated condition/time-model check. | One explicit time model, traffic/report schedules appropriate to the longer duration, and no accelerated sky clock disguised as physical elapsed time. | Assigned M3; not implemented. Current dusk is a one-hour interval, not a complete day. |
| Checkpoint 3 | Compare airport size and traffic demand independently; evaluate the integrated experience across conditions, speeds, orientations, latency, reconnection, failures and phone/larger-screen use with representative learners. | Preserve aircraft dimensions and turning envelopes; control evidence tasks/reporting delays; report repeatable results, failures, device/runtime limits and final contributions. | Assigned M3; not implemented or evaluated. |

The immediate environment work is visual presentation, not a weather model or a
change to aircraft performance. Rain does not currently create a braking penalty;
snow does not accumulate on the pavement or implement de-icing; dusk does not
establish operational visibility. Weather is not inserted as an assistant report.
The aircraft keep their existing reserved paths and report-grounded answers.

The driver supports a one-hour source timeline in guided/full-hour profiles and
a separate short typed-practice profile. Removing a UI estimate does not change
those profile durations. Guided demonstration accelerates quiet periods to 30×
and uses 1× at teaching moments and during pending answers. The short practice
profile still ends at 210 seconds of source time, with pauses for answers/review.

The preserved 13:25 video with Person 1 narration predates the weather extension and uses fixed daytime. The archived 16:18 edit appends labelled rain, snow and dusk/night clips in Person 2’s section; do not claim weather was in an older recording. The earlier accident and M1 research
records remain unchanged. Physical-phone verification and Person 2 narration
remain outstanding submission tasks.

## Current AirfieldLens publication

The current 30:33.5 edit adds typed practice to the earlier 27:48 fog recording. It preserves Person 1’s approved opening-name edit and all earlier footage through the connected Terminal 2/3 setting. A separate fog case starts at 24:12 and shows three actual report-based assistant answers from a completed source-hour run. Person 2 is assigned the narration for this added section; that recording remains outstanding. Weather-driven queues are assigned to M2 and airport-size/demand comparisons to M3. The fog practice lesson is now built for M1, with a complete native fog practice run and a new typed chapter from 27:42; the earlier fog chapter remains a separate unscored demonstration. Earlier recordings remain archived. Download: https://drive.google.com/file/d/1uHIweEFSlO4CRb8-VyNM7aZUd4mhsMhQ/view

The four additional runway/emergency profiles passed 20 seeds each in the 241-test backend suite and 113 Unity checks. Each selected native run reached its one-hour debrief and displayed three actual accepted model responses, twelve across four runs. These are functional examples, not an accuracy benchmark. The first water capture is retained; its oversized close-view map label was corrected and that case was recorded again. See outputs/checkpoint1/runway-acceptance.json.

The app header, visible app name, current scripts and shared documents use AirfieldLens. The earlier recordings and frozen research retain their original labels. Terminal 3 combines mapped geometry, attributed free FlightGear detail and authored canopy/facade detail; its lettering is attached to the building. Map labels hide in close views. This is not a surveyed current digital twin.

## Connected airport setting

The setting now connects the Queen’s Terminal—Terminal 2—with Terminal 3 and their surrounding roads and buildings. Terminal 2B remains separate above ground, and the former Terminal 1 area is shown as a reference outline. Passing cars follow a mapped one-way road loop using the same scenario clock. The added water outlines preserve their islands. This is a sourced, simplified teaching environment; the traffic is authored, and visible movement does not create operational reports.

The extension passed independent source/geometry review, 245 backend tests and 127 Unity checks. Native landscape/portrait inspection verified the terminal view, label visibility and Sources scrolling. A new rejected-takeoff run reached one source-hour with three actual accepted answers. The first cold request timed out; that failure is retained. The 24:18 video appends the setting at 23:42 and preserves prior narration/cues. See outputs/checkpoint1/connected-setting-acceptance.json.

## Assigned learning tasks

The [training scenario register](TRAINING_SCENARIO_REGISTER.md) tracks 15 current coverage entries and twelve assigned work items (nine P-series items and three E-series topics), preserving their historical proposal IDs and verification gates. Its [editable copy](https://docs.google.com/document/d/1IxdtKDWxUWhK9r1QpWOi_MGtqnmmWsMd0sd-nme8ulk) supports tracking. M2 includes the bounded weather-driven queue task, visual-evidence study and distinct turnaround task, with the assigned stand/route/weather branches. M3 includes airport-size/demand comparisons and integrated evaluation, including the pushback-clearance and response-handover variations. These are bounded tasks within the existing milestones, not additional courses. Fog rendering and the source-hour demonstration are accepted; the M1 typed fog lesson is built with bounded model/native acceptance and known semantic limitations. Aircraft dimensions and turning envelopes remain fixed when airport size changes.


Fog update and milestone decisions

The fog visual profile and separate report-led demonstration are complete for this increment. The native source-hour run displayed three accepted Qwen3.5-9B answers in 11.140, 12.472 and 11.749 seconds. It reached debrief in about 3:35 of wall time. The earlier fog edit starts that chapter at 24:12; the current typed supplement extends the recording to 30:33.5; all earlier cue times and Person 1’s approved speech remain preserved. See outputs/checkpoint1/fog-acceptance.json and fog-demo-edit.json.

The milestone review was followed by an explicit instruction to implement the fourth fog practice lesson in M1. `fog_restrictions` is now built as a 210-second lesson-only world, with typed questions at 60/120/180 seconds, A1 feedback and cutoff-eligible reports. Its normal flow uses actual model-generated qualitative review, while the earlier shuffled choices remain an explicit internal regression mode. Its visual recovery precedes procedure cancellation; TRN101 remains parked and departure clearance stays unconfirmed. The original three lesson worlds and all five demonstrations retain their complete pre-change fingerprints across 20 seeds each.

The restored v2 backend passed 276 tests and 19 focused checks. The 18 authored v2 development cases produced 14 usable reviews and four withheld failures; a second bounded revision was rejected and exact v2 restored. These are development results, not a grading benchmark. One complete native typed fog run reached debrief with three accepted reviews from four attempts, including a genuine quotation failure and successful edited retry. Native portrait/landscape input, hidden question context, scrolling, ordinary question entry, failure retention and retry were inspected. Targeted native checks for the original three lessons are recorded separately; they are not new full lesson runs. See [typed native evidence](../../outputs/checkpoint1/typed-native-acceptance.json), [independent development review](../../outputs/checkpoint1/typed-review-independent.json) and [correctness contract](../CORRECTNESS_CONTRACT.md).

M2 weather-driven queues, visual-evidence research and a distinct turnaround task are assigned work. M3 airport-size/demand comparisons and integrated evaluation are assigned work. Acceptance gates govern completion. [MILESTONE_LEDGER.md](MILESTONE_LEDGER.md) retains the decision record and reusable review process.


The E01–E03 assignments follow ledger ML-012. BA38/G-YMMM supplies a both-engine thrust-reduction precedent involving restricted fuel flow; it does not supply an exploding-engine or wing-break mechanism. Existing gear-collapse/fire visuals and the water case's loss-of-thrust report do not establish the requested engine or structural scenarios. E01 requires its own suitable source review and a successful-return outcome branch. E02/E03 remain bounded M3 report/incident variations, each needing its own causal reports and movement/visual acceptance before being marked built.

Typed review is qualitative practice feedback. The model evaluates the learner's text against received reports and authored criteria, including unsupported extra claims. Input bounds, exact IDs, eligible citations and learner-quote checks restrict what can be accepted structurally; they do not establish the semantic correctness of every judgment. Failed or timed-out reviews preserve the response for retry and never use scripted replacement feedback. The M1 evidence includes actual-model examples and native typing/review checks; these do not establish general semantic accuracy or professional competence.
