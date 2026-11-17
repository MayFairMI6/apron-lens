"""SUBSTANTIVE: verify bounded, already-extracted claims at a scenario cutoff."""
from dataclasses import dataclass
from math import isfinite

from backend.evidence import FIELDS, classify, received_facts


@dataclass(frozen=True)
class Claim:
    run_id: str
    aircraft_id: str
    flight: str
    property: str
    value: str
    source_ids: tuple[str, ...]
    historical: bool = False


@dataclass(frozen=True)
class ClaimCheck:
    status: str
    rule: str
    eligible_source_ids: tuple[str, ...] = ()


def check_claim(world, cutoff, claim, camera_observations=()):
    """Evaluate exact typed values. Language interpretation belongs upstream."""
    if not isfinite(cutoff) or not 0 <= cutoff <= world["duration"]:
        raise ValueError("Cutoff outside scenario")
    if claim.run_id != world["scenarioId"]:
        return ClaimCheck("unknown", "wrong_run")
    aircraft = next((plane for plane in world["aircraft"] if plane["id"] == claim.aircraft_id), None)
    if aircraft is None or aircraft["flightInstance"] != claim.flight:
        return ClaimCheck("unknown", "wrong_flight")
    if claim.property == "visible_vehicle":
        return _check_observation(claim, cutoff, camera_observations)
    if claim.property not in FIELDS:
        raise ValueError("Unsupported claim property")
    facts = classify([
        fact for fact in received_facts(world, cutoff)
        if fact["aircraftId"] == claim.aircraft_id
        and fact["flightInstance"] == claim.flight
        and fact["property"] == claim.property
    ], cutoff)
    statuses = {"current", "conflicting"}
    if claim.historical:
        statuses |= {"superseded", "expired"}
    eligible = [fact for fact in facts if fact["status"] in statuses]
    ids = tuple(dict.fromkeys(fact["event_id"] for fact in eligible))
    if not claim.source_ids or any(source_id not in ids for source_id in claim.source_ids):
        return ClaimCheck("unknown", "missing_or_ineligible_citation", ids)
    if not claim.historical and any(fact["status"] == "conflicting" for fact in eligible):
        return ClaimCheck("conflicting", "active_reports_disagree", ids)
    cited = [fact for fact in eligible if fact["event_id"] in claim.source_ids]
    if any(fact["value"] == claim.value for fact in cited):
        return ClaimCheck("supported", "cited_report_matches", ids)
    if claim.historical:
        return ClaimCheck("unknown", "cited_history_does_not_match", ids)
    if any(fact["value"] == claim.value for fact in eligible):
        return ClaimCheck("unknown", "claim_not_supported_by_its_citation", ids)
    return ClaimCheck("contradicted", "current_report_disagrees", ids)


def _check_observation(claim, cutoff, camera_observations):
    # Observation age is a statement about the exact sampled moment. A stale
    # frame may support historical presence but never current visibility.
    for item in camera_observations:
        if (item["captureId"] not in claim.source_ids
                or item["runId"] != claim.run_id
                or item["aircraftId"] != claim.aircraft_id
                or item["flightInstance"] != claim.flight
                or not 0 <= item["sourceTime"] <= cutoff
                or (not claim.historical and item["sourceTime"] != cutoff)
                or not item["trackingValid"]):
            continue
        if item.get("visibleVehicle") == claim.value and claim.value == "present":
            return ClaimCheck("supported", "camera_observed_presence", (item["captureId"],))
    return ClaimCheck("unknown", "no_matching_camera_observation")
