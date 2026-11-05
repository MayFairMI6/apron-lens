# Typed reviewer: native end-to-end acceptance plan (ML-052)

Status: PREPARATION ONLY, written 3 November 2026. Nothing below the "Preparation findings" section has been executed. No native acceptance has happened, no model owner was started by this preparation, and nothing here implies that the new typed reviewer is semantically accepted. Backend-only tests do not establish native acceptance.

Scope reminder: iOS Simulator only. No physical-phone or TestFlight claim.

## 1. Path map (read from source, not run)

Learner path, left to right:

1. Unity simulator player. `IosSimulatorBuild.Run` (unity/SurfaceSafetyCoach/Assets/SurfaceSafety/Editor/IosSimulatorBuild.cs) builds a scene whose `WorldArBootstrap` has `autonomousTraffic=true`, which adds `ExternalTrafficDriver` (bound to `ConversationClient`).
2. `ExternalTrafficDriver.Poll` GETs `/traffic` once a second. When the snapshot has `training.runId` it adds `TrainingView` and calls `TrainingView.Apply(state)`. Apply ignores a lower revision of the same run, keeps the typed draft per `runId|checkpointId`, and clears busy flags on a new run or non-checkpoint phase.
3. Connection config: `ConversationClient.LoadConnection` (under `APRONLENS_SIMULATOR`) reads `Documents/assistant-connection.json` in the app container, written by `scripts/configure_ios_assistant.py DEVICE --port 8767` from `work/qwen-server-token.txt` (exists, 43 bytes, mode 600). The token is never bundled.
4. Typed submit: `TrainingView.ReviewResponse` (button "Review my answer") builds `TrainingResponse{actionId=new GUID, runId, revision, checkpointId, responseText=draft}` and `ResponseRequest` POSTs it through `ConversationClient.TrainingResponseRequest` to `POST /training/response` (client timeout 90 s). The coroutine tries twice with the SAME body (same actionId, so the retry is idempotent). A 409 shows "This checkpoint has changed..."; any other 4xx (including the 429 busy/not-ready reply) shows "Your answer could not be reviewed. Please try again."; a network or 5xx failure shows "The review did not arrive. Your answer is kept here...". The draft stays in the input field. A later tap makes a NEW actionId.
5. Server, `backend/training.py` `training_app` (port 8767):
   - A middleware (`gate_questions`) authenticates, caps the body at 16 KiB including chunked input, and stores it.
   - `response()` calls `driver.prepare_response`. A busy lock or a non-ready owner returns the cached duplicate if one exists, otherwise HTTP 429 `ReviewBusy` with no state change. Otherwise it acquires `app.state.busy`.
   - `TrainingSession.prepare_response` (backend/training_session.py) validates keys, runId (stale attempt gives 409), duplicate actionId plus identical fingerprint (returns cached state, no model call), a different body under the same actionId (409), phase or revision change (409), checkpointId mismatch (409), already pending (409). It freezes the receipt-bounded reports, builds the rubric (`rubric_for`), saves `response_text`, sets `review_status='pending'`, bumps the revision and returns a `ReviewContext`.
   - `perform_review` runs `generate_review` on the ordinary Qwen owner by default. When a `typed_review_service` is passed it runs `backend.typed_review_service.generate_semantic_review` on that owner instead. The task is shielded, so it holds the busy lock until the worker actually returns, even after an HTTP timeout or client disconnect.
   - `response()` waits at most 60 s (`review_timeout_seconds`). On timeout it applies "The review took too long..." (status `failed`, response saved) while the worker may still be running (`typed_review_timeout` audit event).
   - `driver.finish_response` applies only the still-current immutable context (same run, revision, phase, action, checkpoint). A stale or late result is discarded and logged (`typed_response_discarded`). On success it re-validates the review and stores `feedback` with `reports` limited to the reports cited by the review points.
