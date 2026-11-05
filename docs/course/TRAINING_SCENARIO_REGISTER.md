# AirfieldLens training scenario register

This register records implemented coverage and the remaining work assigned to each milestone. The snapshot was checked on 2 November 2026 against the scenario code and primary sources. The assignments reflect teaching value and implementation fit, not a ranking by accident frequency.

The milestone assignments are fixed: **M1 typed fog restrictions; M2 weather-driven queues, visual-evidence research and a distinct turnaround task; M3 airport-size/demand comparisons and integrated evaluation**. Every remaining row below is a bounded part of that work. Stand, route, service and handover variations use the existing driver and task families; they do not create additional standalone courses.

A real investigation supplies background and debrief material. The learner must still answer from the reports available at the exercise cutoff. Mapped roads, visible cars, aircraft animation and weather effects do not themselves establish clearance, cause, damage or readiness. The current passing cars are ambient landside traffic, not incident evidence.

## Current coverage

| ID | Scenario | Current status | Main learner task |
|---|---|---|---|
| A01 | A vehicle on the route | Built — typed practice; targeted native input/feedback check recorded | Explain the reported hold, what remains unknown, and the later explicit release. |
| A02 | An occupied arrival stand | Built — typed practice; targeted native input/feedback check recorded | Separate estimated arrival, stand occupancy and confirmed stand availability. |
| A03 | A changing departure estimate | Built — typed practice; targeted native input/feedback check recorded | Distinguish baggage progress, revised estimate and confirmed readiness. |
| A04 | Wildlife report, inspection and release | Built — unscored continuous demonstration | Track a reported bird hazard, inspection completion and separate exercise release. |
| A05 | Dropped baggage and service-area obstruction | Built — unscored continuous demonstration | Explain why collection, inspection, loading completion and movement release are distinct. |
| A06 | Aircraft–vehicle contact and inspection hold | Built — unscored continuous demonstration | Track stopped aircraft, isolated route and pending inspection/release. |
| A07 | Stand engine fire and continuing closure | Built — unscored continuous demonstration | Distinguish fire containment from stand reopening and aircraft movement permission. |
| A08 | Damaging landing and runway recovery hold | Built — unscored continuous demonstration | Explain why a contained fire or stopped aircraft does not establish runway reopening. |
| A09 | Rejected takeoff after an airspeed concern | Built — independent unscored case | Track rejection, deceleration, stop and outstanding runway/recovery status. |
| A10 | Go-around while the runway remains occupied | Built — independent unscored case | Identify the aircraft going around and the traffic still occupying the runway. |
| A11 | Maintenance vehicle runway incursion | Built — independent unscored case | Follow the cancelled departure, vehicle withdrawal and unresolved runway status. |
| A12 | Emergency water landing | Built — independent unscored case | Track reported loss of thrust, location, water contact and response coordination. |
| A13 | Rain, snowfall and dusk/night presentation | Built — visual context only | Use presentation conditions while practising existing report reasoning. |
| A14 | Fog and changing restrictions | Built — independent unscored source-hour case; native/model verified | Separate visual improvement, cancellation of low-visibility procedures, safeguarding and unconfirmed departure authority. |
| A15 | Fog and reported restrictions | Built — fourth typed-response practice lesson (`fog_restrictions`); one full native typed run recorded; known review failures | Type responses to three fixed-cutoff questions to distinguish active LVP/safeguarding, continuing safeguarding/hold after LVP cancellation, and departure authority still unconfirmed after safeguarding cancellation. |

A01–A03 and A15 are the four practice lessons. Normal learner checkpoints now take typed responses and return qualitative model feedback without a numerical score. The original fixed-choice acceptance records are historical; current evidence separates one full native typed fog run, targeted checks for the original three lessons, and 18 authored API development cases. These are limited functional checks, not validated grading. A09–A12 and A14 are independent unscored cases; A04–A08 are parts of the continuous demonstration. A13 is visual presentation, not operational weather training. A catalogue title alone does not establish a built exercise. The older ten-item catalogue is therefore not counted as ten further completed cases.

## Assigned work tracker

