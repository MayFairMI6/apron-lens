# Shared backbone

This folder is the frozen vision-language backbone shared by **ApronLens** and the
**context-compaction project**. It is copied identically into both repositories.
Each project adds its own modules on top; the backbone itself is never a
research contribution of either project.

## Boundary

| Inside the backbone | Outside: belongs to a project |
|---|---|
| Model registry with exact revisions (`models.json`) | Prompts and prompt versions |
| Device and number-type choice (`runtime.py`) | Datasets, splits, labels, answer keys |
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
| `load_engine(name)`, `VLMEngine` | Load a pinned model; refuses a download whose manifest does not match |
| `engine.generate(prompt, image)` | Free text; returns `(text, input_tokens, output_tokens)` |
| `engine.score_labels(prompt, image, labels)` | Next-token log-probabilities of single-token labels |
| `engine.embed(prompt, image=None)` | Mean-pooled final hidden state: frozen features for project modules |
| `pick_device(torch)`, `pick_dtype(torch, device)`, `check_transformers(name, version)` | Runtime helpers |

## Models

| Name | Role | Model | Environment |
|---|---|---|---|
| `qwen2.5-vl-3b` | primary | Qwen/Qwen2.5-VL-3B-Instruct | `requirements-qwen.lock.txt` |
| `qwen3-vl-4b` | robustness: the one second backbone both projects report | Qwen/Qwen3-VL-4B-Instruct | `requirements-qwen.lock.txt` |
| `qwen3-vl-8b`, `qwen3.5-9b`, `gemma-4-e4b` | exploratory, outside course scope | see `models.json` | transformers 5 models: `requirements-candidates.txt` |

On NVIDIA GPUs the engine uses bfloat16 where supported; on Apple Silicon it
uses each entry's `dtype` (float16 for the primary, as evaluated).

## Rules

1. **Frozen weights.** Neither project fine-tunes the backbone. Trained modules
   (for example a retention scorer on `embed` features, or a LoRA adapter) live
   in the project and are reported as that project's contribution.
2. **One-way dependency.** The backbone imports only the standard library,
   torch, transformers and huggingface_hub, never project code.
3. **Public interface only.** Projects never import backbone submodules.
4. **Versioned changes.** Any change here needs a bump of `VERSION` and
   `python -m backbone.check --stamp`, then the same change in the other
   repository. Matching `MANIFEST.json` files prove the copies are identical.
5. **Same pins everywhere.** Both projects use the same revisions, so a
   backbone difference can never explain a difference between their results.

`python -m backbone.check` enforces rules 2–4 and runs in each repository's CI.

## Download a model

```sh
python -m backbone.download --model qwen3-vl-4b
```

Weights go to the ignored `models/<local_dir>/` folder with a download
manifest. To add a model, add an entry with `"revision": null`, read its model
card, run `python -m backbone.download --model <name> --pin`, bump `VERSION`
and re-stamp.