6. Typed review service (inactive scaffold): `backend/typed_review_service.py` `IsolatedReviewService` (subclass of `IsolatedTrainingAdapter`, backend/training_worker.py) runs a killable child process. The child runs `factory()`, `load()`, `warmup()`, then loops on `review(request)`. `generate_semantic_review` builds `ReviewRequest('typed-'+runId+'-'+actionId, fingerprint, payload)`, validates the `ReviewOutcome` (identity, model id and revision, policy version, finite timing, review contract), and appends a `typed_review_classification` record to the review audit file. A failure returns `(None, error)`; there is no fallback to the old reviewer.
   - The child factory is `backend/typed_classifier_adapter.py` `TypedClassifierAdapter`. `load()` does `from backend import typed_review_policy` (deliberately no experiments fallback) and builds `modelaccess/nli.py` `PairClassifier(device='mps')` (DeBERTa-v3-large, revision b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7, local files only). `review()` calls `policy.evaluate(payload, engine, started+55)`.
7. State back to the app: `GET /traffic` and `GET /training` carry `training` state: `phase`, `revision`, `checkpoint.question`, `reviewStatus` (`idle`/`pending`/`failed`), `reviewError`, `responseText`, `feedback`, `reviews`. With a typed service attached `state['typedReviewStatus']` is also present. `TrainingView` shows "Reviewing your answer against the checkpoint reports..." while pending, shows `reviewError` when failed, and on success shows a "Feedback on your answer" card.
8. Feedback rendering, `TrainingView.FeedbackText` (kind `typed`): question, "Your answer", "PRACTICE FEEDBACK" explanation, then per point a label (Supported point, Missing point, Recheck this point, Needs clarification), the comment, `Your words: "<learnerQuote>"` and `Reports: <ids>`. After the points it lists "REPORTS AVAILABLE AT <cutoff> s" followed by the cited report texts (message, source, received time, ID). The debrief repeats this text for every review.
   - Note for the reviewer: the typed feedback has no collapse or expand control in this card; it is a scrolling text card and the report list is the cited reports only. The "Sources" and "Recent reports" toggles belong to the ordinary assistant panel (`BuildAssistant`/`RefreshAnswer`). The handoff phrase "expandable sources" should be checked against what is actually on screen and recorded accurately.
9. Ordinary assistant path (must stay unchanged): `POST /conversation` goes through the middleware in `training.py` (blocked while `phase` is not practice/debrief, 503 while an attached typed owner or ordinary owner is not ready and the lock is free), then the existing Qwen adapter.

### How the typed service would be selected

Currently it is NOT selectable from the command line. `training.py main()` builds only `IsolatedTrainingAdapter(partial(TrainingAdapter, 'qwen3.5-9b', ...))` and calls `training_app(adapter, settings, driver)` without `typed_review_service`. The only constructor pattern in the repo is the unit test:

    IsolatedReviewService(factory, served_model, model_revision=..., policy_version=..., audit_path=..., generation_timeout=..., startup_timeout=..., cleanup_timeout=...)

Activation therefore needs (coordinator/implementation owner, not done here): (a) `backend/typed_review_policy.py` exposing `VERSION` and `evaluate(payload, engine, deadline)`; (b) a deliberate wiring in `main()` (for example a flag) that passes `IsolatedReviewService(TypedClassifierAdapter, MODEL_ID, model_revision=MODEL_REVISION, policy_version=policy.VERSION, audit_path=ROOT/'work/training-typed-worker.jsonl')` as `typed_review_service`. Open parameter question: the worker's default `generation_timeout` is 55 s and the policy deadline is also 55 s, with the HTTP wait at 60 s; check that the overall budget is consistent when wiring.

## 2. Preparation findings (what was and was not checked)

Checked, no model owner started:

