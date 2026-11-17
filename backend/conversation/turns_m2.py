"""SUBSTANTIVE: the M2 conversational turn: camera evidence arms and one validator-guided retry.

Freeze 1 (config/conversation-freeze.json) fixes turns.py and validate.py, so
this module builds on them without editing them; freeze 2 will cover this file.

- Prompt (conversation-prompt-v7-camera): the v6 prompt from turns.build_prompt,
  with three additions. Each candidate flight the camera is about lists
  "camera" (backend/conversation/camera.listed), the reply schema gains an
  eleventh key "camera", and one paragraph explains the arm. The arm "off"
  (reports only) states that no camera observation is available, so every arm
  differs only in its camera evidence.
- Validation: validate.validate_proposal on the ten v2 keys, then camera.check
  on the "camera" list against the observations listed for the referent. A
  camera entry is displayed with fixed wording and never becomes a claim.
- Retry (validator-retry-v1): when the first reply is rejected for any reason
  other than a model error, one more call carries the rejected reply and the
  checker's error codes. Both attempts are kept, so zero retries and one retry
  are scored from the same run.

Images are not used on this path; the camera arms carry detector records as text.
"""
import json

from modelaccess.contract import Request
from modelaccess.repair import REPAIR_POLICY_VERSION, parse_json_output
from backend.conversation import camera as camera_evidence
from backend.conversation.context import receipt_times
from backend.conversation.identity import resolve_flight
from backend.conversation.state import AssistantTurn, IntentRecord, StaleRevision
from backend.conversation.turns import (REFERENT_RULE_VERSION, apply_correction, away_intervals, build_prompt,
                                         candidate_flights)
from backend.conversation.validate import VALIDATOR_VERSION, _withheld, validate_proposal

PROMPT_VERSION = 'conversation-prompt-v7-camera'
VALIDATOR_M2_VERSION = 'conversation-validator-v3-camera'
RETRY_POLICY_VERSION = 'validator-retry-v1'
_CANDIDATES = 'Candidate flights and received facts: '
_V6_SCHEMA_END = '"observations":[]}\nEvery reply has all ten keys.'


def camera_config(arm, form, records):
    if arm not in camera_evidence.CAMERA_ARMS or form not in camera_evidence.CAMERA_FORMS:
        raise ValueError('Unknown camera arm or form')
    return dict(arm=arm, form=form, records=records if arm != 'off' else [])


def build_prompt_m2(data, cutoff, selection, referent, intents, previous_by_flight, question, away, camera):
    text = build_prompt(data, cutoff, selection, referent, intents, previous_by_flight, question, away=away)
    head, tail = text.split(_CANDIDATES, 1)
    candidates, end = json.JSONDecoder().raw_decode(tail)
    if camera['arm'] != 'off':
        for c in candidates:
            block, _ = camera_evidence.listed(camera['records'], c['aircraftId'], c['flightInstance'], cutoff,
                                              camera['form'])
            if block is not None:
                c['camera'] = block
    if head.count(_V6_SCHEMA_END) != 1 or head.count('\nMemory: ') != 1:
        raise RuntimeError('The v6 prompt layout changed; the M2 prompt cannot be built')
    head = head.replace(_V6_SCHEMA_END, '"observations":[],"camera":[{"captureId":"...","finding":"'
                        + '|'.join(camera_evidence.FINDINGS) + '","place":"' + '|'.join(camera_evidence.PLACES)
                        + '"}]}\nEvery reply has all eleven keys.')
    head = head.replace('\nMemory: ', '\n' + camera_evidence.instructions(camera['arm'], camera['form'])
                        + '\nMemory: ')
    return head + _CANDIDATES + json.dumps(candidates, sort_keys=True) + tail[end:]


def allowed_for(camera, cutoff):
    def allowed(aircraft, flight):
        if camera['arm'] == 'off':
            return {}
        return camera_evidence.listed(camera['records'], aircraft, flight, cutoff, camera['form'])[1]
    return allowed


