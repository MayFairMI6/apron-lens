"""Deployment and evaluation guards for the conversational path.

check_bind: once hosted provider keys sit behind the backend, the bearer token
spends money. A non-loopback bind (Wi-Fi mode, plain HTTP) is refused unless
the operator confirms an encrypted tunnel terminates in front of the server.
Use USB with `adb reverse tcp:8765 tcp:8765` and the default 127.0.0.1 bind.

load_heldout: held-out answer files must live outside the repository working
tree, where reviewers and coding agents with repository access cannot read
them by accident, and must match a hash committed before the run.

load_heldout_set: a conversation held-out set (families plus their scenario
files) loaded the same way, against config/heldout-<set>.json, where <set> is
the families file's "set" (m1, m2 or final; docs/AR_SCOPE.md): every
file outside the repository and matching its committed hash, with no file
added or missing. Its results must also be written outside the repository,
since they carry the questions.
"""
import hashlib
import ipaddress
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class UnsafeBind(Exception):
    pass


class HeldoutLocationError(Exception):
    pass


def check_bind(host, hosted_enabled, encrypted_tunnel=False):
    if not hosted_enabled or encrypted_tunnel:
        return
    if host == 'localhost':
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise UnsafeBind('Hosted providers are enabled: bind to 127.0.0.1 and use adb reverse, '
                     'or put the server behind an encrypted tunnel')


def load_heldout(path, expected_sha256, repo_root=ROOT):
    path = Path(path).expanduser().resolve()
    if path.is_relative_to(Path(repo_root).resolve()):
        raise HeldoutLocationError('Held-out answers must be stored outside the repository working tree')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise HeldoutLocationError('Held-out answer file does not match its committed hash')
    return json.loads(raw)


HELDOUT_RECORD_VERSION = 'conversation-heldout-record-v1'
HELDOUT_SETS = ('m1', 'm2', 'final')  # one per milestone, each used once after its freeze


def heldout_record_path(families, repo_root=ROOT):
    """config/heldout-<set>.json for a families document."""
    name = families.get('set')
    if name not in HELDOUT_SETS:
        raise HeldoutLocationError(f'A held-out families file needs "set": one of {", ".join(HELDOUT_SETS)}')
    return Path(repo_root) / f'config/heldout-{name}.json'


def outside_repo(path, repo_root=ROOT):
    return not Path(path).expanduser().resolve().is_relative_to(Path(repo_root).resolve())


def scenario_hashes(directory):
    """file name -> SHA-256 of every scenario JSON in directory."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(directory).glob('*.json'))}


def heldout_record(families_path, scenarios_dir):
    """The record to commit once the held-out author has finished (scripts/check_heldout.py --record)."""
    return dict(record=HELDOUT_RECORD_VERSION, set=json.loads(Path(families_path).read_text()).get('set'),
                families=hashlib.sha256(Path(families_path).read_bytes()).hexdigest(),
                scenarios=scenario_hashes(scenarios_dir))


def load_heldout_set(families_path, scenarios_dir, record_path=None, repo_root=ROOT):
    """Return (families, {scenarioId: scenario}) after checking location and every committed hash.

    record_path defaults to the set's committed record (heldout_record_path)."""
    if not outside_repo(families_path, repo_root):
        raise HeldoutLocationError('Held-out answers must be stored outside the repository working tree')
    if record_path is None:
        record_path = heldout_record_path(json.loads(Path(families_path).read_text()), repo_root)
    if not Path(record_path).exists():
        raise HeldoutLocationError(f'No committed held-out record at {record_path}')
    record = json.loads(Path(record_path).read_text())
    if not outside_repo(scenarios_dir, repo_root):
        raise HeldoutLocationError('Held-out scenarios must be stored outside the repository working tree')
    families = load_heldout(families_path, record['families'], repo_root)
    found = scenario_hashes(scenarios_dir)
    if found != record['scenarios']:
        changed = sorted(set(found) ^ set(record['scenarios']) |
                         {name for name in set(found) & set(record['scenarios']) if found[name] != record['scenarios'][name]})
        raise HeldoutLocationError('Held-out scenarios do not match their committed hashes: ' + ', '.join(changed))
    scenarios = {}
    for name in found:
        data = json.loads((Path(scenarios_dir) / name).read_text())
        if data['scenarioId'] in scenarios:
            raise HeldoutLocationError(f'Duplicate scenario ID {data["scenarioId"]}')
        scenarios[data['scenarioId']] = data
    return families, scenarios
