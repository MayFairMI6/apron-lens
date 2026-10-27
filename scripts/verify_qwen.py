"""Local-only, synthetic-image installation check; not an aviation benchmark."""
import json
import platform
import time
from pathlib import Path
import torch
import transformers
from PIL import Image, ImageDraw
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

ROOT = Path(__file__).resolve().parents[1]
model_path = ROOT / "models" / "Qwen2.5-VL-3B-Instruct"
work = ROOT / "work"
work.mkdir(exist_ok=True)
image = Image.new("RGB", (448, 280), "white")
draw = ImageDraw.Draw(image)
draw.rectangle((45, 75, 155, 185), fill="red")
draw.ellipse((285, 75, 395, 185), fill="blue")
image.save(work / "qwen-smoke-input.png")
device = "mps" if torch.backends.mps.is_available() else "cpu"
dtype = torch.float16 if device == "mps" else torch.float32
print(f"Loading on {device} ({dtype}); torch={torch.__version__}", flush=True)
start = time.perf_counter()
processor = AutoProcessor.from_pretrained(model_path, local_files_only=True, use_fast=False)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_path,
    dtype=dtype,
    attn_implementation="eager",
    local_files_only=True,
).to(device).eval()
load_seconds = time.perf_counter() - start
messages = [{"role": "user", "content": [
    {"type": "image"},
    {"type": "text", "text": "Describe the two shapes and their left/right positions in one short sentence."},
]}]
prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=[prompt], images=[image], return_tensors="pt").to(device)
if "pixel_values" in inputs:
    inputs["pixel_values"] = inputs["pixel_values"].to(dtype)
start = time.perf_counter()
with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=48, do_sample=False)
if device == "mps":
    torch.mps.synchronize()
seconds = time.perf_counter() - start
answer = processor.batch_decode(output[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
if not answer.strip():
    raise RuntimeError("Model returned an empty response")
result = {
    "status": "generated_nonempty_response",
    "scope": "Installation smoke test only; synthetic shapes, not aviation validation",
    "model": json.loads((model_path / "download-manifest.json").read_text()),
    "device": device,
    "dtype": str(dtype),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "transformers": transformers.__version__,
    "load_seconds": round(load_seconds, 2),
    "generation_seconds": round(seconds, 2),
    "generated_tokens": int(output.shape[1] - inputs["input_ids"].shape[1]),
    "answer": answer,
}
(work / "qwen-verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2), flush=True)
