# Checkpoint 2 decision log (Claude ↔ Codex handoff)

Every choice made while continuing Checkpoint 2, newest last, so another agent
can take over at any point. Evidence lives in the
[milestone ledger](MILESTONE_LEDGER.md) (ML-054 onward). The resume steps live
in [CHECKPOINT2_CONTINUATION.md](CHECKPOINT2_CONTINUATION.md). This log records
*what was decided, by whom and why*; it is not evidence that work is accepted.

**Who decides.** "Owner" means the project owner's own words in chat. "Agent"
means a working choice made by the agent within the owner's instructions; the
owner can reverse any agent choice.

## How to take over

1. Read `AGENTS.md`, this log, then `CHECKPOINT2_CONTINUATION.md`.
2. Run `git status`. All Checkpoint 2 work is uncommitted on
   `codex/airfieldlens-checkpoint2` (base 2fe7ef5) unless a later entry says
   otherwise. Do not discard or reformat other agents' uncommitted files.
3. Check for running processes before loading a model:
   `ps aux | grep -E "backend.replay|backend.training|checkpoint2_scenarios|handoff_answers"`.
   Only one process may hold the 9B model; only one service may use port 8767.
4. Add a row below for every choice you make, and evidence to the ledger.

## Standing owner rules that shape choices

| Rule | Source |
|---|---|
| Work stays in Unity on the computer; no printed board, tabletop or physical phone | Owner memory |
| Never write "team", "solo" or "teammate" in course or project docs | Owner memory |
| Commit only named paths (`git commit -o <paths>`); a rename is kept staged | Owner memory |
| Visual/scenery/movement changes use the reference → implementation → independent review workflow | `AGENTS.md` |
| Effort: medium by default; high only for a concrete hard problem or final scientific review | `AGENTS.md`, `docs/AGENT_EXECUTION_POLICY.md` |
| Preserve failures, frozen data and earlier results; never retune on held-out data | Execution queue, ledger |

## Decisions

