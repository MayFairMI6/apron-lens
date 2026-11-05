# Checkpoint 1: achievement and reflection

Historical draft, not ready for submission. The current controller-focused
simulator experience is documented in `CHECKPOINT1_CURRENT.md`; the editor views
below describe an earlier build. Team meeting, coordination and contribution
statements below need confirmation from the actual members. They are not verified
by source code or a recording. Match the final reflection to the assignment's
actual fields and length before submitting. Speaking assignments in the video
must not be treated as development authorship.

## What we achieved

ApronLens is a conversational AR assistant for airport stand coordination. In a
simulated AR session (Unity with AR Foundation's XR Simulation), the camera
sees a full-scale fictional apron, and the app overlays a replay of aircraft,
ground vehicles and arriving operational reports.

- **Pointing in AR:** the user selects an aircraft by tapping it in the camera
  view, and asks about it.
- **Corrections:** the user can correct the assistant ("I mean its next
  rotation"), and the correction carries over to later questions.
- **Looking away:** when the user turns away and back, a "While you were away"
  card lists the reports that arrived meanwhile.
- **Checked answers:** a local vision-language model (Qwen) answers. Every claim
  is checked against a received report, and anything unsupported is withheld or
  labelled.
- **First evaluation:** 40 questions in 17 conversations, written separately
  from the system's development.
  - AR pointing measurably helps: one model drops 15 points without it.
  - The best model answers 60% correctly, against 40% for a rule-based
    baseline.
  - Tracking information given to the model did not help, so the app now
    computes the change card itself.

## Plan for the remaining checkpoints

- **Checkpoint 2, AR visual evidence:**
  - what the camera itself sees as evidence;
  - realistic aircraft and vehicle models;
  - a computer-vision detector whose detections become checked reports;
  - references that depend on where the user stands;
  - an AI judge for answer quality.
- **Checkpoint 3, integrated evaluation:** the complete system on a
  200-question test set, a comparison with a hosted model, and the final report.

## Reflection

**Coordination.**
- Work is organised into milestones with a fixed scope, their own evaluation
  set and a report, and progress is tracked against them.
- Went well: each milestone ended in a concrete result.
- To improve: some scope changes arrived mid-milestone (AR becoming central,
  the move to fully simulated world-scale AR). That needed rework that earlier
  scoping would have avoided.

**Meetings.**
- Progress reviews happen at planned checkpoints: after development results,
  after each evaluation run, and before each method freeze.
- Went well: each review had one concrete question, such as "does this
  condition show any effect yet?", which kept it short.
- To improve: write the agenda before long runs start, so each review is ready
  when the results arrive.

**Decision-making.**
- Decisions go into a shared decision log (what, why, where).
- The method is frozen and approved before each evaluation, so results can't
  drift towards what was hoped for.
- Went well: when a result contradicted the plan (tracking information didn't
  help), the plan changed openly at the next checkpoint.
- To improve: settle scope questions, such as how the demo is recorded and the
  AR setup, earlier in each checkpoint.