| ID | Milestone | Task | Design | Implementation | Native verification | Task boundary |
|---|---|---|---|---|---|---|
| P01 | M2 | Arriving stand not clear of equipment | Source-backed draft | Not built | Pending | Turnaround stand-clearance branch |
| P02 | M3 | Pushback clearance and wingtip conflict | Source-backed draft | Not built | Pending | Integrated clearance comparison using the stand/route task |
| P03 | M2 | Aircraft not fully parked protrudes into taxi route | Source-backed draft | Not built | Pending | Queue/route-obstruction branch |
| P04 | M1 | Typed fog restriction lesson extending A14; now A15 | Three typed questions and cutoff-specific criteria | Built; restored v2 suite 276 tests passed | Full native fog typed flow and failures recorded | Fourth practice lesson; see ledger F03/T01 |
| P05 | M2 | Works or wind debris closes a route until inspection | Source-backed draft | Not built | Pending | Restriction, inspection and release branch |
| P06 | M2 | Connector-road closure and a changed route briefing | Source-backed draft | Not built | Pending | Timed report/route-change branch |
| P07 | M2 | Winter readiness and surface-condition handover | Source-backed draft | Not built | Pending | Weather/turnaround dependency branch |
| P08 | M3 | Water-incident location and response handover | Source-backed draft | Not built | Pending | Integrated handover variation of the existing water case |
| P09 | M2 | Weather-driven arrival and departure queues | Driver design drafted | Not built | Pending | Bounded capacity/queue task |

P04 is implemented as A15 in M1. P01/P03/P05/P06/P07/P09 are assigned M2 tasks; P02/P08 are assigned M3 variations for integrated evaluation. Their placement is settled, and acceptance gates determine completion. The retained P identifiers trace the earlier proposal records; they no longer indicate unassigned work. These tasks concern awareness and coordination, not flight handling or professional certification.

## Scenario cards

### P01 · Arriving stand not clear of equipment

**M2 · Assigned task — not built.** Setting: Terminal 2/3 stand and service access.

Extends A06 with a new decision task; it is not a second claim that the existing animation is newly built.

