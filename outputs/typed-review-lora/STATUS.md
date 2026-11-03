# B05: bounded typed-review weight-training pilot

Implementation and local checks are prepared; no trained-candidate accuracy result
or deployment is claimed. The existing application, video and historical results
remain unchanged.

The recipe is in `experiments/typed_review_lora/protocol.json`. The authored pilot
contains144 training,48 validation and48 sealed evaluation examples. These are
6/2/2 scenario families, with four correlated substitutions and six response kinds
per family. This is a small supplied-report semantic review experiment, not a
retrieval benchmark, independent real-airport sample or validated learner assessment.
Source eligibility is checked structurally; citation semantics are not certified.

The independent pre-training review found and corrected three draft target defects:

- Incomplete baggage loading did not establish that loading was actively underway.
- Claiming arrival at a destination contradicted the criterion that it was only intended.
- Claiming a waiting aircraft occupied the stand also contradicted its waiting-state criterion.

Draft-v1 and corrected-v2 manifests are preserved separately. No model was trained
on the rejected draft. All192 train/validation targets were independently checked;
sealed evaluation model responses do not exist yet. The tokenizer audit verified
all192 inputs:890–962 total tokens, identical inference/training prompt prefixes,
masked prompt loss and retained end-of-turn targets. The limit is4096; no target
was truncated. All340 existing plus added local tests passed. Backbone boundary
and frozen160-record research-integrity checks passed.

GAIVI setup is isolated under `/data/aravindav/airfieldlens-review-lora`. Probe571254
failed before GPU work with `ModuleNotFoundError: torch` because its temporary
venv had not completed creation. Its failed receipt is retained. The replacement
environment inherits torch2.7.1+cu118, transformers5.22.1 and accelerate1.15.0,
adding peft0.21.2 and bitsandbytes0.50.2 without upgrading the shared environment.
Probe571255 completed successfully on an NVIDIA TITAN RTX: the small NF4 quantized
backward check passed. Its exact package/runtime receipt is retained. Full9B
load/backward/save/reload remains a separate gate.

The primary metric counts each erroneous criterion marked `met`, even when the
whole answer is labelled `needs_review`. Positive-answer usefulness, structural
rejections, omissions versus contradictions, latency and token use are also reported.
The same quantized model/runtime is used with the adapter disabled and enabled.
Validation loss selects one of24/48/72-step checkpoints; the selected adapter and
all executable prompt/runtime dependencies must be locked before sealed evaluation.
No new false acceptance is permitted for promotion, and a separate native-runtime
acceptance check is required before changing the app.
