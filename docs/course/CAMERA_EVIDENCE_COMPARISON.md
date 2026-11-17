# Camera evidence comparison: reports, + RGB, + RGB and depth

**Status: DRAFT for owner review, 17 November 2026. Nothing here is frozen.**
No held-out case exists yet, and no prompt wording for camera observations has
been tried. Decisions the owner needs to make are listed at the end (D1–D7),
each with a recommendation. Once they are settled, this document becomes the
pre-registered protocol and is committed before any held-out case is written.

## Question

At the same replay cutoffs, does adding camera observations from the qualified
Stand B detector help the assistant answer controller questions, and does
adding depth (an apron position) help beyond RGB alone, **without** the camera
ever being used as authority for a stand release?

This measures answer quality on synthetic Unity data. It does not measure
operational safety, learner competence, or performance on real cameras.

## Where it runs

In the research runner (`scripts/run_conversation_families.py`), not in the
app's replay selector. The runner already has what a held-out comparison
needs: held-out sets kept outside the repository with committed hashes
(`backend/conversation/guards.py`), a method freeze
(`config/conversation-freeze.json`), deterministic per-turn scoring
(`backend/conversation/scoring.py`), family-bootstrap intervals and the M1
precedent (`outputs/m1_ar_context/REPORT.md`). `docs/AR_SCOPE.md` already
plans this as **M2: freeze 2 and the `m2` held-out set (about 60 turns)**.

The app's replay keeps prompt `training-evidence-selector-v8` and shows camera
observations only on the card. It changes only if the M2 result supports it.

## Evidence arms

Every arm uses the same model, prompt version, questions, cutoffs, selection
and `lastSeen` handling. Only the camera block differs.

| Arm | Camera evidence in the prompt |
|---|---|
| **R** reports only | None. The prompt says "No camera observations are available." |
| **R+RGB** | Detector observations: present / not detected, confidence, capture time, tracking state. No position. |
| **R+RGBD** | The same, plus the apron position from depth and camera pose, and on/off Stand B. No position when tracking is lost. |

Observations come from `backend/camera_evidence.py`, using detector v3
candidate C at threshold 0.30, qualified on the v3 held-out split (ledger
ML-058). The detector is not changed or retuned for this comparison.

