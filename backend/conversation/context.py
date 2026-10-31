"""Flight-scoped evidence snapshots for the conversational path.

Uses the frozen deterministic functions in backend.evidence, but scopes by the
explicitly requested (aircraft, flight instance) pair rather than the single
flightInstance that build_context reads from the aircraft record.
"""
import hashlib
import json
import math

from backend.evidence import classify, received_facts, validate_scenario
from backend.conversation.identity import resolve_flight, validate_rotations


def snapshot(data, aircraft_id, flight_instance, cutoff):
    """Immutable view of evidence received at or before `cutoff` for one flight."""
    if not isinstance(cutoff, (int, float)) or not math.isfinite(cutoff) or not 0 <= cutoff <= data['duration']:
        raise ValueError('Cutoff outside scenario')
    validate_scenario(data)
    validate_rotations(data)
    resolve_flight(data, aircraft_id, flight_instance)
    scoped = [f for f in received_facts(data, cutoff)
              if f['aircraftId'] == aircraft_id and f['flightInstance'] == flight_instance]
    facts = classify(scoped, cutoff)
    digest = hashlib.sha256(json.dumps(
        [(f['fact_id'], f['value'], f['status']) for f in facts], sort_keys=True).encode()).hexdigest()
    return dict(scenarioId=data['scenarioId'], aircraftId=aircraft_id, flightInstance=flight_instance,
                cutoff=cutoff, facts=facts, factsById={f['fact_id']: f for f in facts},
                evidenceDigest=digest)


def receipt_times(data):
    """Event ID -> receipt time, used to mask memory that cites later evidence."""
    return {e['id']: e['receiptTime'] for e in data['events']}


def changed_facts(previous, current):
    """Fact IDs that are new or whose status changed between two snapshots of one flight."""
    if (previous['aircraftId'], previous['flightInstance']) != (current['aircraftId'], current['flightInstance']):
        raise ValueError('Snapshots refer to different flights')
    before = {f['fact_id']: f['status'] for f in previous['facts']}
    return sorted(f['fact_id'] for f in current['facts'] if before.get(f['fact_id']) != f['status'])
