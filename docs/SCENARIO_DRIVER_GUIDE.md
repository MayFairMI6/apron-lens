# Replicating scenarios with the driver

This guide shows how to regenerate any AirfieldLens scenario exactly, confirm
it matches someone else's copy, run it, and add a new one. Everything here is
synthetic and authored. The driver has no operational authority.

For the design background, see [TRAINING_DRIVER.md](TRAINING_DRIVER.md). For
the full inventory and sources, see the
[scenario register](course/TRAINING_SCENARIO_REGISTER.md).

## What "the driver" is

The driver is ordinary Python code that turns an **exercise name** and a
**seed** into one complete world: aircraft, motion, reports with their event
and receipt times, questions and runway or stand reservations. No model is
involved. The same name and seed always give the same world.

| Part | File | Role |
|---|---|---|
| Scenario builders | `backend/lessons.py`, `fog_lesson.py`, `stand_clearance_lesson.py`, `runway_scenarios.py`, `fleet_scenarios.py`, `fleet_incident_variations.py`, `surface_queue_variations.py`, `turnaround_variations.py`, `bluebird_inbound.py` | Build the world from name and seed |
| Lesson driver | `backend/training_session.py` | Owns the live clock, checkpoints and releases |
| Replay driver | `backend/replay_session.py` | Read-only replay of the same world at any cutoff |
| Services | `backend/training.py` (lessons), `backend/replay.py` (controller replay) | Publish one driver on port 8767 |

All commands run from the repository root with `.venv-candidates/bin/python`.

## 1. Regenerate a scenario and check it is the same one

```sh
.venv-candidates/bin/python -m scripts.describe_scenario fleet_a380_go_around --seed 17
```

This prints the world hash, the aircraft, every report (happened → received,
source, flight) and the built-in questions. It loads no model and starts no
service. For seed 17 the A380 case prints:

```text
world sha256 f557c8a2f5895e9668575e11cb8cc1a21e0e98736e0ef18dd88c22bc5c2ade90
  01:24.0 → 01:25.0 · exercise-operations · TRN102 · F002: TRN102 remains stopped on Runway 09R.
  01:44.0 → 01:45.0 · exercise-operations · TRN101 · F003: TRN101 goes around because TRN102 has not vacated Runway 09R.
```

**Two copies are the same scenario when the hash matches.** The hash covers
aircraft, motion samples, reports, reservations and provenance. It leaves out
only the per-run scenario ID.

List every exercise with its hash:

```sh
.venv-candidates/bin/python -m scripts.describe_scenario --all            # seed 17
.venv-candidates/bin/python -m scripts.describe_scenario --all --seed 3
```

Add `--json` to one exercise for the full reports, questions and reservations
in machine-readable form.

A different hash for the same name and seed means the builder code differs
(a different commit or a local edit). Compare `git rev-parse HEAD` and
`git status` first.

## 2. Exercise names

| Kind | Names | Run with |
|---|---|---|
| Practice lessons (210 s, three typed checkpoints) | `surface_conflict`, `late_arrival`, `late_baggage`, `fog_restrictions`, `stand_clearance` | `--mode lesson` |
| Runway and water incidents | `rejected_takeoff`, `occupied_runway_go_around`, `runway_incursion`, `water_landing`, `fog_visibility` | `--mode demo` or `continuous` |
| Fleet cases | `fleet_a320_birds`, `fleet_b737_rejected_takeoff`, `fleet_b787_priority_landing`, `fleet_a380_go_around` | `--mode demo` or `continuous`; also the replay |
| Fleet variations | `fleet_b737_single_engine_return`, `fleet_a320_wildlife_return` | `--mode demo` or `continuous` |
| Surface and queue | `apron_route_obstruction`, `connector_road_closure`, `weather_runway_queues` | `--mode demo` or `continuous` |
| Turnaround | `debris_route_reopening`, `winter_surface_handover`, `fuel_service_interruption` | `--mode demo` or `continuous` |
| Inbound handoff | `fleet_b787_bluebird_handoff` | `--mode demo` or `continuous`; also the replay |

The seed changes authored timing by a few seconds and, in the queue case, the
demand. It never changes which reports exist or their order of meaning. Tests
cover seeds 0–19.

## 3. Run a scenario

Only one service may use port 8767, and only one process may hold the model.

**Controller replay (read-only, any cutoff):**

```sh
.venv-candidates/bin/python -m backend.replay --exercise fleet_a380_go_around --seed 17 --port 8767
```

Replay accepts the four fleet cases and `fleet_b787_bluebird_handoff`.

**Lesson or incident on the live clock:**

