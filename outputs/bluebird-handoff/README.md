# 787-8 inbound handoff offline comparison

The authored 787-8 priority-landing replay is the baseline. The paired arm adds
an inbound observation history from BluebirdATC 0.4.0, I-Sector Two Aircraft,
descender configuration, seed 17. AIR0 is mapped explicitly to the exercise
flight TRN101. AIR1 is a separate synthetic track. Bluebird source time runs
from 6 through 66 seconds. The comparison maps those times to −90 through −30
seconds on its own clock, then starts the unchanged airport replay at zero.
The 30-second gap is authored. Latitudes, longitudes and pressure flight levels
are retained as source observations. The trace represents synthetic en-route
airspace, with no interpolated approach across the gap.

Eleven paired frames produced 22 observations. Two exports in separate runs
matched byte for byte. At eight cutoffs the comparison excluded future samples,
preserved each track's identity and reported the age of the last observation.
Airport evidence selected by the deterministic baseline matched at all four
airport cutoffs. That includes the hydraulic concern with uncertain diagnosis,
priority authorisation, inspection hold, and unconfirmed runway release.

This result verifies the offline data and evidence comparison. Native Simulator
presentation, route-change scenarios, and model answers remain unverified.

## Reproduce

Use a separate Python 3.12 environment for the export and install the pinned
[export environment](export-environment.txt). From the repository root, run
the first command with that environment and the second with the normal AirfieldLens
backend environment.

```sh
python -m experiments.bluebird_handoff.replay export work/bluebird-trace.json
python -m experiments.bluebird_handoff.replay compare work/bluebird-trace.json --report work/bluebird-comparison.json
```

See [the trace](trace.json) and [paired results](comparison.json). The upstream
code stays in the dedicated environment. The source package and the scenario are
documented in the [AGPL-3.0 BluebirdATC release](https://github.com/project-bluebird/BluebirdATC/releases/tag/v0.4.0)
and the [pinned scenario source](https://github.com/project-bluebird/BluebirdATC/blob/v0.4.0/bluebird-dt/bluebird_dt/scenario_manager/two_aircraft.py).
