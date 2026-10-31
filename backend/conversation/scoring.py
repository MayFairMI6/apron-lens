"""Evaluation-only scoring of conversation runs against family labels.

Never import this module from the request path: labels are evaluation data,
as visual ground truth is (see the request-path test in
tests/test_visual_observations.py).

A family is a short scripted dialogue on one scenario. Each turn carries the
app selection, the question, an optional evidence image and an `expect` label
(field meanings: data/conversation_dev/families.json, "labelFields"). A turn is
correct when the proposal passed validation and every labelled criterion holds;
criteria are also reported separately, so a family shows where it fails.

The deterministic baseline answers without language understanding: the
referent is the current referent from the session (the app selection, or an
earlier accepted correction), claims are every received fact of that flight
with its status, and on a follow-up every changed fact is cited. It never
clarifies, never resolves a correction and reports no observations. Scored the
same way, it shows what the model adds beyond selection plus bookkeeping.
"""
import json
from pathlib import Path

from backend.conversation.context import changed_facts, snapshot
from backend.conversation.identity import resolve_flight

SCORING_VERSION = 'conversation-scoring-v1'
CRITERIA = ('valid', 'status', 'referent', 'cites', 'changed', 'unknowns', 'observations')


def load_families(path):
    return json.loads(Path(path).read_text())


def turns_of(family):
    for index, turn in enumerate(family['turns']):
        yield index, dict(turn, scenario=turn.get('scenario') or family['scenario'])


def validate_families(families, scenarios):
    """Raise ValueError if a label cannot hold for its scenario (a broken label, not a model error)."""
    seen = set()
    for family in families['families']:
        if family['id'] in seen:
            raise ValueError(f'Duplicate family {family["id"]}')
        seen.add(family['id'])
        for index, turn in turns_of(family):
            where = f'{family["id"]} turn {index + 1}'
            data = scenarios.get(turn['scenario'])
            if data is None:
                raise ValueError(f'{where}: unknown scenario {turn["scenario"]}')
            selected = turn['selected']
            resolve_flight(data, selected['aircraftId'], selected['flightInstance'])
            expect = turn['expect']
            referent = expect.get('referent') or expect.get('referentIfAnswer')
            if referent is not None:
                resolve_flight(data, referent['aircraftId'], referent['flightInstance'])
                facts = snapshot(data, referent['aircraftId'], referent['flightInstance'], turn['cutoff'])['factsById']
                missing = [f for f in expect.get('mustCite', []) if f not in facts]
                if missing:
                    raise ValueError(f'{where}: {missing} not received for the referent by {turn["cutoff"]} s')
            elif expect.get('mustCite'):
                raise ValueError(f'{where}: mustCite without a referent')
            if not set(expect['status']) <= {'answer', 'clarify', 'unknown'}:
                raise ValueError(f'{where}: unknown status')
            if turn.get('image') and turn['cutoff'] < 0:
                raise ValueError(f'{where}: bad image time')
    return families


def baseline_proposal(data, cutoff, referent, previous_cutoff=None):
    """Deterministic proposal for `referent` (aircraft, flight); see the module docstring."""
    snap = snapshot(data, *referent, cutoff)
    claims = [dict(fact_id=f['fact_id'], value=f['value'], status=f['status'], evidence_ids=[f['event_id']])
              for f in snap['facts']]
    changed = None
    if previous_cutoff is not None and previous_cutoff <= cutoff:
        changed = bool(changed_facts(snapshot(data, *referent, previous_cutoff), snap))
    return dict(status='answer', referent=dict(aircraftId=referent[0], flightInstance=referent[1]), claims=claims,
                unknowns=[], explanationChanged=changed, changesNotDiscussed=[], memoryUpdate=None,
                rationale='Deterministic baseline: every received fact of the current referent.', observations=[])


def _proposal(result):
    try:
        value = json.loads(result.get('rawModelOutput') or '')
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def score_turn(expect, result):
    """Return {criterion: True/False/None (not labelled)} plus 'correct'."""
    p = _proposal(result) or {}
    accepted = bool(result.get('accepted'))
    status = p.get('status') if accepted else None
    referent = result.get('referent') if accepted else None
    cited = {c['fact_id'] for c in (result.get('display') or {}).get('claims', [])} if accepted else set()
    scores = dict(valid=accepted, status=status in expect['status'])
    if 'referent' in expect:
        scores['referent'] = accepted and referent == expect['referent']
    elif 'referentIfAnswer' in expect:
        scores['referent'] = accepted and (status != 'answer' or referent == expect['referentIfAnswer'])
    else:
        scores['referent'] = None
    scores['cites'] = (accepted and set(expect['mustCite']) <= cited) if expect.get('mustCite') else None
    scores['changed'] = (accepted and p.get('explanationChanged') == expect['explanationChanged']) \
        if 'explanationChanged' in expect else None
    scores['unknowns'] = (accepted and set(expect['unknowns']) <= set(p.get('unknowns') or [])) \
        if expect.get('unknowns') else None
    if expect.get('observations'):
        seen = {o['kind']: o['value'] for o in (p.get('observations') or [])
                if referent and o.get('aircraftId') == referent['aircraftId']} if accepted else {}
        scores['observations'] = accepted and all(
            (kind not in seen) if value is None else seen.get(kind) == value
            for kind, value in expect['observations'].items())
    else:
        scores['observations'] = None
    scores['correct'] = all(v for v in scores.values() if v is not None)
    return scores


def summarize(rows):
    """rows: [{family, scores}] -> {family or 'all': {turns, correct, <criterion>: [passed, labelled]}}."""
    out = {}
    for row in rows:
        for key in (row['family'], 'all'):
            bucket = out.setdefault(key, dict(turns=0, correct=0, **{c: [0, 0] for c in CRITERIA}))
            bucket['turns'] += 1
            bucket['correct'] += row['scores']['correct']
            for c in CRITERIA:
                if row['scores'][c] is not None:
                    bucket[c][1] += 1
                    bucket[c][0] += row['scores'][c]
    return out
