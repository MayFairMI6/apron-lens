"""One conversational turn: prompt, model call, validation and an atomic commit.

The model sees only receipt-eligible evidence for the candidate flights and the
memory visible at the turn's cutoff. Its proposal is parsed under the shared
repair policy and checked by validate.validate_proposal; only accepted claims
are displayed, through fixed templates.

Referent memory. The client sends the aircraft and flight currently selected
in the app on every turn. Selecting a different aircraft (or starting a
session) records a 'reference' intent and resets the referent. Re-sending the
same aircraft keeps the current referent, so an accepted correction such as
"its next rotation" persists until the user selects another aircraft. Intents
come only from the user's selection or from a validated memory update; the
model's rationale never becomes memory.

Correction rule (referent-rule-v2). When the proposal's memory update is a
correction to a flight that exists in the scenario, that flight becomes the
proposal's referent before validation, replacing the model's referent field.
Development runs showed models naming the corrected rotation in the memory
update while leaving the referent on the app's selection. The corrected
proposal is then validated as usual: its claims must be that flight's received
facts, so a mix of the old and new flight is still withheld. Other memory
update kinds never change the referent.

AR conditions (conversation-prompt-v6, referent-rule-v3; docs/AR_SCOPE.md).
- Nothing selected (the text-only condition): the request carries no aircraft.
  The candidates are then every flight in the scenario, and an accepted answer's
  referent is recorded as a 'reference' intent, as a selection would be, so it
  persists to the next turn.
- lastSeen: the replay time when the board was last in the camera's view. For
  each candidate flight the prompt then lists changedWhileAway, the facts that
  are new or changed status since then, from the same changed_facts function.

Authored visual ground truth is never read on this path.
"""
import json

from modelaccess.contract import ImageInput, Request
from modelaccess.repair import REPAIR_POLICY_VERSION, parse_json_output
from backend.evidence import FIELDS, STATUSES
from backend.conversation.context import changed_facts, receipt_times, snapshot
from backend.conversation.identity import next_rotation, resolve_flight, rotations_for
from backend.conversation.observations import VISUAL_KINDS
from backend.conversation.state import AssistantTurn, IntentRecord, StaleRevision
from backend.conversation.validate import VALIDATOR_VERSION, validate_proposal

PROMPT_VERSION = 'conversation-prompt-v6'
REFERENT_RULE_VERSION = 'referent-rule-v3'
MAX_MEMORY_IN_PROMPT = 6


def candidate_flights(data, selection, referent):
    """Every rotation of the selected aircraft (of every aircraft when nothing is selected),
    plus the current referent if it differs."""
    aircraft = [a['id'] for a in data['aircraft']] if selection is None else [selection[0]]
    flights = [(a, r['flightInstance']) for a in aircraft for r in rotations_for(data, a)]
    if referent is not None and referent not in flights:
        flights.append(referent)
    return flights


def apply_correction(data, proposal):
    """Return (proposal, referent source): a valid correction's flight replaces the referent."""
    mu = proposal.get('memoryUpdate') if isinstance(proposal, dict) else None
    if not (isinstance(mu, dict) and mu.get('kind') == 'correction'
            and isinstance(mu.get('aircraftId'), str) and isinstance(mu.get('flightInstance'), str)):
        return proposal, 'model'
    try:
        resolve_flight(data, mu['aircraftId'], mu['flightInstance'])
    except ValueError:
        return proposal, 'model'  # left for the validator to reject
    target = {'aircraftId': mu['aircraftId'], 'flightInstance': mu['flightInstance']}
    if proposal.get('referent') == target:
        return proposal, 'model'
    return dict(proposal, referent=target), 'correction'


