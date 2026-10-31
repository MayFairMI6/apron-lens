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
| 2 | Aircraft cannot have a next rotation | Done (backend). Scenarios may declare `rotations`; legacy single-flight data still loads. Open: add `flightInstance` to the Unity request and author rotation scenarios | `backend/conversation/identity.py`, `context.py` |
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
| 13 | Plain-HTTP Wi-Fi exposes the API budget | Done (guard). Open: call `check_bind` from the future `/conversation` server | `backend/conversation/guards.check_bind` |
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

## Not verified

GenAI repository code; Claude and DeepSeek strict structured-output support;
hosted logprobs; image-token counts for OpenAI, Claude and Gemini; whether
OpenAI bills reasoning tokens as output; provider minimum deposits; Gemini
free-tier data-use terms; Android build with the new scripts; physical
Android behaviour.