- No Unity editor process was running (`ps aux`), and no UnityLockfile exists under unity/SurfaceSafetyCoach/Temp. No python or backend.training process was visible at that moment.
- Xcode 27.1 (build 27A9275); iOS Simulator SDK 27.1 available; runtimes iOS 27.0 and 27.1.
- Simulators (all Shutdown): iPhone 18 Pro, iPhone 18 Pro Max, iPhone 17e, iPhone Air, iPhone 17, several iPad models (iOS 27.0), plus "AR Demo iPhone" D5BC2DAD-32E3-4154-86DD-F58D7491D447 and "iPhone Duo" 2EC221E5-D745-4512-B975-F1FD9CE90B96 (iOS 27.1). Which device the earlier acceptance used is not recorded in what I read; I recommend an iOS 27.1 device and recording the choice.
- The app `edu.airfieldresearch.apronlens.simulator` is NOT installed in any simulator (`simctl get_app_container` fails for all).
- There is no existing simulator build: no work/ios-project, work/ios-xcode, work/ios-derived. Earlier evidence exists only as outputs (for example outputs/checkpoint1/native-ios-rerun.json, typed-fog-*.png), not as a reusable app.
- Unity 6000.2.2f1 at /Applications/Unity/Hub/Editor/6000.2.2f1 has NO iOS playback engine (PlaybackEngines contains only WebGLSupport; modules.json lists `ios` as not selected). The project-local copy `work/unity-editor/Unity.app` DOES contain PlaybackEngines/iOSSupport (and AndroidPlayer). Use `UNITY_EDITOR=$PWD/work/unity-editor/Unity.app/Contents/MacOS/Unity`. Whether that editor is licensed and starts in batch mode was NOT tested.
- `tests.test_typed_review_service` ran: 7 tests OK (fake worker only, no model). This is not native evidence.
- The classifier weights are cached (HF cache has the pinned DeBERTa revision snapshot b3546ea...), and models/qwen3.5-9b exists. Not loaded.
- Disk: 171 GiB free.
- I generated the four lessons offline (seed 17, no model) to read the checkpoint questions and reports used in Section 4.

Blockers or open items found:

1. `backend/typed_review_policy.py` does not exist (confirmed). The adapter will fail load and the service will report failed. Semantic gates not passed per the handoff.
2. `training.py main()` has no wiring for the typed service (above). Native acceptance cannot start the typed path until this exists.
3. No app build exists. A first build requires a cold Unity import of a copied project plus IL2CPP and xcodebuild. I deliberately did NOT start it: it is CPU-heavy and could disturb the timing of another agent's MPS evaluations. Run it when the coordinator says the evaluation host is idle (or accept the risk). The build needs no model.
4. Unity batch run against the disposable copy is safe even if the source project is open, but still check `ps aux | grep -i unity` first as instructed.
5. Two heavy MPS owners (Qwen3.5-9B plus DeBERTa-large) in one service: memory pressure and startup time are unmeasured. `startup_timeout` defaults to 300 s per owner.
6. The 429 reply from `/training/response` appears in the app as the generic "could not be reviewed" text; the specific "Feedback is not available yet" message does not reach the learner. Record this as observed behavior, not as a defect, unless the coordinator decides otherwise.

## 3. Commands (to run later; not run)

All from the repository root `/Users/mayfairmi6/Documents/Codex/2026-10-12/the-final-project-is-to-create`. Pick a fresh `RUN=outputs/typed-native-acceptance-<YYYYMMDD-HHMM>` and `mkdir -p $RUN/screens $RUN/logs` first. Never overwrite existing outputs.

### 3a. Pre-flight (no models)

    ps aux | grep -i -E "unity|backend\.training|uvicorn|run_relation|python" | grep -v grep
    lsof -nP -iTCP:8767 -sTCP:LISTEN
    git status --short; git rev-parse HEAD
    shasum -a 256 backend/typed_review_policy.py backend/typed_review_service.py backend/typed_classifier_adapter.py modelaccess/nli.py backend/training.py backend/training_session.py > $RUN/source-hashes.txt
    shasum -a 256 /Users/mayfairmi6/Downloads/AirfieldLens-Checkpoint-1-Presentation.mp4   # must equal 5d7a20600a32c9211ef16ab9fcb5dd891366b4badb4c7f0888af728f62af3af1

Proceed only when no other GPU model owner is running and nothing listens on 8767.

