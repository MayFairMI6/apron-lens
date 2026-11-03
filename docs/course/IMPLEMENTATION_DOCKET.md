# AirfieldLens implementation docket

The project owner approved **AirfieldLens** as the current title after reviewing
a voice-matched opening that replaces the spoken project name. Update the app
header, title cards and current submission materials consistently. Preserve the
original recording; document the synthetic opening sentence. Repository/package
identifiers and frozen research records retain their existing names.

The presentation uses distinct scenarios with time scaling within each. The
scenario clock describes simulated elapsed time; narration length and video
length are separate. The external driver owns movement, reports and visual
conditions. The original Checkpoint 1 core remains three scored lessons.

## Scenario coverage correction

The rejected-takeoff review found a delivery gap: the older catalogue contains ten
report-led profiles, but the current lesson service exposes only three scored
exercises. Later visual additions were not checked against a complete coverage
matrix. A catalogue entry, animation, recorded answer and scored lesson are
separate deliverables. The archived 16:18 video is not a comprehensive controller
scenario set.

The three immediate recommendations have now been implemented as independent
Checkpoint 1 demonstration profiles, together with the user's water-landing request.
They extend the external driver and use sourced Heathrow geography. They do not add
scored courses. Native capture and actual-answer verification are recorded separately
from the older video. Operational weather and communication exercises remain
Checkpoint 2 work; Checkpoint 3 evaluates the resulting experience.

| Scenario | Verified current coverage | Missing learning task / next step | Priority and stage |
|---|---|---|---|
| Rejected takeoff | Independent `rejected_takeoff` profile: roll, rejection, deceleration, runway stop and three model questions. | Follow takeoff roll → reported rejection → deceleration → stopped aircraft; distinguish aircraft status, runway occupancy/restriction and later inspection/release. Cause and damage stay unknown unless reported. | Implemented M1 demonstration; native acceptance recorded separately. |
| Occupied-runway go-around | Independent go-around profile; TRN101 climbs away while TRN102 occupies the mapped runway. | Show an arrival discontinuing its approach while the preceding aircraft has not vacated; identify both aircraft and the reported runway status. A go-around does not establish a collision or emergency. | Implemented M1 demonstration. |
| Runway incursion / stop-bar conflict | Independent vehicle runway-incursion profile; takeoff cancelled before roll, vehicle turns and withdraws. Specific red-stop-bar conflict still not implemented. | Show a vehicle or aircraft crossing a defined protected boundary, with received restriction/correction reports and identifiable affected traffic. Distinguish an illuminated stop bar, a reported instruction and actual runway occupancy. | Incursion implemented in M1; specific stop-bar learning task deferred. |
| Water landing | Independent `water_landing` profile over actual Wraysbury Reservoir geometry; descent, water contact/spray, stopped aircraft, response reports. | Interpret the reported emergency/location and missing evacuation confirmation. No local accident precedent, viable diversion or validated flotation is claimed. | User-requested M1 illustration; formal assessment and performance modelling excluded. |
| Runway debris and inspection | Dropped bags on a stand and later inspections exist; no runway-debris exercise. | Track a reported debris location, inspection vehicle, recovery and explicit operational update. A clear-looking image cannot establish runway release. | Include inspection/release in RTO first; distinct debris case in M2. |
| Low visibility / fog | Fog presentation and an independent report-led case are built and verified; three live answers preserve remaining restrictions. | Distinguish safeguarding, procedures in force, partial cancellation and unconfirmed departure authority. Appearance alone does not change these states. | CURRENT delivered for visual/demo; a separately scored lesson is CURRENT planned next increment after independent reconsideration. |
| Wet or snow-contaminated surface / de-icing delay | Rain/snow particles exist; surface reports, clearance operations and de-icing dependencies do not. | Track received surface/inspection/service updates and what remains unconfirmed. Avoid inferring braking action or aircraft readiness from precipitation. | M2 weather and turnaround tasks. |
| Callsign/readback confusion; missing acknowledgement | Flight identity and source cutoffs exist; no dedicated communication-error lesson. | Match an instruction/correction to its addressee, recognise an unresolved acknowledgement, and avoid treating silence or a stale report as release. Start with report transcripts; live voice is not required. | M2 context-reasoning task. |
| Wildlife sighting versus reported bird strike | Animated flock and pre-departure hold; the reports explicitly say no strike is reported. | Introduce a separate reported/suspected strike and follow inspection/return updates without inventing damage or a causal link to another incident. | M2 variation after the three runway gaps. |
| Disabled aircraft without fire; recovery/reopening | A disabled aircraft and closed runway are shown after the damaging landing; recovery and reopening remain pending. | Follow towing/recovery, runway vacancy, inspection and separate reopening; do not make every interruption a fire or crash. | M2 continuation; partial coverage already present. |
| Emergency return with an uneventful landing / diversion | An emergency request and damaging landing are shown; no successful emergency-return or diversion branch. | Distinguish reported emergency, intended destination, confirmed landing and subsequent restrictions. | M2 variation; no additional crash animation needed. |
| Fuelling interruption / spill; turnaround handover | `fuel_delay` is a legacy report profile; the scored baggage lesson has fuel-completion facts. No dedicated interruption/spill task. | Identify outstanding service, a reported exclusion/restriction and handover needs; distinguish a fuel delay from a confirmed spill. | M2 turnaround handover. |
| Conflicting stand assignment / corrected report | `conflicting_stand` is legacy only. The current occupied-stand lesson concerns occupancy, not contradictory assignments. | Preserve the original and correcting sources and identify the currently supported assignment without changing aircraft identity or position. | M2 context-reasoning variation. |
| Departure sequencing delay | `late_departure` is legacy; the baggage lesson partly covers revised estimates and unconfirmed readiness. | Show a service-ready flight that remains held by a separate reported sequencing restriction. | M2 variation; reuse the existing lesson. |
| Takeoff accident / runway excursion | `takeoff_accident` and `landing_accident` remain legacy labels. The current damaging landing stops on the runway; it is not an animated runway excursion. | Keep these labels separate from rejected takeoff and from accidental off-pavement animation. Detailed accident dynamics add less immediate value than the three missing runway-awareness tasks. | Later backlog; not part of this recommended supplement. |

