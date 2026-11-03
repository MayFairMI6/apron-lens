# AirfieldLens Checkpoint 1

The core application scope remains controller situational-awareness training,
three scored exercises, moving aircraft and a report-grounded assistant. Pilot
and turnaround implications appear in debrief. A dedicated turnaround task is
deferred to Checkpoint 2, alongside the planned visual-evidence research. No
separate pilot course is delivered. The separate video-memory project is deferred.

The project is now titled **AirfieldLens** (previously ApronLens). The owner
approved a voice-matched replacement of Person 1's opening sentence and updated
video branding. The original narration and earlier recordings remain archived.
Repository paths, bundle identifiers and frozen research records retain their
existing names for compatibility.

The presentation uses distinct scenarios, with time scaling within each case.
Routine operational disruptions anchor the scored lessons; wildlife, dropped
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
before the roll, matching the cited D-AEAD sequence. These cases add no scored
questions. A specific red-stop-bar conflict, operational weather, runway debris,
communication-error tasks and full recovery/reopening remain later work.

The four additional runway/emergency profiles passed 20 seeds each in the 241-test backend suite and 113 Unity checks. Each selected native run reached its one-hour debrief and displayed three actual accepted model responses, twelve across four runs. These are functional examples, not an accuracy benchmark. The first water capture is retained; its oversized close-view map label was corrected and that case was recorded again. See outputs/checkpoint1/runway-acceptance.json.

The [23:42 AirfieldLens recording](https://drive.google.com/file/d/1uHIweEFSlO4CRb8-VyNM7aZUd4mhsMhQ/view) includes the approved opening-name edit, current branding, mapped Terminal 3 and the four additional runway cases. Person 2’s narration remains to be recorded. [The two-person plan](TEAM_RECORDING_PLAN.txt) and [Person 2’s script](PERSON2_SCRIPT.txt) contain current cues. The original recordings remain archived.

The edit uses genuine source footage and model responses. Earlier incident chapters are targeted excerpts; each new runway/emergency profile completed an independent one-hour run. Branding overlays update only the name in earlier footage and the labelled saved debrief. They do not alter answers, scenario clocks or evidence.

Heathrow's AI-assisted digital-tower trials provide relevant motivation for the
next research stage. NATS describes testing, and Searidge describes camera-based
monitoring of aircraft and runway thresholds to assist people. AirfieldLens currently
answers from reports. Checkpoint 2 will test whether images add reliable evidence;
Checkpoint 3 will evaluate the integrated experience and failures. See the
[primary-source design notes](../HEATHROW_SCENARIO_BASIS.txt). Rain, snowfall and late-afternoon → dusk → night are implemented as visual conditions on the external source clock. Operational weather decisions, de-icing and visual-evidence evaluation remain Checkpoint 2 work; integrated condition testing belongs to Checkpoint 3. The current dusk profile is one source hour, not a full 24-hour solar cycle. See the [implementation docket](IMPLEMENTATION_DOCKET.md).

The learner-facing header is simply AIRFIELDLENS followed by the exercise title.
Controller situational awareness describes the learning objective in developer
and course documentation; it is not a role selector or a label in the header.

The current preview ran in the iOS Simulator on Apple Silicon. The fictional
Heathrow-informed environment includes an occupied stand, paved turns, a local
takeoff/landing circuit, wildlife, dropped baggage, ground contact and separate emergency examples. This recording does
not establish physical-device AR tracking, survey-grade Heathrow accuracy or
professional training competence.

AirfieldLens is positioned as portable scenario practice and review for learners, not an operational control workstation. The phone suits a focused flight/report/checkpoint task; a tablet or larger display is the recommended format for a broader traffic overview. This is a design recommendation, not a completed controller-usability finding. Checkpoint 3 should compare phone and larger-screen use with representative learners. See the [mobile-training source note](../HEATHROW_SCENARIO_BASIS.txt).

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
has three scored checkpoints and ends at 3:30 of source time. The extended
driver now includes eleven automatic questions, including four collision/landing
questions. The three scored lessons remain unchanged.

- [Collision and landing acceptance](../../outputs/checkpoint1/accident-acceptance.json):
  229 backend tests, 60 Unity checks, native build/install and two targeted landscape
  recordings with four actual accepted answers (10.203–17.736 seconds). An earlier
  cold-model request exceeded the app timeout; its failure is retained. These checks
  do not replace the earlier full-hour or three-lesson acceptance records.
- [Current video edit record](../../outputs/checkpoint1/scenario-demo-edit.json):
  source cuts, Person 1 audio identity, separate scenario cards and verification.

- [Weather acceptance](../../outputs/checkpoint1/weather-acceptance.json): 231 backend tests, 69 Unity checks, native build and rain/snow/dusk captures. Visual changes follow source time; they do not alter aircraft performance or create operational evidence. The private 30× capture profile suppresses question/teaching pauses and adds no new model-response acceptance claims.
- [Weather video edit](../../outputs/checkpoint1/weather-demo-edit.json): appended clips, source windows and preserved Person 1 audio.

The in-app “Allow 3–5 minutes” estimate has been removed, and the elapsed clock is labelled “Scenario”. Guided/full-hour profiles still span 3,600 source seconds; short scored practice still spans 210 source seconds with question/review pauses.

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

Add `--environment rain`, `--environment snow` or `--environment dusk` to the launch command; the default is clear daytime. The driver supplies the visual timeline and Unity renders it at the same source time as movement and reports.

The model loads before readiness on port 8767. Each host generates its own local
token in the ignored work directory. Use one training service at a time. For
scored practice, use `--mode lesson --exercise surface_conflict`; Next exercise
cycles through all three. Use `--mode continuous` for the hour at normal speed.

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
blank Coordination/Meetings sections and physical-phone verification remain outstanding. No video duration was specified in the supplied
wording. No course submission or instructor approval is implied by this snapshot.

## Current publication records

- [Runway-case and native acceptance](../../outputs/checkpoint1/runway-acceptance.json).
- [AirfieldLens video edit and narration verification](../../outputs/checkpoint1/airfieldlens-demo-edit.json).
- [Approved opening-sentence edit](../../outputs/checkpoint1/airfieldlens-name-edit.json).
- [Mapped geometry and free-asset provenance](../../data/geography/README.md).