### 3b. Build and install the simulator app (no model needed)

    export UNITY_EDITOR="$PWD/work/unity-editor/Unity.app/Contents/MacOS/Unity"
    python3 scripts/prepare_ios_simulator.py "$PWD/work/ios-project-typed-<date>"          # destination must not exist
    export APRONLENS_IOS_OUTPUT="$PWD/work/ios-xcode-typed-<date>"
    "$UNITY_EDITOR" -batchmode -quit -projectPath "$PWD/work/ios-project-typed-<date>" \
      -buildTarget iOS -executeMethod IosSimulatorBuild.Run -logFile "$RUN/logs/unity-ios-export.log"
    grep IOS_SIMULATOR_EXPORT_PASS "$RUN/logs/unity-ios-export.log"
    python3 scripts/patch_ios_simulator_lifecycle.py "$APRONLENS_IOS_OUTPUT"
    export APRONLENS_DEVICE=D5BC2DAD-32E3-4154-86DD-F58D7491D447     # AR Demo iPhone, iOS 27.1 (recorded choice)
    xcodebuild -project "$APRONLENS_IOS_OUTPUT/Unity-iPhone.xcodeproj" -scheme Unity-iPhone \
      -configuration Debug -sdk iphonesimulator -destination "platform=iOS Simulator,id=$APRONLENS_DEVICE" \
      -derivedDataPath "$PWD/work/ios-derived-typed-<date>" CODE_SIGNING_ALLOWED=NO \
      'OTHER_LDFLAGS=$(inherited) -framework UIKit' 2>&1 | tee "$RUN/logs/xcodebuild.log"
    xcrun simctl boot "$APRONLENS_DEVICE"; xcrun simctl bootstatus "$APRONLENS_DEVICE" -b
    xcrun simctl install "$APRONLENS_DEVICE" "$PWD/work/ios-derived-typed-<date>/Build/Products/Debug-iphonesimulator/ApronLensPreview.app"
    # Record the .app name actually produced; the docs say ApronLensPreview.app but this was not rebuilt here.

The Unity source files must be the ones in the checkout at acceptance time (hash the copied `Assets/SurfaceSafety` tree into `$RUN`). The patch script and docs specify the flow; I did not run any of these steps.

### 3c. Start the service with the typed reviewer (after promotion and wiring)

Exact flag name depends on the coordinator's wiring; placeholder below. Start ONE service on 8767, in a terminal whose output is teed.

    .venv-candidates/bin/python -m backend.training --exercise surface_conflict --mode lesson --seed 17 \
      <TYPED_REVIEWER_ACTIVATION_FLAG_TBD> 2>&1 | tee "$RUN/logs/service-surface_conflict.log"

Wait for `TRAINING_READY inference warmup complete` (printed after both owners warm up) before provisioning the app. Then, with the token:

    TOKEN=$(cat work/qwen-server-token.txt)
    curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8767/training | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('phase'),d.get('assessmentMode'),d.get('typedReviewStatus'))"
    python3 scripts/configure_ios_assistant.py "$APRONLENS_DEVICE" --port 8767
    xcrun simctl launch "$APRONLENS_DEVICE" edu.airfieldresearch.apronlens.simulator

Do not print the token. Expect `typedReviewStatus` = `ready`; if it is missing the typed service is not attached; stop and report.

Other lessons for the cases below: `late_arrival`, `late_baggage`, `fog_restrictions` (lesson mode only; omit `--environment` for fog). Stop the service completely between profiles (Section 5), then start the next.

## 4. Native test cases

Operate the simulator through the live panel and `mcp__Claude_Code_iOS_Simulator__control` (tap, text, screenshot); screenshots also with `xcrun simctl io $APRONLENS_DEVICE screenshot PATH`. For every case: screenshot before submit, screenshot of pending, screenshot of final state; record action time, the app's displayed text, and the matching jsonl records. Use the real checkpoint question displayed in the app. The sample answers below are DRAFTS keyed to the seed-17 reports I read offline; the independent semantic reviewer should confirm or replace them, and the expected outcome is a hypothesis to compare against what the app shows, not a claim.

Reports read offline (seed 17, receipt time s):

- surface_conflict, target TRN102: L010 (27.6) "TRN102 is held because a service vehicle is obstructing its ground route."; L011 (104.0) "The vehicle is clear. The exercise ground hold for TRN102 is released."; L006 route within apron, no runway or takeoff clearance represented. Checkpoint questions: check-1 "Which flight is held, and what reported obstruction explains the hold?"; check-2 "What happened to TRN102's ground hold, and which reported change explains it?"; check-3 "What permission is still unconfirmed, and how does it differ from the reported ground-hold release?"
- late_arrival, target TRN103: check-1 "Which inbound flight is waiting, and which stand and occupying aircraft explain the hold?" (L010: TRN103 waits, Stand B occupied by TRN102).
- late_baggage, target TRN102: check-2 "What is the latest target off-block estimate, and does that estimate establish departure clearance?" (L015 supersedes 10:20 with 10:35 per the probe; read the live reports to confirm).
- fog_restrictions, target TRN101: three checkpoints at 60, 120, 180 s.

