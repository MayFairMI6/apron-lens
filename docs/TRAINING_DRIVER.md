# Controller exercises

The controller experience follows one external service that owns source time, movement, reports and lesson transitions. The viewer offers aircraft selection, pan/zoom, report answers and expandable evidence. Models and playback controls stay outside the learner interface.

The external driver is local to the Mac: `backend/lessons.py` generates the seeded world, routes and report schedule; `backend/training_session.py` owns its clock, reservations and lesson state; `backend/training.py` publishes it on port 8767. Unity's `ExternalTrafficDriver.cs` consumes `/traffic`. This is repeatable generated training traffic, not a live aircraft feed. The same seed reproduces the same world.

**Sources** expands the reports cited by the current accepted answer, limited to that answer's receipt cutoff. It shows each report's text, reporting source, received time and ID. **Recent reports** shows up to twelve received reports for the selected flight at the current scenario time, which may be later than the answer. An unavailable answer has no accepted claims to expand; its underlying reports remain accessible through Recent reports.

Run one profile from the repository root:

```sh
# Short lesson with three checkpoint pauses; Next exercise cycles the set.
.venv-candidates/bin/python -m backend.training --exercise surface_conflict --mode lesson --seed 17
# Full hour at normal speed.
.venv-candidates/bin/python -m backend.training --exercise late_arrival --mode continuous --seed 17
# Full hour condensed around eleven ordinary assistant questions and incident/movement windows.
.venv-candidates/bin/python -m backend.training --exercise late_baggage --mode demo --seed 17
```

Use one service at a time on port 8767. Qwen3.5-9B and the working `apronlens-v2-mps` profile are preselected and preloaded. No paid voice or model API is used. Configure an installed iOS preview with `python3 scripts/configure_ios_assistant.py DEVICE_UUID --port 8767`.

The lessons cover a vehicle obstructing a route, a late inbound waiting for an occupied stand, and delayed baggage changing an off-block estimate. Each has briefing, practice, three four-choice checkpoints, source-backed feedback and a debrief. Checkpoints freeze at 60, 120 and 180 source seconds; the lesson ends at 210. The scene, history and assistant are hidden during questions. Scores are deterministic formative feedback, not a validated assessment of professional competence. Pilot and turnaround perspectives appear in debrief. Dedicated cockpit procedures and separate role courses remain outside this milestone.

The seeded hour-long world is identical across profiles. Quiet demonstration periods use 30×; teaching windows and pending assistant requests use 1×. Requests receive ten seconds of reading time afterward. A failed or timed-out request is recorded as a failure, never replaced with a scripted answer. A disconnected viewer predicts for at most three seconds, never crosses the next server boundary, then freezes.

After the 210-second scored portion, the guided and full-hour profiles include TRN101's local circuit: pushback, taxi to a separate 1,800-metre training runway, line-up, takeoff roll, rotation, climb, return approach, flare, touchdown/rollout, runway exit and taxi back to Stand A. This is a continuous authored 3D path, not a flight-dynamics simulation. Pitch is supplied independently of travel direction, including a nose-up landing flare; landing gear retracts and deploys. Runway occupancy is reserved separately and the existing conservative ground reservation prevents conflicting ground movements. Reports of the exercise authorisations and flight phases are delivered at their source times; future movement plans never become answer evidence.

The guided viewer follows the departing and returning aircraft automatically, with phase and altitude labels. Wildlife, takeoff, landing, the stand-fire response and dropped-baggage recovery use 1×; quiet intervals use 30×. The earlier five-question recording lasted 8:27; the added baggage window extends a fresh full run, depending on inference time. Apron, Runway and Follow flight views remain available. The short scored lesson still ends at 210 seconds; it does not run the later flight circuit. Dedicated cockpit procedures remain outside this milestone. Separate incident demonstrations follow; the camera illustrates events while the assistant uses received reports.

Ground pavement and aircraft trajectories now share the geometry from `backend/ground_routes.py`. Taxi corners are tangent circular arcs sampled at no more than five degrees, with measured radius and turn sweep retained in the snapshot. Nose headings are explicit: straight reverse pushback preserves the stand-facing heading, followed by a forward quarter-circle; runway roll uses local heading 090°. Headings refer to the training coordinate system, not surveyed Heathrow magnetic bearings. `predictionBoundaries` marks reports, phase changes, stops and starts; dense interpolation samples do not stall client prediction. Older snapshots retain their waypoint boundaries.

Before departure, the driver adds a flock near the runway entry, a wildlife hold, an inspection report and a separate controller release. The aircraft cannot enter before that release. After return, an engine-fire report stops TRN101 at Stand A; containment does not reopen the stand. Other traffic gets a later separate release and TRN101 remains parked for the rest of the hour. Visual birds, flame and smoke use the external source clock. They freeze with it and are not assistant evidence. Two ordinary assistant questions target TRN101 for wildlife and fire, in addition to the original three scored-topic questions.

