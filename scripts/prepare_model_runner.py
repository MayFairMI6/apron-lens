"""Attach an existing model cache to a clean checkout; never download weights in CI."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.engines import DEFAULT_MODEL, expected_manifest, model_dir, model_names


def prepare(cache, model=DEFAULT_MODEL):
    cache = Path(cache).expanduser().resolve()
    expected = expected_manifest(model)
    actual = json.loads((cache / 'download-manifest.json').read_text())
    if actual != expected or not list(cache.glob('*.safetensors')):
        raise ValueError('Cache must contain the pinned model revision, manifest and weights')
    target = ROOT / 'models/Qwen2.5-VL-3B-Instruct' if model == DEFAULT_MODEL else model_dir(model)
    target.parent.mkdir(exist_ok=True)
    if target.exists() or target.is_symlink():
        if target.resolve() != cache:
            raise ValueError('A different local model already exists; nothing replaced')
    else:
        target.symlink_to(cache, target_is_directory=True)
    print('Pinned local model cache attached; weights remain outside Git.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-cache', required=True)
    parser.add_argument('--model', choices=model_names(), default=DEFAULT_MODEL)
    args = parser.parse_args()
    prepare(args.model_cache, args.model)
