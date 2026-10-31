"""Pinned model identities and named runtime profiles. Weights live outside Git under <repo>/models/<local_dir>."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path(__file__).with_name('models.json')
PRIMARY_MODEL = 'qwen2.5-vl-3b'
MANIFEST_FIELDS = ('model_id', 'revision', 'source', 'license')
RUNTIME_FIELDS = ('device', 'dtype', 'attn_implementation')


def _registry():
    return json.loads(REGISTRY_PATH.read_text())


def _models():
    return _registry()['models']


def model_names():
    return list(_models())


def model_entry(name):
    models = _models()
    if name not in models:
        raise ValueError(f'Unknown model {name!r}; choose one of: ' + ', '.join(models))
    return models[name]


def model_dir(name):
    return ROOT / 'models' / model_entry(name)['local_dir']


def expected_manifest(name):
    """Identity and exact revision a downloaded model must carry before it is loaded."""
    entry = model_entry(name)
    if not entry['revision']:
        raise ValueError(f'{name} has no pinned revision; run python -m backbone.download --model {name} --pin')
    return {k: entry[k] for k in MANIFEST_FIELDS}


def runtime_profiles():
    return list(_registry()['runtimeProfiles'])


def runtime_profile(name):
    """Device, dtype and attention implementation for a named profile, e.g. apronlens-v2-mps."""
    profiles = _registry()['runtimeProfiles']
    if name not in profiles:
        raise ValueError(f'Unknown runtime profile {name!r}; choose one of: ' + ', '.join(profiles))
    return {k: profiles[name][k] for k in RUNTIME_FIELDS}


def _release(version):
    parts = []
    for part in version.split('.'):
        if not part.isdigit():
            break
        parts.append(int(part))
    return tuple(parts)


def check_transformers(name, installed):
    """Fail early with the fix, rather than deep inside model loading."""
    minimum = model_entry(name)['transformers'].removeprefix('>=')
    if _release(installed) < _release(minimum):
        raise ValueError(f'{name} needs transformers {minimum} or later (installed {installed}); '
                         'use an environment built from requirements-candidates.txt')
