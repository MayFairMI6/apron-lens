"""SUBSTANTIVE: paired source and identity checks for the 787 inbound handoff."""
import argparse
import json
from importlib.metadata import version
from pathlib import Path

BLUEBIRD_VERSION = "0.4.0"
BLUEBIRD_COMMIT = "d25de6ced993f0e3e1b0a9e07d3b57d9fdd38959"
EXERCISE = "fleet_b787_priority_landing"
SEED = 17
GAP_SECONDS = 30
FLIGHTS = {"AIR0": "TRN101", "AIR1": "BLUEBIRD-TRAFFIC"}


def export_trace():
    from bluebird_dt.scenario_manager.two_aircraft import TwoAircraft

    if version("bluebird-dt") != BLUEBIRD_VERSION:
        raise RuntimeError(f"Use bluebird-dt=={BLUEBIRD_VERSION}")
    simulator = TwoAircraft.setup(
        "I-Sector", scenario_type="descender", random_seed=SEED,
        use_wind=False, use_forecast=False, attach_context_to_logger=False,
        save_log_to_file=False, save_csv=False, autosave_interval=None,
    )
    frames = []
    for index in range(11):
        environment = simulator.manager.environment
        frames.append({
            "sourceSeconds": environment.time,
            "aircraft": [
                {
                    "callsign": plane.callsign,
                    "latitudeDegrees": plane.lat,
                    "longitudeDegrees": plane.lon,
                    "flightLevel": plane.fl,
                }
                for plane in sorted(environment.aircraft.values(), key=lambda plane: plane.callsign)
            ],
        })
        if index < 10:
            simulator.evolve(6)
    return {
        "source": "BluebirdATC public synthetic I-Sector, Two Aircraft/descender",
        "version": BLUEBIRD_VERSION, "commit": BLUEBIRD_COMMIT,
        "seed": SEED, "frames": frames,
    }


def inbound_observations(trace):
    frames = trace["frames"]
    times = [frame["sourceSeconds"] for frame in frames]
    if len(times) != 11 or any(b - a != 6 for a, b in zip(times, times[1:])):
        raise ValueError("Expected eleven consecutive six-second samples")
    observations = []
    for frame in frames:
        aircraft = frame["aircraft"]
        if sorted(plane["callsign"] for plane in aircraft) != sorted(FLIGHTS):
            raise ValueError("The pinned scenario must preserve both source identities")
        for plane in aircraft:
            # Align only the study clocks. Source coordinates and pressure levels
            # remain as observed; there is no inferred path across the handoff.
            observations.append({
                **plane, "flightInstance": FLIGHTS[plane["callsign"]],
                "sourceSeconds": frame["sourceSeconds"],
                "replaySeconds": frame["sourceSeconds"] - times[-1] - GAP_SECONDS,
                "source": "bluebird-synthetic-observation",
            })
    return observations


def latest_observation(observations, flight, cutoff):
    return next((
        item for item in reversed(observations)
        if item["flightInstance"] == flight and item["replaySeconds"] <= cutoff
    ), None)


def compare(trace):
    from backend.evidence import build_context, expected_selection, validate_scenario
    from backend.fleet_scenarios import build_fleet

    world, _, _ = build_fleet(SEED, EXERCISE)
    validate_scenario(world)
    inbound = inbound_observations(trace)
    # Both arms use the same airport replay and production evidence selector.
    # Bluebird samples are available to the handoff query only.
    rows = []
    for name, cutoff in [
        ("before first sample", -91), ("mid-trace", -60),
        ("last available sample", -30), ("handoff gap", -1),
        ("first airport report", 0),
        *((cue["id"], cue["at"]) for cue in world["demoQuestions"]),
    ]:
        airport = expected_selection(build_context(world, "A1", cutoff)) if cutoff >= 0 else None
        baseline_observation = latest_observation([], "TRN101", cutoff)
        augmented_observation = latest_observation(inbound, "TRN101", cutoff)
        other = latest_observation(inbound, "BLUEBIRD-TRAFFIC", cutoff)
        rows.append({
            "check": name, "cutoffSeconds": cutoff,
            "authoredOnly": {"observation": baseline_observation, "airportSelection": airport},
            "withBluebird": {
                "observation": augmented_observation,
                "sampleAgeSeconds": cutoff - augmented_observation["replaySeconds"] if augmented_observation else None,
                "airportSelection": expected_selection(build_context(world, "A1", cutoff)) if cutoff >= 0 else None,
            },
            "otherTrafficCallsign": other["callsign"] if other else None,
        })

    airport_equal = all(row["authoredOnly"]["airportSelection"] == row["withBluebird"]["airportSelection"] for row in rows)
    identity_ok = all(
        row["withBluebird"]["observation"]["callsign"] == "AIR0"
        and row["otherTrafficCallsign"] == "AIR1"
        for row in rows[1:]
    )
    cutoff_ok = rows[0]["withBluebird"]["observation"] is None and all(
        row["withBluebird"]["sampleAgeSeconds"] >= 0 for row in rows[1:]
    )
    gap_ok = rows[3]["withBluebird"]["sampleAgeSeconds"] == 29 and rows[3]["withBluebird"]["airportSelection"] is None
    if not all((airport_equal, identity_ok, cutoff_ok, gap_ok)):
        raise RuntimeError("Bluebird replay comparison failed")
    return {
        "exercise": EXERCISE, "seed": SEED,
        "gapSeconds": GAP_SECONDS, "observationCount": len(inbound),
        "checks": {
            "airportEvidenceIdentical": airport_equal, "identitySeparated": identity_ok,
            "futureObservationsExcluded": cutoff_ok, "gapPreserved": gap_ok,
        },
        "pairedCutoffs": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "compare"))
    parser.add_argument("trace", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.mode == "export":
        args.trace.write_text(json.dumps(export_trace(), indent=2, allow_nan=False) + "\n")
        return
    report = json.dumps(compare(json.loads(args.trace.read_text())), indent=2, allow_nan=False) + "\n"
    if args.report:
        args.report.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