def validate_m2(proposal, data, cutoff, previous_turn, allowed):
    """validate_proposal on the ten v2 keys, then the camera list."""
    if not isinstance(proposal, dict) or 'camera' not in proposal:
        return _withheld(['schema'])
    base = {k: v for k, v in proposal.items() if k != 'camera'}
    checked = validate_proposal(base, data, cutoff, previous_turn)
    if not checked['accepted']:
        return checked
    entries = proposal['camera']
    referent = proposal['referent']
    if referent is None:
        if entries:
            return _withheld(['camera_without_referent'])
        checked['display'] = dict(checked['display'], camera=[])
        return checked
    listed = allowed(referent['aircraftId'], referent['flightInstance'])
    errors = camera_evidence.check(entries, listed)
    if errors:
        return _withheld(sorted(set(errors)), checked['snapshot'], checked['changes'])
    lines = [camera_evidence.describe(listed[e['captureId']], cutoff) for e in entries]
    display = dict(checked['display'], camera=entries)
    if lines:
        answer = display['answer'] if display['answer'] not in ('No supported claim selected.',) else ''
        display['answer'] = '\n\n'.join([x for x in (answer, *lines) if x])
    return dict(checked, display=display)


def retry_prompt(prompt, raw, errors):
    return (prompt + '\n\nYour previous reply was:\n' + (raw or '')[:4000]
            + '\nThe checker rejected it with these error codes: ' + ', '.join(errors)
            + '. Return one corrected JSON reply with all eleven keys, following the rules above.')


def _attempt(adapter, request_id, prompt, settings, data, cutoff, session, receipts, allowed):
    reply = adapter.generate(Request(request_id, (('user', prompt),), settings))
    proposal, raw_valid, repairs, referent_source = None, False, (), 'model'
    if not reply.ok:
        checked = _withheld(['model_error:' + reply.error])
    else:
        proposal, raw_valid, repairs, parse_error = parse_json_output(reply.text)
        if parse_error:
            checked = _withheld([parse_error])
        else:
            proposal, referent_source = apply_correction(data, proposal)
            ref = proposal.get('referent') if isinstance(proposal, dict) else None
            prior = None
            if isinstance(ref, dict) and isinstance(ref.get('aircraftId'), str) \
                    and isinstance(ref.get('flightInstance'), str):
                prior = session.previous_turn_for(ref['aircraftId'], ref['flightInstance'], cutoff, receipts)
            checked = validate_m2(proposal, data, cutoff, prior, allowed)
    return dict(reply=reply, proposal=proposal, checked=checked, rawJsonValid=raw_valid, repairs=list(repairs),
                referentSource=referent_source)


