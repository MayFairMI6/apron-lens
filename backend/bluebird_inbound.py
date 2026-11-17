"""SUBSTANTIVE: join source-attributed en-route observations to the 787 lesson clock."""
import json
from pathlib import Path

from backend.fleet_scenarios import build_fleet

BLUEBIRD_787 = "fleet_b787_bluebird_handoff"
TITLE = "Inbound handoff and priority landing"
OBJECTIVE = "Follow the right aircraft across the inbound handoff and check which airport updates are available."
HANDOFF = 90
TRACE = Path(__file__).resolve().parents[1] / "outputs" / "bluebird-handoff" / "trace.json"


def build_bluebird_inbound(seed, _exercise):
    world, reservations, probes = build_fleet(seed, "fleet_b787_priority_landing")
    trace = json.loads(TRACE.read_text())
    if trace["version"] != "0.4.0" or trace["seed"] != 17:
        raise ValueError("Unexpected Bluebird source identity")
    frames = trace["frames"]
    origin = frames[0]["sourceSeconds"]
    if frames[-1]["sourceSeconds"] - origin != HANDOFF - 30:
        raise ValueError("Bluebird trace must leave a 30-second handoff gap")
    world["scenarioId"] = f"INBOUND-{BLUEBIRD_787}-{seed}"
    world["trainingProfile"] = BLUEBIRD_787
    world["trainingObjective"] = OBJECTIVE
    provenance = world["provenance"]
    provenance["sources"].append("https://github.com/project-bluebird/BluebirdATC/releases/tag/v0.4.0")
    provenance["limitations"] += (
        " The inbound contacts are synthetic Bluebird sector observations. "
        "A 30-second gap precedes the authored airport replay. No trajectory "
        "joins the sector coordinates to the airport approach."
    )

    for event in world["events"]:
        event["eventTime"] += HANDOFF
        event["receiptTime"] += HANDOFF
    for aircraft in world["aircraft"]:
        for point in aircraft["waypoints"]:
            point["t"] = min(world["duration"], point["t"] + HANDOFF)
        for phase in aircraft["phases"]:
            phase["t"] += HANDOFF
    target = world["aircraft"][0]
    target["visibleFrom"] = HANDOFF
    target["phases"][:0] = [
        dict(t=0, id="inbound_sector", label="Inbound sector observation"),
        dict(t=60, id="handoff_gap", label="Waiting for airport update"),
    ]
    # The second contact is a separate identity slot, with no airport aircraft
    # or authored reports. It is available only as a scoped observation.
    world["aircraft"].append(dict(
        id="A5", flightInstance="BLUEBIRD-TRAFFIC", hidden=True,
        waypoints=[dict(t=t, x=0, z=0) for t in (0, world["duration"])],
    ))
    for collection in (world["runwayReservations"], world["flightTeachingWindows"], world["flightShowcases"]):
        for interval in collection:
            interval["start"] += HANDOFF
            interval["end"] = min(world["duration"], interval["end"] + HANDOFF)
    for cue in world["demoQuestions"]:
        cue["at"] += HANDOFF
    world["demoQuestions"].insert(0, dict(
        id="inbound-gap", at=75, aircraftId="A1",
        assistantQuestion="What is the latest inbound observation for TRN101, and has an airport landing release been received?",
    ))
    world["flightTeachingWindows"].insert(0, dict(start=0, end=HANDOFF))
    contacts = {"AIR0": ("A1", "TRN101"), "AIR1": ("A5", "BLUEBIRD-TRAFFIC")}
    for idx, frame in enumerate(frames):
        seen = set()
        for row in frame["aircraft"]:
            callsign = row["callsign"]
            if callsign in seen or callsign not in contacts:
                raise ValueError("Bluebird source identities changed")
            seen.add(callsign)
            aircraft_id, flight = contacts[callsign]
            t = frame["sourceSeconds"] - origin
            key = f"BB-{callsign}-{idx}"
            prop = "trajectory_checkpoint"
            value = f"Synthetic inbound sector observation for {flight}, flight level {row['flightLevel']:g}, source time {frame['sourceSeconds']:g} s"
            fact = dict(property=prop, value=value)
            if idx:
                fact["supersedes"] = [f"BB-{callsign}-{idx-1}:{prop}"]
            world["events"].append(dict(
                id=key, aircraftId=aircraft_id, flightInstance=flight,
                source="bluebird-synthetic-observation", eventTime=t, receiptTime=t,
                message=value, facts=[fact],
            ))
        if seen != set(contacts):
            raise ValueError("Missing paired Bluebird contact")
    world["events"].sort(key=lambda event: (event["receiptTime"], event["id"]))
    world["predictionBoundaries"] = sorted(
        {min(world["duration"], t + HANDOFF) for t in world["predictionBoundaries"]}
        | {event["receiptTime"] for event in world["events"]}
    )
    return world, world["runwayReservations"], probes
