# AirfieldLens Checkpoint 1

The core application scope remains controller situational-awareness training,
four practice exercises, moving aircraft and a report-grounded assistant. The fourth,
`fog_restrictions`, is implemented. All four lessons now use typed responses and qualitative model feedback; the bounded qualitative prototype has native acceptance evidence and documented model failures. Pilot
and turnaround implications appear in debrief. Weather-driven queues, a dedicated
turnaround task and visual-evidence research are assigned to Checkpoint 2. No
separate pilot course is delivered. The separate video-memory project is deferred.

The [execution queue](EXECUTION_QUEUE.md) records completed C01 documentation and bounded checks of the current evidence, time, identity and request-lifecycle contracts. This is specified and tested behavior, not formal proof. A new structured
claim checker and bounded driver-state specification are queued for M2; formal
model checking and comparative evaluation are queued for M3. No new reasoning
architecture is required for the present M1 acceptance, and frozen M1 research
results remain unchanged.

The project is now titled **AirfieldLens** (previously ApronLens). The owner
approved a voice-matched replacement of Person 1's opening sentence and updated
video branding. The original narration and earlier recordings remain archived.
Repository paths, bundle identifiers and frozen research records retain their
existing names for compatibility.

The presentation uses distinct scenarios, with time scaling within each case.
Routine operational disruptions anchor the practice lessons; wildlife, dropped
baggage, aircraft–vehicle contact, stand fire and a damaging emergency landing
provide separate demonstrations of evidence and restrictions. The emergency cases
are not presented as probable events in one airport hour. Geometry, response
intervals and incident physics remain authored illustrations. Heathrow sources
support the hazard categories; they do not establish our timings or probabilities.

The coverage audit led to four additional independent demonstration profiles:
rejected takeoff, occupied-runway go-around, vehicle runway incursion and a water
landing at the geographically positioned Wraysbury Reservoir. Each has its own run
identity, reports, three ordinary assistant questions and a one-hour source clock.
The water case is authored; no Heathrow reservoir accident or operational suitability
is claimed. Official investigations inform event sequence, while generic aircraft,
kinematics and response timing remain illustrative. The incursion cancels departure
before the roll, matching the cited D-AEAD sequence. These demonstrations add no learner assessment
questions. A separate fog practice lesson now addresses reported restrictions. A
specific red-stop-bar conflict, further operational-weather tasks, runway debris,
communication-error tasks and full recovery/reopening are assigned to Checkpoint 2.

The four additional runway/emergency profiles passed 20 seeds each in the 241-test backend suite and 113 Unity checks. Each selected native run reached its one-hour debrief and displayed three actual accepted model responses, twelve across four runs. These are functional examples, not an accuracy benchmark. The first water capture is retained; its oversized close-view map label was corrected and that case was recorded again. See outputs/checkpoint1/runway-acceptance.json.

