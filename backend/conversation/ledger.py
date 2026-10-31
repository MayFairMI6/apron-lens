"""Application-owned API budget ledger (ApronLens only; the $40 is ApronLens's).

- SQLite file, so state survives process and job restarts.
- Reservations are atomic across threads and processes (BEGIN IMMEDIATE).
- A conservative maximum is reserved before any call: all input at the
  uncached rate and the full output cap (which includes billed reasoning).
- Rates come from config/hosted-models.json by effective date. A rate marked
  as a lower bound ("from $X") cannot be used for a reservation.
- Missing usage keeps the reserved charge. A cancelled or abandoned call keeps
  its reserved charge too, because the provider may still bill it.
- Retries are separate attempts with their own reservations under the same
  request ID; a repeated (request ID, attempt) returns the existing reservation.
- Spending pauses at the review checkpoint (default $10) until acknowledged.
  This is an accounting stop, not permission to exceed the total.
Amounts are stored as integer micro-dollars.
"""
import datetime as dt
import json
import sqlite3
from contextlib import closing
from pathlib import Path

MICRO = 1_000_000
DEFAULT_PURPOSES = {'screening': 8.0, 'primary': 12.0, 'comparison': 12.0, 'review': 3.0, 'contingency': 5.0}
DEFAULT_TOTAL = 40.0
DEFAULT_CHECKPOINT = 10.0


class BudgetExceeded(Exception):
    pass


class CheckpointPause(Exception):
    pass


class RateUnavailable(Exception):
    pass


class RateTable:
    def __init__(self, models):
        self.models = models

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text())['models'])

    def rate_for(self, model, on_date):
        if model not in self.models:
            raise RateUnavailable(f'No recorded rate for {model}')
        day = on_date.isoformat() if isinstance(on_date, dt.date) else str(on_date)
        rates = sorted(self.models[model]['rates'], key=lambda r: r['effectiveFrom'])
        applicable = [r for r in rates if r['effectiveFrom'] <= day]
        if not applicable:
            raise RateUnavailable(f'No rate for {model} effective on {day}')
        rate = applicable[-1]
        if rate.get('rateIsLowerBound'):
            raise RateUnavailable(f'{model} has only a starting ("from") rate; set an exact rate first')
        return rate

    def max_cost_micro(self, model, on_date, max_input_tokens, max_output_tokens):
        rate = self.rate_for(model, on_date)
        dollars = (max_input_tokens * rate['inputPerMTok'] + max_output_tokens * rate['outputPerMTok']) / MICRO
        return _ceil_micro(dollars)

    def actual_cost_micro(self, model, on_date, usage):
        """usage: dict(input_tokens, output_tokens, cached_input_tokens=0). Reasoning is billed in output."""
        rate = self.rate_for(model, on_date)
        cached = usage.get('cached_input_tokens') or 0
        uncached = usage['input_tokens'] - cached
        cached_rate = rate.get('cachedInputPerMTok', rate['inputPerMTok'])
        dollars = (uncached * rate['inputPerMTok'] + cached * cached_rate
                   + usage['output_tokens'] * rate['outputPerMTok']) / MICRO
        return _ceil_micro(dollars)


def _ceil_micro(dollars):
    value = dollars * MICRO
    return int(value) + (0 if value == int(value) else 1)