def build_prompt(data, cutoff, selection, referent, intents, previous_by_flight, question, image_time=None, tap=None,
                 last_seen=None):
    """`previous_by_flight` maps (aircraft, flight) to the visible previous answer about that flight.

    For each such flight the prompt carries the changed-fact set that
    validate_proposal will check, computed by the same function, so a
    follow-up's required explanationChanged and coverage can be read
    from the prompt rather than inferred.
    """
    candidates = []
    for aircraft, flight in candidate_flights(data, selection, referent):
        snap = snapshot(data, aircraft, flight, cutoff)
        following = next_rotation(data, aircraft, flight)
        previous = previous_by_flight.get((aircraft, flight))
        candidates.append(dict(aircraftId=aircraft, flightInstance=flight,
                               nextRotation=following['flightInstance'] if following else None,
                               facts=[{k: f[k] for k in ('fact_id', 'event_id', 'property', 'value', 'status',
                                                          'eventTime', 'receiptTime', 'source')}
                                      for f in snap['facts']],
                               previousAnswer=None if previous is None else dict(
                                   atReplayTime=previous.cutoff, status=previous.status,
                                   citedFacts=list(previous.claims),
                                   changedSincePreviousAnswer=changed_facts(
                                       snapshot(data, aircraft, flight, previous.cutoff), snap))))
        if last_seen is not None:
            candidates[-1]['changedWhileAway'] = changed_facts(snapshot(data, aircraft, flight, last_seen), snap)
    memory = dict(
        currentReferent=None if referent is None else dict(aircraftId=referent[0], flightInstance=referent[1]),
        userIntents=[dict(kind=i.kind, aircraftId=i.aircraft_id, flightInstance=i.flight_instance, text=i.text,
                          atReplayTime=i.cutoff) for i in intents[-MAX_MEMORY_IN_PROMPT:]])
    view = ('No image is attached; "observations" must be [].' if image_time is None else
            f'An image of the current view is attached, captured at {image_time:g} s. You may report what is visible '
            f'for the referent aircraft only, as observations with captureTime {image_time:g}: '
            + '; '.join(f'{k} in {list(v["values"])}' for k, v in VISUAL_KINDS.items())
            + '. How they look in this rendering: '
            + '; '.join(f'{k} ({v["appearance"]})' for k, v in VISUAL_KINDS.items())
            + '. Report a kind only if you can see that part of the referent aircraft; otherwise leave it out. '
              'Observations describe the image only: report what you see even if it disagrees with a report.'
            + ('' if tap is None else f' The user tapped the image at ({tap[0]:.3f}, {tap[1]:.3f}), '
                                      'origin bottom-left, 0..1.'))
    return (
        'You are the conversational assistant of a FICTIONAL airfield replay. Answer the user about one aircraft '
        'flight, using only the facts listed below. Return JSON only, no prose or markdown.\n'
        'Schema: {"status":"answer|clarify|unknown","referent":{"aircraftId":"...","flightInstance":"..."} or null,'
        '"claims":[{"fact_id":"ID:property","value":"...","status":"' + '|'.join(STATUSES) + '",'
        '"evidence_ids":["event ID"]}],"unknowns":["property"],'
        '"explanationChanged":true|false|null,"changesNotDiscussed":["fact_id"],'
        '"memoryUpdate":{"kind":"reference|correction|scope","aircraftId":"...","flightInstance":"..."} or null,'
        '"rationale":"one or two sentences","observations":'
        + ('[]' if image_time is None else
           '[{"kind":"' + '|'.join(VISUAL_KINDS) + f'","aircraftId":"...","value":"...","captureTime":{image_time:g}}}]')
        + '}\n'
        'Every reply has all ten keys. Every claim has all four keys and copies fact_id, value, status and '
        'event_id (as the only evidence_ids entry) from one listed fact.\n'
        'Rules: the referent must be one of the candidate flights, and claims cite only facts listed under the '
        'referent flight. '
        'A user correction changes the referent and is recorded as a memoryUpdate of kind "correction" with the '
        'same aircraft and flight as the new referent; it never changes a fact. "Its next rotation" means the '
        'flight named in nextRotation of the current referent. If the referent flight has a previousAnswer, '
        'set explanationChanged to true exactly when its changedSincePreviousAnswer is non-empty, and cite or list '
        'in changesNotDiscussed every fact ID in changedSincePreviousAnswer; if it has no previousAnswer, '
        'explanationChanged is null and changesNotDiscussed is []. '
        'Status: "answer" whenever you name one referent flight and reply about it, also when some facts are '
        'missing (list their properties in unknowns) or conflicting (cite each conflicting fact with its status). '
        '"clarify" only when the user\'s words could mean more than one candidate flight and neither the selection '
        'nor the memory decides it; then referent is null and claims is []. "unknown" when the referent is clear but '
        'no listed fact bears on the question; list the missing properties in unknowns. Unknowns use these properties: '
        + ', '.join(FIELDS) + '.\n'
        f'Replay time (receipt cutoff): {cutoff:g} s. '
        + ('Nothing is selected in the app: identify the flight from the user\'s words and the memory, and use '
           '"clarify" when they could mean more than one candidate flight. ' if selection is None else
           f'Selected in the app: aircraft {selection[0]}, flight {selection[1]}. ')
        + ('' if last_seen is None else
           f'The board was out of the user\'s view from {last_seen:g} s until now, while reports kept arriving; '
           'each candidate\'s changedWhileAway lists the facts that are new or changed since then. Cite those of '
           'the referent flight that bear on the question, so the user hears what changed while they were not '
           'looking. ')
        + f'\n{view}\n'
        f'Memory: {json.dumps(memory, sort_keys=True)}\n'
        f'Candidate flights and received facts: {json.dumps(candidates, sort_keys=True)}\n'
        f'User: {question}')


