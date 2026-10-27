"""Download a candidate model from config/model-candidates.json at its exact revision.

The evaluated default model keeps its own downloader, scripts/download_qwen.py.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Use resumable HTTP downloads; the development Mac's Xet route was substantially slower.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.engines import CANDIDATES_PATH, MANIFEST_FIELDS, candidate, model_dir


def download(name, pin=False):
    from huggingface_hub import HfApi, snapshot_download
    entry = candidate(name)
    revision = entry['revision']
    if revision is None:
        if not pin:
            raise ValueError(f'{name} has no pinned revision. Check its model card, then rerun with --pin.')
        revision = HfApi().model_info(entry['model_id']).sha
    target = model_dir(name)
    print(f"Downloading {entry['model_id']} at {revision}", flush=True)
    snapshot_download(
        entry['model_id'],
        revision=revision,
        local_dir=target,
        allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja", "*.model", "README.md", "LICENSE*"],
        max_workers=3,
    )
    if entry['revision'] is None:
        data = json.loads(CANDIDATES_PATH.read_text())
        data['models'][name]['revision'] = revision
        CANDIDATES_PATH.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Recorded revision in {CANDIDATES_PATH.relative_to(ROOT)}; commit it with your results.", flush=True)
    manifest = {k: entry[k] for k in MANIFEST_FIELDS} | {'revision': revision}
    (target / "download-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Download complete: {target}", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--pin', action='store_true', help='Resolve and record the current revision of an unpinned entry')
    args = parser.parse_args()
    download(args.model, args.pin)
