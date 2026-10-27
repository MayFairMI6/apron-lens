"""Model choice for development comparisons. The evaluated Qwen2.5-VL-3B stays the default.

Candidate results are development observations. They are not comparable with the
frozen V2 evaluation unless a new protocol, dataset and model revision are frozen.
"""
import json
from backend.evidence import ROOT

DEFAULT_MODEL = 'qwen2.5-vl-3b'
CANDIDATES_PATH = ROOT / 'config/model-candidates.json'
MANIFEST_FIELDS = ('model_id', 'revision', 'source', 'license')


def candidates():
    return json.loads(CANDIDATES_PATH.read_text())['models']


def model_names():
    return [DEFAULT_MODEL, *candidates()]


def candidate(name):
    models = candidates()
    if name not in models:
        raise ValueError(f'Unknown model {name!r}; choose one of: ' + ', '.join(model_names()))
    return models[name]


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


def _release(version):
    parts = []
    for part in version.split('.'):
        if not part.isdigit():
            break
        parts.append(int(part))
    return tuple(parts)


def check_transformers(name, installed):
    """Fail early with the fix, rather than deep inside model loading."""
    minimum = candidate(name)['transformers'].removeprefix('>=')
    if _release(installed) < _release(minimum):
        raise ValueError(f'{name} needs transformers {minimum} or later (installed {installed}); '
                         'use an environment built from requirements-candidates.txt')


def model_dir(name):
    return ROOT / 'models' / name


def expected_manifest(name):
    """Identity and exact revision a downloaded model must carry before it is loaded."""
    if name == DEFAULT_MODEL:
        return json.loads((ROOT / 'config/model-manifest.json').read_text())
    entry = candidate(name)
    if not entry['revision']:
        raise ValueError(f'{name} has no pinned revision; run scripts/download_model.py --model {name} --pin')
    return {k: entry[k] for k in MANIFEST_FIELDS}
