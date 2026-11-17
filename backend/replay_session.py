"""Read-only controller replay over an immutable scenario.

The replay has its own clock and never touches the lesson clock, the scenario
driver, reservations, releases or movement. One source cutoff selects the scene,
the eligible reports and observations, and the assistant's context. Controller
notes are annotations: they record what a reviewer wrote at a cutoff and change
nothing else. Authored synthetic scenarios only; no operational authority.
"""
import bisect
import copy
import hashlib
import json
import secrets
import threading
import time
from pathlib import Path

from backend.bluebird_inbound import BLUEBIRD_787, TITLE as BLUEBIRD_TITLE, build_bluebird_inbound
from backend.conversation.context import changed_facts, receipt_times, snapshot
from backend.conversation.state import DEVELOPMENT, SessionState
from backend.evidence import classify, received_facts, validate_scenario
from backend.fleet_scenarios import FLEET_DEMONSTRATIONS, TITLES as FLEET_TITLES, build_fleet
from backend.fleet_incident_variations import FLEET_VARIATIONS, VARIATION_TITLES, build_fleet_variation
from backend.lessons import build_lesson
from backend.stand_clearance_lesson import STAND_CLEARANCE_LESSON

LEAD_CASE = 'fleet_a380_go_around'
# Presentation order: the A380 go-around leads and the 787 handoff follows.
REPLAY_CASES = ((LEAD_CASE, BLUEBIRD_787) + tuple(c for c in FLEET_DEMONSTRATIONS if c != LEAD_CASE) + FLEET_VARIATIONS
                + (STAND_CLEARANCE_LESSON,))  # Stand B: engineering and camera-evidence replay
TITLES = {**FLEET_TITLES, **VARIATION_TITLES, BLUEBIRD_787: BLUEBIRD_TITLE,
          STAND_CLEARANCE_LESSON: 'An arriving stand not clear of equipment'}
CAMERA_ARMS = ('rgb', 'rgb_depth')
RATES = (1., 4., 10.)
MAX_NOTE_CHARS = 280
MAX_QUESTION_CHARS = 400
TAIL_SECONDS = 30.
SOURCE_KINDS = {
    'bluebird-synthetic-observation': ('airborne_observation', 'Airborne observation'),
    'camera': ('camera_observation', 'Camera observation'),
}
AIRPORT_REPORT = ('airport_report', 'Airport report')


class ReplayConflict(ValueError):
    """The request names another run, an old view, or reuses an ID differently."""


def source_kind(source):
    return SOURCE_KINDS.get(source, AIRPORT_REPORT)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _position(aircraft, t):
    """Authored motion at source time `t`; linear between recorded samples."""
    points = aircraft['waypoints']
    i = bisect.bisect_right([p['t'] for p in points], t)
    if i == 0:
        a = b = points[0]
    elif i == len(points):
        a = b = points[-1]
    else:
        a, b = points[i - 1], points[i]
    u = 0. if b['t'] == a['t'] else (t - a['t']) / (b['t'] - a['t'])
    row = {k: a.get(k, 0.) + (b.get(k, 0.) - a.get(k, 0.)) * u for k in ('x', 'y', 'z', 'heading', 'pitch')}
    row['gearRetracted'] = bool(a.get('gearRetracted', False))
    return row