### Case matrix

| # | Case | Lesson and checkpoint | Draft learner answer | Expected for acceptance |
|---|------|-----------------------|----------------------|-------------------------|
| 1 | Correct new answer | surface_conflict check-1 | "TRN102 is held because a service vehicle is obstructing its ground route." | Verdict supportive; both content points met; grounding met; quote is an exact literal excerpt of the typed text; cited report is L010. |
| 2 | Omitted point | surface_conflict check-1 | "TRN102 is held." (no obstruction) | Obstruction point missing; flight point met; no false credit. |
| 3 | Correct core plus unsupported same-sentence extra | surface_conflict check-1 | "TRN102 is held because a service vehicle is obstructing its route, and takeoff has been cleared." | Core met; grounding point flags the unsupported clearance (not met/contradicted); no overall full credit. |
| 4 | Wrong-flight attribution | surface_conflict check-1 | "TRN101 is held because a service vehicle is obstructing its ground route." | Flight point not met; no credit for another flight's fact; grounding flags attribution. |
| 5 | Explicit unknown permission | surface_conflict check-3 | "Takeoff clearance is still unconfirmed; the reports only show the ground hold was released." | Permission unknown credited; difference from ground release credited; no invented clearance. Do case 5 at check-3 after cases 1 to 4 finish (see ordering note). |
| 6 | Saved input and retry | any checkpoint | Type an answer, trigger a recoverable failure (Section 6), tap again | Draft stays in the field and in `responseText`; failure text shown; retry makes a new actionId and yields exactly one applied review. |
| 7 | Stale checkpoint | any | Submit, then (via `curl` with the token) send the same body with an old revision, or let the checkpoint advance and replay | 409; state unchanged; app shows "This checkpoint has changed..." only for the app-originated case. |
| 8 | Timeout, hang, crash recovery and retry idempotence | any | Section 6 | See Section 6. |
| 9 | Shutdown of both owners | n/a | Section 5 | No leftover child processes on exit. |
| 10 | Ordinary assistant unaffected | practice phase and debrief | Ask "Latest update" and the Readiness question, with Sources and Recent reports | Same accepted-answer behavior and UI as before; blocked during checkpoints; no typed-owner involvement in `training-conversations.jsonl`. |

Ordering note: a checkpoint advances after a review is accepted and the learner taps Continue; Try again or a new run restarts the lesson with a fresh run id. A single lesson run gives only three checkpoints, so cases 1 to 5 need several runs or the "Try again" restart in the debrief. Plan: run 1 = cases 1 and 5 on checkpoints 1 and 3 (case 3 wording differs on check-2 wording as needed); use debrief "Try again" or restart the service to repeat for cases 2 to 4. Record the run id for each case. Do not tune the draft answers after seeing the result; add new rows for new variations.

Additional lessons: run at least one answer through each of late_arrival, late_baggage and fog_restrictions (one correct answer each, and one fog case with an unsupported extra), to cover different rubrics and the fog bug-prone restrictions wording. Include one portrait and one landscape screenshot of the feedback card (the layout code branches on orientation; use `rotate`).

For each submit, verify against the screen and the audit file:

- feedback schema and wording unchanged: label names, "Your words" quote, "Reports:" ids, "REPORTS AVAILABLE AT <cutoff> s";
- every displayed quote appears literally in what was typed (a character-for-character check against the saved `responseText`);
- every displayed report ID is at or before the checkpoint cutoff and belongs to the target or an allowed comparison flight;
- the learner's own response is preserved, then displayed in "Your answer";
- exactly one `typed_review_completion` event per actionId with `stateApplied=true`, and a matching `typed_review_classification` record with `contractAccepted=true`.

## 5. Shutdown checks (both owners)

