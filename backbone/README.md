# Shared backbone

This folder is the frozen vision-language backbone shared by **ApronLens** and the
**context-compaction project**. It is copied identically into both repositories.
Each project adds its own modules on top; the backbone itself is never a
research contribution of either project.

## Boundary

| Inside the backbone | Outside: belongs to a project |
|---|---|
| Model registry with exact revisions (`models.json`) | Prompts and prompt versions |
| Runtime validation and named runtime profiles (`runtime.py`, `models.json`) | Datasets, splits, labels, answer keys |
| Frozen-model engine: `generate`, `score_labels`, `embed` (`engine.py`) | Evidence rules, memory policies, retention scorers |
| Weight download and revision check (`download.py`) | Anything trained, including LoRA adapters |
| Boundary enforcement (`check.py`) | API servers, apps, job scripts, evaluation harnesses |

Planned for extraction later, now project-local: the frozen-protocol kit
(hash freezing, attempts log) and the generic "cite only what was available
at time t" check.

## Public interface

Projects import only these names: `from backbone import ...`

| Name | Purpose |
|---|---|
| `PRIMARY_MODEL` | `qwen2.5-vl-3b`, the backbone both projects report first |
| `model_names()`, `model_entry(name)`, `model_dir(name)`, `expected_manifest(name)` | Registry lookups |
| `load_engine(name, profile=...)`, `VLMEngine` | Load a pinned model with a named runtime profile (or explicit device, dtype and attention); refuses a download whose manifest does not match and an unavailable device |
| `runtime_profile(name)`, `runtime_profiles()`, `resolve_runtime(torch, ...)` | Named runtime profiles and their validation |
| `engine.generate(prompt, image)` | Free text; returns `(text, input_tokens, output_tokens)` |
| `engine.score_labels(prompt, image, labels)` | Next-token log-probabilities of single-token labels |
| `engine.embed(prompt, image=None)` | Mean-pooled final hidden state: frozen features for project modules |
| `pick_device(torch)`, `pick_dtype(torch, device)` | Suggestions for interactive use only; engines never call them |
| `check_transformers(name, version)` | Transformers version gate |

## Models

| Name | Role | Model | Environment |
|---|---|---|---|
| `qwen2.5-vl-3b` | primary | Qwen/Qwen2.5-VL-3B-Instruct | `requirements-qwen.lock.txt` |
| `qwen3-vl-4b` | robustness: the one second backbone both projects report | Qwen/Qwen3-VL-4B-Instruct | `requirements-qwen.lock.txt` |
| `qwen3-vl-8b`, `qwen3.5-9b`, `gemma-4-e4b` | exploratory, outside course scope | see `models.json` | transformers 5 models: `requirements-candidates.txt` |

A registry entry may set `chat_template_kwargs` (1.2.0), passed to the
processor's chat template. `qwen3.5-9b` sets `enable_thinking: false`: by
default it writes a reasoning trace before answering, which used the whole
output budget in the conversation runs. No other model sets it, so their
prompts are unchanged.

## Runtime profiles (1.1.0)

The engine never chooses device, number type or attention implementation.
Each run names a profile and records it in `engine.runtime`; a requested
device that is unavailable is an error, never a fallback.

| Profile | Device | dtype | Attention | Use |
|---|---|---|---|---|
| `apronlens-v2-mps` | mps | float16 | eager | The frozen ApronLens V2 evaluation configuration |
| `compaction-gaivi-cuda` | cuda | float16 | sdpa | The compaction project's GAIVI runner configuration |
| `cuda-bfloat16-eager` | cuda | bfloat16 | eager | What 1.0.0 chose automatically on NVIDIA; equivalent to neither evaluated profile |
| `cpu-float32` | cpu | float32 | eager | Debugging only |

Results under different profiles are not same-backend results, even with the
same weights and revision.

## Rules

1. **Frozen weights.** Neither project fine-tunes the backbone. Trained modules
   (for example a retention scorer on `embed` features, or a LoRA adapter) live
   in the project and are reported as that project's contribution.
2. **One-way dependency.** The backbone imports only the standard library,
   torch, transformers and huggingface_hub, never project code.
3. **Public interface only.** Projects never import backbone submodules.
4. **Versioned changes.** Any change here needs a bump of `VERSION` and
   `python -m backbone.check --stamp`. Each repository adopts a new version by
   an explicit change of its own, and every result records the backbone
   version it used, so one update never silently changes both experiments.
   Matching `MANIFEST.json` files prove two copies at the same version are identical.
5. **Same pins, explicit runtime.** Both projects use the same model revisions.
   Runtime is part of the backend: every engine is created with a named
   profile, and comparisons across projects state which profiles they used.
6. **Frozen paths stay frozen.** Evaluated code (ApronLens `backend/server.py`
   and the historical runners) never imports the backbone; the
   `apronlens-v2-mps` profile reproduces its configuration for new code.

`python -m backbone.check` enforces rules 2–4 and runs in each repository's CI.

## Relation to `modelaccess`

The backbone covers local frozen weights only. The separate `modelaccess`
package defines one inference contract over local engines and hosted APIs
(capabilities, usage, finish reasons, returned-model checks). Its local adapter
creates a backbone engine with an explicit profile; hosted adapters never pass
through the backbone.

## Download a model

```sh
python -m backbone.download --model qwen3-vl-4b
```

Weights go to the ignored `models/<local_dir>/` folder with a download
manifest. To add a model, add an entry with `"revision": null`, read its model
card, run `python -m backbone.download --model <name> --pin`, bump `VERSION`
and re-stamp.