The three scored lessons—ground-route obstruction, occupied arrival stand and late
baggage—remain delivered. Normal takeoff/return, wildlife, dropped baggage, ground
contact, stand fire and damaging landing have visual demonstrations. Their existence
does not close the specific gaps above. This audit covers all ten legacy catalogue
IDs and the current demonstration builders (`lessons.py`, `flight_cycle.py`,
`baggage_incident.py`, `accident_scenarios.py`, `training_environment.py`). It is a
prioritised coverage review, not an exhaustive aerodrome hazard assessment.

Each new case should have its own run identity and time-scaled profile, rather than
adding another emergency to the existing accident sequence. The normal-speed and
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
| Checkpoint 2 | Operational weather lessons: reported visibility, surface-condition changes, snow clearance/de-icing dependencies and restrictions. Reports must establish operational facts; falling snow or darker lighting alone does not establish braking action, readiness or clearance. | Distinct learning tasks, explicit available evidence, source-supported unknowns and feedback. Reuse the shared driver. | Planned; requires scenario/report design and source review. |
| Checkpoint 2 | Visual-evidence study under rain/snow/light changes; compare with and without images and separate perception from report reasoning. Add a distinct turnaround handover task. | Questions that require visual evidence, frozen evaluation contract, perception-error analysis and no claims inferred from validator acceptance alone. | Planned. |
| Checkpoint 2, only if required by a learning task | Full 24-hour solar cycle and longer operating-day profiles, including sunrise. | One explicit time model, traffic/report schedules appropriate to the longer duration, and no accelerated sky clock disguised as physical elapsed time. | Not implemented. Current dusk is a one-hour interval, not a complete day. |
| Checkpoint 3 | Integrated evaluation across conditions, speeds and orientations; latency, reconnection, failures and learning-flow usability, including phone versus larger-screen use with representative learners. | Repeatable results, condition-specific failure analysis, clear device/runtime limits and final contribution accounting. | Planned. |

The immediate environment work is visual presentation, not a weather model or a
change to aircraft performance. Rain does not currently create a braking penalty;
snow does not accumulate on the pavement or implement de-icing; dusk does not
establish operational visibility. Weather is not inserted as an assistant report.
The aircraft keep their existing reserved paths and report-grounded answers.

The driver supports a one-hour source timeline in guided/full-hour profiles and
a separate short scored-practice profile. Removing a UI estimate does not change
those profile durations. Guided demonstration accelerates quiet periods to 30×
and uses 1× at teaching moments and during pending answers. The short practice
profile still ends at 210 seconds of source time, with pauses for answers/review.

