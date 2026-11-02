# ApronLens Checkpoint 1

The application scope is frozen: controller situational-awareness training,
three scored exercises, moving aircraft and a report-grounded assistant. Pilot
and turnaround implications appear in debrief. A dedicated turnaround task is
deferred to Checkpoint 2, alongside the planned visual-evidence research. No
separate pilot course is delivered. The separate video-memory project is deferred.

The current preview ran in the iOS Simulator on Apple Silicon. The fictional
Heathrow-informed environment includes an occupied stand, paved turns, a local
takeoff/landing circuit, wildlife and a separate stand fire. This recording does
not establish physical-device AR tracking, accurate Heathrow geometry or
professional training competence.

## Evidence and presentation

- [Presenter guide](CHECKPOINT1_PRESENTER_GUIDE.txt): narration, video-player cues,
  short presentation route and likely questions. Suggested durations are not a
  verified assignment limit.
- [Saved demo acceptance](../../outputs/checkpoint1/heathrow-acceptance.json):
  the source-hour run, six actual model responses, original failures and source
  hashes. This is the original pre-publication record, not a new run per commit.
- [Three-lesson acceptance](../../outputs/checkpoint1/lesson-acceptance.json):
  the initial simulator lesson completions and failures retained for context.
- [Frozen M1 report](../../outputs/m1_ar_context/REPORT.md): 40 distinct held-out
  turns, 17 families, four scenarios, two local Qwen models and a deterministic
  baseline in three conditions; images off. Qwen3.5-9B scored 24/40 in full AR.
- [Training driver](../TRAINING_DRIVER.md) and [scenario sources](../HEATHROW_SCENARIO_BASIS.txt).

The assistant uses Qwen3.5-9B to select eligible report facts, checked by a
deterministic validator and rendered as a report summary. Images are sent in
the demo, but its answers do not establish visual recognition. Sources expands
reports behind an answer at its cutoff; Recent reports can include later arrivals.
Six accepted demo answers are not a model benchmark.

The saved 8:27 recording is an unscored guided demonstration with five automatic
questions and one manual post-containment question. The short learner profile
has three scored checkpoints and ends at 3:30 of source time.

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

The exact Checkpoint 1 rubric, recording limit, upload format and required team
reflection fields have not yet been matched against the assignment page.
No course submission or instructor approval is implied by this source snapshot.
