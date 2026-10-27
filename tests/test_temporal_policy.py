"""Independent policy regressions using original inline fixtures, not evaluation gold."""
import copy
import unittest

from backend.evidence import build_context, expected_selection, validate_scenario


def event(eid, prop, value, event_time=0, receipt=None, valid_from=None, valid_until=None,
          supersedes=(), aircraft='A2', flight='F2-R1'):
    fact = {'property': prop, 'value': value, 'supersedes': list(supersedes)}
    if valid_from is not None:
        fact['validFrom'] = valid_from
    if valid_until is not None:
        fact['validUntil'] = valid_until
    return {'id': eid, 'aircraftId': aircraft, 'flightInstance': flight,
            'source': 'fictional-policy-test', 'eventTime': event_time,
            'receiptTime': event_time if receipt is None else receipt,
            'message': 'Inline policy fixture.', 'facts': [fact]}


def scenario(events):
    data = {'scenarioId': 'policy-test', 'duration': 100,
            'aircraft': [{'id': 'A2', 'flightInstance': 'F2-R1'}], 'events': events}
    validate_scenario(data)
    return data


def selected(data, time, kind='current', props=('route',)):
    return expected_selection(build_context(data, 'A2', time, kind, list(props)))


class TemporalPolicyTests(unittest.TestCase):
    def test_replaced_future_plan_is_historical_not_scheduled(self):
        data = scenario([
            event('P1', 'route', 'east', valid_from=50),
            event('P2', 'route', 'west', 10, supersedes=['P1:route']),
        ])
        history = selected(data, 20, 'change')
        self.assertEqual({c['fact_id']: c['status'] for c in history['claims']},
                         {'P1:route': 'superseded', 'P2:route': 'current'})
        self.assertEqual([c['value'] for c in selected(data, 20)['claims']], ['west'])

    def test_scheduled_replacement_does_not_retire_current_plan_early(self):
        data = scenario([
            event('P1', 'route', 'east'),
            event('P2', 'route', 'west', 10, valid_from=30, supersedes=['P1:route']),
        ])
        self.assertEqual([c['value'] for c in selected(data, 29)['claims']], ['east'])
        self.assertEqual([c['value'] for c in selected(data, 30)['claims']], ['west'])

    def test_expired_replacement_never_revives_old_plan(self):
        data = scenario([
            event('P1', 'route', 'east', valid_until=90),
            event('P2', 'route', 'west', 10, valid_until=20, supersedes=['P1:route']),
        ])
        result = selected(data, 20)
        self.assertEqual(result['claims'], [])
        self.assertEqual(result['unknown_properties'], ['route'])
        states = {c['fact_id']: c['status'] for c in selected(data, 25, 'change')['claims']}
        self.assertEqual(states, {'P1:route': 'superseded', 'P2:route': 'expired'})

    def test_latest_receipt_ties_include_all_matching_events(self):
        data = scenario([
            event('Z9', 'stand', 'B', 3, receipt=10),
            event('A1', 'fuel_status', 'complete', 7, receipt=10),
            event('M4', 'baggage_status', 'pending', 1, receipt=9),
        ])
        result = selected(data, 10, 'latest', ())
        self.assertEqual({c['fact_id'] for c in result['claims']}, {'Z9:stand', 'A1:fuel_status'})
        # Event IDs and input order have no authority to break receipt-time ties.
        reordered = copy.deepcopy(data)
        reordered['events'].reverse()
        self.assertEqual(result, selected(reordered, 10, 'latest', ()))

    def test_latest_property_filter_precedes_time_selection(self):
        data = scenario([
            event('P1', 'stand', 'B', 3, receipt=5),
            event('P2', 'fuel_status', 'complete', 10),
        ])
        result = selected(data, 12, 'latest', ('stand',))
        self.assertEqual([c['fact_id'] for c in result['claims']], ['P1:stand'])

    def test_future_arrival_and_wrong_rotation_cannot_change_current_answer(self):
        base = scenario([event('P1', 'route', 'east')])
        augmented = scenario(base['events'] + [
            event('P2', 'route', 'west', 10, receipt=21, supersedes=['P1:route']),
            event('P3', 'route', 'north', 15, flight='F2-R0'),
        ])
        self.assertEqual(selected(base, 20), selected(augmented, 20))
        self.assertEqual([c['value'] for c in selected(augmented, 21)['claims']], ['west'])

    def test_scheduled_only_means_unknown_current_not_negative_value(self):
        data = scenario([event('P1', 'fuel_status', 'complete', 5, valid_from=30)])
        current = selected(data, 20, 'current', ('fuel_status',))
        self.assertEqual(current, {'claims': [], 'unknown_properties': ['fuel_status']})
        history = selected(data, 20, 'change', ('fuel_status',))
        self.assertEqual(history['claims'][0]['value'], 'complete')
        self.assertEqual(history['claims'][0]['status'], 'scheduled')
        self.assertEqual(history['unknown_properties'], ['fuel_status'])


if __name__ == '__main__':
    unittest.main()
