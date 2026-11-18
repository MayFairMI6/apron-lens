# Checkpoint 2 continuation note

**Read the last update at the end of this file first.** Earlier sections are kept as history.

Updated 16 November 2026. Branch `codex/airfieldlens-checkpoint2`, base commit
2fe7ef5. Nothing from this session is committed or pushed. Evidence and limits
are in ledger entry ML-054; the full remaining plan is in
[EXECUTION_QUEUE.md](EXECUTION_QUEUE.md).

## Done and verified this session

- Replay backend: `backend/replay_session.py`, `backend/replay.py`,
  `tests/test_replay_session.py` (24 tests).
- Handoff retry for invented unknown names: `backend/training_adapter.py`
  (policy v6), `tests/test_training_completeness.py`.
- Genuine 9B handoff development runs:
  `experiments/bluebird_handoff/handoff_answers.py`, results in
  `outputs/bluebird-handoff/handoff-answers-v5-run1.jsonl` (6/8) and
  `handoff-answers-v6-run1.jsonl` (7/8).
- Preview for approval:
  `outputs/checkpoint2-run/controller-replay-preview/` (HTML source and PNG).
- Docs: safety motivation and status in `EXECUTION_QUEUE.md`; ML-054 in the ledger.

## Commands

```sh
.venv-candidates/bin/python -m unittest discover -s tests          # 695 pass
.venv-candidates/bin/python -m unittest tests.test_replay_session  # 24 pass
.venv-candidates/bin/python -m experiments.bluebird_handoff.handoff_answers work/checkpoint2-native/handoff-answers-v6-run2.jsonl
.venv-candidates/bin/python -m backend.replay --exercise fleet_a380_go_around   # port 8768, loads the 9B
```

Logs: `work/replay-handoff-full-suite.log`,
`work/checkpoint2-native/handoff-answers-v{5,6}-run1.log`.

## Failed or open checks

- `gap-negative-authorisation` fails in both model runs (no unreported property named).
- Replay has no Simulator run and no genuine-model run over HTTP.
- Camera observations do not reach the assistant prompt.

## Running processes

None started by this session remain. `ollama serve` was already running and idle.

## First unfinished action as of 16 November (done; the current one is in the last update below)

Get the owner's decision on the preview image. On approval, build the
controller workspace in Unity against `/replay`, `/replay/action`,
`/replay/question` and `/traffic` on port 8768 (start from `TrainingView.cs`
and `WorldArBootstrap.cs`, which have uncommitted edits to preserve), then run
the A380 and 787 journeys in the iPhone 18 Pro Simulator in both orientations.

## Next, in order, where approval is not needed

1. Genuine answers for cues 2 and 3 of the eight new driver cases (extend
   `experiments/checkpoint2_scenarios/run.py`; new output file each run).
2. Build the unbuilt variants: protected-boundary/stop-bar evidence,
   callsign/readback and conflicting-stand corrections, disabled-aircraft
   towing, vacancy, inspection and reopening.
3. Stand B checks: tanker footprint at 92 and 95 s, release at 150 s, TRN103
   movement at 158 s; native and orientation checks recorded separately.
4. Detector: revise on development data, freeze a fresh held-out split, then
   evaluate. Keep the zero-detection pilot and the unqualified development fit.
5. Freeze the Checkpoint 2 scenarios, labels, splits and scoring before the
   three-arm evaluation (reports; plus RGB detections; plus simulated depth).
6. C02 model-to-typed-claims integration; C03 trace comparison.
7. B06: twelve contrasts stay sealed; a new candidate needs an eligible
   exposed result first.
8. Checkpoint 2 deliverables (Simulator build, A380-first narrated demo,
   one-page reflection in Downloads, GitHub links), then Checkpoint 3.

## Update, end of 16 November 2026

See ledger ML-055 and its two addenda. Nothing is committed or pushed.

- Controller replay screens are built (`TrainingView.Replay.cs` plus gated
  hooks) and were approved from the preview.
- Current app build: `work/checkpoint2-native/derived-replay` (fourth build),
  installed on the iPhone 18 Pro Simulator (15E94EB0-7558-4181-91B0-6716D718F19B).
