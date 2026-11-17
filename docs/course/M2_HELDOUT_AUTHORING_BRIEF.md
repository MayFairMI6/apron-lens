# Brief for the `m2` held-out author

**Status: DRAFT. Do not hand this to an agent until the owner has settled
D1–D7 in `CAMERA_EVIDENCE_COMPARISON.md` and the format additions below exist
in the code.**

This brief goes to a fresh agent with no access to this conversation. It
contains no development case, prompt or result.

## Your task

Write the `m2` held-out set for the camera evidence comparison: about 60 turns
in about 24 families, about controller questions on the Stand B exercise
(TRN103 waiting for Stand B while a fuel-transfer vehicle is removed).

Work only in `~/Documents/Codex/apronlens-heldout/m2/`. Write:

- `families.json` with `"split": "heldout"`, `"set": "m2"` and a `version`;
- `sessions/*.json`: the scripted camera paths, one per session;
- `scenarios/*.json` only if timing variants are approved (D4);
- `AUTHORING.md`: what you opened, how you wrote the set, and the counts.

## What you may open

- `docs/AR_SCOPE.md` (the turn fields and family types);
- `docs/course/CAMERA_EVIDENCE_COMPARISON.md` (this comparison; read the
  question families and data sections);
- `backend/evidence.py`, `backend/conversation/scoring.py`, and the
  `VISUAL_KINDS` block of `backend/conversation/observations.py` (formats only);
- `backend/stand_clearance_lesson.py` and `docs/SCENARIO_DRIVER_GUIDE.md`
  (the exercise's timeline);
- `backend/camera_evidence.py` (what an observation contains);
- `../m1/AUTHORING.md` and `../final/AUTHORING.md` (label policy).

## What you must not open

- `data/conversation_dev/`, any development family, and anything under
  `outputs/`;
- prompts, the validator, `backend/training_adapter.py` and
  `backend/conversation/turns.py`;
- the ledgers and decision logs;
- any model result or review note.

Do not run a model. You may run `scripts/check_heldout.py`, but do not read
its source.

## Rules

- Spread the turns across the family types in the comparison's table. Give at
  least 4 turns each to the authority control, conflict (camera versus report)
  and missing-evidence types. Give at least 6 to report-only controls on
  TRN101 and TRN102.
- **Cutoffs.** Put cutoffs both inside and outside the 88–100 s departure
  window, around 150 s (release received) and around 158 s (TRN103 moves).
- **Per-arm labels.** Where the right answer differs by arm (`reports`,
  `rgb`, `rgb_depth`), use `expectByArm`. Otherwise one `expect` applies to all.
- **Releases come from reports only.** A release or readiness answer must
  depend on reports alone. No label may let a camera observation establish a
  release.
- **"Not detected" is not "gone".** It never supports an answer that the
  vehicle has left.
- **Look-aways** follow the m1 rules: every look-away must add information;
  `mustCite` and `citeOnly` apply as in m1.
- **Sessions.** Each session gives its look-away windows, tracking-loss windows
  and camera positions within the ranges stated in the comparison. Nothing in a
  session may depend on where the detector succeeds or fails.
- **Self-check.** Write a local checker, seed errors into a copy of the set,
  and confirm that the checker catches them.

## Finishing

Report the counts and any rule you could not meet. The set is reviewed
before its hashes are recorded. After that it is never edited.
