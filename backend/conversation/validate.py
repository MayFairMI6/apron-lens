"""Deterministic checks on a model's proposed conversational answer.

What this validates: provenance and completeness against the receipt-eligible
evidence for the proposed flight. Every displayed claim must match a typed fact,
its temporal status and its own source; on a follow-up about the same flight,
every fact that is new or changed status since the previous answer must be
cited or explicitly listed as not discussed, and the answer may not deny a
change that occurred.

What this does not validate: whether the referent is the aircraft the user
meant (a valid ID does not prove "behind this one" was resolved correctly) and
whether the free-text rationale is true. The rationale is therefore displayed
only under a "model interpretation" label, never as a fact. Claims are shown
through fixed templates. No gold label is used here.

Visual observations (v2): the model may report what it sees in the image
(kind, value, capture time). They are checked only for form, for the image's
capture time and for the referent aircraft; their truth is not checked here.
Each is related to the reports by authored rules and displayed as an
unverified observation. Observations never change claims, report statuses or
the changed-fact checks. Visual ground truth is never read on this path.
"""
import math

from backend.evidence import FIELDS, render_claim
from backend.conversation.context import changed_facts, snapshot
from backend.conversation.identity import resolve_flight
from backend.conversation.observations import VISUAL_KINDS, describe, relate
from backend.conversation.state import INTENT_KINDS

VALIDATOR_VERSION = 'conversation-validator-v2'
STATUSES = ('answer', 'clarify', 'unknown')
KEYS = {'status', 'referent', 'claims', 'unknowns', 'explanationChanged',
        'changesNotDiscussed', 'memoryUpdate', 'rationale', 'observations'}
OBSERVATION_KEYS = {'kind', 'aircraftId', 'value', 'captureTime'}
MAX_OBSERVATIONS = 6
CLAIM_KEYS = {'fact_id', 'value', 'status', 'evidence_ids'}
MAX_RATIONALE = 600
INTERPRETATION_LABEL = 'Model interpretation (not checked against reports)'


def _schema_errors(p):
    if not isinstance(p, dict) or set(p) != KEYS:
        return ['schema']
    errors = []
    if p['status'] not in STATUSES:
        errors.append('status_value')
    ref = p['referent']
    if ref is not None and (not isinstance(ref, dict) or set(ref) != {'aircraftId', 'flightInstance'}
                            or not all(isinstance(v, str) for v in ref.values())):
        errors.append('referent_schema')
    if not isinstance(p['claims'], list) or len(p['claims']) > 20:
        errors.append('claims_schema')
    else:
        for c in p['claims']:
            if (not isinstance(c, dict) or set(c) != CLAIM_KEYS
                    or not all(isinstance(c[k], str) for k in ('fact_id', 'value', 'status'))
                    or not isinstance(c['evidence_ids'], list)
                    or not all(isinstance(i, str) for i in c['evidence_ids'])):
                errors.append('claim_schema')
                break
    if (not isinstance(p['unknowns'], list) or any(u not in FIELDS for u in p['unknowns'])
            or len(set(p['unknowns'])) != len(p['unknowns'])):
        errors.append('unknowns_schema')
    if p['explanationChanged'] not in (True, False, None):
        errors.append('explanation_changed_schema')
    if not isinstance(p['changesNotDiscussed'], list) or not all(isinstance(i, str) for i in p['changesNotDiscussed']):
        errors.append('changes_schema')
    mu = p['memoryUpdate']
    if mu is not None and (not isinstance(mu, dict) or set(mu) != {'kind', 'aircraftId', 'flightInstance'}
                           or mu.get('kind') not in INTENT_KINDS):
        errors.append('memory_update_schema')
    if not isinstance(p['rationale'], str) or len(p['rationale']) > MAX_RATIONALE:
        errors.append('rationale_schema')
    obs = p['observations']
    if not isinstance(obs, list) or len(obs) > MAX_OBSERVATIONS:
        errors.append('observations_schema')
    else:
        for o in obs:
            if (not isinstance(o, dict) or set(o) != OBSERVATION_KEYS or o['kind'] not in VISUAL_KINDS
                    or o['value'] not in VISUAL_KINDS[o['kind']]['values'] or not isinstance(o['aircraftId'], str)
                    or not isinstance(o['captureTime'], (int, float)) or isinstance(o['captureTime'], bool)
                    or not math.isfinite(o['captureTime'])):
                errors.append('observation_schema')
                break
    return errors


