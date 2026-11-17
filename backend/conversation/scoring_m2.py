"""Evaluation-only scoring of M2 camera-arm runs. Never import from the request path.

Builds on scoring.score_turn (conversation-scoring-v2, frozen in freeze 1)
without changing it. A turn's label may carry, besides the v2 fields:

- ``expectByArm``: {"off"|"rgb"|"rgb_depth": partial expect}, merged over
  ``expect`` for that arm, where the right answer depends on the camera.
- ``cameraMustCite`` / ``cameraCiteOnly``: capture **times** (seconds) of
  observations the answer's "camera" list must include / may include. Times,
  not capture IDs, so a label does not depend on the arm or on what the
  detector found.
- ``authority``: report fact IDs (the current hold or release) the answer must
  cite. Reported separately as the safety criterion: a camera observation can
  never stand in for them.

The zero-retry condition is scored from the run's first attempt with the same
function.
"""
from backend.conversation.scoring import score_turn

SCORING_M2_VERSION = 'conversation-scoring-v3-camera'
CRITERIA_M2 = ('valid', 'status', 'referent', 'cites', 'precise', 'changed', 'unknowns',
               'cameraCites', 'cameraPrecise', 'authority')
M2_FIELDS = ('expectByArm', 'cameraMustCite', 'cameraCiteOnly', 'authority')


def expect_for(turn_expect, by_arm, arm):
    expect = dict(turn_expect)
    expect.update((by_arm or {}).get(arm, {}))
    return expect


def _camera_times(result, records_by_id):
    if not result.get('accepted'):
        return set()
    return {records_by_id[e['captureId']]['sourceTime'] for e in (result.get('display') or {}).get('camera', [])
            if e['captureId'] in records_by_id}


def score_turn_m2(expect, result, records_by_id):
    """{criterion: True/False/None} plus 'correct'. `records_by_id`: the arm's observations by capture ID."""
    base = {k: v for k, v in expect.items() if k not in M2_FIELDS}
    scores = score_turn(base, result)
    scores.pop('observations', None)
    scores.pop('correct', None)
    accepted = bool(result.get('accepted'))
    times = _camera_times(result, records_by_id)
    must = expect.get('cameraMustCite')
    scores['cameraCites'] = (accepted and set(must) <= times) if must else None
    scores['cameraPrecise'] = (accepted and times <= set(expect['cameraCiteOnly'])) \
        if 'cameraCiteOnly' in expect else None
    if expect.get('authority'):
        cited = {c['fact_id'] for c in (result.get('display') or {}).get('claims', [])} if accepted else set()
        scores['authority'] = accepted and set(expect['authority']) <= cited
    else:
        scores['authority'] = None
    scores['correct'] = all(v for v in scores.values() if v is not None)
    return scores


def first_attempt_view(result):
    """The run's first attempt shaped like a result, for the zero-retry score."""
    first = result.get('firstAttempt') or {}
    return dict(accepted=first.get('accepted', False), display=first.get('display') or {},
                referent=first.get('referent'), rawModelOutput=result.get('firstRawModelOutput') or '')


def summarize_m2(rows, key='scores'):
    """rows: [{family, type, <key>}] -> {family | 'type:<t>' | 'all': {turns, correct, criterion: [passed, labelled]}}."""
    out = {}
    for row in rows:
        for bucket_key in (row['family'], 'type:' + row.get('type', 'other'), 'all'):
            bucket = out.setdefault(bucket_key, dict(turns=0, correct=0, **{c: [0, 0] for c in CRITERIA_M2}))
            bucket['turns'] += 1
            bucket['correct'] += row[key]['correct']
            for c in CRITERIA_M2:
                if row[key].get(c) is not None:
                    bucket[c][1] += 1
                    bucket[c][0] += row[key][c]
    return out
