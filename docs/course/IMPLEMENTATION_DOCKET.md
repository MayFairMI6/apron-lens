# ApronLens implementation docket

The presentation uses distinct scenarios with time scaling within each. The
scenario clock describes simulated elapsed time; narration length and video
length are separate. The external driver owns movement, reports and visual
conditions. The original Checkpoint 1 core remains three scored lessons.

## Scenario coverage correction

The rejected-takeoff review found a delivery gap: the older catalogue contains ten
report-led profiles, but the current lesson service exposes only three scored
exercises. Later visual additions were not checked against a complete coverage
matrix. A catalogue entry, animation, recorded answer and scored lesson are
separate deliverables. The current 16:18 video is not a comprehensive controller
scenario set.

The next recommended additions are **rejected takeoff**, **occupied-runway go-around**
and **runway incursion/stop-bar conflict**, in that implementation order. These are
proposed Checkpoint 1 supplements, not implemented features or new scored courses.
The ordering reflects learning value, current architecture and the user's explicit
rejected-takeoff priority; it is not a Heathrow frequency or risk ranking. Operational
weather and communication exercises remain Checkpoint 2 work; Checkpoint 3 evaluates
the resulting experience. Preserve the existing acceptance records and Person 1 audio.

| Scenario | Verified current coverage | Missing learning task / next step | Priority and stage |
|---|---|---|---|
| Rejected takeoff | Legacy `rejected_takeoff` report profile only; no reject/brake/stop animation or current video chapter. | Follow takeoff roll → reported rejection → deceleration → stopped aircraft; distinguish aircraft status, runway occupancy/restriction and later inspection/release. Cause and damage stay unknown unless reported. | First proposed M1 supplement. |
| Occupied-runway go-around | No go-around branch. Current arrivals land. | Show an arrival discontinuing its approach while the preceding aircraft has not vacated; identify both aircraft and the reported runway status. A go-around does not establish a collision or emergency. | Second proposed M1 supplement. |
| Runway incursion / stop-bar conflict | An apron obstruction and apron vehicle contact exist; neither is an incorrect presence in a protected runway area. | Show a vehicle or aircraft crossing a defined protected boundary, with received restriction/correction reports and identifiable affected traffic. Distinguish an illuminated stop bar, a reported instruction and actual runway occupancy. | Third proposed M1 supplement. |
| Runway debris and inspection | Dropped bags on a stand and later inspections exist; no runway-debris exercise. | Track a reported debris location, inspection vehicle, recovery and explicit operational update. A clear-looking image cannot establish runway release. | Include inspection/release in RTO first; distinct debris case in M2. |
| Low visibility / fog | Rain, snow and dusk are visual only; no fog profile or low-visibility operating state. | Distinguish safeguarding, procedures in force and later cancellation; identify uncertain observations and reported restrictions. Darkness alone does not activate these states. | M2 weather/evidence priority. |
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

The preserved 13:25 video with Person 1 narration predates the weather extension and uses fixed daytime. The current 16:18 edit appends labelled rain, snow and dusk/night clips in Person 2’s section; do not claim weather was in an older recording. The earlier accident and M1 research
records remain unchanged. Physical-phone verification and Person 2 narration
remain outstanding submission tasks.
