"""Aircraft versus flight-instance (rotation) identity.

An aircraft may fly several rotations. Scenarios may declare
    "aircraft": [{"id": "A2", "rotations": [
        {"flightInstance": "F2-R1", "from": 0, "until": 60},
        {"flightInstance": "F2-R2", "from": 60}]}]
Legacy scenarios with a single "flightInstance" are read as one open rotation,
so existing data and the frozen /reason path are unaffected.

The binding of rotations to aircraft comes only from scenario data. A user
correction such as "its next rotation" selects among these rotations; it never
creates or rewrites a binding.
"""
import math


def rotations_for(data, aircraft_id):
    aircraft = next((a for a in data['aircraft'] if a['id'] == aircraft_id), None)
    if aircraft is None:
        raise ValueError('Unknown aircraft')
    if 'rotations' in aircraft:
        return [dict(r, until=r.get('until')) for r in aircraft['rotations']]
    return [{'flightInstance': aircraft['flightInstance'], 'from': 0, 'until': None}]


def validate_rotations(data):
    owner = {}
    for aircraft in data['aircraft']:
        rotations = rotations_for(data, aircraft['id'])
        if not rotations:
            raise ValueError('Aircraft without rotations')
        previous_end = None
        for index, rotation in enumerate(rotations):
            flight = rotation.get('flightInstance')
            start, end = rotation.get('from'), rotation.get('until')
            if not isinstance(flight, str) or not flight:
                raise ValueError('Invalid flight instance')
            if flight in owner:
                raise ValueError('Flight instance assigned to more than one aircraft or rotation')
            owner[flight] = aircraft['id']
            if not isinstance(start, (int, float)) or not math.isfinite(start) or start < 0:
                raise ValueError('Invalid rotation start')
            if end is not None and (not isinstance(end, (int, float)) or not math.isfinite(end) or end <= start):
                raise ValueError('Invalid rotation end')
            if index and (previous_end is None or start < previous_end):
                raise ValueError('Rotations must be ordered and non-overlapping')
            previous_end = end
    for event in data['events']:
        if owner.get(event['flightInstance']) != event['aircraftId']:
            raise ValueError('Event flight instance does not belong to its aircraft')
    return owner


def resolve_flight(data, aircraft_id, flight_instance):
    """Return the rotation record, or raise if the flight is not this aircraft's."""
    for rotation in rotations_for(data, aircraft_id):
        if rotation['flightInstance'] == flight_instance:
            return rotation
    raise ValueError('Flight instance does not belong to the selected aircraft')


def rotation_at(data, aircraft_id, time):
    for rotation in rotations_for(data, aircraft_id):
        if rotation['from'] <= time and (rotation['until'] is None or time < rotation['until']):
            return rotation
    return None


def next_rotation(data, aircraft_id, flight_instance):
    rotations = rotations_for(data, aircraft_id)
    for index, rotation in enumerate(rotations):
        if rotation['flightInstance'] == flight_instance:
            return rotations[index + 1] if index + 1 < len(rotations) else None
    raise ValueError('Flight instance does not belong to the selected aircraft')
