# Review dispositions — AI API use plan (review of 31 October 2026)

Independent review by Claude (Claude app, outside the API budget) of the
30 October plan and the ApronLens code. The GenAI repository was not
inspected. No paid API calls were made. Frozen files hash-checked by
`scripts/check_research_integrity.py` were not modified; all changes are new
modules, a new Unity script, and the regenerated plan PDF.

**Held-out incident.** While listing data files the reviewer printed two
existing held-out answers (`data/reasoning_v2_fresh/queries.json`, N01-Q1 and
N01-Q2). They were not used for anything. Treat them as seen by a reviewer.
The existing suite stays in place because it is frozen and hash-checked;
new held-out answers go outside the repository (finding 6).

Status key: **Done** = implemented with unit tests · **Plan** = plan PDF revised ·
**Open** = still to do.

| # | Finding | Disposition | Where |
|---|---------|-------------|-------|
| 1 | Evidence image reveals the selected aircraft; fixed virtual camera | Done in part / Plan. New capture omits ring and paths, renders from the AR camera pose, returns the tap as coordinates. **Verified in the Unity editor (batch mode with graphics, 31 October):** the project compiles; the existing capture differs by selection (leak confirmed); the new capture is byte-identical for either selection and not blank (672x504, 70 sampled colours); the tap is returned as viewport coordinates. Log: `work/unity-visual-capture-check.log`. Open: uniform livery and 3+ aircraft (StandReplay still builds two index-coloured aircraft); Android build and on-device check | `unity/.../Scripts/VisualEvidenceCapture.cs`, `unity/.../Editor/VisualCaptureVerification.cs` |
| 2 | Aircraft cannot have a next rotation | Done (backend). Scenarios may declare `rotations`; legacy single-flight data still loads. Done (backend and Unity). The Unity conversation client sends the rotation under way; Unity scenarios may declare `rotations` (`visual_dev_03`) | `backend/conversation/identity.py`, `context.py`, `Scenario.cs`, `ConversationClient.cs` |
| 3 | Seek-back leaks future evidence through memory | Done. Memory is tagged with its cutoff and masked; formal runs reject backward seeks | `backend/conversation/state.py` |
| 4 | Validator checks support but not completeness; rationale unverifiable | Done. Changed-fact coverage, deny-change check, unknown-vs-current check, template claims, labelled interpretation | `backend/conversation/validate.py` |
| 5 | Budget assumes text-only, low-reasoning calls | Plan + Done (ledger). Astra out of screening; comparison cost gate; stress illustration. Open: one development cost probe per provider, check minimum deposits | `backend/conversation/ledger.py`, `selection.comparison_eligible`, plan budget section |
| 6 | Held-out answers sit in the working tree | Done (loader) / Plan. Loader refuses paths inside the repository and checks a committed hash | `backend/conversation/guards.load_heldout` |
| 7 | Gates not disqualifying; small screening slices | Done / Plan. Ordered selection; weighted total still published | `backend/conversation/selection.py` |
| 8 | Turn construction unspecified | Plan + protocol constant (`on_policy`). Open: build the formal runner | `selection.PROTOCOL` |
| 9 | Hosted models cannot reproduce label scoring | Done. Unsupported operations raise; hosted label scoring marked unsupported | `modelaccess/contract.py`, `config/hosted-models.json` |
| 10 | Silent model changes behind aliases | Done. Returned model must equal the configured model or a listed snapshot | `modelaccess/contract.py` |
| 11 | Device and dtype differ between projects | Done for new code. Frozen `backend/server.py` intentionally unchanged | `modelaccess/local_qwen.py` |
| 12 | Shared library could change both experiments; order front-loads it | Plan. Library used only in new code paths; pin by commit SHA. Open: extract once the GenAI project adopts it | `modelaccess/__init__.py`, plan delivery sequence |
| 13 | Plain-HTTP Wi-Fi exposes the API budget | Done. The `/conversation` server calls `check_bind` before binding whenever its adapter can spend money | `backend/conversation/guards.check_bind`, `backend/conversation/server.py` |
| 14 | Retries, cancellations, tracking loss | Done (idempotent commits, cancelled calls stay charged) / Plan (tracking-loss rule). Open: Unity side | `state.py`, `ledger.py` |
| 15 | Provider-specific JSON repair | Done. One policy, `json-repair-v1`; raw validity reported | `modelaccess/repair.py` |
| 16 | Dated prices, peak rates, thinking defaults | Done. Rates by effective date; "from" rates refused | `config/hosted-models.json`, `ledger.RateTable` |
| 17 | Stakeholder claims need domain review | Plan wording | plan, research question |

