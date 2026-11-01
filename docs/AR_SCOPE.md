# AR scope and milestones (from 1 November 2026)

ApronLens is an AR project. Its development results so far treated AR as a
pointer and a picture, and the picture added nothing measurable (ledger D-078).
From here, the research question is answered through three AR-specific
conditions, all measured inside the Unity simulation (physical device tests
stay out of scope, D-010):

1. **AR pointing.** The user selects or taps an aircraft in the AR view. This
   is compared with a text-only user, who names the aircraft, stand or flight
   in words.
2. **Tracking interruptions.** The user looks away and the board leaves the
   camera's view, while reports keep arriving. When tracking returns, the
   assistant must say what changed while the user wasn't looking.
3. **The user's viewpoint as evidence.** The evidence image is what the AR
   camera sees from where the user stands, not a crop of the whole scene.
   Props hidden from that viewpoint, or aircraft outside it, aren't visible.

## Milestones

Each milestone is complete in itself: it builds its part, freezes it, runs it
once on its own held-out set, and ends with a report in `outputs/`. Each
held-out set is used once, after its freeze, so earlier held-out results can't
shape later development.

| Milestone | Builds | Evaluates | Report |
|---|---|---|---|
| **M1. AR conversational context** | Held-out tooling (`scripts/check_heldout.py`, `HeldoutRender`, hashed loading); AR pointing (selection on vs text-only); tracking interruptions (`lastSeen`, a clock that runs while untracked) | Development families, then freeze 1 and the `m1` held-out set (about 60 turns) | `outputs/m1_ar_context/REPORT.md` |
| **M2. AR visual evidence** | User-viewpoint capture (`visual-capture-v3`); licensed realistic aircraft and ground-vehicle models (each asset approved by the user); a real-photo perception check on public-domain apron photos | Development families, then freeze 2 and the `m2` held-out set (about 60 turns) | `outputs/m2_ar_visual/REPORT.md` |
| **M3. Integrated evaluation** | The final freeze of the complete method | The `final` held-out set (about 200 turns, all conditions); the hosted comparison (cost approved by the user) | `outputs/m3_evaluation/REPORT.md` and the write-up |

## Held-out sets

Three sets, written outside the repository by an author who hasn't seen the
development families, the prompt or any result:
`~/Documents/Codex/apronlens-heldout/{m1,m2,final}/`, each with
`families.json`, `scenarios/*.json`, `renders.json` and `AUTHORING.md`.

- `families.json` has `"split": "heldout"`, a `version`, and `"set"`
  (`m1`, `m2` or `final`). Its record is `config/heldout-<set>.json`, written by
  `scripts/check_heldout.py --record` once the author has finished, and
  committed before the run.
- Each family has `type`, one of: `rotation-correction`, `ambiguous-reference`,
  `late-report`, `no-change`, `missing-evidence`, `conflicting-reports`,
  `superseded-report`, `visual-observation`, `scene-change`, `ar-pointing`,
  `tracking-interruption`, `viewpoint`, or `other:<name>`. Reports break down by
  type.
- **`m1`:** conversational AR. Every turn has `textOnly`. About half the
  families include a `lastSeen` turn. Images are optional.
- **`m2`:** visual AR. Every turn has an image and a `viewpoint`.
- **`final`:** every type. Every turn has `textOnly`; `lastSeen` and
  `viewpoint` are used where natural, and at least a third of the turns carry an
  image.

## Turn fields added for the AR conditions

All are optional unless a set requires them.

- **`textOnly`:** `{"question": "...", "expect": {...}}`. The question a user
  without AR pointing would ask for the same intent, naming the aircraft, stand
  or flight in words. The text-only condition sends this question with nothing
  selected. Its `expect` replaces the turn's `expect` when the right outcome
  differs; for example, when the words alone can't identify the aircraft, the
  right status is `clarify`. Without `expect`, the turn's `expect` applies.
- **`lastSeen`:** the replay time (seconds) when the board was last in the
  camera's view before this turn. The user looked away from `lastSeen` until
  the turn's `cutoff` while reports kept arriving. It must be below `cutoff`,
  and not below the previous turn's `cutoff` in the family. Label the changes
  the user should hear about with `mustCite` (and `explanationChanged` on a
  follow-up). A scenario with `lastSeen` turns sets
  `"clockWhileUntracked": "runs"`, so the Unity replay keeps running while the
  board is out of view (the default, `"pauses"`, is the Milestone 1 behaviour).
- **`viewpoint`** (M2; its exact coordinates are fixed in M2): the AR camera
  pose for the turn's image, as `{"position": [x, y, z], "lookAt": [x, y, z]}`
  in board metres, with y up. Observation labels describe what is visible from
  that pose; a prop outside the frame or hidden from that side is labelled
  `null`. Without it, the default overview pose is used.

## Conditions per run

`scripts/run_conversation_families.py` gains `--selection on|off` (AR pointing
vs text-only) and `--tracking on|off` (whether `lastSeen` is sent), next to
`--images on|off`. The full AR condition is selection on, tracking on and
images on; each ablation turns one of them off.