- A380 and 787 journeys both ran in that Simulator with real taps and real
  Qwen3.5-9B answers. Exactly what was and was not checked on which build is
  tabulated in ML-055.
- No service or model process is running.

To run it again:

```sh
.venv-candidates/bin/python -m backend.replay --exercise fleet_a380_go_around --port 8767   # or fleet_b787_bluebird_handoff; wait for REPLAY_READY
python3 scripts/configure_ios_assistant.py --port 8767 15E94EB0-7558-4181-91B0-6716D718F19B
xcrun simctl launch 15E94EB0-7558-4181-91B0-6716D718F19B edu.airfieldresearch.apronlens.simulator
```

To rebuild after a script change, use the Unity at `work/unity-editor`
(the Hub install lacks the Android module and fails to compile), sync
`Assets/SurfaceSafety/Scripts` into `work/checkpoint2-native/project-visual`,
then export, patch and `xcodebuild` as in `docs/UNITY_SETUP.md`.

Update 17 November 2026 (ledger ML-056): the open replay checks, the remaining
driver questions (24/25 accepted) and the Stand B model-free timing checks are
done. [SCENARIO_DRIVER_GUIDE.md](../SCENARIO_DRIVER_GUIDE.md) explains how to
replicate any scenario. `python -m backend.replay --no-model` runs the replay
without loading the assistant.

First unfinished action (owner chose this on 17 November 2026, decision log
#25): the visual evidence workstream. Start from `experiments/apron_detector/`
and the P01 capture scripts; revise the detector on development data only,
then freeze a fresh held-out split before evaluating it, then feed qualified
detections into the replay as camera reports for the reports / +RGB / +depth
comparison. The issue #39 variants are queued after it. The unknown-name
question is settled (decision log #17 to #20).

Update 17 November 2026, later (ledger ML-058 addenda 1–3, decision log #31–#56):
detector v3 qualified as camera evidence for synthetic Stand B frames; a
recorded Stand B camera session loads into the replay with one arm
(`--camera-session outputs/checkpoint2-run/stand-b-session-observations.json
--camera-arm rgb|rgb_depth`), and the app shows a "latest camera observation"
card for TRN103.

First unfinished action: draft the reports / +RGB / +depth comparison protocol
for owner review (prompt wording for camera observations, question families,
scoring, and a brief for a fresh agent to draft held-out cases). The owner asked
that this start only after the session is switched to high effort (decision
log #52). Nothing is frozen yet.

Update 17 November 2026, latest: the comparison protocol is drafted
(`docs/course/CAMERA_EVIDENCE_COMPARISON.md`, with the author brief
`docs/course/M2_HELDOUT_AUTHORING_BRIEF.md`). First unfinished action: the
owner settles D1–D7 in that document; then build on development data only,
freeze 2, and only then hand the brief to a fresh agent.

## Local continuation after the Claude cloud handoff

See ML-060 for research and submission placement. The current app work stays
on `codex/airfieldlens-checkpoint2`. The research-only port remains on PR #75.

The current iPhone Simulator acceptance path uses the approved controller
replay at `fe82fdf`. The submission walkthrough uses three native recordings:
A380, 787 Bluebird, and Stand B. The replay service advanced the cutoffs
during capture, and earlier native taps and real Qwen answers have separate
receipts. The submission folder is `~/Downloads/AirfieldLens Checkpoint 2`.

Android phone support starts with the existing approved controller Board.
`IosSimulatorBuild.AndroidBoard` builds that scene as an Android development
APK from a disposable replay project. Use the embedded Unity Android SDK,
configure the installed debug app with
`python3 scripts/configure_android_replay.py <adb-serial> --port 8767`, and
start the local replay service. This uses a private app file and ADB reverse.
The live-camera interaction and Board/camera transition need their own
preview and Android acceptance work.

M2 camera development runs resume from `work/m2-camera/handoff-20261117/`.
The deterministic baseline ran 15 turns in all five evidence forms, with
14 correct and 9/9 authority checks in each. Camera citing was 7/7 in the four
camera forms. This is the existing development set. Preserve the raw records.
The 9B runs use a separate set of files in the same work directory. Before
freezing, settle the remaining protocol decisions, collect the blind-judge
calibration, and use a fresh author for the sealed held-out families.