| # | Date | Decision | By | Why / evidence |
|---|---|---|---|---|
| 1 | 2026-11-16 | Build the controller replay as a separate read-only session (`backend/replay_session.py`) with its own clock, not a mode of the lesson driver | Agent | Keeps the lesson clock, typed checkpoints and their acceptance untouched; ML-054 |
| 2 | 2026-11-16 | One source cutoff drives scene, report list, camera observations and assistant context; seek/selection bumps a view revision and stale answers are discarded | Agent | Execution queue item 2; 24 replay tests |
| 3 | 2026-11-16 | Backward seek: assistant memory is filtered with the existing `SessionState.visible_memory` rule, not a copy | Agent | One rule for both paths |
| 4 | 2026-11-16 | Timeline markers carry no report content; unreceived markers later stripped of event time and label | Agent + reviewer | Requirement that future reports never leak; ML-055 |
| 5 | 2026-11-16 | Notes are annotations stamped with run, cutoff, aircraft and eligible evidence IDs; they never bump the view | Agent | Execution queue item 2 |
| 6 | 2026-11-16 | Replay service runs on its own module `backend/replay.py`, same token, port chosen at launch (8767 for the app) | Agent | App already polls 8767 |
| 7 | 2026-11-16 | 787 `unknowns_schema` diagnosed as an invented property name, not a wrong answer; add one retry for out-of-vocabulary unknowns (policy v5, then v6 naming the bad entry) | Agent | Retry can only fire on an answer the validator would withhold; ML-054 |
| 8 | 2026-11-16 | Safety motivation written as the occupied-runway / incursion problem, using the two sources already in the register; no new citations | Agent, at owner's request | Owner asked to make the airfield safety motivation clearer |
| 9 | 2026-11-16 | Preview image approved | Owner ("Approve, build it") | `outputs/checkpoint2-run/controller-replay-preview/` |
| 10 | 2026-11-16 | Screens built as a partial class `TrainingView.Replay.cs`; every hook gated on replay mode | Agent | Leaves lesson/demo paths unchanged; reviewer confirmed |
| 11 | 2026-11-16 | Panel uses four tabs (Reports, Changed, Note, Ask) in both orientations instead of the preview's two-row footer | Agent | Report list must stay reachable; recorded as a deviation in ML-055 |
| 12 | 2026-11-16 | Independent code review by a separate agent before the second build; all four confirmed defects fixed | Agent | `AGENTS.md` review rule; ML-055 |
| 13 | 2026-11-16 | Unity validation counts only drawn aircraft (hidden observation-only contacts allowed beyond four) | Agent | Pre-existing defect stopped the 787 handoff loading; ML-055 |
| 14 | 2026-11-16 | Build with `work/unity-editor` Unity, not the Hub install | Agent | Hub install lacks the Android module and fails to compile |
| 15 | 2026-11-17 | Driver replication guide plus model-free `scripts/describe_scenario.py`; scenario identity = SHA-256 of the world without its run ID | Agent, at owner's request | Owner asked for a guide; ML-056 |
| 16 | 2026-11-17 | `backend.replay --no-model` for screen checks that need no answer | Agent | Starts in seconds; frees the GPU |
| 17 | 2026-11-17 | Keep withholding answers with an out-of-vocabulary unknown; do not drop the name in code | Owner ("ok do the recommended") | Dropping it hides the model's statement of what is unknown; ML-057 |
| 18 | 2026-11-17 | Withheld answers of that kind point at the received report the model selected | Owner-approved recommendation | ML-057 |
| 19 | 2026-11-17 | Selector prompt candidate v9 not promoted; live prompt stays v8 | Agent | Did not fix its target case and changed 6 of 43 answers; ML-057 |
| 20 | 2026-11-17 | Built-in questions not reworded | Agent | Rewording changes scenario hashes already recorded |
| 21 | 2026-11-17 | Execution-queue wording changed to drop "teammates"/"teamwork" | Agent | Owner memory rule on team wording |
| 22 | 2026-11-17 | Effort recommendation: medium by default; high for designing and freezing the evaluation protocol and for the final scientific review | Agent recommendation, owner asked | Matches `AGENTS.md` effort policy |
| 23 | 2026-11-17 | Replay also serves the two fleet return variations (single-engine, wildlife) | Agent | Queue item 5 says to cover the other assigned cases after A380 and 787; needed a case that reliably produces the withheld message; ML-057 addendum |
| 24 | 2026-11-17 | Withheld-answer pointer verified on screen in the fifth build | Agent | ML-057 addendum |
| 25 | 2026-11-17 | Next workstream: visual evidence (detector revision, detections into the replay as camera reports, reports / +RGB / +depth comparison) | Owner (chose the recommended option) | Main research question with no results yet |
| 26 | 2026-11-17 | Approval of the frozen Checkpoint 2 evaluation set is delegated to Claude | Owner ("you can approve it") | Owner's answer to who authors/approves the held-out set |
| 27 | 2026-11-17 | Drafting of that set goes to a fresh agent given only the protocol, never development cases or results; Claude reviews and approves; the ledger states this is weaker than an independent human author | Agent, within decision 26 | Keeps the author separate from development as far as possible; does not remove bias |
| 28 | 2026-11-17 | Commit and push all Checkpoint 2 work on `codex/airfieldlens-checkpoint2`; no PR | Owner ("Commit and push") | Clean takeover point for Codex |
| 29 | 2026-11-17 | Keep this log as the working handoff ledger, updated and committed with each meaningful slice | Owner ("keep a working handoff ledger") | Codex can take over at any time |
| 30 | 2026-11-17 | Commit `c1d01c3` pushed to `origin/codex/airfieldlens-checkpoint2` (107 files, 700 tests passing); no PR | Agent, per decision 28 | Clean takeover point |
| 31 | 2026-11-17 | Diagnosis of the detector pilot: the tanker is ~60×25 px in 960×540 frames, SSDLite resizes to 320 px, and training had 13 positive boxes | Agent | `outputs/checkpoint2-run/detector-pilot.json`, pilot capture metadata |
| 32 | 2026-11-17 | Download approved: torchvision Faster R-CNN MobileNetV3-Large-FPN COCO weights (`fasterrcnn_mobilenet_v3_large_fpn-fb6a3cc7.pth`, ~77 MB, download.pytorch.org, BSD-3); compare it with tiled SSDLite on development data | Owner ("Download now") | Small-object detection |
| 33 | 2026-11-17 | Render a larger development set in Unity from the existing Stand B scene (more viewpoints, times, colours; tug and cart as distractors); held-out variants disjoint and fixed by a pre-registered seed before training | Owner (chose the recommended option) | 13 positive boxes is too few |
| 34 | 2026-11-17 | Detector v2 protocol pre-registered in `experiments/apron_detector/PROTOCOL.md` before rendering or training: seeds 20261117 (development) and 20261118 (held-out), split by domain, evaluable-box rule, threshold and candidate selection on validation only, single held-out run, gate precision ≥ 0.90 and recall ≥ 0.70 | Agent | Held-out split for the detector is fixed by a pre-registered seed (decision 33), not by the fresh-agent route of decision 27, which is for the reports-versus-camera evaluation |
| 35 | 2026-11-17 | Plan mode added to `P01CaptureBatch.cs` (camera set directly in apron metres; pilot path unchanged). No scenery, asset or route changes, so the `AGENTS.md` visual workflow does not apply | Agent | Data generation only |
| 36 | 2026-11-17 | Development set rendered (640 frames, 380 training and 118 validation evaluable boxes); labels spot-checked on development frames only | Agent | `work/detector-v2/development`, log `work/detector-v2/render-development.log` |
| 37 | 2026-11-17 | Held-out set rendered (200 frames) and frozen in `outputs/checkpoint2-run/detector-v2-heldout-manifest.json` before training; held-out images not opened | Agent | PROTOCOL.md held-out access rule |
| 38 | 2026-11-17 | Camera evidence arms defined in `backend/camera_evidence.py`: `rgb` = detected/not detected with confidence, no location; `rgb_depth` = adds apron position from depth and camera pose, and on/off Stand B. Records use the typed-claim checker's camera format; mask and label boxes are never read; "not_detected" is not absence; no observation can establish a release | Agent | Execution queue (reports / +RGB / +depth arms); 7 tests |
| 39 | 2026-11-17 | Depth geometry validated on development validation frames: median 2.4 m, max 5.7 m from the true route position; on/off Stand B agrees in 117 of 118 boxes (the miss is mid-departure at the stand edge) | Agent | `outputs/checkpoint2-run/detector-v2-depth-location-check.json` |
| 40 | 2026-11-17 | Development fit complete. Validation (evaluable boxes): A tiled SSDLite P 0.69 / R 0.36 at 0.80; B Faster R-CNN P 0.92 / R 0.92 at 0.65, 0 false detections on look-away frames. B selected by the pre-registered rule; fit report committed before the held-out run | Agent (rule fixed in PROTOCOL.md) | `outputs/checkpoint2-run/detector-v2-fit-report.json` |
| 41 | 2026-11-17 | Held-out run (once): B precision 0.869, recall 0.930. Gate failed on precision; detector recorded as not qualified; held-out split v2 spent | Protocol rule | ML-058; `outputs/checkpoint2-run/detector-v2-heldout.json` |
| 42 | 2026-11-17 | Detector route after the failed gate: add an evidence gate (presence precision ≥ 0.95, recall ≥ 0.80; depth location within 8 m in ≥ 90%; on/off Stand B ≥ 95%), keep the box gate reported, fresh v3 held-out split (seed 20261119), small box revision C (1.5× input, 10 epochs) | Owner (chose the recommended option) | PROTOCOL.md amendment 1 |
| 43 | 2026-11-17 | Interpretation: qualification **as camera evidence** is decided by the evidence gate; the box gate remains reported as detector quality and does not block evidence use | Agent interpretation of decision 42; owner may reverse | Matches how the assistant consumes camera observations |
| 44 | 2026-11-17 | v3 held-out split rendered and frozen (`detector-v3-heldout-manifest.json`) before candidate C is fitted; not opened | Agent | Amendment 1 |
| 45 | 2026-11-17 | Candidate C fitted; B carried unchanged (validation reproduced exactly). Validation box F1: C 0.962 (P 0.958, R 0.966 at 0.30) vs B 0.924; C selected by the unchanged rule; fit report committed before the v3 run | Agent (rule fixed in PROTOCOL.md) | `outputs/checkpoint2-run/detector-v3-fit-report.json` |
| 46 | 2026-11-17 | v3 held-out run (once): candidate C passes the box gate (P 0.975, R 0.957) and the evidence gate (presence P 1.00, R 0.963; location within 8 m 100%; Stand B agreement 98.1%). Recorded as qualified camera evidence for synthetic Stand B frames only | Protocol rule | ML-058 addendum; `outputs/checkpoint2-run/detector-v3-heldout.json` |
| 47 | 2026-11-17 | Recorded Stand B camera session: scripted AR viewpoint once per second, 0–210 s; observations from the qualified detector for both arms; presence right in 211/211 frames | Agent | ML-058 addendum 2 |
| 48 | 2026-11-17 | Tracking-lost frames keep presence but never a location | Agent | No pose, no place on the apron |
| 49 | 2026-11-17 | Replay serves Stand B and loads exactly one camera arm per run; only a qualified session can be loaded | Agent | Arms stay separable for the comparison |
| 50 | 2026-11-17 | Camera observations are **not** added to the assistant prompt yet; their prompt wording is part of the frozen comparison design. App display of camera rows waits for preview approval | Agent | Evaluation integrity; preview rule |
| 51 | 2026-11-17 | Camera observation card approved for the Stand B replay (one "latest camera observation" card above the reports, lower-authority label, arm fixed at launch) | Owner ("Approve, build it") | `outputs/checkpoint2-run/camera-observation-preview/` |
| 52 | 2026-11-17 | The reports / +RGB / +depth comparison design starts only after the owner switches the session to high effort; the agent then drafts the protocol for owner review before anything is frozen | Owner ("You switch to high, then I start") | Effort policy in `AGENTS.md` |
| 53 | 2026-11-17 | Card wording is composed by the replay service (`cameraLatest` in the view) and only displayed by the app; the report list rebuilds on report changes, not on each camera second | Agent | Testable wording; scroll position kept during playback |

