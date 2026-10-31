"""Conversational-path regressions using inline fictional fixtures, not evaluation gold."""
import os
import tempfile
import threading
import unittest

from backend.conversation import identity
from backend.conversation.context import receipt_times, snapshot
from backend.conversation.guards import HeldoutLocationError, UnsafeBind, check_bind, load_heldout
from backend.conversation.ledger import BudgetExceeded, CheckpointPause, Ledger, RateTable, RateUnavailable
from backend.conversation.selection import comparison_eligible, select, zero_event_upper_bound
from backend.conversation.state import (AssistantTurn, DuplicateRequestConflict, FORMAL, IntentRecord,
                                        SeekBackwardInFormalRun, SessionState, StaleRevision)
from backend.conversation.validate import INTERPRETATION_LABEL, validate_proposal


def event(eid, flight, prop, value, t, receipt=None, supersedes=(), aircraft='A2'):
    return {'id': eid, 'aircraftId': aircraft, 'flightInstance': flight, 'source': 'fictional-test',
            'eventTime': t, 'receiptTime': t if receipt is None else receipt, 'message': 'Inline fixture.',
            'facts': [{'property': prop, 'value': value, 'supersedes': list(supersedes)}]}


def two_rotation_scenario():
    return {'scenarioId': 'conv-test', 'duration': 100,
            'aircraft': [{'id': 'A1', 'flightInstance': 'F1-R1'},
                         {'id': 'A2', 'rotations': [{'flightInstance': 'F2-R1', 'from': 0, 'until': 50},
                                                    {'flightInstance': 'F2-R2', 'from': 50}]}],
            'events': [event('E01', 'F2-R1', 'stand', 'B', 0),
                       event('E02', 'F2-R2', 'stand', 'C', 5),
                       event('E03', 'F2-R1', 'stand', 'D', 20, receipt=30, supersedes=['E01:stand']),
                       event('E04', 'F1-R1', 'stand', 'A', 0, aircraft='A1')]}


def proposal(**overrides):
    base = dict(status='answer', referent={'aircraftId': 'A2', 'flightInstance': 'F2-R1'}, claims=[],
                unknowns=[], explanationChanged=None, changesNotDiscussed=[], memoryUpdate=None, rationale='',
                observations=[])
    base.update(overrides)
    return base


def claim(fid, value, status, eid):
    return {'fact_id': fid, 'value': value, 'status': status, 'evidence_ids': [eid]}


class RotationIdentity(unittest.TestCase):
    def test_next_rotation_is_resolved_from_scenario_binding(self):
        data = two_rotation_scenario()
        identity.validate_rotations(data)
        self.assertEqual(identity.next_rotation(data, 'A2', 'F2-R1')['flightInstance'], 'F2-R2')
        self.assertEqual(identity.rotation_at(data, 'A2', 60)['flightInstance'], 'F2-R2')
        with self.assertRaises(ValueError):
            identity.resolve_flight(data, 'A1', 'F2-R2')

    def test_legacy_single_flight_scenarios_still_work(self):
        data = two_rotation_scenario()
        self.assertEqual(identity.rotations_for(data, 'A1'), [{'flightInstance': 'F1-R1', 'from': 0, 'until': None}])

    def test_event_for_foreign_rotation_is_rejected(self):
        data = two_rotation_scenario()
        data['events'].append(event('E05', 'F1-R1', 'stand', 'Z', 1))  # A2 event on A1's flight
        with self.assertRaises(ValueError):
            identity.validate_rotations(data)

    def test_correction_selects_next_rotation_and_rejects_first_rotation_citations(self):
        data = two_rotation_scenario()
        corrected = proposal(referent={'aircraftId': 'A2', 'flightInstance': 'F2-R2'},
                             memoryUpdate={'kind': 'correction', 'aircraftId': 'A2', 'flightInstance': 'F2-R2'},
                             claims=[claim('E02:stand', 'C', 'current', 'E02')])
        self.assertTrue(validate_proposal(corrected, data, 40)['accepted'])
        wrong = dict(corrected, claims=[claim('E01:stand', 'B', 'superseded', 'E01')])
        self.assertIn('claim_outside_eligible_evidence', validate_proposal(wrong, data, 40)['errors'])
        mismatch = dict(corrected, memoryUpdate={'kind': 'correction', 'aircraftId': 'A2', 'flightInstance': 'F2-R1'})
        self.assertIn('memory_update_mismatch', validate_proposal(mismatch, data, 40)['errors'])
        foreign = dict(corrected, memoryUpdate={'kind': 'correction', 'aircraftId': 'A1', 'flightInstance': 'F2-R2'})
        self.assertFalse(validate_proposal(foreign, data, 40)['accepted'])


