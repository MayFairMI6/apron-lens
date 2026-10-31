"""Evaluation-only access to authored visual ground truth ("visualProps").

Never import this module from the request path (context, state, validate,
observations or any server code): the system under test must learn visible
state only from the image. tests/test_visual_observations.py enforces this.
"""


def prop_value(data, aircraft_id, flight_instance, kind, time):
    matches = [p for p in data.get('visualProps', [])
               if (p['aircraftId'], p['flightInstance'], p['kind']) == (aircraft_id, flight_instance, kind)]
    if len(matches) != 1:
        return None
    states = matches[0]['states']
    value = states[0]['value']
    for state in states:
        if state['t'] <= time:
            value = state['value']
    return value


def score_observation(data, flight_instance, observation):
    """Return (correct, truth). truth is None when the scenario has no such prop."""
    truth = prop_value(data, observation['aircraftId'], flight_instance, observation['kind'], observation['captureTime'])
    return (truth is not None and truth == observation['value']), truth