The linked [30:33 historical Drive recording](https://drive.google.com/file/d/1uHIweEFSlO4CRb8-VyNM7aZUd4mhsMhQ/view) is an earlier edit. The subsequent local `AirfieldLens-demo.mp4` and `AirfieldLens-demo-without-voiceover.mp4` are 30:28.5, with internal presenter divider cards removed and the approved opening audio preserved. The new local edits are `AirfieldLens-presentation.mp4` (8:06.4) and `AirfieldLens-walkthrough.mp4` (40:02.1), each with a `-without-voiceover` counterpart. Their opening narration is unchanged; later footage has no new narration. Verification records are in `outputs/checkpoint1`. Existing scripts retain historical cue times and should not be used as the new edit's timing sheet. The original recordings remain archived.

The edit uses genuine source footage and model responses. Earlier incident chapters are targeted excerpts; each new runway/emergency profile completed an independent one-hour run. Branding overlays update only the name in earlier footage and the labelled saved debrief. They do not alter answers, scenario clocks or evidence.

Heathrow's AI-assisted digital-tower trials provide relevant motivation for the
next research stage. NATS describes testing, and Searidge describes camera-based
monitoring of aircraft and runway thresholds to assist people. AirfieldLens currently
answers from reports. Checkpoint 2 will test whether images add reliable evidence;
Checkpoint 3 will evaluate the integrated experience and failures. See the
[primary-source design notes](../HEATHROW_SCENARIO_BASIS.txt). Rain, snowfall and late-afternoon → dusk → night are implemented as visual conditions on the external source clock. The reported fog-restriction lesson belongs to Checkpoint 1. Weather-driven queues, visual-evidence evaluation and a distinct turnaround task are assigned to Checkpoint 2; airport-size/demand comparisons and integrated condition testing are assigned to Checkpoint 3. The current dusk profile is one source hour, not a full 24-hour solar cycle. See the [implementation docket](IMPLEMENTATION_DOCKET.md).

The learner-facing header is simply AIRFIELDLENS followed by the exercise title.
Controller situational awareness describes the learning objective in developer
and course documentation; it is not a role selector or a label in the header.

The current preview ran in the iOS Simulator on Apple Silicon. The fictional
Heathrow-informed environment includes an occupied stand, paved turns, a local
takeoff/landing circuit, wildlife, dropped baggage, ground contact and separate emergency examples. This recording does
not establish physical-device AR tracking, survey-grade Heathrow accuracy or
professional training competence.

AirfieldLens is positioned as portable scenario practice and review for learners, not an operational control workstation. The phone suits a focused flight/report/checkpoint task; a tablet or larger display is the recommended format for a broader traffic overview. This is a design recommendation, not a completed controller-usability finding. Checkpoint 3 will compare phone and larger-screen use with representative learners. See the [mobile-training source note](../HEATHROW_SCENARIO_BASIS.txt).

## Evidence and presentation

- [Presenter guide](CHECKPOINT1_PRESENTER_GUIDE.txt): narration, video-player cues,
  short presentation route and likely questions. Suggested durations are not a
  verified assignment limit.
- [Saved demo acceptance](../../outputs/checkpoint1/heathrow-acceptance.json):
  the source-hour run, six actual model responses, original failures and source
  hashes. This is the original pre-publication record, not a new run per commit.
- [Three-lesson acceptance](../../outputs/checkpoint1/lesson-acceptance.json):
  the initial simulator lesson completions and failures retained for context.
- [Fresh native rerun](../../outputs/checkpoint1/native-ios-rerun.json): another
  complete source-hour run with six actual model responses accepted, before the
  cosmetic header update. The [header verification](../../outputs/checkpoint1/learner-header-verification.json)
  records the subsequent native rebuild and visual check; the full demo was not
  repeated for that label-only change.
- [Frozen M1 report](../../outputs/m1_ar_context/REPORT.md): 40 distinct held-out
  turns, 17 families, four scenarios, two local Qwen models and a deterministic
  baseline in three conditions; images off. Qwen3.5-9B scored 24/40 in full AR.
- [Training driver](../TRAINING_DRIVER.md) and [scenario sources](../HEATHROW_SCENARIO_BASIS.txt).
- [Bird and baggage acceptance](../../outputs/checkpoint1/incident-acceptance.json):
  226 backend tests, 52 Unity checks, native build/install and targeted native clips
  with actual model responses. These clips use explicit source-time jumps between
  incident windows; they are not another uninterrupted full-hour acceptance run.

The assistant uses Qwen3.5-9B to select eligible report facts, checked by a
deterministic validator and rendered as a report summary. Images are sent in
the demo, but its answers do not establish visual recognition. Sources expands
reports behind an answer at its cutoff; Recent reports can include later arrivals.
Six accepted demo answers are not a model benchmark.

The saved 8:27 recording is an unscored guided demonstration with five automatic
questions and one manual post-containment question. The short learner profile
used three fixed-choice scored checkpoints and ended at 3:30 of source time. The current learner flow retains the three source-time checkpoints but uses typed responses and qualitative practice feedback. The extended
driver now includes eleven automatic questions, including four collision/landing
questions. Those historical captures cover the original three fixed-choice lessons. Their worlds remain unchanged; the fourth fog practice lesson has separate acceptance.

- [Collision and landing acceptance](../../outputs/checkpoint1/accident-acceptance.json):
  229 backend tests, 60 Unity checks, native build/install and two targeted landscape
  recordings with four actual accepted answers (10.203–17.736 seconds). An earlier
  cold-model request exceeded the app timeout; its failure is retained. These checks
  do not replace the earlier full-hour or three-lesson acceptance records.
- [Current video edit record](../../outputs/checkpoint1/scenario-demo-edit.json):
  source cuts, Person 1 audio identity, separate scenario cards and verification.

- [Weather acceptance](../../outputs/checkpoint1/weather-acceptance.json): 231 backend tests, 69 Unity checks, native build and rain/snow/dusk captures. Visual changes follow source time; they do not alter aircraft performance or create operational evidence. The private 30× capture profile suppresses question/teaching pauses and adds no new model-response acceptance claims.
- [Weather video edit](../../outputs/checkpoint1/weather-demo-edit.json): appended clips, source windows and preserved Person 1 audio.

The in-app “Allow 3–5 minutes” estimate has been removed, and the elapsed clock is labelled “Scenario”. Guided/full-hour profiles still span 3,600 source seconds; short typed practice still spans 210 source seconds with question/review pauses.

## Try the source without model weights

From this checkout, with Python 3.12:

```sh
python3.12 -m venv .venv-ci
.venv-ci/bin/python -m pip install -r requirements-ci.txt
.venv-ci/bin/python -m unittest discover -s tests -v
.venv-ci/bin/python scripts/check_research_integrity.py --current
.venv-ci/bin/python -m backbone.check --project backend scripts tests modelaccess
```

These checks do not run the real model or Unity viewer. The pre-publication local
run passed 224 tests and both integrity checks. The earlier simulator record has
121 targeted Python tests, 43 Unity checks and 60 seeded worlds; those are different
check sets, not additional independent research samples.

## Run the real assistant

Use an Apple Silicon Mac with sufficient memory for the pinned unquantized local
Qwen3.5-9B model and Unity/Xcode. The runtime is fixed to Apple MPS and does not
silently select a CPU or another model. Weights are a separate large download.
The original host is verified; a teammate's machine needs its own setup check.

```sh
python3.12 -m venv .venv-candidates
.venv-candidates/bin/python -m pip install -r requirements-candidates.txt
.venv-candidates/bin/python -m backbone.download --model qwen3.5-9b
.venv-candidates/bin/python -m backend.training --exercise late_arrival --mode demo --seed 17
```

Add `--environment rain`, `--environment snow`, `--environment dusk` or `--environment fog` to compatible cases. Other cases default to clear daytime; the two fog cases automatically use their own fog timeline. The driver supplies the visual timeline and Unity renders it at the same source time as movement and reports.

The model loads before readiness on port 8767. Each host generates its own local
token in the ignored work directory. Use one training service at a time. For
typed practice, use `--mode lesson --exercise surface_conflict`; Next exercise
cycles through all four. Launch the fourth directly with `--mode lesson --exercise fog_restrictions`. It uses a separate 210-second world and rejects continuous/demo modes and explicitly conflicting environments. Use `--exercise fog_visibility --mode continuous` for the unchanged fog hour at normal speed.

## Build an iOS Simulator preview

Prerequisites: Unity 6000.2.2f1 with iOS Build Support and an editor license, full
Xcode and an installed Apple Silicon iOS Simulator runtime. The recorded host
used iOS 27.0; other runtime versions have not all been verified. The disposable
project omits Vuforia and local connection files. It does not use physical AR.

Run from the repository root with new work directories:

```sh
export UNITY_EDITOR='/path/to/Unity.app/Contents/MacOS/Unity'
python3 scripts/prepare_ios_simulator.py work/ios-project
export APRONLENS_IOS_OUTPUT="$PWD/work/ios-xcode"
"$UNITY_EDITOR" -batchmode -quit -projectPath "$PWD/work/ios-project" \
  -buildTarget iOS -executeMethod IosSimulatorBuild.Run \
  -logFile "$PWD/work/ios-export.log"
python3 scripts/patch_ios_simulator_lifecycle.py work/ios-xcode
xcodebuild -project work/ios-xcode/Unity-iPhone.xcodeproj \
  -scheme Unity-iPhone -configuration Debug -sdk iphonesimulator \
  -derivedDataPath work/ios-derived CODE_SIGNING_ALLOWED=NO \
  'OTHER_LDFLAGS=$(inherited) -framework UIKit'
xcrun simctl list devices available
```

Choose an available simulator and set its identifier locally. With the service ready:

```sh
export APRONLENS_DEVICE='YOUR_SIMULATOR_IDENTIFIER'
xcrun simctl boot "$APRONLENS_DEVICE"
xcrun simctl bootstatus "$APRONLENS_DEVICE" -b
xcrun simctl install "$APRONLENS_DEVICE" \
  work/ios-derived/Build/Products/Debug-iphonesimulator/ApronLensPreview.app
python3 scripts/configure_ios_assistant.py "$APRONLENS_DEVICE" --port 8767
xcrun simctl launch "$APRONLENS_DEVICE" edu.airfieldresearch.apronlens.simulator
```

Skip boot if already running. Missing Unity modules, simulator architecture or
Xcode runtimes must be fixed locally. A fork alone does not include those tools.

Record a fresh guided run using a new filename:

```sh
.venv-candidates/bin/python scripts/record_controller_demo.py \
  --device "$APRONLENS_DEVICE" --timeout 900 --output work/new-guided-demo.mp4
```

## Submission boundary

The owner supplied the assignment wording; see [requirement status](CHECKPOINT1_ASSIGNMENT_STATUS.md).
The video now contains Person 1’s supplied narration; Person 2’s narration, the
final review of the user-edited Coordination/Meetings content and physical-phone verification remain outstanding. No video duration was specified in the supplied
wording. No course submission or instructor approval is implied by this snapshot.

## Current publication records

- [Runway-case and native acceptance](../../outputs/checkpoint1/runway-acceptance.json).
- [AirfieldLens video edit and narration verification](../../outputs/checkpoint1/airfieldlens-demo-edit.json).
- [Approved opening-sentence edit](../../outputs/checkpoint1/airfieldlens-name-edit.json).
- [Mapped geometry and free-asset provenance](../../data/geography/README.md).

## Connected setting and next tasks

The setting now connects the Queen’s Terminal—Terminal 2—with Terminal 3 and their surrounding roads and buildings. Terminal 2B remains separate above ground, and the former Terminal 1 area is shown as a reference outline. Passing cars follow a mapped one-way road loop using the same scenario clock. The added water outlines preserve their islands. This is a sourced, simplified teaching environment; the traffic is authored, and visible movement does not create operational reports.

The connected update passed 245 backend tests, 127 Unity checks and a native simulator build. Across 4,000 sampled poses, the full road-vehicle envelope stayed on the rendered pavement. Landscape, portrait and Sources scrolling were inspected. A fresh rejected-takeoff source-hour run produced three real accepted answers (8.465–12.569 seconds); a separate 77.825-second cold request timed out and is retained. The label-only final build was inspected after that capture; it did not rerun model inference. See [connected-setting acceptance](../../outputs/checkpoint1/connected-setting-acceptance.json) and [video edit](../../outputs/checkpoint1/connected-setting-demo-edit.json).

The local [scenario register](TRAINING_SCENARIO_REGISTER.md) tracks 15 current coverage entries and twelve assigned work items (nine P-series items and three E-series topics), retaining the original proposal IDs for traceability. The [editable Google Doc](https://docs.google.com/document/d/1IxdtKDWxUWhK9r1QpWOi_MGtqnmmWsMd0sd-nme8ulk) tracks the same current scope. Fog presentation, its hour-long report-led demonstration and the separate fog practice lesson are included. The practice lesson is assigned to Checkpoint 1 and built, with bounded native acceptance recorded. Weather-driven queues are assigned to Checkpoint 2; airport-size/demand comparisons are assigned to Checkpoint 3.


Fog update and milestone decisions

The fog visual profile and separate report-led demonstration are complete for this increment. The native source-hour run displayed three accepted Qwen3.5-9B answers in 11.140, 12.472 and 11.749 seconds. It reached debrief in about 3:35 of wall time. The earlier fog edit starts the fog chapter at 24:12 and ends at 27:48; all earlier cue times and Person 1’s approved speech remain preserved. See outputs/checkpoint1/fog-acceptance.json and fog-demo-edit.json.

The milestone review was followed by an explicit implementation instruction. Checkpoint 1 now includes the fourth practice lesson, `fog_restrictions`; its 210-second practice world remains distinct from the completed source-hour fog demonstration. The lesson asks about LVP and safeguarding at 60 seconds, remaining safeguarding/hold after LVP cancellation at 120, and unconfirmed departure clearance after safeguarding cancellation at 180. TRN101 stays parked. The fog clears before the cancellation reports, and answers depend on received reports.

The restored v2 backend passed 276 tests and 19 focused checks. The 18 authored v2 development cases produced 14 usable reviews and four withheld failures; a second bounded revision was rejected and exact v2 restored. These are development results, not a grading benchmark. One complete native typed fog run reached debrief with three accepted reviews from four attempts, including a genuine quotation failure and successful edited retry. Native portrait/landscape input, hidden question context, scrolling, ordinary question entry, failure retention and retry were inspected. Targeted native checks for the original three lessons are recorded separately; they are not new full lesson runs. See [typed native evidence](../../outputs/checkpoint1/typed-native-acceptance.json), [independent development review](../../outputs/checkpoint1/typed-review-independent.json) and [correctness contract](../CORRECTNESS_CONTRACT.md).

The assignments are fixed: Checkpoint 2 develops weather-driven queues, the visual-evidence study and a distinct turnaround task. Checkpoint 3 compares airport size and traffic demand and evaluates the integrated experience, including devices, latency, reconnection, failures and learning flow. Acceptance gates remain necessary for completion. [MILESTONE_LEDGER.md](MILESTONE_LEDGER.md) records the decisions; the reusable review instructions preserve them across sessions.


The normal learner flow now asks for a short typed response at each checkpoint. The same local model reviews the response against the received reports and three explicit criteria, including unsupported extra assertions. It returns qualitative points and cited feedback, with the learner's exact words preserved. Failed, malformed or timed-out reviews keep the response available for retry. Automated checks establish format, identities, receipt eligibility and quotation fidelity, not the correctness of every model judgment. No numerical score or professional-competence result is claimed. The earlier fixed-choice mode remains an internal regression path.

The ledger also assigns three unbuilt topics within the existing future tasks: E01 one-engine emergency return with a successful landing in M2; E02 both-engine thrust loss/reduction on approach in M3; E03 reported wing/structural damage in M3 incident comparison. Existing fire, gear-collapse and loss-of-thrust illustrations do not implement these separate branches or a failure-physics model.


Typed-practice recording

The 30:33.5 edit preserves the approved Person 1 audio and earlier cue times. The earlier baseline is labelled because its narration describes fixed-choice checkpoints. The appended chapter shows current typed input, actual feedback, a withheld review, edited retry, an ordinary typed assistant question with Sources, and the debrief. It uses selected excerpts from the full 210-source-second fog practice run; it is not another one-hour scenario. Person 2 narration remains outstanding. See [typed edit provenance](../../outputs/checkpoint1/typed-demo-edit.json).

C01 is complete as a contract and evidence record, not a proof or a validated grader. C02/C03 are queued for M2 and C04 for M3. The Heathrow busy-airport refinement combines small illustrative queues, reported runway-use changes and local wind/visibility restrictions within Q01; it is researched and unbuilt.


Portability follow-up

The first GitHub run exposed a missing CI-only server dependency and a raw floating-point fingerprint difference on Linux. The repair changes only test dependencies and fingerprint serialization, keeping all production source hashes intact. A fresh environment passed 277 tests; an independent pre-change archive comparison covered all eight cases and twenty seeds. The source artifacts preserve the failed CI runs and local results; the pull request shows subsequent Linux outcomes. See [portability repair](../../outputs/checkpoint1/ci-portability-repair.json) and [independent review](../../outputs/checkpoint1/ci-portability-independent-review.json).


The current bounded fleet increment adds A320, B737, B787 and A380 family exteriors with nominal size references and authored landing gear, plus four independent bird-hold, rejected-takeoff, priority-landing and occupied-runway-go-around demonstrations. The external driver owns all movement and report timing. See [the fleet guide](../FLEET_DEMONSTRATION.md), [asset attribution](../../data/aircraft/amvlab/ATTRIBUTION.md) and [published 09R reference limits](../HEATHROW_PROCEDURE_REFERENCE.md). The final code passed 289 backend tests and native Editor/build checks. Four independent native runs reached their one-hour debriefs and displayed twelve nonempty, actual model answers; available-source references were checked. The first A380 run failed when question cues overlapped; it remains preserved alongside the spacing fix and successful full rerun. See [fleet acceptance](../../outputs/checkpoint1/fleet-native-acceptance.json) and [independent review](../../outputs/checkpoint1/fleet-independent-review.json). These are functional examples, not an accuracy benchmark. Portrait rebind checks and a positioned occupancy overview are separate supplemental inspections. No full SID, aircraft-system simulation or evaluated visual-reasoning claim follows from this increment.


## Current reliability corrections

The live training selector now rejects an identified-flight response with neither
facts nor missing-property statements. It allows one model retry using exactly the
same eligible reports, image and cutoff, then displays an explicit failure if still
empty. Both attempts are audited; this does not establish general semantic
completeness. The client and driver deadlines are unchanged. The frozen research
runner remains unchanged; live training uses a separate handler.

Aircraft labels use selected-flight priority, collision checks, bounded offsets
and leader lines in both orientations. Lower-priority labels can be hidden when
nearby space is exhausted, while aircraft selection remains available. See the
[correction evidence](../../outputs/checkpoint1/reliability-fix/acceptance.json).
The existing presentation and walkthrough videos are preserved.

The application remains scenario-based learning and review, not live operational
ATC monitoring. Typed responses receive qualitative feedback on report-supported
points, missing distinctions and unconfirmed conditions; they receive no numerical
grade. Monitoring the simulated situation and practising an explanation serve the
same learning objective. Real-world operational reliability and measured learning
benefit are not established by this milestone.

## Ordinary assistant reliability update

The [B04 reliability record](ASSISTANT_RELIABILITY.md) adopts ordinary-assistant v8
with a bounded flight-reference retry and model inference before startup readiness.
Known regression questions passed 24/24; both frozen v5 and v8 passed 24/24 newly
worded same-family probes. The typed candidate passed 15/18 and made three semantic
errors, so it was rejected and the published typed reviewer restored exactly.
The original 60-second typed server budget is retained. Native readiness answering
and original typed review were checked; this is not a new full lesson acceptance.
Old results and approved video remain unchanged. Typed semantic/quotation failures
and indefinite-worker/latency risks remain documented in #60/#61/#62.