The preserved 13:25 video with Person 1 narration predates the weather extension and uses fixed daytime. The archived 16:18 edit appends labelled rain, snow and dusk/night clips in Person 2’s section; do not claim weather was in an older recording. The earlier accident and M1 research
records remain unchanged. Physical-phone verification and Person 2 narration
remain outstanding submission tasks.

## Current AirfieldLens publication

The current 27:48 edit is airfieldlens-fog-checkpoint1-person1-audio.mp4. It preserves Person 1’s approved opening-name edit and all earlier footage through the connected Terminal 2/3 setting. A separate fog case starts at 24:12 and shows three actual report-based assistant answers from a completed source-hour run. Person 2 narrates this added section. Weather-driven queues and comparisons across airport sizes remain planned; the scored fog lesson is recommended for the next increment of the current checkpoint and is not built. Earlier recordings remain archived. Download: https://drive.google.com/file/d/1uHIweEFSlO4CRb8-VyNM7aZUd4mhsMhQ/view

The four additional runway/emergency profiles passed 20 seeds each in the 241-test backend suite and 113 Unity checks. Each selected native run reached its one-hour debrief and displayed three actual accepted model responses, twelve across four runs. These are functional examples, not an accuracy benchmark. The first water capture is retained; its oversized close-view map label was corrected and that case was recorded again. See outputs/checkpoint1/runway-acceptance.json.

The app header, visible app name, current scripts and shared documents use AirfieldLens. The earlier recordings and frozen research retain their original labels. Terminal 3 combines mapped geometry, attributed free FlightGear detail and authored canopy/facade detail; its lettering is attached to the building. Map labels hide in close views. This is not a surveyed current digital twin.

## Connected airport setting

The setting now connects the Queen’s Terminal—Terminal 2—with Terminal 3 and their surrounding roads and buildings. Terminal 2B remains separate above ground, and the former Terminal 1 area is shown as a reference outline. Passing cars follow a mapped one-way road loop using the same scenario clock. The added water outlines preserve their islands. This is a sourced, simplified teaching environment; the traffic is authored, and visible movement does not create operational reports.

The extension passed independent source/geometry review, 245 backend tests and 127 Unity checks. Native landscape/portrait inspection verified the terminal view, label visibility and Sources scrolling. A new rejected-takeoff run reached one source-hour with three actual accepted answers. The first cold request timed out; that failure is retained. The 24:18 video appends the setting at 23:42 and preserves prior narration/cues. See outputs/checkpoint1/connected-setting-acceptance.json.

## Candidate learning tasks

The [training scenario register](TRAINING_SCENARIO_REGISTER.md) separates 14 current coverage entries from nine proposed additions, with primary-source precedents and verification gates. Its [editable copy](https://docs.google.com/document/d/1IxdtKDWxUWhK9r1QpWOi_MGtqnmmWsMd0sd-nme8ulk) supports tracking. Prioritise one bounded obstruction or queue task for Checkpoint 2; comparisons across airport size and traffic demand are candidates for Checkpoint 3. Fog rendering and the report-led case are now implemented and accepted; the scored extension and weather-driven capacity remain unimplemented. Aircraft dimensions and turning envelopes must remain fixed when airport size changes.


Fog update and milestone decisions

The fog visual profile and separate report-led demonstration are complete for this increment. The native source-hour run displayed three accepted Qwen3.5-9B answers in 11.140, 12.472 and 11.749 seconds. It reached debrief in about 3:35 of wall time. The new video starts the fog chapter at 24:12 and ends at 27:48; all earlier cue times and Person 1’s approved speech remain preserved. See outputs/checkpoint1/fog-acceptance.json and fog-demo-edit.json.

The independent milestone review explicitly compared the current checkpoint, later checkpoints, deferral and rejection. It recommends a short scored fog lesson next within the CURRENT checkpoint; this is planned, not built or included in the three existing scored lessons. Weather-driven queues remain M2 development and airport-size comparisons M3 evaluation, subject to their acceptance gates. The original M2 visual-evidence study remains required. MILESTONE_LEDGER.md is the current decision record; MILESTONE_LEDGER_AGENT.md and the project agent definition make the review reusable across sessions. Persistence is file-based, not an always-running process.