def run_turn_m2(session, data, turn, adapter, settings, camera, retry=True):
    """Serve one M2 turn and return the stored result (turns.run_turn's contract, text only).

    `camera` comes from camera_config. The result adds cameraArm, cameraForm,
    attempts (1 or 2) and firstAttempt (accepted, errors, display) for scoring
    the zero-retry condition.
    """
    request_id, turn_id, expected = turn['requestId'], turn['turnId'], turn['expectedRevision']
    if session.result_for(request_id) is not None:
        return session.commit(request_id, turn_id, expected)
    if expected != session.revision:
        raise StaleRevision(f'expected revision {expected}, current {session.revision}')
    cutoff = turn['cutoff']
    selection = (turn['aircraftId'], turn['flightInstance']) if turn.get('aircraftId') else None
    if selection is not None:
        resolve_flight(data, *selection)
    if not 0 <= cutoff <= data['duration']:
        raise ValueError('Cutoff outside scenario')
    away = away_intervals(turn, cutoff)
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
    prompt = build_prompt_m2(data, cutoff, selection, referent, intents + new_intents, previous_by_flight,
                             turn['question'], away, camera)
    allowed = allowed_for(camera, cutoff)
    first = _attempt(adapter, request_id, prompt, settings, data, cutoff, session, receipts, allowed)
    final, attempts, second_prompt = first, 1, None
    if retry and not first['checked']['accepted'] and first['reply'].ok:
        second_prompt = retry_prompt(prompt, first['reply'].text, first['checked']['errors'])
        final = _attempt(adapter, request_id + '-retry', second_prompt, settings, data, cutoff, session, receipts,
                         allowed)
        attempts = 2

    checked, proposal, reply = final['checked'], final['proposal'], final['reply']
    stored_turn = None
    if checked['accepted']:
        p = proposal
        mu = p['memoryUpdate']
        if mu is not None:
            new_intents.append(IntentRecord(turn_id, mu['kind'], mu['aircraftId'], mu['flightInstance'],
                                            turn['question'], cutoff))
        elif selection is None and p['referent'] is not None and \
                (p['referent']['aircraftId'], p['referent']['flightInstance']) != referent:
            new_intents.append(IntentRecord(turn_id, 'reference', p['referent']['aircraftId'],
                                            p['referent']['flightInstance'], turn['question'], cutoff))
        if p['referent'] is not None:
            snap = checked['snapshot']
            stored_turn = AssistantTurn(
                turn_id, request_id, p['referent']['aircraftId'], p['referent']['flightInstance'], cutoff,
                evidence_ids=tuple(sorted({e for c in p['claims'] for e in c['evidence_ids']})),
                claims=tuple(c['fact_id'] for c in p['claims']), status=p['status'],
                evidence_digest=snap['evidenceDigest'], interpretation=p['rationale'] or None, observations=())
    after = (new_intents[-1].aircraft_id, new_intents[-1].flight_instance) if new_intents else referent
    latency = first['reply'].latency_seconds + (final['reply'].latency_seconds if attempts == 2 else 0)
    usage = [a['reply'].usage for a in ((first, final) if attempts == 2 else (first,))]
    result = dict(
        requestId=request_id, turnId=turn_id, sessionId=session.session_id, cutoff=cutoff,
        accepted=checked['accepted'], errors=checked['errors'], display=checked['display'],
        referent=proposal['referent'] if checked['accepted'] else None,
        currentReferent=None if after is None else dict(aircraftId=after[0], flightInstance=after[1]),
        changes=checked['changes'], imageUsedForInference=False,
        provider=reply.provider, configuredModel=reply.configured_model, returnedModel=reply.returned_model,
        finishReason=reply.finish_reason.value,
        inputTokens=sum(u.input_tokens or 0 for u in usage), outputTokens=sum(u.output_tokens or 0 for u in usage),
        latencySeconds=round(latency, 3), ignoredSettings=list(reply.ignored_settings),
        rawJsonValid=final['rawJsonValid'], repairs=final['repairs'],
        selectionSent=selection is not None, awayIntervals=[t for interval in away for t in interval],
        referentSource=final['referentSource'], promptVersion=PROMPT_VERSION, referentRule=REFERENT_RULE_VERSION,
        validatorVersion=VALIDATOR_VERSION, validatorM2Version=VALIDATOR_M2_VERSION,
        repairPolicy=REPAIR_POLICY_VERSION, retryPolicy=RETRY_POLICY_VERSION if retry else 'none',
        cameraArm=camera['arm'], cameraForm=camera['form'],
        cameraDescriptionVersion=camera_evidence.CAMERA_DESCRIPTION_VERSION, attempts=attempts,
        firstAttempt=dict(accepted=first['checked']['accepted'], errors=first['checked']['errors'],
                          display=first['checked']['display'],
                          referent=first['proposal'].get('referent') if first['checked']['accepted'] else None))
    stored = session.commit(request_id, turn_id, expected, new_intents, stored_turn, result)
    return dict(stored, prompt=prompt, retryPrompt=second_prompt, rawModelOutput=reply.text,
                firstRawModelOutput=first['reply'].text)
