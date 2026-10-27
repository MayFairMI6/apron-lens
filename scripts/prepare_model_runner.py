"""Attach an existing model cache to a clean checkout; never download weights in CI."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(cache):
    cache = Path(cache).expanduser().resolve()
    expected = json.loads((ROOT / 'config/model-manifest.json').read_text())
    actual = json.loads((cache / 'download-manifest.json').read_text())
    if actual != expected or not list(cache.glob('*.safetensors')):
        raise ValueError('Cache must contain the pinned model revision, manifest and weights')
    target = ROOT / 'models/Qwen2.5-VL-3B-Instruct'
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
    prepare(parser.parse_args().model_cache)
