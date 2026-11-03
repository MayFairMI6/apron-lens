# Typed-response reviewer: bounded weight-training pilot

This separate experiment tests whether a small supervised adapter can reduce incorrect
credit in report-grounded practice feedback. It does not change the running app.
The pinned base is Qwen3.5-9B; previous 18 exposed cases are development evidence only.

`protocol.json` fixes family allocation and the training budget before generation.
Training and evaluation use the same quantized runtime, so neither result is silently
compared with the earlier unquantized Mac results. Four variants within a family are
correlated. Shared JSON output conventions are unavoidable; withheld scenario families
do not establish general linguistic or real-airport generalization.

Training is gated on independent target review and a successful GPU compatibility
check. Final evaluation must follow checkpoint selection, with the checkpoint and
runner hashes recorded before opening test responses. A failed compatibility check,
unhelpful adapter or regression is a reportable outcome, not permission to silently
change the recipe or overwrite results. Deployment requires a separate acceptance check.

Reproduce data with:

```sh
python -m experiments.typed_review_lora.build_data --output work/typed-review-lora/data-v2
```

The output directory must not already exist. The independent review's approval
binds the dataset manifest, protocol and executable source hashes. `train` refuses
missing/stale approval or a failed full-model smoke check. `run.sbatch` gives the
commands for compatibility and bounded training, followed by a separately invoked
paired evaluation after independent checkpoint-lock review.
It uses the experiment's isolated GAIVI environment and never starts the application.
See `outputs/typed-review-lora/STATUS.md` for actual execution status rather than
assuming the presence of scripts means the experiment has run.