## Extension: visual observations (31 October)

Added after the review so that the image carries information the system does
not otherwise have.

- `unity/.../Resources/visual_dev_01.json`: development scenario with a fuel
  vehicle and a cargo hatch whose states are rendered but never reported
  (report and view conflict from 22 to 30 s; the view runs ahead of a late
  baggage report from 28 to 34 s). The Milestone 1 scenario is unchanged.
- `Scenario.cs`, `StandReplay.cs`, `SceneBootstrap.cs`: optional `visualProps`
  with validated timed states, rendered as unlabelled neutral shapes attached to
  the aircraft; scenarios can be chosen by resource name (default `milestone1`).
- `backend/conversation/observations.py`: observations relate to reports as
  consistent, conflicting, no report yet, or report describes a later time;
  never supersede a report. Linking rules are authored and need domain review.
- `backend/conversation/visual_truth.py`: evaluation-only ground truth; a test
  fails if any request-path module reads it.
- `validate.py` v2: observations must carry the image's capture time and
  concern the referent; shown as unverified; claims and changed-fact checks
  are unaffected.
- Unity editor checks (batch mode with graphics): `VisualCaptureVerification.Run`
  (6 checks), `.RunObservations` (8 checks), and existing
  `ClaimClientVerification` (5) and `CoordinatorUiVerification` (16) all pass.
  Sample captures: `work/visual-observation-{24,29,31}s.png`.
- Prop legibility (`visual-capture-v2`): measured with
  `VisualCaptureVerification.MeasurePropCoverage`, the props first covered 220 px
  (fuel vehicle) and 81 px (hatch) of a 672 × 504 capture, 0.06% and 0.02% of the
  frame, not the 1% estimated earlier. A referent-centred crop was rejected
  because its framing would reveal the referent. The capture now renders a crop
  fitted to all aircraft and stand markers (`SceneCrop`, about 2× zoom in the
  development view; identical for either selection, and the tap is returned in
  crop coordinates). Props are dark grey instead of near-white and the hatch is
  1.5× larger in plan. Result: 892 px (0.26%) and 783 px (0.23%);
  `.RunObservations` now fails if a prop drops below 0.15%.
- Similar aircraft: scenarios may declare two to four aircraft and
  `"livery": "uniform"` (one colour for every aircraft and a neutral chip
  marker). `visual_dev_02` has three same-livery aircraft: A1 parked at Stand A
  with a fuel vehicle until 26 s, A2 at Stand B with the hatch open until 32 s,
  and A3 taxiing past both; a late baggage report (event 30 s, received 38 s)
  lets the view run ahead of the reports. The deterministic baseline text keeps
  its authored wording for Milestone 1 only and lists the selected flight's
  reports elsewhere. `VisualCaptureVerification.RunMultiAircraft` (14 checks)
  covers this; Milestone 1 keeps two indexed aircraft and its original layout.
- Open: occlusion families not yet authored. The crop shrinks as aircraft spread
  apart, so wider scenes zoom less.

## Conversation endpoint (31 October)

The context modules now run as one conversation. The frozen `/reason` server
is unchanged.

- `backend/conversation/turns.py` serves one turn:
  1. Takes the receipt-eligible facts of every rotation of the selected aircraft,
     plus the current referent, and the memory visible at the turn's cutoff.
  2. Builds the prompt (`conversation-prompt-v4`) and calls the model through
     the model-access contract. For each candidate flight with a previous
     answer, the prompt carries the changed-fact set the validator checks, from
     the same `changed_facts` function. (v1 listed only the previous answer's
     cited facts, so the required follow-up answer could not be read from it.)
     v3 lists the allowed status values, requires every key, puts the real
     image capture time in the example and defines "next rotation"; v2's
     placeholder wording was copied literally by the 3B model. v4 adds a
     one-line appearance legend for each prop (from `VISUAL_KINDS`) and the rule
     that observations describe the image even when a report disagrees.
  3. Parses the reply under `json-repair-v1` and runs `validate_proposal`.
  4. Commits atomically against the session revision.