class Ledger:
    def __init__(self, path, purposes=None, total=DEFAULT_TOTAL, checkpoint=DEFAULT_CHECKPOINT,
                 session_limit=None):
        self.path = str(path)
        self.purposes = {k: int(round(v * MICRO)) for k, v in (purposes or DEFAULT_PURPOSES).items()}
        self.total = int(round(total * MICRO))
        if sum(self.purposes.values()) > self.total:
            raise ValueError('Purpose limits exceed the total allocation')
        self.checkpoint = int(round(checkpoint * MICRO)) if checkpoint else None
        self.session_limit = int(round(session_limit * MICRO)) if session_limit else None
        with closing(self._connect()) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY, request_id TEXT NOT NULL, attempt INTEGER NOT NULL,
                    purpose TEXT NOT NULL, session_id TEXT, model TEXT NOT NULL,
                    reserved INTEGER NOT NULL, actual INTEGER, state TEXT NOT NULL,
                    note TEXT, created TEXT NOT NULL, UNIQUE(request_id, attempt));
                CREATE TABLE IF NOT EXISTS checkpoints (amount INTEGER PRIMARY KEY, acknowledged TEXT NOT NULL);''')

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _charge_sql():
        # Reserved amount counts until reconciled with real usage.
        return "COALESCE(SUM(CASE WHEN state = 'reconciled' THEN actual ELSE reserved END), 0)"

    def committed(self, purpose=None, session_id=None):
        query = f'SELECT {self._charge_sql()} AS c FROM reservations WHERE 1=1'
        args = []
        if purpose:
            query += ' AND purpose = ?'; args.append(purpose)
        if session_id:
            query += ' AND session_id = ?'; args.append(session_id)
        with closing(self._connect()) as db:
            return db.execute(query, args).fetchone()['c']

    def reserve(self, request_id, attempt, purpose, model, amount_micro, session_id=None):
        if purpose not in self.purposes:
            raise ValueError('Unknown budget purpose')
        db = self._connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM reservations WHERE request_id = ? AND attempt = ?',
                                  (request_id, attempt)).fetchone()
            if existing:
                db.execute('COMMIT')
                return existing['id']
            charge = self._charge_sql()
            total = db.execute(f'SELECT {charge} AS c FROM reservations').fetchone()['c']
            used = db.execute(f'SELECT {charge} AS c FROM reservations WHERE purpose = ?', (purpose,)).fetchone()['c']
            if self.checkpoint is not None and total >= self.checkpoint:
                ack = db.execute('SELECT 1 FROM checkpoints WHERE amount = ?', (self.checkpoint,)).fetchone()
                if not ack:
                    raise CheckpointPause('Review measured cost and latency, then acknowledge the checkpoint')
            if total + amount_micro > self.total:
                raise BudgetExceeded('Total allocation would be exceeded')
            if used + amount_micro > self.purposes[purpose]:
                raise BudgetExceeded(f'{purpose} allocation would be exceeded')
            if self.session_limit is not None and session_id is not None:
                session_used = db.execute(f'SELECT {charge} AS c FROM reservations WHERE session_id = ?',
                                          (session_id,)).fetchone()['c']
                if session_used + amount_micro > self.session_limit:
                    raise BudgetExceeded('Session limit would be exceeded')
            cur = db.execute('INSERT INTO reservations (request_id, attempt, purpose, session_id, model, reserved, '
                             'state, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                             (request_id, attempt, purpose, session_id, model, amount_micro, 'reserved',
                              dt.datetime.now(dt.timezone.utc).isoformat()))
            db.execute('COMMIT')
            return cur.lastrowid
        except Exception:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        finally:
            db.close()

    def reconcile(self, reservation_id, actual_micro):
        """Record real cost. Pass None when the provider reported no usage: the reservation stands."""
        with closing(self._connect()) as db:
            if actual_micro is None:
                db.execute("UPDATE reservations SET state = 'usage_missing', note = 'reserved amount kept' "
                           "WHERE id = ? AND state = 'reserved'", (reservation_id,))
            else:
                db.execute("UPDATE reservations SET state = 'reconciled', actual = ? WHERE id = ?",
                           (actual_micro, reservation_id))

    def cancel(self, reservation_id):
        """Client cancelled or abandoned the call; the provider may still bill it."""
        with closing(self._connect()) as db:
            db.execute("UPDATE reservations SET state = 'cancelled_charged', note = 'charged until usage is known' "
                       "WHERE id = ? AND state = 'reserved'", (reservation_id,))

    def acknowledge_checkpoint(self):
        if self.checkpoint is None:
            return
        with closing(self._connect()) as db:
            db.execute('INSERT OR IGNORE INTO checkpoints (amount, acknowledged) VALUES (?, ?)',
                       (self.checkpoint, dt.datetime.now(dt.timezone.utc).isoformat()))
