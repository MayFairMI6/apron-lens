# Qwen setup for ApronLens

This project uses the proposal baseline, `Qwen/Qwen2.5-VL-3B-Instruct`, with
Hugging Face Transformers and PyTorch. Packages are isolated in `.venv-qwen`;
the model is stored in `models/Qwen2.5-VL-3B-Instruct`. The download manifest
records the exact upstream revision. `requirements-qwen.lock.txt` records
installed package versions.

## Run the installation check

From this project directory:

```sh
.venv-qwen/bin/python scripts/verify_qwen.py
```

It runs locally, uses Apple Metal (MPS) when available, and saves a response
and runtime details to `work/qwen-verification.json`. It creates a synthetic
red-square/blue-circle image to verify visual inference. This is an
installation check, not evidence of airport reasoning accuracy or training
effectiveness. The Unity app now connects to this model through a local service. See QWEN_CONNECTION.md for the implemented workflow and current verification limits.

Verified locally on 2026-10-26 with Python 3.12.13, PyTorch 2.14.1,
Transformers 4.57.6, and MPS float16. The model correctly answered:
"The red square is to the left of the blue circle." The single run loaded in
11.83 seconds and generated 13 tokens in 6.03 seconds. These are installation
measurements for this tiny input, not throughput estimates for airport videos.

The model's upstream `LICENSE` is retained alongside the weights. This 3B
variant uses the Qwen Research License for non-commercial research/evaluation.
Source: https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct

## Keep the two project goals distinct

**ApronLens:** study shared spatial and temporal context across AR conversation
turns, user corrections and changing external reports. The implemented foundation
is aircraft replay, source-aware report selection and a local Qwen service.
Conversation memory, visual reference resolution and hosted APIs are proposed.
Evaluate grounding, correction recovery, evidence validity and interaction cost.

**Separate airport-video AI study:** according to saved personal project notes,
AVIS anchors learned visual-evidence retention and reasoning-rollout allocation.
The goal is to compare evidence-selection/reasoning methods under compute
constraints. The other project's current proposal was not available here for
fresh verification; these notes are a recalled comparison, not a live status
report.

Shared model weights or basic utilities do not make the projects identical.
Keep scenario/question splits, results, evaluation criteria, and claimed
contributions separate. This AR setup does not implement the other project's
learned frame-selection method.