The later dropped-baggage incident targets TRN102 at its actual parked stand. A tug and cart approach on a paved service lane, the gate opens, bags spill and recovery markers appear. Collection, inspection, loading completion and movement release have separate receipt times. Two further ordinary assistant questions ask why the aircraft is held and whether collection has released it. The bird/baggage extension introduced seven automatic questions; the current collision/landing extension has eleven; the scored lesson still has exactly three checkpoints. Background movement reservations keep the affected aircraft stationary until the cart has cleared. The bird flock has articulated wings, individual feathers, staggered flapping/gliding and a dispersal path; the guided camera follows the flock and later focuses on the baggage incident. Both use original free procedural models. These are illustrative 3D animations, not photogrammetry or validated bird/vehicle physics. See the [native incident checks](../outputs/checkpoint1/incident-acceptance.json) and [supplemental recording guide](course/INCIDENT_DEMO_SUPPLEMENT.txt).

Heathrow and UK CAA guidance informs the reporting distinctions and debrief. `docs/HEATHROW_SCENARIO_BASIS.txt` identifies the exact publications, versions, applicable sections and authored simplifications. The publications are design references, not live report evidence. The exercise is not a reproduction of Heathrow emergency orders or operational flight clearances.

All endpoints require the existing local bearer token. `GET /traffic` retains existing fields and adds optional `clock` (`runId`, `revision`, `rate`, `state`, `nextBoundary`) and `training`. Old snapshots default to 1×. `GET /training` provides learner state without answer keys. `POST /training/action` accepts readiness, answers, continuation, retry, next exercise and demonstration acknowledgements. Every action has `actionId`, `runId` and phase `revision`; retries are idempotent, stale or conflicting actions return 409. Pending answers are discarded after flight, attempt or checkpoint-phase changes.

`evidencekit.SourceRecord` version 1 records episode identity, source identity, source time, availability time and evidence kind. Availability and provenance checks do not certify visual truth. Movement plans are rendering input, not model evidence. The training adapter selects available typed facts, expands them and uses the existing validator. Original prompts, outputs and acceptance outcomes remain in audit logs.

This is an authored apron, not surveyed Heathrow geometry or live traffic. The whole circuit is conservatively reserved for one moving aircraft at a time. Stand release requires physical vacancy and an explicit received report. Ground release and time estimates do not establish takeoff clearance. Free assets remain in use. Physical-device ARKit, continuous voice, airborne accident dynamics and full Heathrow reconstruction are deferred. A damaging-landing illustration is present; it is not a flight-physics model.

The training-only evidence-selector prompt is version 4. It distinguishes a known negative/restricted state from an absent report; a current hold is not an unknown property. The model still chooses the fact IDs and unknown properties, and the unchanged validator rejects contradictory or unsupported proposals. No failed answer is repaired by deleting an unknown, and no scenario-specific answer is inserted. The training parser accepts one complete JSON object either directly or in one JSON-only Markdown fence (`single-json-or-fence-v1`). It does not extract objects from prose, repair malformed JSON or change evidence selections. The original fenced wildlife response and its initial rejection are retained in the audit; revalidation changes only its outer format.

For a real-model regression before starting the service:

```sh
.venv-candidates/bin/python -m scripts.verify_training_answers --output work/stand-answer-check.json
```

This checks the original stand-availability question, a paraphrase with another seed, the report receipt boundary, a later answer and a missing fuel report. These text-only probes complement the simulator's image-bearing requests. The output path must be new; original model selections are retained in its companion prompt audit.

```sh
.venv-candidates/bin/python -m unittest discover -s tests -p 'test_training*.py'
PYTHONPATH=tests .venv-candidates/bin/python -m unittest discover -s tests -p 'test_conversation*.py'
.venv-candidates/bin/python -m unittest tests.test_traffic tests.test_role_demo tests.test_flight_cycle tests.test_ground_incidents
```

Tests cover 60 seeded worlds (20 per lesson), reservations, pavement coverage, tangent headings, wildlife hold/release, fire containment/stand closure, occupied-stand sequencing, report timing, normal/accelerated equivalence, pause/scoring behavior, stale responses, duplicate actions and authenticated endpoints. Simulator acceptance is recorded separately. Logs: `work/training-sessions.jsonl`, `work/training-conversations.jsonl` and `work/training-prompts.jsonl`. Historical profiles and frozen research results remain unchanged. This training milestone does not establish the earlier visual-perception research milestone.

Distinct incident presentation

The recording plan presents separate time-scaled cases, not a probable chain of incidents in one airport hour. The service currently authors these windows on one source timeline; report cutoffs stay intact in edited excerpts. Individual chapter titles are presentation boundaries, not new independent runs.

