"""Deployment and evaluation guards for the conversational path.

check_bind: once hosted provider keys sit behind the backend, the bearer token
spends money. A non-loopback bind (Wi-Fi mode, plain HTTP) is refused unless
the operator confirms an encrypted tunnel terminates in front of the server.
Use USB with `adb reverse tcp:8765 tcp:8765` and the default 127.0.0.1 bind.

load_heldout: held-out answer files must live outside the repository working
tree, where reviewers and coding agents with repository access cannot read
them by accident, and must match a hash committed before the run.
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