After each profile, press Ctrl-C in the service terminal (or SIGTERM to the `python -m backend.training` PID) and then:

    sleep 5; ps aux | grep -E "backend\.training|multiprocessing|TypedClassifierAdapter|python" | grep -v grep
    lsof -nP -iTCP:8767 -sTCP:LISTEN
    tail -20 work/training-worker.jsonl; ls -t work/*typed*worker*.jsonl | head -1 | xargs tail -20

Pass condition: no remaining child processes for either the Qwen owner or the typed owner; port 8767 free; worker audit shows closing events for both. Also verify one abnormal shutdown: send SIGTERM during an in-flight review and confirm no orphaned child remains (this may leave the saved response unreviewed, which is expected).

## 6. Fault-injection cases (timeout, hang, crash)

These must exercise the real separate typed owner. Do NOT edit source files for injection (this plan owns no code). Options, in order of preference; choose and record what is possible once the wiring exists:

1. Crash: find the typed child PID (from the typed worker audit file or `ps` children of the service) and `kill -9` it while a review is pending. Expected: HTTP completes with the "could not be reviewed reliably... saved" failure state, owner status moves to `recovering` then `ready` after a reload and warmup, busy lock retained until the old call is stopped, response text preserved, next submit (new actionId) completes normally, and the same-actionId re-POST of the failed request returns the cached state and does not schedule a second inference.
2. Hang: `kill -STOP` the typed child during a review, wait past the 55 s owner budget and the 60 s HTTP wait, then confirm: failure message; busy lock held until the stuck call is terminated; no overlapping MPS inference; subsequent `/training/response` returns 429 while recovering; after the owner is `ready` the retry succeeds. Then `kill -CONT` is unnecessary because the owner terminates the child; confirm no zombie.
3. Timeout with late result: only possible if a deliberately slow input can be supplied; do not invent one. If it cannot be produced without code changes, report it as not exercised.

For each: capture the three screenshots, `GET /training` before and after, the audit lines (`typed_review_timeout`, `typed_review_completion`, `typed_response_discarded` if any), owner status transitions, and the elapsed times. Also include a duplicate POST of the identical body with `curl` after success (should return the cached state with no new classification record), and a body with the same actionId but different text (expect 409). These curl probes are supplementary evidence; the primary evidence is in-app.

Expected app text when checks fail: failed state text from `reviewError` (for example "Your answer could not be reviewed reliably. It is saved; please try again."). Record what is actually shown.

## 7. Evidence to capture

Under `$RUN` (a new `outputs/typed-native-acceptance-<date>/` directory; do not modify existing outputs):

- `screens/<case>-<step>.png` for each step, plus portrait and landscape captures;
- `logs/service-*.log`, `logs/unity-ios-export.log`, `logs/xcodebuild.log`;
- copies (not moves) of the run's slice of `work/training-sessions.jsonl`, `work/training-assessments.jsonl` (typed classification and completion records are written here by default), `work/training-worker.jsonl`, the typed worker audit file, `work/training-conversations.jsonl` and `work/training-prompts.jsonl` for the ordinary assistant, each with line ranges and SHA256;
- `source-hashes.txt`, simulator device id and runtime, Xcode version, model/revision/policy version from the warmup record, and exact commands;
- a results table (case, run id, action id, displayed outcome, pass/fail, reason). Record failures honestly and keep every raw artifact.

## 8. Pass criteria (from the handoff; no weakening)

Native acceptance passes only if cases 1 to 10 are exercised in the real simulator app with real owner(s) and: schema unchanged; literal bounded quotes; relevant source display; user response preserved; exactly one state application per review; failure and recovery behave as above; shutdown clean; ordinary assistant intact. A mock policy check or a ready log does not substitute. Any case that cannot be run must be listed as not run, not counted as passed.

## 9. Not claimed

This document does not claim that any step was executed other than the read-only checks in Section 2, that the app builds, that the Unity editor in `work/unity-editor` is licensed, that the typed reviewer is accepted, or that physical-device behavior is validated.


## Codex environment reconciliation — 3 November 2026

The earlier “no app build exists” finding was limited to the repository work directory. An existing build is present at `/Users/mayfairmi6/Documents/Codex/2026-11-01/is-there-a-voice-api-model/work/ios-derived/Build/Products/Debug-iphonesimulator/ApronLensPreview.app`, with adjacent `ios-project` and `ios-xcode` directories. `xcrun simctl list devices available -j` confirms the prior iPhone18Pro/iOS27 device `15E94EB0-7558-4181-91B0-6716D718F19B` is available and shutdown. This verifies file/device availability only, not current source equivalence, installation, launch, or R11 multi-quote acceptance. Inspect source/build identity before reuse and rebuild if required by promoted UI changes. No model or simulator was started for this reconciliation.
