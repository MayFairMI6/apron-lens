"""Per-session conversational state with revisioned, idempotent commits.

Three kinds of memory are kept apart:
- user intent (references and corrections; never a source of facts),
- external evidence (not stored here; always re-read from the scenario snapshot),
- assistant interpretations (proposed answers tied to a receipt cutoff).

Every memory item records the receipt cutoff it was produced under. When the
replay is seeked backward, items produced under a later cutoff, or citing
evidence received after the current cutoff, are masked. Formal runs reject
backward seeks; the harness must start a new session instead.
"""
import threading
from dataclasses import dataclass

FORMAL = 'formal'
DEVELOPMENT = 'development'
INTENT_KINDS = ('reference', 'correction', 'scope')


class StaleRevision(Exception):
    """Commit attempted against a revision that is no longer current."""


class SeekBackwardInFormalRun(Exception):
    """A formal run moved the receipt cutoff backward; start a new session."""


class DuplicateRequestConflict(Exception):
    """A request ID was reused for a different turn."""


@dataclass(frozen=True)
class IntentRecord:
    turn_id: str
    kind: str
    aircraft_id: str
    flight_instance: str
    text: str
    cutoff: float

    def __post_init__(self):
        if self.kind not in INTENT_KINDS:
            raise ValueError('Unknown intent kind')


@dataclass(frozen=True)
class AssistantTurn:
    turn_id: str
    request_id: str
    aircraft_id: str
    flight_instance: str
    cutoff: float
    evidence_ids: tuple
    claims: tuple
    status: str
    evidence_digest: str
    interpretation: str | None = None
    observations: tuple = ()  # related, unverified visual observations; never facts


class SessionState:
    def __init__(self, session_id, mode=DEVELOPMENT):
        if mode not in (FORMAL, DEVELOPMENT):
            raise ValueError('Unknown session mode')
        self.session_id, self.mode = session_id, mode
        self.revision = 0
        self.max_cutoff = None
        self.intents = []
        self.turns = []
        self._results = {}
        self._lock = threading.Lock()

    # ---- cutoff handling ----------------------------------------------------------
    def observe_cutoff(self, cutoff):
        """Register the cutoff a request is served under; enforces the seek rule."""
        with self._lock:
            if self.max_cutoff is not None and cutoff < self.max_cutoff and self.mode == FORMAL:
                raise SeekBackwardInFormalRun('Cutoff moved backward in a formal run; start a new session')
            self.max_cutoff = cutoff if self.max_cutoff is None else max(self.max_cutoff, cutoff)

    def visible_memory(self, cutoff, receipt_times):
        """Memory usable at `cutoff`: nothing produced later or citing later evidence."""
        with self._lock:
            intents = [i for i in self.intents if i.cutoff <= cutoff]
            turns = [t for t in self.turns if t.cutoff <= cutoff and all(
                receipt_times.get(eid, float('inf')) <= cutoff for eid in t.evidence_ids)]
            return intents, turns

    def current_referent(self, cutoff, receipt_times):
        intents, _ = self.visible_memory(cutoff, receipt_times)
        if not intents:
            return None
        latest = intents[-1]
        return latest.aircraft_id, latest.flight_instance

    def previous_turn_for(self, aircraft_id, flight_instance, cutoff, receipt_times):
        _, turns = self.visible_memory(cutoff, receipt_times)
        scoped = [t for t in turns if (t.aircraft_id, t.flight_instance) == (aircraft_id, flight_instance)
                  and t.status in ('answer', 'clarify', 'unknown')]
        return scoped[-1] if scoped else None

    # ---- commits -------------------------------------------------------------------
    def result_for(self, request_id):
        with self._lock:
            return self._results.get(request_id)

    def commit(self, request_id, turn_id, expected_revision, intents=(), turn=None, result=None):
        """Apply accepted changes atomically.

        Re-sending the same request ID returns the stored result without a second
        commit (client retries must reuse their request ID). A commit against a
        revision that has moved on raises StaleRevision and changes nothing.
        """
        with self._lock:
            if request_id in self._results:
                stored_turn, stored = self._results[request_id]
                if stored_turn != turn_id:
                    raise DuplicateRequestConflict('Request ID reused for a different turn')
                return stored
            if expected_revision != self.revision:
                raise StaleRevision(f'expected revision {expected_revision}, current {self.revision}')
            self.intents.extend(intents)
            if turn is not None:
                self.turns.append(turn)
            self.revision += 1
            stored = dict(result or {}, revision=self.revision)
            self._results[request_id] = (turn_id, stored)
            return stored
