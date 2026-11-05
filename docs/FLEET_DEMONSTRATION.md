# Four aircraft, four changing situations

The external driver runs four separate one-hour scenarios. Guided demonstration mode accelerates quiet periods and slows for aircraft movement, assistant questions and reading. The learner does not choose a model or a playback rate.

| Scenario | What unfolds | What to notice |
|---|---|---|
| Birds before departure | An Airbus A320 is held, birds disperse, an inspection arrives, and a separate release precedes departure. | Inspection completion alone does not establish permission to depart. |
| A rejected takeoff | A Boeing 737 begins its roll, the crew reports unreliable airspeed, and it stops on the runway. | The report identifies the concern; its cause and runway release remain unconfirmed. |
| A priority landing | A Boeing 787 arrives after a reported hydraulic concern, lands and stops for inspection. | A reported concern is not a confirmed diagnosis; landing does not establish recovery completion. |
| A runway-occupied go-around | An Airbus A380 approaches an occupied runway and climbs away. | The go-around is visible and reported; a future approach remains unconfirmed. |

These incidents are assigned to aircraft for variety. They do not represent manufacturer-specific failure rates. Three other aircraft provide size and traffic context in each scenario.

Use the `codex/checkpoint1-controller-training` branch in PR #22; the default branch does not necessarily contain this preview. A teammate who forks the repository should select that branch or fetch it from the source repository. The source includes the external driver and free aircraft assets; model weights, local connection credentials and a signed TestFlight build are not bundled.

Run the driver from the repository using the existing model environment:

```sh
python -m backend.training --exercise fleet_a320_birds --mode demo --seed 17
```

Use `fleet_b737_rejected_takeoff`, `fleet_b787_priority_landing` or `fleet_a380_go_around` for the other cases. `--mode continuous` runs the source hour at normal speed. The four profiles are demonstrations; the existing four practice lessons retain their checkpoint flow. The app connects to the existing authenticated local service. Its model runs on the host computer, not on the phone.

The new model exteriors come from AMV Lab under CC BY 4.0, with custom landing gear and nominal aircraft dimensions. See `data/aircraft/amvlab/ATTRIBUTION.md` for original sources, changes and limitations. They are not manufacturer CAD.

Selected Heathrow 09R reference values inform the final approach and initial straight-ahead missed approach. See `docs/HEATHROW_PROCEDURE_REFERENCE.md` for the dated chart references and limits. Speeds, flare, incident timing and subsequent off-scene motion remain authored. No complete SID or operational clearance procedure is reproduced.

The presentation edit preserves the approved opening narration and shows selected significant features. The longer walkthrough retains more of the changing situations and report answers. Excerpts must remain identified as excerpts; neither edit implies an uninterrupted live run or narration throughout. Versions without voiceover are supplied separately. Previous recordings remain preserved.

Suggested narration for the new aircraft section:

“Here, the same airport supports four different situations using Airbus and Boeing aircraft of different sizes. The A320 waits for birds to disperse, but inspection completion still does not mean it has been released. The 737 rejects takeoff after a reported airspeed concern and remains on the runway. The 787 makes a priority landing, while the A380 goes around because the runway is occupied. In each case, the assistant answers from the reports available at that moment. We can distinguish what has happened, what has changed, and what still needs confirmation. The motion makes those reports easier to follow; it is an authored training illustration. The next checkpoints will test whether visual evidence improves answers and evaluate the integrated experience.”

This text is preparation guidance, not additional recorded narration. Keep the approved opening audio intact. No internal presenter labels should appear in the finished video.


Delivered local edits: `AirfieldLens-presentation.mp4` (8:06.4), `AirfieldLens-presentation-without-voiceover.mp4`, `AirfieldLens-walkthrough.mp4` (40:02.1), and `AirfieldLens-walkthrough-without-voiceover.mp4`. Both silent copies contain identical compressed video to their narrated counterparts and zero audio tracks. The approved opening's compressed audio is unchanged. Full source recordings and the failed A380 first attempt remain archived separately.

The current functional gate passed four complete source-hour runs and twelve nonempty actual assistant answers after the cue-spacing repair. This does not remove the known occasional empty-answer limitation, establish a learning benefit, or satisfy the separate physical-phone and team-participation requirements.
