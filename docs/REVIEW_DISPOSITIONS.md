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
  (4 checks), `.RunObservations` (7 checks), and existing
  `ClaimClientVerification` (5) and `CoordinatorUiVerification` (16) all pass.
  Sample captures: `work/visual-observation-{24,29,31}s.png`.
- Open: props occupy about 1% of the frame, which a 3B model may miss; consider
  a referent-centred crop or larger props. Occlusion families not yet authored.

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