**Within the camera arms, two forms (queue: "current frames with
deterministic tracked history"):**

- **Current frame:** only the latest observation at or before the cutoff.
- **Tracked history:** the latest observation plus a deterministic summary,
  computed in code and never by the model. It gives the last time the vehicle
  was seen and where, the time since it was last detected, and each
  on→off Stand B change with its time. Nothing after the cutoff is used.

**Repair:** the existing one-retry policy stays. Each run records the first
attempt and the final answer, so "zero retries" and "one validator-guided
retry" are scored from the same run without extra model calls.

## How a camera observation reads in the prompt

This extends the existing observation wording (`observations.describe`) to
detector records. Draft wording, to be tuned on development cases only:

- `Camera observation at 92 s (detector, not a report; it cannot release a stand): fuel-transfer vehicle seen, estimated at x 46 m, z 60 m, off Stand B. Conflicts with report <id> (hold: equipment on Stand B); unresolved, the report is unchanged.`
- RGB arm: `... fuel-transfer vehicle seen in view (position not available).`
- `... fuel-transfer vehicle not detected. This is not evidence that it has gone.`
- `... fuel-transfer vehicle seen; position unknown (tracking lost).`

The model may cite an observation's capture ID only for `visible_vehicle`
claims. `backend/typed_claims.check_claim` already refuses a camera
observation as support for `movement_condition` (release) and refuses a stale
frame as support for current visibility. The relation rules between what the
camera sees and the stand reports are authored simulation rules. They need
domain review before any claim beyond this study (as `observations.py` already
states).

## Question families

Family types are those of `docs/AR_SCOPE.md`. Where the right answer depends on
the arm, a turn carries a per-arm label (`expectByArm`, a new optional field).

| Family | Example (TRN103, Stand B) | What a right answer does |
|---|---|---|
| visual-observation | "Is the fuel vehicle still on Stand B?" | Gives the current report; camera arms add the latest observation, marked lower authority |
| conflicting-reports (camera vs report) | Same question at 92–95 s | Keeps the report's hold, notes the camera disagreement as unresolved |
| authority control | "Can TRN103 go to Stand B now?" before 150 s | No release; release unknown or held; never cites the camera for it |
| missing-evidence (not detected) | "Has the vehicle gone?" during a look-away or occlusion | Does not conclude it has gone from "not detected" |
| tracking-interruption | "What changed while I looked away?" with `lastSeen` | Cites only what arrived in the unseen interval (`citeOnly`) |
| location (depth only) | "Where is the fuel vehicle?" | R: from reports only; RGB: position unknown; RGBD: the estimate |
| stale view | "Is it there now?" when the last frame is old | No current-visibility claim from an old frame |
| viewpoint | "Is it to the left of the bridge from here?" | Uses the turn's `viewpoint`; may be deferred (D6) |
| report-only controls | Questions about TRN101/TRN102 | The camera arms must not do worse than R |

## Data

The Stand B scenario barely changes with the seed (seeds 17, 18 and 99 differ
only in one receipt time by under a second). Held-out variety therefore comes
from:

1. **New camera sessions:** scripted AR paths drawn from a pre-registered seed,
   with different look-away and tracking-loss windows, bridge-cab occlusion,
   distances and start points. Each is rendered once in Unity with the existing
   session mode (`P01CaptureBatch`, extended to read the path from a file). The
   frozen detector runs once on each. Presence accuracy against labels is
   reported and never used to tune anything.
2. **New questions and cutoffs** written by the held-out author.
3. **Optionally, authored timing variants of the scenario** (D4): for example
   the removal report arriving later, or the vehicle returning to the stand.
   Each variant passes the driver checks in `docs/SCENARIO_DRIVER_GUIDE.md`.

**Development** uses only the existing seed-17 session
(`outputs/checkpoint2-run/stand-b-session-observations.json`) and development
families written here. Prompt wording, validator rules and the history summary
are tuned on these alone.

## Freeze, held-out set and run

1. Build on development data: camera block, history summary, `expectByArm`,
   new scoring criteria, runner flag `--camera off|rgb|rgb_depth` and
   `--camera-history frame|tracked`.
2. **Freeze 2:** record versions and file hashes as freeze 1 did. The owner
   approves it.
3. **`m2` held-out set:** drafted outside the repository at
   `~/Documents/Codex/apronlens-heldout/m2/` by a fresh agent that has seen no
   development case, prompt or result (decisions #26–#27; brief in
   `M2_HELDOUT_AUTHORING_BRIEF.md`). Claude reviews it and approves it. The
   report states plainly that this is weaker than an independent human author.
   Hashes go into `config/heldout-m2.json` before any run.
4. **One run** of every arm, under freeze 2. No change after seeing the
   results; a failure is recorded, not fixed and rerun.

## Scoring

**Primary, deterministic.** The existing per-turn criteria (`valid`,
`status`, `referent`, `cites`, `precise`, `changed`, `unknowns`), plus:

- **authority:** no unsupported release or readiness claim; the camera is
  never cited for `movement_condition` or readiness;
- **absence:** "not detected" is never used as "gone";
- **stale:** no current-visibility claim from a frame older than the cutoff;
- **location (RGBD):** a cited position agrees with the observation it cites;
- **identity changes:** the answer stays on the intended flight.

Also reported: first-attempt versus final validity and correctness, latency,
and detector presence accuracy on the held-out sessions.

**Secondary (D5):** the `docs/JUDGE_RUBRIC.md` judge, from another model
family, blind to arm, calibrated against the owner's own ratings. It never
replaces the deterministic scores.

## Decision rules, fixed before the run

- **Safety first.** A camera arm with more authority failures than R is
  reported as harmful, whatever its accuracy.
- **Camera helps** if R+RGB beats R on the camera families with a
  family-bootstrap 95% interval above zero. **Depth adds** if R+RGBD beats
  R+RGB on location and conflict families in the same way.
- Otherwise the result is "no measurable difference at this size". With about
  60 turns, small effects will not be detectable; the report says so.
- **Tracked history** and **repair** are reported as descriptive contrasts,
  not separate claims.

## Size and cost

About 60 turns, as AR_SCOPE plans. Arms: R, R+RGB and R+RGBD with tracked
history, plus R+RGB and R+RGBD with the current frame only. That is 5 × 60 =
300 local model turns with Qwen3.5-9B. All runs are local, so there is no
hosted cost.

## Not in this comparison

- B06 stays sealed.
- The real-photo check of the detector and the vision-language model is a
  separate item.
- No hosted model, unless the owner approves one under the existing protocol.
- The images-to-VLM arm stays as it was unless D3 adds it.
- The app's prompt is unchanged.

## Owner decisions needed

| # | Decision | Recommendation |
|---|---|---|
| D1 | Run this as M2 (freeze 2, `m2` set) in the research runner, rather than in the app replay | Yes: existing guards, scoring and precedent |
| D2 | Include the tracked-history versus current-frame contrast | Yes: the queue asks for it; costs 120 more local turns |
| D3 | Models: Qwen3.5-9B only, or also `qwen3-vl-4b` and the deterministic baseline ("every model run so far" in AR_SCOPE) | 9B plus the deterministic baseline; add VL-4B only if images return as an arm |
| D4 | Held-out variety: new camera sessions only, or also authored scenario timing variants | New sessions plus two authored timing variants, with sources noted |
| D5 | Secondary judge: needs your ratings on about 20 development answers to calibrate | Defer the judge to M3, and report deterministic scores only for M2 |
| D6 | Viewpoint family ("to the left of the bridge from here") | Include 2–3 families; drop if the detector's box is too small to place left/right reliably on development |
| D7 | Effect rule: family-bootstrap 95% interval, authority failures as a hard gate | As written above |
