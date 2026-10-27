"""Check preserved research artifacts without model weights or third-party packages."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(current=False):
    for suite in ('reasoning_v1', 'reasoning_v2_fresh'):
        base = ROOT / 'data' / suite
        manifest = json.loads((base / 'manifest.json').read_text())
        for rel, expected in manifest['files'].items():
            path = (base / rel).resolve()
            if not path.is_relative_to(base.resolve()) or digest(path) != expected:
                raise ValueError('Dataset integrity failure: ' + suite + '/' + rel)
    out = ROOT / 'outputs/reasoning_v2'
    protocol = json.loads((out / 'protocol.json').read_text())
    for rel, expected in protocol['sources'].items():
        if digest(out / 'source_snapshot' / rel) != expected:
            raise ValueError('Frozen source changed: ' + rel)
        if current and digest(ROOT / rel) != expected:
            raise ValueError('Current source differs from V2: ' + rel)
    model = ROOT / 'config/model-manifest.json'
    if digest(model) != protocol['modelManifestSha256']:
        raise ValueError('Pinned model manifest differs from evaluation')
    if digest(ROOT / 'data/reasoning_v2_fresh/manifest.json') != protocol['config']['expectedSuiteManifestSha256']:
        raise ValueError('Fresh suite manifest changed')
    rows = [json.loads(line) for line in (out / 'fresh-runs.jsonl').read_text().splitlines()]
    attempts = [json.loads(line) for line in (out / 'attempts.jsonl').read_text().splitlines()]
    keys = [(r['questionId'], r['condition']) for r in rows]
    attempt_keys = [(r['questionId'], r['condition']) for r in attempts]
    expected_count = protocol['config']['questionCount'] * (len(protocol['config']['conditions']) + 1)
    if len(keys) != expected_count or len(set(keys)) != expected_count or set(keys) != set(attempt_keys) or len(attempt_keys) != expected_count:
        raise ValueError('Incomplete or duplicate frozen attempt/result records')
    sha = digest(out / 'protocol.json')
    if any(r['protocolSha256'] != sha for r in rows + attempts):
        raise ValueError('Protocol/result mismatch')
    print(f'Research integrity passed: dataset hashes, frozen sources, pinned model and {len(rows)} result records.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', action='store_true', help='Also require current inference code to match V2')
    check(parser.parse_args().current)
