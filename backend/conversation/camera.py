"""SUBSTANTIVE: detector camera observations as a prompt block, a checked answer field and a display line.

M2 camera evidence arms (docs/course/CAMERA_EVIDENCE_COMPARISON.md):

- ``off``: reports only; the prompt says no camera observation is available.
- ``rgb``: detector observations (seen / not detected, confidence, tracking).
- ``rgb_depth``: the same plus an apron position and on/off Stand B.

Two forms within the camera arms: ``frame`` lists only the latest observation
at or before the cutoff; ``tracked`` adds a summary computed here, never by
the model: when the vehicle was last seen and where, since when it has not
been detected, and each on/off Stand B change. Nothing after the cutoff is
read.

Observations are lower authority than reports. The model may restate one in
its ``camera`` answer field by copying a listed capture ID and its finding and
place; this module checks the copy. A camera entry never becomes a claim,
never changes a report status and cannot support a release (typed_claims
refuses it). Labels and masks from the capture are never read here: records
come from backend.camera_evidence, which reads RGB detections, depth, pose
and tracking only.
"""
import json
from pathlib import Path

CAMERA_ARMS = ('off', 'rgb', 'rgb_depth')
CAMERA_FORMS = ('frame', 'tracked')
CAMERA_DESCRIPTION_VERSION = 'camera-evidence-v1'
FINDINGS = ('seen', 'not_detected')
PLACES = ('on_stand_b', 'off_stand_b', 'unknown')
ENTRY_KEYS = {'captureId', 'finding', 'place'}
MAX_ENTRIES = 3
LABEL = 'fuel-transfer vehicle'
WARNING = 'A camera observation is not a report and cannot release a stand.'


def load_session(path, arm, scenario_id):
    """Observations of one arm from a recorded session, bound to the scenario; [] for arm 'off'."""
    if arm not in CAMERA_ARMS:
        raise ValueError('Camera arm must be one of ' + ', '.join(CAMERA_ARMS))
    if arm == 'off':
        return []
    body = json.loads(Path(path).read_text())
    if not body.get('qualified'):
        raise ValueError('The session detector is not qualified as camera evidence')
    records = [dict(r, runId=scenario_id) for r in body['observations'] if r['arm'] == arm]
    if not records:
        raise ValueError('The session has no observations for this arm')
    return sorted(records, key=lambda r: r['sourceTime'])


def finding(record):
    return 'seen' if record['visibleVehicle'] == 'present' else 'not_detected'


def place(record):
    """on/off Stand B only when the record carries a position (depth arm, tracking valid)."""
    if record.get('onStandB') is None:
        return 'unknown'
    return 'on_stand_b' if record['onStandB'] else 'off_stand_b'


def _entry(record, cutoff):
    item = dict(captureId=record['captureId'], captureTime=record['sourceTime'],
                ageSeconds=round(cutoff - record['sourceTime'], 3), finding=finding(record), place=place(record),
                trackingValid=record['trackingValid'])
    if record.get('confidence') is not None:
        item['confidence'] = record['confidence']
    if record.get('apronPositionMetres'):
        p = record['apronPositionMetres']
        item['estimatedPositionMetres'] = dict(x=round(p['x']), z=round(p['z']))
    return item


def summary(records, cutoff):
    """Deterministic tracked history up to the cutoff."""
    seen = [r for r in records if r['sourceTime'] <= cutoff and finding(r) == 'seen']
    last = seen[-1] if seen else None
    after = [r for r in records if last is not None and last['sourceTime'] < r['sourceTime'] <= cutoff]
    changes, previous = [], None
    for r in seen:
        here = place(r)
        if here == 'unknown':
            continue
        if previous is not None and here != previous[1]:
            changes.append(dict(atTime=r['sourceTime'], fromPlace=previous[1], toPlace=here, captureId=r['captureId']))
        previous = (r['sourceTime'], here)
    return dict(lastSeen=None if last is None else _entry(last, cutoff),
                notDetectedSince=after[0]['sourceTime'] if after and all(finding(r) == 'not_detected' for r in after)
                else None,
                placeChanges=changes)


def listed(records, aircraft_id, flight, cutoff, form):
    """(prompt block, {captureId: record}) for one candidate flight; (None, {}) when no record is about it."""
    mine = [r for r in records if r['aircraftId'] == aircraft_id and r['flightInstance'] == flight
            and r['sourceTime'] <= cutoff]
    if not any(r['aircraftId'] == aircraft_id and r['flightInstance'] == flight for r in records):
        return None, {}
    if not mine:
        return dict(latest=None), {}
    latest = mine[-1]
    block, allowed = dict(latest=_entry(latest, cutoff)), {latest['captureId']: latest}
    if form == 'tracked':
        history = summary(mine, cutoff)
        block['history'] = history
        by_id = {r['captureId']: r for r in mine}
        for capture in [history['lastSeen'] and history['lastSeen']['captureId']] + \
                       [c['captureId'] for c in history['placeChanges']]:
            if capture:
                allowed[capture] = by_id[capture]
    return block, allowed


def instructions(arm, form):
    """Prompt text for the camera block. Arm 'off' says that no camera evidence exists."""
    if arm == 'off':
        return 'No camera observations are available; "camera" must be [].'
    position = ('An entry may carry an estimated apron position and place (on_stand_b or off_stand_b) from depth; '
                'place is unknown when tracking was lost.' if arm == 'rgb_depth' else
                'This camera gives no position: place is always "unknown".')
    history = (' Each "history" is computed from earlier frames: lastSeen, notDetectedSince and placeChanges.'
               if form == 'tracked' else '')
    return ('Candidate flights may list "camera": observations from a fixed-view detector, lower authority than '
            'reports. ' + position + history + ' To mention one, copy its captureId, finding and place into the '
            '"camera" list (at most three; only entries listed under the referent flight). A camera observation is '
            'never a report: it cannot release a stand, complete a check or replace a report, so cite the reports '
            'for any hold or release. "not_detected" is not evidence that the vehicle has gone. Report status '
            'fields are unchanged by camera observations; when a camera observation and a report disagree, cite '
            'both and leave the disagreement unresolved.')


def check(entries, allowed):
    """Errors for the proposal's camera list against the observations listed for its referent."""
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        return ['camera_schema']
    errors, ids = [], set()
    for e in entries:
        if (not isinstance(e, dict) or set(e) != ENTRY_KEYS or not isinstance(e['captureId'], str)
                or e['finding'] not in FINDINGS or e['place'] not in PLACES):
            return ['camera_schema']
        record = allowed.get(e['captureId'])
        if record is None:
            errors.append('camera_outside_listed')
            continue
        if e['captureId'] in ids:
            errors.append('duplicate_camera')
        ids.add(e['captureId'])
        if e['finding'] != finding(record) or e['place'] != place(record):
            errors.append('camera_value_mismatch')
    return errors


def describe(record, cutoff):
    """Fixed display wording, the same as the replay card."""
    age = int(round(cutoff - record['sourceTime']))
    head = f"Camera observation at {record['sourceTime']:g} s ({age} s old)"
    if finding(record) == 'not_detected':
        body = f'{LABEL} not detected (not proof it has gone)'
    elif not record['trackingValid']:
        body = f'{LABEL} seen; position unknown (tracking lost)'
    elif place(record) == 'unknown':
        body = f'{LABEL} seen in view'
    else:
        p = record['apronPositionMetres']
        body = (f"{LABEL} seen {'on' if record['onStandB'] else 'off'} Stand B "
                f"(est. x {p['x']:.0f} m, z {p['z']:.0f} m)")
    return f'{head}: {body}. {WARNING}'
