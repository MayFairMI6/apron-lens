# ApronLens implementation docket

The presentation uses distinct scenarios with time scaling within each. The
scenario clock describes simulated elapsed time; narration length and video
length are separate. The external driver owns movement, reports and visual
conditions. The original Checkpoint 1 core remains three scored lessons.

| Milestone | Work | Acceptance condition | Current position |
|---|---|---|---|
| Immediate Checkpoint 1 extension | Remove the in-app 3–5-minute estimate and label the scenario clock explicitly. Return the viewer to Guided demonstration. | Native briefing has no fixed wall-time estimate; guided clock and 30× indicator remain visible. | Implemented; native build, 231 backend tests, 69 Unity checks and recorded visual checks passed. |
| Immediate Checkpoint 1 extension | Separate rain, snowfall and late-afternoon → dusk → night settings. Conditions and particles follow external source time, including pause/reconnection. Default clear daytime remains compatible. | Native rain/snow/dusk captures; timing/repeatability and legacy-input checks; readable interface in both orientations. | Implemented; native build, 231 backend tests, 69 Unity checks and recorded visual checks passed. |
| Immediate presentation update | Keep Person 1 audio, add Person 2 weather cues and a labelled environment supplement. Preserve previous recordings and source cutoffs. | Current Drive documents, video provenance, handoff and GitHub PR agree on implemented features. | Native clips captured and incorporated in the 16:18 edit; Person 1 audio preserved. Updated scripts, acceptance and shared handoff accompany the video. |
| Checkpoint 2 | Operational weather lessons: reported visibility, surface-condition changes, snow clearance/de-icing dependencies and restrictions. Reports must establish operational facts; falling snow or darker lighting alone does not establish braking action, readiness or clearance. | Distinct learning tasks, explicit available evidence, source-supported unknowns and feedback. Reuse the shared driver. | Planned; requires scenario/report design and source review. |
| Checkpoint 2 | Visual-evidence study under rain/snow/light changes; compare with and without images and separate perception from report reasoning. Add a distinct turnaround handover task. | Questions that require visual evidence, frozen evaluation contract, perception-error analysis and no claims inferred from validator acceptance alone. | Planned. |
| Checkpoint 2, only if required by a learning task | Full 24-hour solar cycle and longer operating-day profiles, including sunrise. | One explicit time model, traffic/report schedules appropriate to the longer duration, and no accelerated sky clock disguised as physical elapsed time. | Not implemented. Current dusk is a one-hour interval, not a complete day. |
| Checkpoint 3 | Integrated evaluation across conditions, speeds and orientations; latency, reconnection, failures and learning-flow usability, including phone versus larger-screen use with representative learners. | Repeatable results, condition-specific failure analysis, clear device/runtime limits and final contribution accounting. | Planned. |

The immediate environment work is visual presentation, not a weather model or a
change to aircraft performance. Rain does not currently create a braking penalty;
snow does not accumulate on the pavement or implement de-icing; dusk does not
establish operational visibility. Weather is not inserted as an assistant report.
The aircraft keep their existing reserved paths and report-grounded answers.

The driver supports a one-hour source timeline in guided/full-hour profiles and
a separate short scored-practice profile. Removing a UI estimate does not change
those profile durations. Guided demonstration accelerates quiet periods to 30×
and uses 1× at teaching moments and during pending answers. The short practice
profile still ends at 210 seconds of source time, with pauses for answers/review.

The preserved 13:25 video with Person 1 narration predates the weather extension and uses fixed daytime. The current 16:18 edit appends labelled rain, snow and dusk/night clips in Person 2’s section; do not claim weather was in an older recording. The earlier accident and M1 research
records remain unchanged. Physical-phone verification and Person 2 narration
remain outstanding submission tasks.