class SeekBack(unittest.TestCase):
    def setUp(self):
        self.data = two_rotation_scenario()
        self.receipts = receipt_times(self.data)

    def later_turn(self):
        return AssistantTurn('t2', 'r2', 'A2', 'F2-R1', 40, ('E03',), (), 'answer', 'digest')

    def test_memory_from_later_cutoff_is_masked_after_seek_back(self):
        state = SessionState('s1')
        state.commit('r1', 't1', 0, intents=[IntentRecord('t1', 'reference', 'A2', 'F2-R1', 'this one', 10)])
        state.commit('r2', 't2', 1, turn=self.later_turn())
        state.observe_cutoff(40)
        state.observe_cutoff(20)  # development mode allows it, with masking
        intents, turns = state.visible_memory(20, self.receipts)
        self.assertEqual(len(intents), 1)
        self.assertEqual(turns, [])

    def test_turn_citing_later_received_evidence_is_masked(self):
        state = SessionState('s1')
        early_turn_late_cite = AssistantTurn('t2', 'r2', 'A2', 'F2-R1', 25, ('E03',), (), 'answer', 'd')
        state.commit('r2', 't2', 0, turn=early_turn_late_cite)
        self.assertEqual(state.visible_memory(25, self.receipts)[1], [])  # E03 received at 30

    def test_formal_runs_reject_backward_seek(self):
        state = SessionState('s1', mode=FORMAL)
        state.observe_cutoff(40)
        with self.assertRaises(SeekBackwardInFormalRun):
            state.observe_cutoff(20)


class Validator(unittest.TestCase):
    def setUp(self):
        self.data = two_rotation_scenario()
        self.previous = AssistantTurn('t1', 'r1', 'A2', 'F2-R1', 10, ('E01',), (), 'answer', 'd')

    def test_denying_a_change_after_superseding_report_is_withheld(self):
        p = proposal(claims=[claim('E01:stand', 'B', 'superseded', 'E01')], explanationChanged=False)
        result = validate_proposal(p, self.data, 35, self.previous)
        self.assertFalse(result['accepted'])
        self.assertIn('denies_change', result['errors'])
        self.assertIn('missing_changed_fact', result['errors'])

    def test_changed_facts_must_be_cited_or_listed(self):
        p = proposal(claims=[claim('E03:stand', 'D', 'current', 'E03')], explanationChanged=True,
                     changesNotDiscussed=['E01:stand'])
        result = validate_proposal(p, self.data, 35, self.previous)
        self.assertTrue(result['accepted'], result['errors'])
        self.assertEqual(result['changes'], ['E01:stand', 'E03:stand'])

    def test_rationale_is_labeled_as_interpretation(self):
        p = proposal(claims=[claim('E01:stand', 'B', 'current', 'E01')],
                     rationale='Probably waiting because fuel is pending.')
        display = validate_proposal(p, self.data, 10)['display']
        self.assertEqual(display['interpretation']['label'], INTERPRETATION_LABEL)
        self.assertNotIn('fuel', display['answer'])

    def test_unknown_cannot_contradict_a_current_fact(self):
        p = proposal(unknowns=['stand'])
        self.assertIn('unknown_contradicts_current_fact', validate_proposal(p, self.data, 10)['errors'])

    def test_wrong_status_and_value_are_withheld(self):
        p = proposal(claims=[claim('E01:stand', 'X', 'current', 'E01')])
        self.assertIn('unsupported_value', validate_proposal(p, self.data, 10)['errors'])
        p = proposal(claims=[claim('E01:stand', 'B', 'current', 'E01')])
        self.assertIn('wrong_temporal_status', validate_proposal(p, self.data, 35)['errors'])

    def test_snapshot_never_includes_future_receipts(self):
        ids = {f['event_id'] for f in snapshot(self.data, 'A2', 'F2-R1', 25)['facts']}
        self.assertEqual(ids, {'E01'})