- Referent rule: the app sends its selected aircraft and flight on every turn.
  Selecting a different aircraft resets the referent. Keeping the same one
  preserves an accepted correction such as "its next rotation". Memory comes
  only from the user's selection or a validated `memoryUpdate`, never from the
  rationale.
- Correction rule (`referent-rule-v2`, adopted 31 October by the user's
  decision): when the memory update is a correction to a flight in the
  scenario, that flight becomes the proposal's referent before validation,
  replacing the model's referent field. Its claims must then be that flight's
  received facts, so mixing two flights is still withheld. Other memory-update
  kinds never move the referent. Each result records `referentSource` (`model`
  or `correction`) and `referentRule`.
- `backend/conversation/server.py` provides `POST /conversation` and `GET /health`:
  - It uses the same bearer token as `/reason`, checked before the body is read.
  - It has one in-memory session per `sessionId`, bound to the scenario and mode it
    started with; a change to either gets 409, because scenarios reuse aircraft and
    flight IDs.
  - Retries with the same request ID return the stored result without a second
    model call.
  - A stale revision, a backward seek in a formal run or a reused request ID
    gets 409.
  - An image needs a capture time at or before the checkpoint.
  - The audit goes to `work/conversation-requests.jsonl`. It holds the prompt,
    the raw output and the image hash, never image bytes.
- Run: `python -m backend.conversation.server --profile apronlens-v2-mps` (port
  8766, `qwen2.5-vl-3b` by default).
- Unity client (`ConversationClient.cs`), opened from More → Ask a question:
  - Each question sends the selected aircraft and its `flightInstance`, the
    replay time and a live `VisualEvidenceCapture` image captured at that time.
  - One session per scenario. The client tracks the committed revision, and a
    409 starts a new session.
  - A failed connection keeps the request, so Retry reuses its ID and the
    server answers it only once.
  - Before showing anything it checks that the response matches this request,
    session and replay time, that the selection hasn't changed, and that every
    accepted claim cites a report received by then for the referent flight.
  - The "Copy session log path" row now holds two half-width buttons, so every
    control keeps its 48 dp height. The S24 layout result is unchanged.
- Unity's `JsonUtility` cannot omit a field, so the server reads an empty
  `imageBase64`, an empty `tapViewport` and a capture time without an image as
  not provided.
- Checks: `ConversationClientVerification.Run` (9, no network), and
  `.RunLive` (optional, needs a running server). The live run on `qwen2.5-vl-3b`
  went through in 17.7 s: the stand claim was checked and shown. Of its two
  unverified observations, "cargo hatch open" was right and "fuel vehicle
  connected" was wrong for that aircraft.
- Open: change follow-ups and referent corrections still fail with the 3B
  model, and observations are unreliable at 3B and 8B (development runs below).

Development run (31 October): `python scripts/run_conversation_smoke.py
--profile apronlens-v2-mps` with `qwen2.5-vl-3b`. Development data only: the
inline fixture, `visual_dev_01`/`visual_dev_02` with sample renders, and v1
families D01 and D03-D08 with turns generated from scenario events (the v1
question and gold file, H01-H04 and `reasoning_v2_fresh` are not read). D02 is
skipped: its `F2-R0` report has no declared rotation. These are development
observations, not evaluation evidence.

| Prompt | Accepted | Notes |
|---|---|---|
| v2 | 2/8 | Status placeholder copied (`"exact fact"`); image turns missing keys |
| v3 | 12/22 | All JSON valid; 9-16 s per turn on MPS |
| v3, `qwen3-vl-8b` | 20/22 | All JSON valid; 16-119 s per turn on MPS (median 53 s) |

Under v3, by situation:
- First question about a flight, no image: 9/9 accepted.
- Follow-up with no change (D06): 1/1.
- Follow-up after a change: 0/7. The model cites the changed facts but sets
  `explanationChanged: false`, and often labels superseded facts "expired".
- "I mean its next rotation": accepted with the wrong referent (F2-R1). The
  rationale names F2-R2, but the referent and memory are unchanged. The
  validator does not verify referent choice, so scoring needs evaluation labels.
- Image turns: 0/2, `captureTime` omitted. Fuel vehicle state was right in both;
  one hatch observation was wrong.

Same 22 turns with `qwen3-vl-8b` (revision `0c351dd`, same profile and prompt):
- Follow-ups after a change: 7/7, each with `explanationChanged: true` and every
  changed fact covered. The 3B failure was the model, not the design.