def validate_proposal(proposal, data, cutoff, previous_turn=None, image_capture_time=None):
    """Return dict(accepted, errors, snapshot, changes, observations, display)."""
    errors = _schema_errors(proposal)
    if errors:
        return _withheld(errors)
    p = proposal
    if p['referent'] is None:
        if p['status'] == 'answer':
            return _withheld(['answer_without_referent'])
        if p['observations']:
            return _withheld(['observation_without_referent'])
        return dict(accepted=True, errors=[], snapshot=None, changes=[], observations=[],
                    display=_display(p, None, [], previous_turn))
    aircraft, flight = p['referent']['aircraftId'], p['referent']['flightInstance']
    try:
        resolve_flight(data, aircraft, flight)
    except ValueError:
        return _withheld(['referent_not_in_scenario'])
    mu = p['memoryUpdate']
    if mu is not None:
        try:
            resolve_flight(data, mu['aircraftId'], mu['flightInstance'])
        except ValueError:
            return _withheld(['memory_update_not_in_scenario'])
        if (mu['aircraftId'], mu['flightInstance']) != (aircraft, flight):
            errors.append('memory_update_mismatch')
    snap = snapshot(data, aircraft, flight, cutoff)
    facts = snap['factsById']
    seen = set()
    for c in p['claims']:
        f = facts.get(c['fact_id'])
        if f is None:
            errors.append('claim_outside_eligible_evidence')
            continue
        if c['fact_id'] in seen:
            errors.append('duplicate_claim')
        seen.add(c['fact_id'])
        if c['value'] != f['value']:
            errors.append('unsupported_value')
        if c['status'] != f['status']:
            errors.append('wrong_temporal_status')
        if c['evidence_ids'] != [f['event_id']]:
            errors.append('incorrect_claim_citation')
    current_props = {f['property'] for f in snap['facts'] if f['status'] == 'current'}
    if any(u in current_props for u in p['unknowns']):
        errors.append('unknown_contradicts_current_fact')

    changes = []
    same_flight = previous_turn is not None and (previous_turn.aircraft_id, previous_turn.flight_instance) == (aircraft, flight)
    if same_flight and previous_turn.cutoff <= cutoff:
        before = snapshot(data, aircraft, flight, previous_turn.cutoff)
        changes = changed_facts(before, snap)
        if p['explanationChanged'] is None:
            errors.append('explanation_changed_missing')
        if changes and p['explanationChanged'] is False:
            errors.append('denies_change')
        if not changes and p['explanationChanged'] is True:
            errors.append('unsupported_change')
        covered = seen | set(p['changesNotDiscussed'])
        if any(c not in covered for c in changes):
            errors.append('missing_changed_fact')
        if any(c not in changes for c in p['changesNotDiscussed']):
            errors.append('invalid_change_reference')
    elif p['changesNotDiscussed']:
        errors.append('invalid_change_reference')
    related = []
    if p['observations']:
        if image_capture_time is None:
            errors.append('observation_without_image')
        elif image_capture_time > cutoff:
            errors.append('image_after_cutoff')
        for o in p['observations']:
            if image_capture_time is not None and o['captureTime'] != image_capture_time:
                errors.append('observation_capture_time_mismatch')
            if o['aircraftId'] != aircraft:
                errors.append('observation_outside_referent')
        if not errors:
            related = [relate(o, snap) for o in p['observations']]
    if errors:
        return _withheld(sorted(set(errors)), snap, changes)
    return dict(accepted=True, errors=[], snapshot=snap, changes=changes, observations=related,
                display=_display(p, snap, changes, previous_turn, related))


def _withheld(errors, snap=None, changes=()):
    return dict(accepted=False, errors=errors, snapshot=snap, changes=list(changes), observations=[],
                display=dict(resultStatus='withheld', validatorVersion=VALIDATOR_VERSION,
                             answer='The model proposal failed support or completeness checks. '
                                    'No model claims were displayed; review the report history.',
                             claims=[], interpretation=None))


def _display(p, snap, changes, previous_turn, related=()):
    lines = []
    if snap is not None:
        lines += [render_claim(snap['factsById'][c['fact_id']]) for c in p['claims']]
        lines += [f'{FIELDS[u]}: no unambiguous current value in received reports.' for u in p['unknowns']]
        if changes:
            lines.append('Changed since the previous answer: ' + ', '.join(changes))
        lines += [describe(r) for r in related]
    return dict(resultStatus=p['status'], validatorVersion=VALIDATOR_VERSION,
                answer='\n\n'.join(lines) or ('Clarification needed.' if p['status'] == 'clarify' else 'No supported claim selected.'),
                claims=p['claims'], unknowns=p['unknowns'], observations=list(related),
                interpretation=dict(label=INTERPRETATION_LABEL, text=p['rationale']) if p['rationale'] else None,
                validation='Claims match receipt-eligible typed facts and their sources; changed facts are covered. '
                           'The referent choice and the interpretation are not verified.')
