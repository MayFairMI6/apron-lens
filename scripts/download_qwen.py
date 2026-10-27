"""Download the proposal's unchanged model and record its exact revision."""
import json
import os
from pathlib import Path

# Use resumable HTTP downloads; this Mac's Xet route was substantially slower.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'config/model-manifest.json').read_text())
MODEL_ID = manifest['model_id']
target = ROOT / "models" / "Qwen2.5-VL-3B-Instruct"
revision = manifest['revision']
print(f"Downloading {MODEL_ID} at {revision}", flush=True)
snapshot_download(
    MODEL_ID,
    revision=revision,
    local_dir=target,
    allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja", "README.md", "LICENSE"],
    max_workers=3,
)
(target / "download-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Download complete: {target}", flush=True)