- "I mean its next rotation": withheld. The memory update names F2-R2, but
  the referent stays F2-R1 and F2-R2's fact is cited under it.
- Image turns: 1/2 accepted, but both observations are wrong. It reported
  "departed" for a fuel vehicle that is connected in the 24 s render, matching
  the "fuel complete" report instead, and "unknown" (not an allowed value)
  for A1's visible vehicle. Observation truth is not validated on the request
  path, so evaluation must score observations against `visual_truth`.
- A median of 53 s per turn on this Mac is too slow for live use.

Visual perception check (`scripts/run_visual_perception_check.py`): the image
and one question per stand aircraft, with no reports, scored against
`visual_truth`; `qwen3-vl-8b`, 18 prop judgements per condition.

| Props | Render | Prompt | Correct |
|---|---|---|---|
| original (grey box, grey panel) | 672 px | plain | 10/18 |
| original | 672 px | shapes described | 14/18 |
| original | 1344 px | plain | 8/18 (7 "cannot tell") |
| original | 1344 px | shapes described | 14/18 |
| redesigned (tanker, flap) | 672 px | plain | 11/18 |
| redesigned | 672 px | v4 legend | 12/18 |

- Resolution does not help: 1344 px matches or trails 672 px at three times the
  input tokens. Captures stay at 672 px.
- The original hatch panel looked like the fuel vehicle from above. The props
  were redesigned (tanker with cab and hose on the aircraft's right; a flap
  hinged out on its left; near-black for contrast on the stand bands; coverage
  0.28% and 0.19%), but perception did not improve: open hatches are still
  mostly missed, and at Stand B the flap is still called a tanker.
- 22 turns under v4 with `qwen3-vl-8b`: 21/22 accepted (the next-rotation
  correction is still withheld). Both image turns now pass the validator, but
  one observation is still wrong: "departed" for a connected tanker, matching
  the "fuel complete" report despite the image-first rule.
- Conclusion: visual grounding of these props is a limit of the local 8B model,
  not the capture size. A hosted comparison is the next step.

## Rotations in Unity scenarios (31 October)

- `Scenario.cs`: an aircraft has one `flightInstance` (legacy) or `rotations`,
  in the backend's format (`{flightInstance, from, until}`, ordered and
  non-overlapping; the last may omit `until`). `FlightAt(t)` gives the
  rotation under way, and between rotations the latest one that has started.
  Validation matches `validate_rotations`: each flight is owned by one
  aircraft, and every report's flight belongs to its own aircraft.
- `StandReplay`: the selected flight, the report history and the chip labels
  follow the rotation under way. Single-flight scenarios are unchanged,
  including the Milestone 1 chip labels and the S24 layout result.
- `ConversationClient`: sends the current rotation, and shows an answer about
  any rotation of the referent aircraft (a "next rotation" correction) only
  when its claims cite reports received for that rotation.
- `visual_dev_03`: A2 flies F2-R1 until 45 s, then F2-R2. F2-R2's off-block
  estimate (70 s, received at 10 s) is revised to 80 s by a report sent at
  30 s and received at 36 s. So a question at 30 s, "I mean its next rotation",
  and a follow-up at 40 s exercise the correction and the change check together.
- Checks: `RotationVerification` (13), Python tests for `visual_dev_03`, and a
  rotation session in `scripts/run_conversation_smoke.py`.
- Development run with `qwen3-vl-8b` (prompt v4), 25 turns: 22 accepted. All
  three rotation turns failed. Asked at 30 s when A2 leaves, it cited F2-R2's
  off-block time under the referent F2-R1 (withheld). On "I mean its next
  rotation" its memory update correctly named F2-R2, but the referent stayed
  F2-R1 and it mixed both rotations' facts (withheld). The follow-up asked for
  clarification. This is the same pattern as the fixture's correction turn:
  the model works out the intended rotation but keeps the app's selection as
  the referent.