`backend/accident_scenarios.py` adds aircraft–vehicle contact for TRN102, followed by an emergency arrival for TRN103. Four ordinary model questions test the initial restrictions and later updates. The contact aircraft remains stopped after the vehicle is secured. The landing path has approach altitude, touchdown/bounce, damaged rollout and final stopped attitude; the runway remains reserved/closed after containment. A final reservation prevents later background circuits from restarting. The new optional waypoint fields `roll` and `bodySink` default to zero for older snapshots. Free procedural response vehicles and closure markers are illustrative.

The simulator captures used a private local inspection harness to select source-time windows. That endpoint is not part of the published training server. See outputs/checkpoint1/accident-acceptance.json for actual questions, latencies, failures, source hashes and capture boundaries.

Weather and daylight

Add `--environment rain`, `--environment snow` or `--environment dusk` to any launch profile; default `clear` preserves previous snapshots and daytime behavior. `backend/training_environment.py` attaches versioned frames containing source time, precipitation intensity and daylight. These frame boundaries join the driver's prediction boundaries. Unity's `TrainingWeather.cs` interpolates lighting and precipitation against `StandReplay.Clock.Time`; particles do not use a separate wall-time clock. Pauses, speed changes, bounded prediction and disconnection freeze therefore apply to the environment too. Restart reproduces the authored progression.

The dusk timeline covers late afternoon through dusk to night across the 3,600-source-second world. It is not a full solar/24-hour cycle and has no sunrise. Rain and snow are separate visual settings, not a meteorological generator; they do not alter braking, aircraft routes, taxi speeds, de-icing, scoring or report evidence. Operational weather lessons are planned in Checkpoint 2; see docs/course/IMPLEMENTATION_DOCKET.md.

The new recording includes separate 30× rain/snow/dusk inspection clips with question/teaching pauses disabled in a private capture harness. The published guided profile retains ordinary 1× teaching/answer pauses. Weather clips are visual checks, not new end-to-end lesson/model acceptance runs.

## Independent runway and water demonstrations

The same external service now also accepts `rejected_takeoff`,
`occupied_runway_go_around`, `runway_incursion`, and `water_landing`.
For example:

```sh
.venv-candidates/bin/python -m backend.training --exercise rejected_takeoff --mode demo --seed 17
```

Change the exercise name to launch another case. In this set, **Next exercise**
cycles these four demonstrations after debrief. Each has a fresh run identity,
its own reports and three ordinary model questions. Each spans 3,600 source seconds;
quiet periods run at 30×, teaching moments and pending answers at 1×, with ten
seconds after a response for reading. `--mode continuous` uses normal speed.
`--mode lesson` explicitly rejects these cases: they have no assessment key and do
not expand the three scored lessons. Model failures remain visible.

`backend/runway_scenarios.py` supplies the cases. The geographic extract is in
`data/geography/heathrow-west.json`; its provenance and ODbL attribution are in
`data/geography/README.md`. **Region** shows the mapped reservoir, both runways and
terminal footprints. **Terminal 3** provides an architectural view of the mapped
hall, courtyard and entrance canopy combined with source pier details. **Runway** gives a broad runway view; **Follow flight** centres
the selected aircraft. The map uses the same kilometre-to-metre scale as movement.
Only received typed reports reach the assistant; the map is not report evidence.

The T3 source asset, original texture, placement, GPL notice and current-outline
derivatives are documented in `data/geography/terminal3/PROVENANCE.txt`.
`scripts/bake_terminal3.py` generates the included Unity resource. Glazing,
unsurveyed hall heights and façade lettering are illustrative. Scenery changes
follow the reference/implementation/independent-review workflow in `AGENTS.md`.

The RTO stops within Runway 09R. The go-around stays airborne with TRN102 occupying
the runway. The incursion keeps TRN101 stationary because cancellation precedes
its takeoff roll. The water case descends onto the actual Wraysbury polygon and
slows to a stop inside it. Paths, speeds, water response and timings are authored;
these are investigation-informed examples, not certified aircraft dynamics or
exact accident reconstructions. No operational suitability of the reservoir is
asserted. Details and source links: `docs/HEATHROW_SCENARIO_BASIS.txt`.

For the geography/incident regression suite:

```sh
.venv-candidates/bin/python -m unittest tests.test_runway_scenarios tests.test_training_session -q
```

The native editor check `RunwayCaseVerification.Run` consumes one JSON fixture
per case from `APRONLENS_RUNWAY_FIXTURES`; fixtures are generated with
`build_demonstration(17, case)[0]`. It checks all four scenarios, sourced shoreline
triangulation, map rendering, source-clock water effects and legacy compatibility.