class ReplaySession:
    def __init__(self, seed, exercise=LEAD_CASE, clock=time.monotonic, audit_path=None,
                 camera_session=None, camera_arm=None):
        if exercise not in REPLAY_CASES:
            raise ValueError('Unknown replay case')
        builder = (build_bluebird_inbound if exercise == BLUEBIRD_787 else
                   build_fleet_variation if exercise in FLEET_VARIATIONS else
                   build_lesson if exercise == STAND_CLEARANCE_LESSON else build_fleet)
        world, _, _ = builder(seed, exercise)
        validate_scenario(world)
        self.seed, self.exercise, self.clock = seed, exercise, clock
        self.title = TITLES[exercise]
        self.audit_path = Path(audit_path) if audit_path else None
        self.run_id = secrets.token_hex(10)
        # The hash covers the authored content only, so one seed has one hash across runs.
        self.scenario_hash = _digest({k: v for k, v in world.items() if k != 'scenarioId'})
        world['scenarioId'] = 'REPLAY-' + self.run_id
        self._frozen = json.dumps(world, sort_keys=True)
        self._world = json.loads(self._frozen)
        self._receipts = receipt_times(self._world)
        self.markers = self._build_markers()
        self.end = min(float(self._world['duration']), max(m['time'] for m in self.markers) + TAIL_SECONDS)
        self.lock = threading.RLock()
        self.view_revision = 0
        self.cutoff = 0.
        self.playing = False
        self.rate = 1.
        self.last_wall = clock()
        self.selected = 'A1'
        self.notes = []
        self.observations = []
        self.camera_arm = None
        if camera_session is not None:
            self._load_camera_session(camera_session, camera_arm)
        self.memory_intents = []
        self.memory_turns = []
        self.pending = None
        self._actions = {}
        self._answers = {}
        self._log('replay_start', seed=seed, exercise=exercise, scenarioHash=self.scenario_hash)

    def _load_camera_session(self, path, arm):
        """Recorded camera observations for one evidence arm, bound to this run.

        Only Stand B has a recorded session. The observations stay separate from
        reports and from the scenario; they never change releases or movement.
        """
        if self.exercise != STAND_CLEARANCE_LESSON:
            raise ValueError('Only the Stand B replay has a recorded camera session')
        if arm not in CAMERA_ARMS:
            raise ValueError('Choose a camera evidence arm: rgb or rgb_depth')
        body = json.loads(Path(path).read_text())
        if not body.get('qualified'):
            raise ValueError('The session detector is not qualified as camera evidence')
        self.camera_arm = arm
        self.camera_session = dict(detector=body['detector'], threshold=body['threshold'], version=body['version'])
        for index, record in enumerate(r for r in body['observations'] if r['arm'] == arm):
            if record['runId'] != 'SESSION' or not 0 <= record['sourceTime'] <= self._world['duration']:
                raise ValueError('Unexpected camera session record')
            self.observations.append(dict(record, id=f'C{index + 1:03d}', runId=self.run_id,
                                          captureTime=float(record['sourceTime']), sourceLabel='Camera observation'))
        self.observations.sort(key=lambda o: (o['captureTime'], o['id']))

    # ---- immutable scenario -------------------------------------------------------
    def scenario(self):
        """A private copy; callers cannot alter the replayed scenario."""
        return json.loads(self._frozen)

    def verify_unchanged(self):
        if json.dumps(self._world, sort_keys=True) != self._frozen:
            raise RuntimeError('Replay scenario changed; the replay is read-only')
        return self.scenario_hash

    def _aircraft(self, aircraft_id):
        found = next((a for a in self._world['aircraft'] if a['id'] == aircraft_id), None)
        if found is None:
            raise ValueError('Unknown aircraft')
        return found

    def _build_markers(self):
        """Navigation points. Report markers carry no report content."""
        markers = []
        for e in self._world['events']:
            kind, label = source_kind(e['source'])
            markers.append(dict(id='R-' + e['id'], kind='received', sourceKind=kind, time=float(e['receiptTime']),
                                eventTime=float(e['eventTime']), aircraftId=e['aircraftId'],
                                flightInstance=e['flightInstance'], label=f"{label} received · {e['flightInstance']}"))
        for a in self._world['aircraft']:
            for p in a.get('phases', []):
                if 0 < p['t'] < self._world['duration'] and p['id'] not in ('outside_area', 'parked'):
                    markers.append(dict(id=f"P-{a['id']}-{p['id']}", kind='movement', sourceKind='authored_motion',
                                        time=float(p['t']), eventTime=float(p['t']), aircraftId=a['id'],
                                        flightInstance=a['flightInstance'], label=p['label']))
        return sorted(markers, key=lambda m: (m['time'], m['id']))

    def _log(self, event, **values):
        if self.audit_path:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open('a') as stream:
                stream.write(json.dumps(dict(recordVersion=1, event=event, runId=self.run_id,
                                             cutoff=getattr(self, 'cutoff', 0.),
                                             viewRevision=getattr(self, 'view_revision', 0), **values)) + '\n')

    # ---- replay clock -------------------------------------------------------------
    def advance(self):
        with self.lock:
            now = self.clock()
            if now < self.last_wall:
                raise ValueError('Monotonic clock moved backward')
            if self.playing:
                self.cutoff = min(self.end, self.cutoff + (now - self.last_wall) * self.rate)
                if self.cutoff >= self.end:
                    self.playing = False
                    self.view_revision += 1
            self.last_wall = now
            return self.cutoff

    def _changed(self):
        self.view_revision += 1

    # ---- one cutoff for scene, evidence and context -------------------------------
    def _reports(self, cutoff):
        rows = []
        facts = received_facts(self._world, cutoff)
        status = {}
        for a in self._world['aircraft']:
            scoped = [f for f in facts if f['aircraftId'] == a['id'] and f['flightInstance'] == a['flightInstance']]
            status.update({f['fact_id']: f['status'] for f in classify(scoped, cutoff)})
        for e in self._world['events']:
            if e['receiptTime'] > cutoff:
                continue
            kind, label = source_kind(e['source'])
            rows.append(dict(id=e['id'], aircraftId=e['aircraftId'], flightInstance=e['flightInstance'],
                             source=e['source'], sourceKind=kind, sourceLabel=label,
                             eventTime=e['eventTime'], receiptTime=e['receiptTime'],
                             ageSeconds=round(cutoff - e['eventTime'], 3),
                             sinceReceiptSeconds=round(cutoff - e['receiptTime'], 3), message=e['message'],
                             facts=[dict(factId=e['id'] + ':' + f['property'], property=f['property'], value=f['value'],
                                         status=status.get(e['id'] + ':' + f['property'], 'current'))
                                    for f in e['facts']]))
        return rows

    def _scene(self, cutoff):
        scene = []
        for a in self._world['aircraft']:
            phases = [p for p in a.get('phases', []) if p['t'] <= cutoff]
            visible = not a.get('hidden', False) and cutoff >= a.get('visibleFrom', 0)
            row = dict(aircraftId=a['id'], flightInstance=a['flightInstance'], aircraftType=a.get('aircraftType', ''),
                       visible=visible, phase=phases[-1]['id'] if phases else '',
                       phaseLabel=phases[-1]['label'] if phases else '')
            if visible:
                row.update(_position(a, cutoff))
            scene.append(row)
        return scene

    @staticmethod
    def _marker_at(marker, cutoff):
        """A marker ahead of the cutoff keeps its position and kind only."""
        if marker['time'] <= cutoff:
            return dict(marker, passed=True)
        return dict(marker, passed=False, eventTime=-1.,
                    label='Movement change' if marker['kind'] == 'movement' else 'Report or observation received')

    def changes(self, aircraft_id, earlier, later):
        """Fact IDs new or re-classified for one flight between two cutoffs."""
        if not 0 <= earlier <= later <= self.end:
            raise ValueError('Cutoffs outside the replay')
        flight = self._aircraft(aircraft_id)['flightInstance']
        return changed_facts(snapshot(self._world, aircraft_id, flight, earlier),
                             snapshot(self._world, aircraft_id, flight, later))

    def view(self):
        with self.lock:
            cutoff = self.advance()
            self.verify_unchanged()
            reports = self._reports(cutoff)
            cameras = [copy.deepcopy(o) for o in self.observations if o['captureTime'] <= cutoff]
            for o in cameras:
                o['ageSeconds'] = round(cutoff - o['captureTime'], 3)
            selected = self._aircraft(self.selected)
            passed = [m['time'] for m in self.markers if m['time'] < cutoff]
            previous = passed[-1] if passed else 0.
            return dict(
                runId=self.run_id, viewRevision=self.view_revision, exercise=self.exercise, title=self.title,
                cutoff=cutoff, end=self.end, playing=self.playing, rate=self.rate if self.playing else 0.,
                readOnly=True, scenarioId=self._world['scenarioId'], scenarioHash=self.scenario_hash,
                selectedAircraft=self.selected, selectedFlight=selected['flightInstance'],
                scene=self._scene(cutoff), reports=reports, cameraObservations=cameras,
                selectedReports=[r for r in reports if r['aircraftId'] == self.selected],
                changedSince=dict(cutoff=previous, factIds=self.changes(self.selected, previous, cutoff)),
                timeline=[self._marker_at(m, cutoff) for m in self.markers],
                notes=copy.deepcopy(self.notes), assistantPending=self.pending is not None,
                evidenceDigest=_digest([[r['id'] for r in reports], [o['id'] for o in cameras]]))

    def snapshot(self):
        """Scene feed in the shape the existing viewer reads, driven by the replay cutoff."""
        with self.lock:
            view = self.view()
            return dict(serverTime=view['cutoff'], scenario=self.scenario(), synthetic=True, exerciseTitle=self.title,
                        clock=dict(runId=self.run_id, revision=self.view_revision, rate=view['rate'], state='replay',
                                   nextBoundary=view['cutoff'] if not self.playing else self.end),
                        # The existing viewer builds its scene from this block. Its revision
                        # is fixed for the run so a seek does not rebuild the screen.
                        training=dict(runId=self.run_id, revision=0, mode='replay', phase='practice',
                                      title=self.title, objective='', exercise=self.exercise,
                                      targetAircraft='A1', spotlightId='', spotlightAircraft='',
                                      sourceTime=view['cutoff'], rate=view['rate'], nextBoundary=view['end']),
                        replay={k: v for k, v in view.items() if k != 'scene'})

    # ---- controls -----------------------------------------------------------------
    def _begin(self, body, id_key):
        if not isinstance(body, dict):
            raise ValueError('Invalid replay request')
        request_id = body.get(id_key)
        if not isinstance(request_id, str) or not 1 <= len(request_id) <= 80:
            raise ValueError('Request ID required')
        if body.get('runId') != self.run_id:
            raise ReplayConflict('This replay has ended')
        return request_id, json.dumps(body, sort_keys=True, ensure_ascii=False)

    def action(self, body):
        with self.lock:
            self.advance()
            action_id, fingerprint = self._begin(body, 'actionId')
            if action_id in self._actions:
                old, result = self._actions[action_id]
                if old != fingerprint:
                    raise ReplayConflict('Action ID reused with different data')
                return copy.deepcopy(result)
            if action_id in self._answers or (self.pending and self.pending['requestId'] == action_id):
                raise ReplayConflict('Action ID already used by a question')
            if body.get('viewRevision') != self.view_revision:
                raise ReplayConflict('The replay view changed; refresh and try again')
            action = body.get('action')
            if action in ('seek', 'jump'):
                if action == 'jump':
                    marker = next((m for m in self.markers if m['id'] == body.get('markerId')), None)
                    if marker is None:
                        raise ValueError('Unknown timeline marker')
                    target = marker['time']
                    if marker['aircraftId'] != self.selected and body.get('select') is True:
                        self.selected = marker['aircraftId']
                else:
                    target = body.get('cutoff')
                    # The app's slider sends 32-bit floats; allow rounding at the end.
                    if isinstance(target, bool) or not isinstance(target, (int, float)) or not 0 <= target <= self.end + .01:
                        raise ValueError('Cutoff outside the replay')
                    target = min(target, self.end)
                self.cutoff = float(target)
                self.playing = False
                self._changed()
            elif action == 'select':
                self._aircraft(body.get('aircraftId'))
                if body['aircraftId'] != self.selected:
                    self.selected = body['aircraftId']
                    self._changed()
            elif action == 'play':
                rate = body.get('rate', 1.)
                if isinstance(rate, bool) or rate not in RATES:
                    raise ValueError('Unsupported replay rate')
                if self.cutoff >= self.end:
                    raise ReplayConflict('The replay is at its end; seek back to play')
                if not self.playing or rate != self.rate:
                    self.playing, self.rate = True, float(rate)
                    self._changed()
            elif action == 'pause':
                if self.playing:
                    self.playing = False
                    self._changed()
            elif action == 'note':
                text = body.get('text')
                if not isinstance(text, str) or not text.strip() or len(text) > MAX_NOTE_CHARS:
                    raise ValueError(f'Enter a note between 1 and {MAX_NOTE_CHARS} characters')
                aircraft = self._aircraft(self.selected)
                # A note is tied to the run and the cutoff it was written at. It
                # never changes the view, so a pending answer stays current.
                self.notes.append(dict(
                    id=f'N{len(self.notes) + 1:03d}', runId=self.run_id, cutoff=self.cutoff, text=text.strip(),
                    aircraftId=self.selected, flightInstance=aircraft['flightInstance'], kind='annotation',
                    evidenceIds=[e['id'] for e in self._world['events']
                                 if e['receiptTime'] <= self.cutoff and e['aircraftId'] == self.selected],
                    scenarioHash=self.scenario_hash))
            else:
                raise ValueError('Unknown replay action')
            self._log('replay_action', action=action, actionId=action_id, selected=self.selected)
            result = self.view()
            self._actions[action_id] = (fingerprint, copy.deepcopy(result))
            return result

    def observe(self, body):
        """Record what the AR camera saw at a capture time; lower authority than a report."""
        with self.lock:
            self.advance()
            action_id, fingerprint = self._begin(body, 'actionId')
            if action_id in self._actions:
                old, result = self._actions[action_id]
                if old != fingerprint:
                    raise ReplayConflict('Action ID reused with different data')
                return copy.deepcopy(result)
            capture = body.get('captureTime')
            if isinstance(capture, bool) or not isinstance(capture, (int, float)) or not 0 <= capture <= self.cutoff + .05:
                raise ValueError('Capture time is ahead of the replay cutoff')
            aircraft = self._aircraft(body.get('aircraftId'))
            kind, value = body.get('kind'), body.get('value')
            confidence = body.get('confidence')
            if not all(isinstance(v, str) and 1 <= len(v) <= 80 for v in (kind, value)):
                raise ValueError('Observation kind and value required')
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                raise ValueError('Observation confidence must be between 0 and 1')
            self.observations.append(dict(
                id=f'C{len(self.observations) + 1:03d}', runId=self.run_id, source='camera',
                sourceKind='camera_observation', sourceLabel='Camera observation', aircraftId=aircraft['id'],
                flightInstance=aircraft['flightInstance'], kind=kind, value=value, confidence=float(confidence),
                captureTime=float(capture)))
            self.observations.sort(key=lambda o: (o['captureTime'], o['id']))
            result = self.view()
            self._actions[action_id] = (fingerprint, copy.deepcopy(result))
            return result

    # ---- assistant context --------------------------------------------------------
    def begin_question(self, body):
        """Freeze the view a question is asked under. Returns (ticket, stored result)."""
        with self.lock:
            self.advance()
            request_id, fingerprint = self._begin(body, 'requestId')
            question = body.get('question')
            if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION_CHARS:
                raise ValueError('Enter a question')
            stored = self._answers.get(request_id)
            if stored:
                if stored[0] != fingerprint:
                    raise ReplayConflict('Request ID reused with different data')
                return None, copy.deepcopy(stored[1])
            if request_id in self._actions:
                raise ReplayConflict('Request ID already used by an action')
            if body.get('viewRevision') != self.view_revision:
                raise ReplayConflict('The replay view changed; ask again')
            if self.pending and self.pending['viewRevision'] == self.view_revision:
                raise ReplayConflict('The assistant is answering another question for this view')
            if self.playing:  # a question is about one fixed cutoff
                self.playing = False
                self._changed()
            aircraft = self._aircraft(self.selected)
            ticket = dict(requestId=request_id, fingerprint=fingerprint, runId=self.run_id,
                          viewRevision=self.view_revision, cutoff=self.cutoff, aircraftId=self.selected,
                          flightInstance=aircraft['flightInstance'], question=question.strip())
            self.pending = ticket
            self._log('replay_question_start', requestId=request_id)
            return copy.deepcopy(ticket), None

    def has_answer(self, request_id):
        with self.lock:
            return request_id in self._answers

    def context_for(self, ticket):
        """Scenario copy and the memory visible at the ticket's cutoff.

        Turns answered under a later cutoff, or citing reports received after
        it, are left out, so a backward seek never carries later answers along.
        """
        with self.lock:
            memory = SessionState('replay-' + self.run_id, DEVELOPMENT)
            # Filter with the conversation path's own rule, not a second copy of it.
            memory.intents, memory.turns = SessionState.visible_memory(
                _Memory(self.memory_intents, self.memory_turns), ticket['cutoff'], self._receipts)
            return self.scenario(), memory

    def finish_question(self, ticket, result=None, memory=None):
        """Apply an answer only if the view it was asked under is still shown."""
        with self.lock:
            self.advance()
            if self.pending and self.pending['requestId'] == ticket['requestId']:
                self.pending = None
            current = ticket['runId'] == self.run_id and ticket['viewRevision'] == self.view_revision
            if not current or result is None:
                self._log('replay_question_discarded', requestId=ticket['requestId'],
                          reason='stale view' if not current else 'no result')
                return False
            if memory is not None:
                self.memory_intents += [i for i in memory.intents if i not in self.memory_intents]
                self.memory_turns += [t for t in memory.turns if t not in self.memory_turns]
            stored = dict(copy.deepcopy(result), runId=self.run_id, viewRevision=ticket['viewRevision'],
                          cutoff=ticket['cutoff'], aircraftId=ticket['aircraftId'])
            self._answers[ticket['requestId']] = (ticket['fingerprint'], stored)
            self._log('replay_question_end', requestId=ticket['requestId'], accepted=bool(result.get('accepted')))
            return True

    def ask(self, body, adapter, settings, turn_handler=None):
        """Serve one question; a view change while the model runs discards the answer."""
        if turn_handler is None:
            from backend.training_turn import run_turn as turn_handler
        ticket, stored = self.begin_question(body)
        if ticket is None:
            return stored
        data, memory = self.context_for(ticket)
        turn = dict(requestId=ticket['requestId'], turnId=ticket['requestId'], expectedRevision=memory.revision,
                    aircraftId=ticket['aircraftId'], flightInstance=ticket['flightInstance'],
                    cutoff=ticket['cutoff'], question=ticket['question'])
        try:
            served = turn_handler(memory, data, turn, adapter, settings)
        except BaseException:
            self.finish_question(ticket)
            raise
        result = {k: v for k, v in served.items() if k not in ('prompt', 'rawModelOutput')}
        if not self.finish_question(ticket, result, memory):
            raise ReplayConflict('The replay view changed while the assistant was answering; ask again')
        return copy.deepcopy(self._answers[ticket['requestId']][1])


class _Memory:
    """Carrier for SessionState.visible_memory's filter over the replay's own lists."""
    def __init__(self, intents, turns):
        self.intents, self.turns, self._lock = intents, turns, threading.Lock()
