"""Pinned model identities (config/models.json) and device choice. Weights live outside Git under models/<local_dir>."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / 'config/models.json'
PRIMARY_MODEL = 'qwen2.5-vl-3b'
MANIFEST_FIELDS = ('model_id', 'revision', 'source', 'license')


def _models():
    return json.loads(REGISTRY_PATH.read_text())['models']


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
        raise ValueError(f'{name} has no pinned revision; run python -m backend.download --model {name} --pin')
    return {k: entry[k] for k in MANIFEST_FIELDS}


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


# Device and number type take the torch module, so they can be tested without torch.
def pick_device(torch):
    """NVIDIA GPU (e.g. GAIVI), then Apple Silicon, then CPU; a Mac keeps the evaluated MPS path."""
    if torch.cuda.is_available():
        return 'cuda'
    return 'mps' if torch.backends.mps.is_available() else 'cpu'


def pick_dtype(torch, device, mps_dtype='float16'):
    """bfloat16 on NVIDIA where supported (float16 can overflow); MPS keeps the configured type."""
    if device == 'cpu':
        return torch.float32
    if device == 'cuda':
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return getattr(torch, mps_dtype)