```sh
.venv-candidates/bin/python -m backend.training --exercise stand_clearance --mode lesson --seed 17
.venv-candidates/bin/python -m backend.training --exercise fleet_b737_single_engine_return --mode demo --seed 17
.venv-candidates/bin/python -m backend.training --exercise weather_runway_queues --mode continuous --seed 17
```

`lesson` pauses at three checkpoints. `continuous` runs at normal speed.
`demo` runs 30× through quiet stretches and 1× around questions and movement.
Normal and accelerated runs expose the same reports at the same source times;
`tests/test_surface_queue_variations.py` checks this over 20 seeds.

Wait for `REPLAY_READY` or `TRAINING_READY` (the model loads first, a few
minutes). Then point the Simulator app at the service and launch it:

```sh
python3 scripts/configure_ios_assistant.py --port 8767 <SIMULATOR_UUID>
xcrun simctl launch <SIMULATOR_UUID> edu.airfieldresearch.apronlens.simulator
```

Stop the service with Ctrl-C before starting another.

## 4. Reproduce a specific moment without the app

The replay driver can be used directly from Python or over HTTP. Neither needs
the model unless you ask a question.

```python
from backend.replay_session import ReplaySession

replay = ReplaySession(17, 'fleet_a380_go_around')
view = replay.action(dict(actionId='a1', runId=replay.run_id, viewRevision=0,
                          action='seek', cutoff=105))
print(replay.scenario_hash)
print([r['id'] for r in view['reports']])        # ['F001', 'F002', 'F003']
print(replay.changes('A1', 85, 105))             # ['F003:movement_condition']
```

Useful actions: `seek` (with `cutoff`), `jump` (with `markerId` from
`view['timeline']`), `select` (with `aircraftId`), `play`, `pause`, `note`
(with `text`). Each needs a fresh `actionId`, the `runId` and the current
`viewRevision`. A report is included exactly when its receipt time is at or
before the cutoff.

Over HTTP the same calls are `GET /replay`, `POST /replay/action` and
`POST /replay/question`, with the bearer token from
`work/qwen-server-token.txt`. `experiments/checkpoint2_scenarios/replay_http.py`
is a complete worked example.

## 5. Reproduce the recorded checks

| What | Command | Needs the model |
|---|---|---|
| All driver and replay tests | `.venv-candidates/bin/python -m unittest discover -s tests` | No |
| Replay rules only | `.venv-candidates/bin/python -m unittest tests.test_replay_session` | No |
| First question of every incident case | `.venv-candidates/bin/python -m experiments.checkpoint2_scenarios.run work/<new>.jsonl` | Yes |
| 787 handoff development cases | `.venv-candidates/bin/python -m experiments.bluebird_handoff.handoff_answers work/<new>.jsonl` | Yes |
| Replay over HTTP (start the A380 replay service first) | `.venv-candidates/bin/python -m experiments.checkpoint2_scenarios.replay_http work/<new>.jsonl` | Yes |

Model runs refuse to overwrite an existing output file, so give each run a new
name. Model answers can vary between runs even on one machine; the world and
its reports do not.

## 6. Add or change a scenario

1. **Write a builder** `build_x(seed, exercise)` returning
   `(world, reservations, probes)`. Copy the structure of
   `backend/fleet_scenarios.py`. Use `random.Random(seed)` for any variation so
   the result is repeatable.
2. **Give every report both times.** Each event needs `eventTime`,
   `receiptTime` (never earlier than the event), `source`, `aircraftId`,
   `flightInstance`, a `message` and typed `facts`. Use `supersedes` when a
   report replaces an earlier one for the same aircraft and property. Allowed
   properties are in `backend/evidence.py` (`FIELDS`).
3. **Keep movement, reports and authority separate.** Motion is rendering
   input. A release, clearance or reopening exists only when a report says so;
   state what stays unconfirmed in a report of its own.
4. **Register it** in `backend/training_session.py` (the exercise tuples, title
   and objective), and in `REPLAY_CASES` in `backend/replay_session.py` if it
   should be replayable.
5. **Test it** the way the existing cases are tested: identical output for the
   same seed, `validate_scenario(world)` passing, strictly increasing waypoint
   times, every built-in question having at least one received report at its
   time, and matched reports between `demo` and `continuous`.
6. **Record the hash** from `scripts.describe_scenario` in the ledger entry
   that introduces the case.

Limits the app enforces: at most four drawn aircraft (hidden, observation-only
contacts do not count), aircraft types from the fleet asset record, and
waypoints within the scenario duration. New scenery or geometry follows the
review workflow in `AGENTS.md`.
