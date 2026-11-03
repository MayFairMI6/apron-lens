# Four aircraft, four changing situations

The external driver runs four separate one-hour scenarios. Guided demonstration mode accelerates quiet periods and slows for aircraft movement, assistant questions and reading. The learner does not choose a model or a playback rate.

| Scenario | What unfolds | What to notice |
|---|---|---|
| Birds before departure | An Airbus A320 is held, birds disperse, an inspection arrives, and a separate release precedes departure. | Inspection completion alone does not establish permission to depart. |
| A rejected takeoff | A Boeing 737 begins its roll, the crew reports unreliable airspeed, and it stops on the runway. | The report identifies the concern; its cause and runway release remain unconfirmed. |
| A priority landing | A Boeing 787 arrives after a reported hydraulic concern, lands and stops for inspection. | A reported concern is not a confirmed diagnosis; landing does not establish recovery completion. |
| A runway-occupied go-around | An Airbus A380 approaches an occupied runway and climbs away. | The go-around is visible and reported; a future approach remains unconfirmed. |

These incidents are assigned to aircraft for variety. They do not represent manufacturer-specific failure rates. Three other aircraft provide size and traffic context in each scenario.

Run the driver from the repository using the existing model environment:

```sh
python -m backend.training --exercise fleet_a320_birds --mode demo --seed 17
```

Use `fleet_b737_rejected_takeoff`, `fleet_b787_priority_landing` or `fleet_a380_go_around` for the other cases. `--mode continuous` runs the source hour at normal speed. The four profiles are demonstrations; the existing four practice lessons retain their checkpoint flow. The app connects to the existing authenticated local service. Its model runs on the host computer, not on the phone.

The new model exteriors come from AMV Lab under CC BY 4.0, with custom landing gear and nominal aircraft dimensions. See `data/aircraft/amvlab/ATTRIBUTION.md` for original sources, changes and limitations. They are not manufacturer CAD.

Selected Heathrow 09R reference values inform the final approach and initial straight-ahead missed approach. See `docs/HEATHROW_PROCEDURE_REFERENCE.md` for the dated chart references and limits. Speeds, flare, incident timing and subsequent off-scene motion remain authored. No complete SID or operational clearance procedure is reproduced.

The presentation edit preserves the approved opening narration and shows selected significant features. The longer walkthrough retains more of the changing situations and report answers. Excerpts must remain identified as excerpts; neither edit implies an uninterrupted live run or narration throughout. Versions without voiceover are supplied separately. Previous recordings remain preserved.