- Taking the referent from a validated correction was then adopted
  (`referent-rule-v2`). Rerun of the same 25 turns:
  - `qwen3-vl-8b`: still 22/25. The rule applied as designed (the
    memory-update mismatch is gone), but both correction turns are still
    withheld. The model now cites facts from both rotations at once (F2-R1's
    stand or baggage alongside F2-R2's off-block time) and lists an unknown
    that contradicts a current fact.
  - `qwen2.5-vl-3b`: 15/25. It makes no correction at all (no memory update,
    referent left on F2-R1), so its "accepted" correction turns answer about
    the wrong rotation. Only evaluation labels can catch that.
- So the rule is safe and removes one failure, but correction turns still need
  a model that keeps to one flight's facts. Evaluation must score the referent
  against labels.

## Hosted adapters and budget enforcement (31 October)

- `modelaccess` 0.2.0 adds `AnthropicAdapter` (Messages API) and `OpenAIAdapter`
  (Responses API) on the official SDKs, imported only when a hosted run starts
  (`requirements-hosted.txt`). Both follow the contract:
  - no fallback to another model: server-side refusal fallbacks are not enabled,
    and a refusal is `finish_refusal`
  - temperature is reported as ignored
  - images are downscaled to the shared `image_max_side`
  - SDK retries are off; each retry is a separate budgeted attempt
  - capabilities stay unverified until a recorded probe
- Claude: thinking is always on and is not configured; effort goes to
  `output_config.effort`. OpenAI: effort goes to `reasoning.effort`, and images
  are sent with detail "high".
- `backend/conversation/hosted.py`:
  - `BudgetedAdapter` reserves a conservative maximum in the ledger before every
    call (input estimated at two characters per token plus 3,000 tokens per image,
    all at the uncached rate, plus the full output cap) and reconciles it with
    reported usage. A refused reservation raises before any network call.
  - `estimate_run` prices a whole run without calling a model.
- Both run scripts take `--provider`, `--estimate-only`, `--confirm-spend` and
  `--max-spend` (default $5, the ledger session limit). A hosted run refuses to
  start without `--confirm-spend` or above the cap.
- Maximum reservations for the 22 turns / 18 perception questions:

  | Model | 22 turns | 18 questions |
  |---|---|---|
  | Claude Sonnet 5.5 | $1.84 | $0.84 |
  | Claude Opus 5.5 | $3.68 | $1.69 |
  | GPT-6.1 Terra | $0.92 | $0.42 |
  | GPT-6 Luna | $0.09 | $0.04 |
  | GPT-6 Astra | $9.20 | $4.22 |

  Claude Haiku 5.5 has only a "from" rate and is refused until an exact rate is set.
- Open: no provider API key is set on the development Mac, so no paid call has
  been made. The first paid call per provider is a cost probe, made only with
  the user's approval.

## Backbone 1.1.0 (branch `backbone/explicit-runtime`)

Built on the unmerged `claude/charming-maxwell-msnzgq` backbone (1.0.0, 27 October),
addressing findings 11 and 12:

- `backend/server.py` restored to the frozen V2 source; it never imports the
  backbone (`check_research_integrity.py --current` passes, and CI now runs it).
  The 1.0.0 branch's `--model` option and optional image on `/reason` are
  therefore not included; candidates are compared with `run_model_check.py`.
- Engines require an explicit runtime: named profiles in `backbone/models.json`
  (`apronlens-v2-mps`, `compaction-gaivi-cuda`, `cuda-bfloat16-eager`,
  `cpu-float32`); an unavailable device is an error, never a fallback.
  `run_model_check.py --runtime`, the workflow and the GAIVI job require one.
- Versioning: each repository adopts a backbone version by its own explicit
  change; results record the backbone version and runtime.
- `modelaccess/local_backbone.py` replaces `local_qwen.py` and delegates to the
  backbone engine, so model loading exists in one place.
- Real-model check (31 October, this Mac): the backbone engine with
  `apronlens-v2-mps` and the frozen `LocalQwen` produced identical outputs and
  log-probabilities (maximum difference 0.0) on 23 Yes/No decisions across four
  Milestone 1 development queries.
- Not done: the compaction repository still loads Qwen directly (float16, SDPA,
  CUDA); it adopts the backbone later with the `compaction-gaivi-cuda` profile.

## Tests

`python -m unittest discover -s tests` runs `tests/test_conversation.py`,
`tests/test_modelaccess.py` and `tests/test_visual_observations.py` (48 tests,
standard library only, no network, no weights) together with the existing tests.
`tests/test_conversation_server.py` (19 tests) drives `/conversation` with a
scripted model through FastAPI's test client.

## Not verified

GenAI repository code; Claude and DeepSeek strict structured-output support;
hosted logprobs; image-token counts for OpenAI, Claude and Gemini; whether
OpenAI bills reasoning tokens as output; provider minimum deposits; Gemini
free-tier data-use terms; Android build with the new scripts; physical
Android behaviour.
