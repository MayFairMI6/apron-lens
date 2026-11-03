"""Live training turn with completeness accounting; frozen conversation runner is unchanged.

Uses the existing prompt, identity and validator helpers. Training selector recovery
is audited by TrainingAdapter and this path exposes its failure honestly.
"""
from modelaccess.contract import ImageInput, Request
from modelaccess.repair import REPAIR_POLICY_VERSION, parse_json_output
from backend.conversation.context import receipt_times
from backend.conversation.identity import resolve_flight
from backend.conversation.state import AssistantTurn, IntentRecord, StaleRevision
from backend.conversation.validate import VALIDATOR_VERSION, validate_proposal
from backend.conversation.turns import (PROMPT_VERSION, REFERENT_RULE_VERSION, candidate_flights,
                                        apply_correction, away_intervals, build_prompt)

def run_turn(session, data, turn, adapter, settings):
    """Serve one turn and return the stored result.

    `turn` keys: requestId, turnId, expectedRevision, aircraftId, flightInstance,
    cutoff, question, and optionally image (bytes), imageMediaType,
    imageCaptureTime, imageSha256, tap ([x, y] in image coordinates),
    lastSeen and backInView, or awayIntervals ([start, end, start, end, ...]
    from the app). aircraftId and flightInstance are None when
    nothing is selected.
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
    away = away_intervals(turn, cutoff)
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
                          turn['question'], image_time, turn.get('tap'), away)
    images = () if image_time is None else (ImageInput(turn['image'], turn['imageMediaType'], image_time),)
    reply = adapter.generate(Request(request_id, (('user', prompt),), settings, images))

    proposal, raw_valid, repairs, parse_error = (None, False, (), None)
    referent_source = 'model'
    if reply.ok:
        proposal, raw_valid, repairs, parse_error = parse_json_output(reply.text)
    if reply.ok and reply.metadata.get('trainingEmptyAnswer'):
        checked = validate_proposal(None, data, cutoff)
        checked['errors'] = ['empty_answer_after_retry' if reply.metadata.get('trainingAttemptCount') == 2 else 'empty_answer']
        checked['display']['answer'] = ("I couldn’t produce an answer from these reports. Try again or open Sources.")
    elif not reply.ok:
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
        selectionSent=selection is not None, awayIntervals=[t for interval in away for t in interval],
        referentSource=referent_source, promptVersion=PROMPT_VERSION, referentRule=REFERENT_RULE_VERSION,
        validatorVersion=VALIDATOR_VERSION, repairPolicy=REPAIR_POLICY_VERSION)
    if 'trainingCompletenessPolicy' in reply.metadata:
        result.update({k:v for k,v in reply.metadata.items() if k.startswith('training')})
    stored = session.commit(request_id, turn_id, expected, new_intents, stored_turn, result)
    return dict(stored, prompt=prompt, rawModelOutput=reply.text)