**Precedent or operational basis.** On 20 December 2019 at Heathrow, G-CIVU hit a fuel-transfer vehicle left on the stand from the previous turnaround. Flight crew and arrival ground staff had not seen it before contact. [AAIB: Boeing 747-436 G-CIVU](https://www.gov.uk/aaib-reports/aaib-investigation-to-boeing-747-436-g-civu) [Heathrow OSI093 v1: Arrival, Turnaround and Departure on Stand](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASGrOps_OSI_093_Aircraft_Arrival_Turnaround_and_Departure_on_Stand_v1.pdf)

**Learner task.** Identify that the stand-clearance check is unresolved; retain the reported arrival hold and explain what must be confirmed.

**Assigned report sequence.** Vehicle reported on stand → Arrival held / stand-clearance check pending → Equipment removal reported → Stand check and explicit exercise release.

**Evidence boundary.** Do not diagnose why a particular worker missed the vehicle; this branch stops before contact. Scenery does not prove stand clearance.

**Implementation task.** Author a prevention branch with three evidence checkpoints.

### P02 · Pushback clearance and wingtip conflict

**M3 · Assigned task — not built.** Setting: Terminal apron / adjacent parked aircraft.

**Precedent or operational basis.** On 6 April 2024 at Heathrow, G-VDIA’s wingtip struck G-XWBC’s horizontal stabiliser. The operator found the tug turned too early; company-required wing walkers were absent. [AAIB: G-VDIA / G-XWBC pushback collision](https://www.gov.uk/aaib-reports/aaib-investigation-to-boeing-787-9-g-vdia-slash-airbus-a350-1041-g-xwbc)

**Learner task.** Recognise the reported clearance concern, distinguish intended pushback from authorised safe movement, and follow a stop/reassessment update.

**Assigned report sequence.** Pushback planned → Wing clearance not confirmed → Movement stopped on hazard report → Route/clearance reassessed; release separately reported.

**Evidence boundary.** Do not import the operator-specific wing-walker rule as universal Heathrow policy or invent the original stand path. Use an authored near-miss variation of the existing stand/route task.

**Implementation task.** Create a slow, reviewable pushback-clearance variation and separate reports for clearance and stop; evaluate it within M3 rather than adding another course.

### P03 · Aircraft not fully parked protrudes into taxi route

**M2 · Assigned task — not built.** Setting: Terminal stand mouth / taxiway.

**Precedent or operational basis.** At Heathrow on 28 September 2022, HL-7782’s wingtip hit TF-FIK’s rudder. TF-FIK was not fully parked; its commander had not advised ground control. The passing crew assumed clearance and green lights meant the path was clear. [AAIB: HL-7782 / TF-FIK ground collision, amended report](https://www.gov.uk/aaib-reports/aaib-investigation-to-boeing-777-300-er-hl-7782-and-boeing-757-256-tf-fik)

**Learner task.** Reconcile the latest stand-position report with a previously issued route; state that the obstruction remains unresolved.

**Assigned report sequence.** Taxi route issued → Neighbour aircraft not fully parked → Obstruction/hold reported → Stand position corrected → Separate route release.

**Evidence boundary.** Do not treat ATC clearance, a green route or a map footprint as proof of physical wingtip clearance. Aircraft envelopes and exact paths must be authored and reviewed.

**Implementation task.** Add a non-collision hold branch that tests a stale route against a newer obstruction report.

### P04 · Typed fog restriction lesson extending A14

**Assigned M1 · Implemented as typed practice A15; bounded model/native acceptance recorded.** `fog_restrictions` provides a separate condensed 210-second practice world, with three typed-response questions at 60, 120 and 180 source seconds. Each question explicitly asks for its two content components; a third grounding criterion checks every additional claim against the received reports. A14 retains its unchanged one-hour demonstration and three accepted native assistant answers. Setting: parked TRN101/A1 on the mapped Terminal 3 apron.

**Precedent or operational basis.** Heathrow OSI052 v3.1 distinguishes preparatory safeguarding from full low-visibility procedures. It explicitly allows safeguarding to remain after procedures are cancelled. NATS explains the associated ILS protection and spacing context. [Heathrow OSI052 v3.1: Low Visibility Operations](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASWeather_OSI_052_v3-1.pdf) [NATS: Low visibility procedures explained](https://nats.aero/blog/2025/10/low-visibility-procedures-what-you-need-to-know/)

**Learner task.** At 60 seconds, identify active LVP and safeguarding with TRN101 held. At 120, retain safeguarding and the hold after LVP cancellation. At 180, distinguish confirmed safeguarding cancellation from still-unconfirmed departure clearance.

**Report sequence.** Safeguarding requested → Safeguarding confirmed → LVP in force → LVP cancelled but safeguarding remains → Safeguarding cancellation requested → Cancellation confirmed; departure clearance still unconfirmed. A15 independently retimes these reports to the short lesson; their event times are 10, 20, 35, 105, 145 and 160 seconds, followed by seeded receipt delays. Its view clears at 100 seconds, before cancellation reports. The aircraft never moves. A14's source-hour timing remains unchanged.

**Evidence boundary.** Fog visuals do not activate or cancel restrictions. Do not teach unverified numerical minima or generate clearances from weather alone.

**Verification.** The restored v2 backend passed 276 tests and 19 focused checks. The 18 authored v2 development cases produced 14 usable reviews and four withheld failures; a second bounded revision was rejected and exact v2 restored. These are development results, not a grading benchmark. One complete native typed fog run reached debrief with three accepted reviews from four attempts, including a genuine quotation failure and successful edited retry. Native portrait/landscape input, hidden question context, scrolling, ordinary question entry, failure retention and retry were inspected. Targeted native checks for the original three lessons are recorded separately; they are not new full lesson runs. See [typed native evidence](../../outputs/checkpoint1/typed-native-acceptance.json), [independent development review](../../outputs/checkpoint1/typed-review-independent.json) and [correctness contract](../CORRECTNESS_CONTRACT.md).

**Mode boundary.** A15 supports lesson mode only, automatically selects its own fog curve and rejects explicitly conflicting environments. A14 remains available in demo/continuous mode. Neither profile generates clearance or capacity from visual weather.

### P05 · Works or wind debris closes a route until inspection

**M2 · Assigned task — not built.** Setting: FormerT1 works boundary / apron connection / runway.

Extends A05 with a new decision task; it is not a second claim that the existing animation is newly built.

**Precedent or operational basis.** Heathrow FOD guidance identifies construction and severe-weather clean-up as sources. The 29 April 2026 T1 demolition account describes controlling and monitoring debris near live operations. This is context, not a reported accident. [Heathrow OSI081 v2.1: Airside Cleanliness and FOD Management](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASGrOps_OSI_081-Airside-Cleanliness-and-FOD-Management_v-2.pdf) [Heathrow: Demolition of Terminal 1](https://www.heathrow.com/heathrow-blog/end-of-an-era-demolition-of-terminal-1)

**Learner task.** Distinguish a suspected object, a confirmed location, recovery, inspection and an explicit reopening report.

**Assigned report sequence.** Unidentified object reported → Affected route closed → Object recovered; origin unconfirmed → Inspection completed → Explicit reopening update.

**Evidence boundary.** Do not assert that T1 works actually contaminated a runway, or label an unidentified object as aircraft debris without confirmation.

**Implementation task.** Create a reported debris branch with uncertainty about origin and a later inspection result.

### P06 · Connector-road closure and a changed route briefing

**M2 · Assigned task — not built.** Setting: Terminal3 Pier 6 / mapped airside roads.

**Precedent or operational basis.** OAN510 v4.1, issued 29 October 2026, schedules overnight Pier 6 Road South closure and diversion across Stand 307 on5–7 November 2026. OAN525 of 27 July 2026 changes Pier 7 connector-road speed following a visibility/pedestrian review. [Heathrow OAN510 v4.1: Pier 6 Road South closure/diversion](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-advice-notices/ASWorks_OAN_510_v4-1.pdf) [Heathrow OAN525 v1: Pier 7 connector-road speed change](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-advice-notices/ASDRVE_OAN_525_Pier_7_Connector_Roads_North_and_South_Speed_Limit_Reduction_v1.pdf)

**Learner task.** Determine whether a notice is future, active or expired at source time; distinguish a planned diversion from a confirmed usable route and identify the affected road.

**Assigned report sequence.** Notice received with future effective window → Closure reported active → Authorised diversion confirmed → Reopening planned → Reopening status received.

**Evidence boundary.** These are operational notices, not accidents. The upcoming works had not occurred at this register’s 2 November cutoff. Do not apply airside notices to the ambient landside loop, infer authority from map connectivity, or claim live routing.

**Implementation task.** First implement a report-only closure/route-change exercise; add route movement only after dedicated topology and restriction review.

### P07 · Winter readiness and surface-condition handover

**M2 · Assigned task — not built.** Setting: Runway, apron and service-road treatment.

**Precedent or operational basis.** Heathrow’s2026/27 snow plan is effective 16 October 2026–16 April 2027 and separately addresses movement-area clearance, surface assessment, information dissemination and remote aircraft de-icing. [Heathrow Snow Plan Airside 2026/27](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/winter-operations/Airside_SMS_Plan_AdverseWeather_Heathrow_Snow_Plan_Airside_2026_27.pdf) [Heathrow OSI093 v1: Arrival, Turnaround and Departure on Stand](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASGrOps_OSI_093_Aircraft_Arrival_Turnaround_and_Departure_on_Stand_v1.pdf)

**Learner task.** Track surface condition, treatment progress, aircraft de-icing/readiness and revised estimate as separate facts.

**Assigned report sequence.** Condition reported → Treatment/clearance in progress → Aircraft service status updated → Surface inspection reported → Readiness and movement release separately received.

**Evidence boundary.** Snow particles do not prove ice, braking condition or de-icing validity. Do not invent holdover times, performance limits or operator procedures.

**Implementation task.** Add explicit condition and treatment reports before changing any aircraft behaviour.

### P08 · Water-incident location and response handover

**M3 · Assigned task — not built.** Setting: Mapped reservoir shoreline / nearby access roads.

Extends A12 with a new decision task; it is not a second claim that the existing animation is newly built.

**Precedent or operational basis.** NTSB found Flight 1549’s survivability benefited from crew actions, suitable equipment and nearby responders’ prompt response. This does not establish rescue capability or access at Wraysbury. [NTSB AAR-10/03: US Airways Flight 1549](https://www.ntsb.gov/investigations/Pages/DCA09MA026.aspx) [Heathrow OSI076 v9: Emergency Orders public notice](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASEO_OSI_076_Emergency_Orders_v9.pdf)

**Learner task.** Reconcile aircraft location and receiving agency; distinguish response requested, dispatched, arrived, evacuation and accounted-for people.

**Assigned report sequence.** Location reported → Location corrected with source/time → Response requested → Dispatch acknowledged → Arrival/status report; people accounted for only if explicitly reported.

**Evidence boundary.** No Hudson ferry timetable, casualty count, shoreline access or water-rescue capability transfers to Heathrow. The actual reservoir’s roads alone do not prove usable emergency access.

**Implementation task.** Extend the existing water case with a bounded information-handover variation for M3 integrated evaluation; leave unknown survival/access facts explicit.

## Engine and structural-failure tasks

These three unbuilt topics are assigned within the existing milestone tasks, as recorded in ledger ML-012. They do not add three standalone courses or a flight-physics project.

| ID | Milestone | Assigned task | Current status and boundary |
|---|---|---|---|
| E01 | M2 | One-engine emergency return with a successful landing | Not built. Add a distinct reported engine problem, requested return, confirmed successful landing and separate movement/recovery update within the existing emergency-return task. |
| E02 | M3 | Both-engine thrust loss/reduction on approach | Not built. Add a bounded integrated emergency case with reported propulsion condition, explicit unknowns and confirmed outcome. No engine-performance model is implemented. |
| E03 | M3 | Reported wing/structural damage | Not built. Add an incident-comparison variation that separates damage location, extent, cause, flight status and inspection/outcome. No wing-break or structural-load simulation is implemented. |

The current accident builder depicts an authored emergency approach, damaging landing, reported gear collapse, fire and continued closure. The water case includes a loss-of-thrust report with cause unconfirmed. Those existing elements do not implement E01–E03. The [AAIB BA38/G-YMMM report](https://www.gov.uk/aaib-reports/1-2010-boeing-777-236er-g-ymmm-17-january-2008) supports a carefully stated both-engine thrust-reduction precedent involving restricted fuel flow; it does not establish exploding engines or a wing-break mechanism. Historical investigation findings remain provenance/debrief material, not automatically available learner facts. E01 needs its own suitable primary-source review; E03 needs a sourced or explicitly fictional report sequence before implementation.

## Existing-case source and limits

**A01 · A vehicle on the route.** Heathrow incident guidance includes vehicle conflicts and aircraft/ground-equipment contact. No specific historical accident is asserted for this fictional lesson. A moving vehicle or a visibly clear route alone cannot create movement permission. [Heathrow OSI067 v3: Incident Reporting and Investigation](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASSMS_OSI_067_Airside_Incident_Reporting_and_Investigation_v3.pdf)

**A02 · An occupied arrival stand.** Heathrow stand guidance distinguishes a hold for an occupied stand from cancellation of that hold. An occupant scheduled to move is not evidence that the stand has become available. [Heathrow OSI047 v3: Allocation of Aircraft Parking Stands](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASGrOps_OSI_047_Allocation_of_Aircraft_Parking_Stands_v3.pdf)

**A03 · A changing departure estimate.** Heathrow separates aircraft arrival, turnaround and departure phases and requires operator-specific procedures. Completed baggage loading does not establish all-service completion or clearance. [Heathrow OSI093 v1: Arrival, Turnaround and Departure on Stand](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASGrOps_OSI_093_Aircraft_Arrival_Turnaround_and_Departure_on_Stand_v1.pdf)

**A04 · Wildlife report, inspection and release.** Heathrow assigns active wildlife control to Airfield Operations and requires reports of hazards and strikes. Species, strike, damage and causal links remain unknown unless reported; nearby mapped water proves none of them. [Heathrow OSI077 v3: Wildlife Hazards and Reporting](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASWHM_OSI_077_Wildlife_Hazards_and_Reporting_v3.pdf)

**A05 · Dropped baggage and service-area obstruction.** The February 2024 Heathrow bulletin describes dropped loads during January on stands, service roads and baggage areas, and discusses load restraint. The animation is authored; it is not a reconstruction of a named dropped-load event or a proven cause. [Heathrow Airside Newsletter, February 2024, pp2–3](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/airside-standards/10596_Heathrow_Airside_Newsletter_Feb24_V3.pdf)

**A06 · Aircraft–vehicle contact and inspection hold.** Heathrow lists aircraft/ground-equipment collisions among reportable incidents. Do not infer injury, damage extent or cause from contact animation. [Heathrow OSI067 v3: Incident Reporting and Investigation](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASSMS_OSI_067_Airside_Incident_Reporting_and_Investigation_v3.pdf)

**A07 · Stand engine fire and continuing closure.** The public Emergency Orders notice addresses alerting and stakeholder coordination; the full orders have controlled distribution. This fictional fire is not caused by earlier birds unless a report establishes that; no real response-time standard is implied. [Heathrow OSI076 v9: Emergency Orders public notice](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASEO_OSI_076_Emergency_Orders_v9.pdf)

**A08 · Damaging landing and runway recovery hold.** G-YMMM lost thrust on approach and touched down short of Heathrow27L on 17 January 2008; AAIB found restricted fuel flow. Heathrow also publishes recovery responsibilities. The app’s gear-collapse/fire sequence is fictional, not BA38; no investigation cause transfers to its live reports. [AAIB AAR 1/2010: Boeing 777-236ER G-YMMM](https://www.gov.uk/aaib-reports/1-2010-boeing-777-236er-g-ymmm-17-january-2008) [Heathrow OSI069 v2: Aircraft Recovery Plan](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASEO_OSI_069_Aircraft_Recovery_Plan_v2.pdf)

**A09 · Rejected takeoff after an airspeed concern.** Heathrow G-EUUO on 9 June 2021 and G-YMMR on 11 June 2021 rejected takeoff; AAIB later identified insect nesting in pitot probes in the investigated series. The learner initially knows the reported concern, not the later investigation cause. The app is not a flight-data trace or V1 training. [AAIB-27362: Heathrow pitot/static events, March 2022 bulletin](https://assets.publishing.service.gov.uk/media/6221e05fe90e0710be03550f/Various_CAT_03-22.pdf)

**A10 · Go-around while the runway remains occupied.** Heathrow’s2024 annual operational report discusses delayed runway vacation as a go-around context. No named flight is reconstructed. A go-around is not automatically an accident; later landing and runway clearance need separate reports. [Heathrow ANATMT Annual Report 2024, section3.5](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/local-community/noise/reports-and-statistics/reports/anatmt/Heathrow_ANATMT_Annual_Report_2024.pdf)

**A11 · Maintenance vehicle runway incursion.** At Heathrow on 26 February 2019, a disorientated maintenance-vehicle driver entered the runway; D-AEAD’s takeoff clearance was cancelled before its roll began. Do not turn this event into a high-speed rejection or assert a specific red-stop-bar crossing. [AAIB: D-AEAD runway incursion](https://www.gov.uk/aaib-reports/aaib-investigation-to-airbus-a300b4-622r-f-d-aead)

**A12 · Emergency water landing.** Flight 1549 ditched on the Hudson on 15 January 2009 after bird ingestion caused near-total loss of thrust in both engines. This occurred in the USA, not at Heathrow. Wraysbury is an authored transfer of a hazard category: no local ditching precedent, feasible diversion, depth, flotation, survivor count or rescue timetable is claimed. [NTSB AAR-10/03: US Airways Flight 1549](https://www.ntsb.gov/investigations/Pages/DCA09MA026.aspx)

**A13 · Rain, snowfall and dusk/night presentation.** Heathrow has a winter plan addressing snow response, treatment and condition reporting. Visual rain/snow/darkness currently establishes no braking action, accumulation, operational visibility, de-icing completion or permission. [Heathrow Snow Plan Airside 2026/27](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/winter-operations/Airside_SMS_Plan_AdverseWeather_Heathrow_Snow_Plan_Airside_2026_27.pdf)

## Completion rule

Mark an assigned row Built only after its reports, movement and questions are implemented. Move verification to Passed only after checking the source clock, correct aircraft or vehicle, report cutoffs, geometry and visible native result. Record the actual build, run and evidence link in the tracker. An accepted model response shows that the current evidence checks passed; it does not independently establish visual truth or professional competence.

Terminal 1 remains a former-terminal area with phased demolition underway. The dated historical outline is not proof of the surviving structure. T2A–T2B and T2–T3 passenger links include underground connections; the map must not invent surface passages to create a training route.

Implementation status was checked against [training_assessment.py](../../backend/training_assessment.py), [lessons.py](../../backend/lessons.py), [fog_lesson.py](../../backend/fog_lesson.py), [runway_scenarios.py](../../backend/runway_scenarios.py), [flight_cycle.py](../../backend/flight_cycle.py), [accident_scenarios.py](../../backend/accident_scenarios.py), [training_environment.py](../../backend/training_environment.py), [IMPLEMENTATION_DOCKET.md](IMPLEMENTATION_DOCKET.md), [HEATHROW_SCENARIO_BASIS.txt](../HEATHROW_SCENARIO_BASIS.txt).

## Weather-driven queues

P09 · Weather-driven arrival and departure queues
Assigned to Checkpoint 2 — not built. Develop one bounded queue exercise; compare the selected task across airport sizes and demand profiles in Checkpoint 3.
Learning task: Identify the reported capacity restriction, distinguish an arrival hold from a departure or stand queue, and update the expected sequence when a newer report changes the situation.
Basis: NATS describes additional separation and movement precautions during low visibility. Its Heathrow account explains how time-based and aircraft-pair-specific separation help preserve arrival throughput. Strong headwinds and low visibility therefore need different authored capacity profiles; ordinary rain or darkness must not automatically imply a closure.
Driver design: Use a scheduled demand stream with seeded variation, separate arrival and departure queues, runway occupancy reservations, stand occupancy and an explicit operating-state timeline. Reserve a runway slot and downstream space before releasing a movement. Represent airborne delay at defined holding locations or as a clearly labelled queue; do not scatter aircraft densely in the sky.
Example teaching hour: normal operations → low-visibility restriction reported → arrival and departure queues build → one occupied stand delays an inbound aircraft → conditions improve but restrictions remain → release confirmed and backlog clears gradually. A separate strong-headwind variant changes arrival throughput without claiming low-visibility procedures are in force.
Keep the original schedule, revised estimate and actual movement times separate. Record why each aircraft is waiting, the source of that reason and its availability time. The same seed and source time must produce the same queues at 1× and 30×. Pending answers and checkpoints keep their existing pauses.
Start with an illustrative capacity model, not operational separation minima. Calibrate it only if suitable public data and a defined comparison are available. Weather effects alone must not create report evidence, invent a clearance, diagnose a flight delay or reproduce Heathrow’s proprietary controller tool.
Acceptance: no overlapping runway reservations, no stand overbooking, no queue teleportation or grass shortcuts, bounded accumulation, safe stop on stale updates, and equal source-time outcomes at normal speed and time-lapse. Report queue length, waiting time and recovery time separately from learner accuracy.
Sources: NATS — Low visibility procedures: what you need to know; NATS — How Heathrow transformed performance with Pairwise Separation.

## Airport scale


Airport size and traffic pressure
These exercise comparisons are assigned to Checkpoint 3; they are not regulatory airport classifications. The current mapped environment is Heathrow. A small airport can still have a difficult layout, and a large airport need not be busy in every exercise; vary physical size and demand separately.
Small setting: one runway, a compact stand area and a few service resources. A single blocked stand or unavailable vehicle becomes the main dependency. Suitable tasks: stand-clearance checks, a reported route obstruction, and missing service confirmation.
Medium setting: several stand groups, a shared taxi route and overlapping arrival/departure demand. Suitable tasks: queue spillback, a changing stand assignment, or a service delay that affects a later movement.
Major-hub setting: multiple terminal areas, runway configurations and concurrent report streams. Suitable tasks: weather-related capacity reductions, arrival and departure queues, conflicting stand demands, and a recovery handover. Heathrow is the current geographic reference for this profile.
These profiles change traffic demand, runway availability, stand capacity, route topology, service resources and reporting delay. They must preserve real aircraft dimensions, turning envelopes and road widths. Use a sourced layout or clearly labelled fictional airport; do not miniaturise Heathrow and call it another real airport.
For a fair evaluation, first hold the evidence task and reporting delays fixed while changing traffic density. Then test layout complexity separately. Measure missed updates and unsupported conclusions as well as completion time; more aircraft alone is not evidence of better training.
Milestones: M1 includes the current Heathrow setting and fog practice lesson; M2 implements and tests the weather-driven queue task, visual-evidence study and a distinct turnaround task; M3 compares the selected task across size and demand profiles and evaluates the integrated experience. Evidence and movement checks are required acceptance conditions for these assigned tasks. Additional airport layouts are not yet implemented.

Fog status: the fog visual profile and A14 source-hour demonstration are implemented and native/model verified. A15/P04 is the implemented fourth practice lesson assigned to M1, with bounded native acceptance recorded. Current visual profiles are clear, rain, snow, dusk/night and fog. Weather-driven queues/capacity are assigned to M2 and not yet implemented. See [fog acceptance](../../outputs/checkpoint1/fog-acceptance.json) and [milestone ledger](MILESTONE_LEDGER.md).

Editable tracking document: https://docs.google.com/document/d/1IxdtKDWxUWhK9r1QpWOi_MGtqnmmWsMd0sd-nme8ulk

Queue-model sources: [NATS on low-visibility procedures](https://nats.aero/blog/2025/10/low-visibility-procedures-what-you-need-to-know/), [NATS on Heathrow Pairwise separation](https://www.nats.aero/news/elevate/may-26/a-real-game-changer-how-heathrow-transformed-performance-with-pairwise-separation/).

## Recent precedents and Heathrow-specific variants

These are researched design recommendations, not newly implemented scenarios or an
expansion of the current recording. They reuse the assigned M2/M3 task families.
The milestone ledger entries ML-016 onward preserve the placement reasoning.

| Reference | Proposed learner task | Placement and boundary |
|---|---|---|
| Jeju Air 2216, Muan, 29 December 2024 | Separate bird warning, reported strike, emergency return request, unknown damage and confirmed outcome. | M2 wildlife/return variation. The preliminary report does not establish a particular engine diagnosis or pilot-error cause; a successful return branch would be authored. |
| Air Busan BX391, Gimhae, 28 January 2025 | Track a cabin-smoke report before pushback, evacuation status and responder access independently. | M2 turnaround/handover variation. This is different from the existing engine-fire visual; do not infer a confirmed battery cause from smoke. |
| Air Canada Express 8646, LaGuardia, 22 March 2026; LATAM 2213, Lima, 18 November 2022 | Identify an aircraft and emergency vehicle, their reported runway use, addressed crossing instructions and unresolved conflicts. | M2 incursion/communication variation. These involved firefighting vehicles, not fuel trucks. Current M1 incursion stops departure before roll; it does not reconstruct either collision. |
| United 169, Newark, 3 May 2026 | Revise an incident summary when a reliable correcting report distinguishes aircraft impact, secondary debris contact and separate road/aircraft status. | M3 integrated road/incident handover. NTSB says the aircraft struck a light pole and its debris hit a tractor-trailer; do not animate direct aircraft–car contact as the established event. |
| Heathrow traffic density, runway configuration and weather | Track the effect of a reported runway-use change on a small arrival/departure queue; identify which earlier assignments and estimates need confirmation. | M2 Q01 design variant. Authored demand/service rates are not Heathrow capacity predictions or operational separation rules. |

Heathrow's busy operation is part of its local identity: its official operational
data records 477,894 air transport movements in 2025 against the 480,000 annual
cap. Its published runway-alternation explanation describes the 15:00 swap during
westerly operations, with weather and operational exceptions. It also describes
strong south-westerly winds interacting with maintenance-area buildings and
affecting approaches to the northern runway, and patchy fog influencing runway use.
These give the existing queue/weather work local context. A published schedule is
not itself a clearance or proof that a planned change has happened.

NATS describes time-based and aircraft-pair-specific arrival spacing at Heathrow.
That supports a learning question about why traffic flow changes with weather and
aircraft mix; it does not license arbitrary shorter gaps or establish that this
app implements NATS' separation system. A future comparison of an airport such as
Gimhae, whose published circling guidance addresses terrain north of the Namhae
Expressway, would require a separately reviewed layout and approach. Do not copy
that terrain-specific difficulty into the Heathrow scene.

Primary sources:
- [ARAIB Jeju preliminary report listing](https://araib.molit.go.kr/USR/airboard0201/m_34497/dtl.jsp?r_id=344) and [readable copy of the ARAIB preliminary report](https://dlapilota.pl/sites/default/files/dlapilota/upld/Raport_wst%C4%99pny_katastrofa_Jeju_Air.pdf).
- [Republic of Korea paper to ICAO, April 2025](https://www.icao.int/sites/default/files/APAC/Meetings/2025/2025%20APRAST23/3-Working%20Papers/APRAST23-WP-16-AI_5-ROK-Lithium-battery-and-E-Cigarette-Cabin-Fire-Risks.pdf). It describes a suspected battery mechanism and ongoing investigation, not a final determination. The later Air Busan interim attachment was not inspected.
- [NTSB LaGuardia investigation](https://www.ntsb.gov/investigations/Pages/DCA26MA161.aspx), marked ongoing with preliminary information; [CIAA Lima final-report listing/file](https://cdn.www.gob.pe/uploads/document/file/5209692/INFORME%20FINAL%20ACCIDENTE%20DE%20AVIACI%C3%93N%20N%C2%B0%20008-2022.pdf), indexed but direct retrieval failed during this review; no detailed causal findings are claimed from the unread attachment.
- [NTSB United 169 investigation](https://www.ntsb.gov/investigations/Pages/DCA26FA194.aspx), preliminary account updated 4 June 2026, ongoing.
- [Heathrow operational data](https://www.heathrow.com/company/local-community/noise/data/operational-data), [runway alternation](https://www.heathrow.com/company/local-community/noise/operations/runway-alternation), [NATS pairwise separation account](https://www.nats.aero/news/elevate/may-26/a-real-game-changer-how-heathrow-transformed-performance-with-pairwise-separation/).
- [Republic of Korea AIP amendment, effective 18 March 2026](https://aim.koca.go.kr/eaipPub/Package/2026-03-18-AIRAC/pdf/AIRAC%20AIP%20AMDT%202_26.pdf), Gimhae circling guidance. It is a dated procedural reference, not a claim that no later amendments exist.

Accident investigations inform the scenario design and debrief. Their later
findings are not automatically available to a learner earlier in the simulated
event. Each exercise needs its own source/receipt times, explicit unknowns,
reviewed movements and independent acceptance before publication.