def run_turn(session, data, turn, adapter, settings):
    """Serve one turn and return the stored result.

    `turn` keys: requestId, turnId, expectedRevision, aircraftId, flightInstance,
    cutoff, question, and optionally image (bytes), imageMediaType,
    imageCaptureTime, imageSha256, tap ([x, y] in image coordinates) and
    lastSeen. aircraftId and flightInstance are None when nothing is selected.
    Raises ValueError for requests that cannot be served, and the state
    module's exceptions for revision, seek and request-ID conflicts.
    """
    request_id, turn_id, expected = turn['requestId'], turn['turnId'], turn['expectedRevision']
    if session.result_for(request_id) is not None:
        return session.commit(request_id, turn_id, expected)  # a retry: stored result, no second model call
    if expected != session.revision:
        raise StaleRevision(f'expected revision {expected}, current {session.revision}')
    cutoff = turn['cutoff']
    selection = (turn['aircraftId'], turn['flightInstance']) if turn.get('aircraftId') else None
    if selection is not None:
        resolve_flight(data, *selection)
    if not 0 <= cutoff <= data['duration']:
        raise ValueError('Cutoff outside scenario')
    last_seen = turn.get('lastSeen')
    if last_seen is not None and not 0 <= last_seen < cutoff:
        raise ValueError('lastSeen must be before the replay time')
    image_time = turn.get('imageCaptureTime') if turn.get('image') is not None else None
    if turn.get('image') is not None and (image_time is None or image_time > cutoff):
        raise ValueError('An image needs a capture time at or before the replay time')
    session.observe_cutoff(cutoff)

    receipts = receipt_times(data)
    intents, _ = session.visible_memory(cutoff, receipts)
    referent = session.current_referent(cutoff, receipts)
    new_intents = []
    if selection is not None and (referent is None or referent[0] != selection[0]):
        new_intents.append(IntentRecord(turn_id, 'reference', *selection, turn['question'], cutoff))
        referent = selection
    previous_by_flight = {}
    for flight in candidate_flights(data, selection, referent):
        previous = session.previous_turn_for(*flight, cutoff, receipts)
        if previous is not None:
            previous_by_flight[flight] = previous
    prompt = build_prompt(data, cutoff, selection, referent, intents + new_intents, previous_by_flight,
                          turn['question'], image_time, turn.get('tap'), last_seen)
    images = () if image_time is None else (ImageInput(turn['image'], turn['imageMediaType'], image_time),)
    reply = adapter.generate(Request(request_id, (('user', prompt),), settings, images))

    proposal, raw_valid, repairs, parse_error = (None, False, (), None)
    referent_source = 'model'
    if reply.ok:
        proposal, raw_valid, repairs, parse_error = parse_json_output(reply.text)
    if not reply.ok:
        checked = validate_proposal(None, data, cutoff)
        checked['errors'] = ['model_error:' + reply.error]
    elif parse_error:
        checked = validate_proposal(None, data, cutoff)
        checked['errors'] = [parse_error]
    else:
        proposal, referent_source = apply_correction(data, proposal)
        ref = proposal.get('referent') if isinstance(proposal, dict) else None
        prior = None
        if isinstance(ref, dict) and isinstance(ref.get('aircraftId'), str) and isinstance(ref.get('flightInstance'), str):
            prior = session.previous_turn_for(ref['aircraftId'], ref['flightInstance'], cutoff, receipts)
        checked = validate_proposal(proposal, data, cutoff, prior, image_time)

    stored_turn = None
    if checked['accepted']:
        p = proposal
        mu = p['memoryUpdate']
        if mu is not None:
            new_intents.append(IntentRecord(turn_id, mu['kind'], mu['aircraftId'], mu['flightInstance'],
                                            turn['question'], cutoff))
        elif selection is None and p['referent'] is not None and \
                (p['referent']['aircraftId'], p['referent']['flightInstance']) != referent:
            # referent-rule-v3: with nothing selected, the answer's referent persists like a selection.
            new_intents.append(IntentRecord(turn_id, 'reference', p['referent']['aircraftId'],
                                            p['referent']['flightInstance'], turn['question'], cutoff))
        if p['referent'] is not None:
            snap = checked['snapshot']
            stored_turn = AssistantTurn(
                turn_id, request_id, p['referent']['aircraftId'], p['referent']['flightInstance'], cutoff,
                evidence_ids=tuple(sorted({e for c in p['claims'] for e in c['evidence_ids']})),
                claims=tuple(c['fact_id'] for c in p['claims']), status=p['status'],
                evidence_digest=snap['evidenceDigest'], interpretation=p['rationale'] or None,
                observations=tuple(checked['observations']))
    after = (new_intents[-1].aircraft_id, new_intents[-1].flight_instance) if new_intents else referent
    result = dict(
        requestId=request_id, turnId=turn_id, sessionId=session.session_id, cutoff=cutoff,
        accepted=checked['accepted'], errors=checked['errors'], display=checked['display'],
        referent=proposal['referent'] if checked['accepted'] else None,
        currentReferent=None if after is None else dict(aircraftId=after[0], flightInstance=after[1]),
        changes=checked['changes'], imageUsedForInference=bool(images),
        provider=reply.provider, configuredModel=reply.configured_model, returnedModel=reply.returned_model,
        finishReason=reply.finish_reason.value, inputTokens=reply.usage.input_tokens,
        outputTokens=reply.usage.output_tokens, latencySeconds=round(reply.latency_seconds, 3),
        ignoredSettings=list(reply.ignored_settings), rawJsonValid=raw_valid, repairs=list(repairs),
        selectionSent=selection is not None, lastSeen=last_seen,
        referentSource=referent_source, promptVersion=PROMPT_VERSION, referentRule=REFERENT_RULE_VERSION,
        validatorVersion=VALIDATOR_VERSION, repairPolicy=REPAIR_POLICY_VERSION)
    stored = session.commit(request_id, turn_id, expected, new_intents, stored_turn, result)
    return dict(stored, prompt=prompt, rawModelOutput=reply.text)