class Commits(unittest.TestCase):
    def test_duplicate_request_ids_commit_once(self):
        state = SessionState('s1')
        results = []

        def send():
            results.append(state.commit('same', 't1', 0, result={'answer': 'x'}))
        threads = [threading.Thread(target=send) for _ in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(state.revision, 1)
        self.assertTrue(all(r == results[0] for r in results))

    def test_stale_revision_changes_nothing(self):
        state = SessionState('s1')
        state.commit('r1', 't1', 0)
        with self.assertRaises(StaleRevision):
            state.commit('r2', 't2', 0, intents=[IntentRecord('t2', 'correction', 'A2', 'F2-R2', 'next', 5)])
        self.assertEqual((state.revision, state.intents), (1, []))

    def test_request_id_reused_for_another_turn_is_rejected(self):
        state = SessionState('s1')
        state.commit('r1', 't1', 0)
        with self.assertRaises(DuplicateRequestConflict):
            state.commit('r1', 't2', 1)


class Budget(unittest.TestCase):
    RATES = {'m': {'rates': [{'effectiveFrom': '2026-10-31', 'inputPerMTok': 2.0, 'outputPerMTok': 10.0},
                             {'effectiveFrom': '2026-12-01', 'inputPerMTok': 4.0, 'outputPerMTok': 20.0}]},
             'low': {'rates': [{'effectiveFrom': '2026-10-31', 'inputPerMTok': 0.1, 'outputPerMTok': 0.5,
                                'rateIsLowerBound': True}]}}

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, 'ledger.sqlite')

    def tearDown(self):
        self.dir.cleanup()

    def test_rates_follow_effective_dates_and_refuse_lower_bounds(self):
        table = RateTable(self.RATES)
        self.assertEqual(table.max_cost_micro('m', '2026-11-30', 6000, 1000), 22000)
        self.assertEqual(table.max_cost_micro('m', '2026-12-01', 6000, 1000), 44000)
        with self.assertRaises(RateUnavailable):
            table.max_cost_micro('low', '2026-11-01', 6000, 1000)

    def test_concurrent_reservations_never_exceed_the_cap(self):
        ledger = Ledger(self.path, purposes={'screening': 1.0}, total=1.0, checkpoint=None)
        accepted, refused = [], []

        def reserve(i):
            try:
                accepted.append(ledger.reserve(f'r{i}', 1, 'screening', 'm', 300_000))
            except BudgetExceeded:
                refused.append(i)
        threads = [threading.Thread(target=reserve, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(accepted), 3)
        self.assertLessEqual(ledger.committed(), 1_000_000)

    def test_missing_usage_and_cancellation_keep_the_reserved_charge(self):
        ledger = Ledger(self.path, purposes={'primary': 5.0}, total=5.0, checkpoint=None)
        a = ledger.reserve('r1', 1, 'primary', 'm', 100_000)
        b = ledger.reserve('r2', 1, 'primary', 'm', 100_000)
        c = ledger.reserve('r2', 2, 'primary', 'm', 100_000)  # retry is a separate, charged attempt
        ledger.reconcile(a, None)
        ledger.cancel(b)
        ledger.reconcile(c, 40_000)
        self.assertEqual(ledger.committed(), 240_000)
        self.assertEqual(ledger.reserve('r2', 2, 'primary', 'm', 100_000), c)  # idempotent

    def test_ledger_survives_restart_and_pauses_at_checkpoint(self):
        ledger = Ledger(self.path, purposes={'primary': 20.0}, total=20.0, checkpoint=10.0)
        ledger.reserve('r1', 1, 'primary', 'm', 10_000_000)
        reopened = Ledger(self.path, purposes={'primary': 20.0}, total=20.0, checkpoint=10.0)
        with self.assertRaises(CheckpointPause):
            reopened.reserve('r2', 1, 'primary', 'm', 1)
        reopened.acknowledge_checkpoint()
        reopened.reserve('r2', 1, 'primary', 'm', 1)

    def test_session_limit(self):
        ledger = Ledger(self.path, purposes={'primary': 5.0}, total=5.0, checkpoint=None, session_limit=0.15)
        ledger.reserve('r1', 1, 'primary', 'm', 100_000, session_id='phone')
        with self.assertRaises(BudgetExceeded):
            ledger.reserve('r2', 1, 'primary', 'm', 100_000, session_id='phone')


class Guards(unittest.TestCase):
    def test_hosted_mode_refuses_lan_bind(self):
        check_bind('127.0.0.1', hosted_enabled=True)
        check_bind('0.0.0.0', hosted_enabled=False)
        check_bind('0.0.0.0', hosted_enabled=True, encrypted_tunnel=True)
        with self.assertRaises(UnsafeBind):
            check_bind('0.0.0.0', hosted_enabled=True)

    def test_heldout_answers_inside_repo_are_refused(self):
        with tempfile.TemporaryDirectory() as root:
            inside = os.path.join(root, 'answers.json')
            with open(inside, 'w') as f:
                f.write('{}')
            with self.assertRaises(HeldoutLocationError):
                load_heldout(inside, 'x', repo_root=root)
            with tempfile.TemporaryDirectory() as elsewhere:
                outside = os.path.join(elsewhere, 'answers.json')
                with open(outside, 'w') as f:
                    f.write('{}')
                import hashlib
                good = hashlib.sha256(b'{}').hexdigest()
                self.assertEqual(load_heldout(outside, good, repo_root=root), {})
                with self.assertRaises(HeldoutLocationError):
                    load_heldout(outside, 'wrong', repo_root=root)


class Selection(unittest.TestCase):
    def metrics(self, **overrides):
        m = dict(referent_accuracy=0.95, supported_claim_rate=0.99, future_evidence_leaks=0,
                 wrong_flight_memory_writes=0, reliability=0.99, cost_per_attempted_turn=0.02,
                 median_latency=4.0, visual_reference=80.0, temporal_correction=80.0,
                 evidence_uncertainty=80.0, cases=24)
        m.update(overrides)
        return m

    def test_gate_failure_disqualifies_despite_higher_weighted_total(self):
        candidates = [dict(name='strong-but-leaky', metrics=self.metrics(visual_reference=99.0, wrong_flight_memory_writes=1)),
                      dict(name='steady', metrics=self.metrics())]
        ranking, excluded, report = select(candidates, planned_calls=252, allocation=12.0)
        self.assertEqual(ranking, ['steady'])
        self.assertIn('wrong_flight_memory_write', excluded['strong-but-leaky'])
        self.assertGreater(report['strong-but-leaky']['weightedTotal'], report['steady']['weightedTotal'])

    def test_cost_and_comparison_eligibility(self):
        self.assertTrue(comparison_eligible(0.11))       # 72 x 0.11 = 7.92 <= 9.60
        self.assertFalse(comparison_eligible(0.22))      # 72 x 0.22 = 15.84
        self.assertAlmostEqual(zero_event_upper_bound(24), 0.125)


if __name__ == '__main__':
    unittest.main()
