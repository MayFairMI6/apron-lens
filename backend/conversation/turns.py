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

Authored visual ground truth is never read on this path.
"""
import json

from modelaccess.contract import ImageInput, Request
from modelaccess.repair import REPAIR_POLICY_VERSION, parse_json_output
from backend.evidence import FIELDS
from backend.conversation.context import receipt_times, snapshot
from backend.conversation.identity import next_rotation, resolve_flight, rotations_for
from backend.conversation.observations import VISUAL_KINDS
from backend.conversation.state import AssistantTurn, IntentRecord, StaleRevision
from backend.conversation.validate import VALIDATOR_VERSION, validate_proposal

PROMPT_VERSION = 'conversation-prompt-v1'
MAX_MEMORY_IN_PROMPT = 6


def candidate_flights(data, aircraft_id, referent):
    """Every rotation of the selected aircraft, plus the current referent if it differs."""
    flights = [(aircraft_id, r['flightInstance']) for r in rotations_for(data, aircraft_id)]
    if referent is not None and referent not in flights:
        flights.append(referent)
    return flights


def build_prompt(data, cutoff, selection, referent, intents, previous, question, image_time=None, tap=None):
    candidates = []
    for aircraft, flight in candidate_flights(data, selection[0], referent):
        snap = snapshot(data, aircraft, flight, cutoff)
        following = next_rotation(data, aircraft, flight)
        candidates.append(dict(aircraftId=aircraft, flightInstance=flight,
                               nextRotation=following['flightInstance'] if following else None,
                               facts=[{k: f[k] for k in ('fact_id', 'event_id', 'property', 'value', 'status',
                                                          'eventTime', 'receiptTime', 'source')}
                                      for f in snap['facts']]))
    memory = dict(
        currentReferent=None if referent is None else dict(aircraftId=referent[0], flightInstance=referent[1]),
        userIntents=[dict(kind=i.kind, aircraftId=i.aircraft_id, flightInstance=i.flight_instance, text=i.text,
                          atReplayTime=i.cutoff) for i in intents[-MAX_MEMORY_IN_PROMPT:]],
        previousAnswer=None if previous is None else dict(
            aircraftId=previous.aircraft_id, flightInstance=previous.flight_instance, atReplayTime=previous.cutoff,
            status=previous.status, citedFacts=list(previous.claims)))
    view = ('No image is attached; "observations" must be [].' if image_time is None else
            f'An image of the current view is attached, captured at {image_time:g} s. You may report what is visible '
            f'for the referent aircraft only, as observations with captureTime {image_time:g}: '
            + '; '.join(f'{k} in {list(v["values"])}' for k, v in VISUAL_KINDS.items()) + '.'
            + ('' if tap is None else f' The user tapped the image at ({tap[0]:.3f}, {tap[1]:.3f}), '
                                      'origin bottom-left, 0..1.'))
    return (
        'You are the conversational assistant of a FICTIONAL airfield replay. Answer the user about one aircraft '
        'flight, using only the facts listed below. Return JSON only, no prose or markdown.\n'
        'Schema: {"status":"answer|clarify|unknown","referent":{"aircraftId":"...","flightInstance":"..."} or null,'
        '"claims":[{"fact_id":"ID:property","value":"exact fact value","status":"exact fact status",'
        '"evidence_ids":["event_id of that fact"]}],"unknowns":["property"],'
        '"explanationChanged":true|false|null,"changesNotDiscussed":["fact_id"],'
        '"memoryUpdate":{"kind":"reference|correction|scope","aircraftId":"...","flightInstance":"..."} or null,'
        '"rationale":"one or two sentences","observations":[{"kind":"...","aircraftId":"...","value":"...",'
        '"captureTime":0}]}\n'
        'Rules: the referent must be one of the candidate flights. Claims copy a listed fact exactly. '
        'A user correction (for example "I mean its next rotation") changes the referent and is recorded as a '
        'memoryUpdate of kind "correction"; it never changes a fact. If a previous answer exists for the same '
        'flight, set explanationChanged and cite or list in changesNotDiscussed every fact that is new or changed '
        'since then; otherwise explanationChanged is null. Use "clarify" when the referent is ambiguous and '
        '"unknown" when the facts do not answer the question. Unknowns use these properties: '
        + ', '.join(FIELDS) + '.\n'
        f'Replay time (receipt cutoff): {cutoff:g} s. Selected in the app: aircraft {selection[0]}, '
        f'flight {selection[1]}.\n{view}\n'
        f'Memory: {json.dumps(memory, sort_keys=True)}\n'
        f'Candidate flights and received facts: {json.dumps(candidates, sort_keys=True)}\n'
        f'User: {question}')


def run_turn(session, data, turn, adapter, settings):
    """Serve one turn and return the stored result.

    `turn` keys: requestId, turnId, expectedRevision, aircraftId, flightInstance,
    cutoff, question, and optionally image (bytes), imageMediaType,
    imageCaptureTime, imageSha256 and tap ([x, y] in image coordinates).
    Raises ValueError for requests that cannot be served, and the state
    module's exceptions for revision, seek and request-ID conflicts.
    """
    request_id, turn_id, expected = turn['requestId'], turn['turnId'], turn['expectedRevision']
    if session.result_for(request_id) is not None:
        return session.commit(request_id, turn_id, expected)  # a retry: stored result, no second model call
    if expected != session.revision:
        raise StaleRevision(f'expected revision {expected}, current {session.revision}')
    cutoff = turn['cutoff']
    selection = (turn['aircraftId'], turn['flightInstance'])
    resolve_flight(data, *selection)
    if not 0 <= cutoff <= data['duration']:
        raise ValueError('Cutoff outside scenario')
    image_time = turn.get('imageCaptureTime') if turn.get('image') is not None else None
    if turn.get('image') is not None and (image_time is None or image_time > cutoff):
        raise ValueError('An image needs a capture time at or before the replay time')
    session.observe_cutoff(cutoff)

    receipts = receipt_times(data)
    intents, _ = session.visible_memory(cutoff, receipts)
    referent = session.current_referent(cutoff, receipts)
    new_intents = []
    if referent is None or referent[0] != selection[0]:
        new_intents.append(IntentRecord(turn_id, 'reference', *selection, turn['question'], cutoff))
        referent = selection
    previous = session.previous_turn_for(*referent, cutoff, receipts)
    prompt = build_prompt(data, cutoff, selection, referent, intents + new_intents, previous, turn['question'],
                          image_time, turn.get('tap'))
    images = () if image_time is None else (ImageInput(turn['image'], turn['imageMediaType'], image_time),)
    reply = adapter.generate(Request(request_id, (('user', prompt),), settings, images))

    proposal, raw_valid, repairs, parse_error = (None, False, (), None)
    if reply.ok:
        proposal, raw_valid, repairs, parse_error = parse_json_output(reply.text)
    if not reply.ok:
        checked = validate_proposal(None, data, cutoff)
        checked['errors'] = ['model_error:' + reply.error]
    elif parse_error:
        checked = validate_proposal(None, data, cutoff)
        checked['errors'] = [parse_error]
    else:
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
        currentReferent=dict(aircraftId=after[0], flightInstance=after[1]),
        changes=checked['changes'], imageUsedForInference=bool(images),
        provider=reply.provider, configuredModel=reply.configured_model, returnedModel=reply.returned_model,
        finishReason=reply.finish_reason.value, inputTokens=reply.usage.input_tokens,
        outputTokens=reply.usage.output_tokens, latencySeconds=round(reply.latency_seconds, 3),
        ignoredSettings=list(reply.ignored_settings), rawJsonValid=raw_valid, repairs=list(repairs),
        promptVersion=PROMPT_VERSION, validatorVersion=VALIDATOR_VERSION, repairPolicy=REPAIR_POLICY_VERSION)
    stored = session.commit(request_id, turn_id, expected, new_intents, stored_turn, result)
    return dict(stored, prompt=prompt, rawModelOutput=reply.text)
