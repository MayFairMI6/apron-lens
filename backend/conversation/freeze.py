"""Freeze record for the conversational method (config/conversation-freeze.json).

The method is the set of files and version constants that decide what a model
sees and how its answer is checked and scored. Before a formal (held-out) run
the record is written with status "proposed", reviewed, and approved by the
user. From then on:
- tests fail if any frozen file changes (tests/test_conversation_freeze.py);
- formal runs refuse to start unless every frozen file matches.
A changed method needs new version constants, a new record and a new approval;
the earlier record stays in git history.

Request construction (the runner's settings, the adapters and image
preprocessing) is frozen with the method, because it decides what the model
sees. Evidence images are not frozen here: their renderer changes with the UI,
so each run records the SHA-256 of the images it used and its effective settings.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

from modelaccess.repair import REPAIR_POLICY_VERSION
from backend.conversation.scoring import SCORING_VERSION
from backend.conversation.turns import PROMPT_VERSION, REFERENT_RULE_VERSION
from backend.conversation.validate import VALIDATOR_VERSION

ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = ROOT / 'config/conversation-freeze.json'
RECORD_VERSION = 'conversation-freeze-v1'
FROZEN_FILES = (
    'backend/conversation/turns.py',
    'backend/conversation/validate.py',
    'backend/conversation/observations.py',
    'backend/conversation/context.py',
    'backend/conversation/identity.py',
    'backend/conversation/state.py',
    'backend/conversation/scoring.py',
    'backend/evidence.py',
    # Request construction and input preprocessing: what the model actually sees.
    'scripts/run_conversation_families.py',
    'modelaccess/contract.py',
    'modelaccess/repair.py',
    'modelaccess/images.py',
    'modelaccess/local_backbone.py',
    'modelaccess/anthropic_api.py',
    'modelaccess/openai_api.py',
    'unity/SurfaceSafetyCoach/Assets/SurfaceSafety/Scripts/VisualEvidenceCapture.cs',
)


def versions():
    capture = (ROOT / FROZEN_FILES[-1]).read_text()
    marker = 'public const string Version = "'
    start = capture.index(marker) + len(marker)
    return dict(prompt=PROMPT_VERSION, referentRule=REFERENT_RULE_VERSION, validator=VALIDATOR_VERSION,
                scoring=SCORING_VERSION, repairPolicy=REPAIR_POLICY_VERSION,
                capture=capture[start:capture.index('"', start)])


def digest(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def current_record():
    return dict(record=RECORD_VERSION, status='proposed', versions=versions(),
                files={rel: digest(rel) for rel in FROZEN_FILES})


def load(path=FREEZE_PATH):
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


def mismatches(record):
    """Frozen files or versions that differ from the record."""
    changed = [rel for rel, expected in record['files'].items() if not (ROOT / rel).exists() or digest(rel) != expected]
    if record['versions'] != versions():
        changed.append('versions')
    if set(record['files']) != set(FROZEN_FILES):
        changed.append('file list')
    return changed


def status(path=FREEZE_PATH):
    """Return dict(status, matches, changed) for result files and guards."""
    record = load(path)
    if record is None:
        return dict(status='none', matches=False, changed=[])
    changed = mismatches(record)
    return dict(status=record['status'], matches=not changed, changed=changed)


def require_approved(path=FREEZE_PATH):
    """Raise SystemExit unless an approved record matches the current method (for formal runs)."""
    state = status(path)
    if state['status'] != 'approved' or not state['matches']:
        raise SystemExit(f'A formal run needs an approved freeze that matches the method; found status '
                         f'{state["status"]!r}, changed: {", ".join(state["changed"]) or "none"}. '
                         'See scripts/freeze_conversation_method.py.')
    return state


def approve(record, by):
    if not by:
        raise ValueError('Approval needs a name')
    return dict(record, status='approved', approvedBy=by, approvedAt=dt.date.today().isoformat())