| 54 | 2026-11-17 | The card appears only when the selected flight is the one the camera observations are about (TRN103); other flights show no card | Agent | A card on TRN101 would imply a camera view of that aircraft |
| 55 | 2026-11-17 | Card built and checked in the Simulator: RGB + depth portrait at 01:32 ("seen off Stand B", report still pending), landscape at 01:40 ("not detected (not proof it has gone)"), RGB landscape at 01:19 ("seen in view", no position). Card first clipped three of four lines and was enlarged before these checks | Agent | `outputs/checkpoint2-run/replay-native/camera-card-*.png`; 712 tests pass |
| 56 | 2026-11-17 | Noted, not fixed: TRN101's stand-assignment report in the Stand B replay reads only "A" in the report list (pre-existing wording, not part of the card) | Agent | Seen in the same Simulator run; queued |
| 57 | 2026-11-17 | Owner switched the session to high effort; comparison design started | Owner ("Switched, start") | Decision 52 |
| 58 | 2026-11-17 | Draft protocol `docs/course/CAMERA_EVIDENCE_COMPARISON.md` and draft author brief `docs/course/M2_HELDOUT_AUTHORING_BRIEF.md` written; nothing frozen. Proposed home: M2 (freeze 2 and the `m2` held-out set) in the research runner, as `docs/AR_SCOPE.md` already plans, not the app selector | Agent; awaiting owner D1–D7 | Existing held-out guards, scoring and M1 precedent |
| 59 | 2026-11-17 | Finding: Stand B varies almost nothing by seed (seeds 17/18/99 differ in one receipt time by <1 s), so held-out variety must come from new camera sessions, new questions and cutoffs, and optionally authored timing variants | Agent | Checked with `build_lesson` |
| 60 | 2026-11-17 | Owner asked whether "it" should remain a handoff note in the UI; answered for the replay's Note tab ("Handoff note"): keep it as a controller annotation, separate from evidence; meaning to be confirmed | Agent recommendation; owner to confirm | Note tab never feeds the assistant |
| 61 | 2026-11-17 | D1: the comparison runs as M2 (freeze 2, `m2` held-out set) in the research runner | Owner ("M2 in runner") | Protocol draft |
| 62 | 2026-11-17 | D3: models are Qwen3.5-9B, `qwen3-vl-4b` and the deterministic baseline; VL-4B runs the same text arms, no images arm added | Owner ("Add qwen3-vl-4b too"); agent reading of "text arms" | 600 local model turns plus baseline |
| 63 | 2026-11-17 | D4: held-out variety from new camera sessions plus two authored timing variants, sources noted | Owner (chose the recommended option) | Stand B varies little by seed (#59) |
| 64 | 2026-11-17 | D5: include the secondary judge; the owner rates about 20 development answers before freeze 2 | Owner ("I'll rate 20 answers") | `docs/JUDGE_RUBRIC.md` |
| 65 | 2026-11-17 | Owner said "Yes, start building" the M2 camera arms on development data | Owner | Protocol draft, D1–D5 |
| 66 | 2026-11-17 | Freeze 1's files (`turns.py`, `validate.py`, `scoring.py`, runner) are not edited: a first attempt edited them and the freeze tests caught the hash change, so it was reverted. The M2 method lives in new modules (`camera.py`, `turns_m2.py`, `scoring_m2.py`, `scripts/run_m2_camera.py`) built on the frozen ones; freeze 2 will cover them | Agent | Keeps M1 reproducible; the approved freeze record is untouched |
| 67 | 2026-11-17 | Camera evidence is typed: the reply's eleventh key "camera" copies a listed capture ID with finding and place, checked against the record; labels name capture **times**, not IDs; one validator-guided retry with the error codes, both attempts kept | Agent | Invented positions and camera-as-claim become rejections; labels do not depend on detector output |
| 68 | 2026-11-17 | Protocol revised before any freeze: report criteria are compared across all arms; camera criteria only among camera arms (they carry different labels); "depth adds" judged on location and conflict turns | Agent; owner may revise | The earlier "camera helps if accuracy rises" rule compared arms on unequal labels |
| 69 | 2026-11-17 | 12 development families (15 turns) in `data/m2_dev/families.json` on the seed-17 session; baseline dry run 14/15 (misses the look-away "what changed" turn by over-citing, as intended); no stale-frame family, because the session has a frame every second | Agent | Development only |
| 70 | 2026-11-17 | Replay's first view button reads "Apron" when a scenario has no regional geography (same rule as the training view); "Region" stays for the A380/787 cases. Checked in the Simulator on Stand B | Owner ("can u fix the mismatch") | `outputs/checkpoint2-run/replay-native/apron-label-stand-b.png` |
| 71 | 2026-11-17 | No 360° or tower view exists: the replay camera only pans, zooms and uses fixed presets facing north. A tower-eye view with turning would be a new visual (preview approval) and scope (ledger review); offered, not built | Agent | `TrainingView.cs` MoveCamera |
