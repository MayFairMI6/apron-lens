"""Write, check or approve the conversational method freeze (config/conversation-freeze.json).

    python scripts/freeze_conversation_method.py --check
    python scripts/freeze_conversation_method.py --write              # record the current method as proposed
    python scripts/freeze_conversation_method.py --approve --by NAME  # the user approves the proposed record

--write refuses to replace an approved record; a changed method after approval
needs new version constants and a new record (approve again). See
backend/conversation/freeze.py.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.conversation.freeze import FREEZE_PATH, approve, current_record, load, mismatches


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--write', action='store_true')
    action.add_argument('--approve', action='store_true')
    parser.add_argument('--by', help='Name of the person approving (with --approve)')
    args = parser.parse_args()
    record = load()
    if args.write:
        if record and record['status'] == 'approved' and not mismatches(record):
            raise SystemExit('The approved record already matches the method; nothing to write.')
        if record and record['status'] == 'approved':
            print('Replacing an approved record whose method changed; it stays in git history.')
        FREEZE_PATH.write_text(json.dumps(current_record(), indent=2) + '\n')
        print(f'Wrote a proposed freeze to {FREEZE_PATH.relative_to(ROOT)}.')
    elif args.approve:
        if record is None or mismatches(record):
            raise SystemExit('Write a current proposed record first (--write).')
        FREEZE_PATH.write_text(json.dumps(approve(record, args.by), indent=2) + '\n')
        print(f'Approved by {args.by}.')
    else:
        if record is None:
            raise SystemExit('No freeze record.')
        changed = mismatches(record)
        print(f'status {record["status"]}; ' + ('matches the current method' if not changed else 'changed: ' + ', '.join(changed)))
        if record['status'] == 'approved' and changed:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
