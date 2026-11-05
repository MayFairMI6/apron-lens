"""Narrow history-selection validation; never supplies facts or resolves ambiguity.

Candidates must be the unchanged same-cutoff eligible snapshots. This guard only
recognizes a literal existing value after an explicit historical relation. Other
history language remains the model's responsibility and the ordinary evidence
validator continues to validate every selected claim.
"""
import json
import re

HISTORY_ERROR = 'historical_fact_missing'


def _mentioned(value, text):
    return re.search(r'(?<!\w)' + re.escape(str(value)) + r'(?!\w)', text, re.I)


def history_error(proposal, prompt, candidates):
    """Return a retry reason for a narrowly recognized missing historical fact.

    `prompt` is the immutable selector prompt, with Memory/Question delimiters.
    Unrecognized or ambiguous requests return None, without editing the proposal.
    """
    try:
        question = prompt.rsplit('\nQuestion: ', 1)[1]
        memory = json.JSONDecoder().raw_decode(prompt.split('\nMemory: ', 1)[1])[0]
    except (IndexError, ValueError, TypeError):
        return None
    if not isinstance(proposal, dict) or not proposal.get('referent'):
        return None
    if re.search(r'\b(compare|comparison|difference|versus)\b|\bchanged?\s+from\b', question, re.I):
        return None
    properties = []
    if re.search(r'\bstand\b', question, re.I):
        properties.append('stand')
    if re.search(r'\btobt\b|\btarget\s+off[- ]block\b|\boff[- ]block\s+(?:time|estimate)\b', question, re.I):
        properties.append('tobt')
    if len(properties) != 1:
        return None
    prop = properties[0]
    if re.search(r'\b(other|another|either|whichever)\b|\b(previous|first|second)\s+(aircraft|flight|rotation)\b', question, re.I):
        return None
    explicit = [c for c in candidates if any(_mentioned(c[k], question) for k in ('aircraftId', 'flightInstance'))]
    if len(explicit) > 1:
        return None
    if explicit:
        intended = {k: explicit[0][k] for k in ('aircraftId', 'flightInstance')}
    elif re.search(r'\b(it|its|that aircraft|same aircraft|that flight|same flight)\b', question, re.I):
        intended = memory.get('currentReferent')
    else:
        return None
    if not intended or proposal['referent'] != intended:
        return None
    candidate = next((c for c in candidates if all(c.get(k) == intended.get(k)
                     for k in ('aircraftId', 'flightInstance'))), None)
    if candidate is None:
        return None
    facts = [f for f in candidate['facts'] if f['property'] == prop]
    anchors = []
    for fact in facts:
        # Full literal-value matching avoids E4 matching E40 or 14:25 matching
        # 14:250. Quotes and an optional property label are permitted.
        value = re.escape(str(fact['value']))
        label = r'(?:stand\s+)?' if prop == 'stand' else r'(?:tobt\s+)?'
        relation = r'\b(?:before|preceding|prior\s+to)\s+'
        pattern = relation + label + r'[\"\'“‘]?(?<!\w)' + value + r'(?!\w|[:-]\w)[\"\'”’]?'
        if re.search(pattern, question, re.I):
            anchors.append(fact)
    # Repeated values/ambiguous anchors do not have a unique historical bound.
    if len(anchors) != 1:
        return None
    anchor = anchors[0]
    try:
        prior = [f for f in facts if f['status'] == 'superseded'
                 and f['eventTime'] < anchor['eventTime']
                 and f['receiptTime'] <= anchor['receiptTime']]
    except (KeyError, TypeError):
        return None
    if not prior:
        return None
    selected = {c.get('fact_id') for c in proposal.get('claims', []) if isinstance(c, dict)}
    # This validates historical coverage, not which predecessor is semantically
    # intended. Never insert a historical ID or rewrite the model's selection.
    if not any(f['fact_id'] in selected for f in prior):
        return HISTORY_ERROR
    return None
