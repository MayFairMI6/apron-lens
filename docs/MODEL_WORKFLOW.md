# Model compute and GitHub workflow

GitHub stores source, datasets, run records and workflow definitions. Inference
runs on a machine with sufficient memory and the pinned local model. The current
engine is verified on Apple Silicon MPS; it falls back to CPU and does not yet
select CUDA. No weights or model API credentials are needed by the hosted checks.

## Workflow choices

| Work | Where it runs | Trigger | Model required |
|---|---|---|---|
| Unit/API tests and frozen artifact integrity | GitHub-hosted Linux | Push / pull request | No |
| Two real-model smoke queries | Your configured Apple Silicon runner | Manual Actions dispatch | Cached Qwen |
| 24-question development regression | Same configured runner | Manual Actions dispatch | Cached Qwen |
| New research evaluation | Deliberately frozen local protocol | Research milestone | Cached Qwen + new untouched set |
| Unity / Android / AR validation | Licensed Unity install / phone | Local build | Model optional |

The [first real-model GitHub job](https://github.com/MayFairMI6/airfield-context-ar/actions/runs/40566003969)
passed both smoke cases using a temporary Apple Silicon runner and saved a
run artifact. That one-job runner stopped and unregistered automatically; no
system background service was installed. The two repository variables are
configured for the original development machine. Register/start a matching
runner for future jobs, and update those variables when using another machine.
A dispatch without an online matching runner waits in the queue.

## Register a Mac runner

1. In this private repository, open **Settings → Actions → Runners → New
   self-hosted runner**. Choose macOS ARM64. Follow GitHub's generated download
   and registration instructions; use its short-lived registration token locally.
2. Add the custom label **airfield-qwen**. Keep the default `self-hosted`, `macOS`
   and `ARM64` labels. Run the runner only while you intend to accept work, or
   configure its service deliberately.
3. Keep the existing model cache and Python environment **outside** the runner's
   checkout directory. Checkout cleanup can remove ignored files in a checkout.
4. In **Settings → Secrets and variables → Actions → Variables**, add:
   - `AIRFIELD_QWEN_PYTHON`: absolute path to the existing model environment's
     Python executable, for example `/path/to/project/.venv-qwen/bin/python`.
   - `AIRFIELD_MODEL_CACHE`: absolute path to the existing
     `models/Qwen2.5-VL-3B-Instruct` folder, including its download manifest.
5. In **Actions → Qwen development check → Run workflow**, select `smoke` or
   `dev`, using reviewed code from a trusted branch.
6. Download the `qwen-…` artifact from that run. It contains raw selections,
   decision prompts/scores, separate baseline results, guard outcome, latency,
   model revision, source hashes and commit ID.

The Python runtime must already have the dependencies from the model lock file.
The workflow validates the cache's manifest and attaches a symlink; it performs
no multi-gigabyte download and does not require a service connection token.
Runner registration tokens are not repository secrets and must not be committed.

The self-hosted workflow is manual-only and has no pull-request trigger. Run
reviewed code because it executes on your machine. See GitHub's
[self-hosted runner guidance](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow).

## Run the same development check locally

```sh
.venv-qwen/bin/python scripts/run_model_check.py --suite smoke --output work/check-001
.venv-qwen/bin/python scripts/run_model_check.py --suite dev --output work/check-002
```

Use a new output directory for each run. The script refuses to overwrite an
existing results file. Model inference completes before the separate baseline
and gold are used for scoring. Model errors are preserved; score differences
are observations, not a requirement to tune until every known answer passes.
The smoke gold is the deterministic query contract, not independent expert labels.

## Preserve the research boundary

`outputs/reasoning_v2/` is a historical frozen run, with every attempt and raw
result retained. Its source snapshot must remain unchanged. The hosted integrity
check verifies preserved files; current code may evolve independently. Use
`python scripts/check_research_integrity.py --current` only when asserting that
current inference source still matches that V2 run.

The 32 previously fresh questions have now been observed. Do not tune on them
and call a later result held out. For the next research comparison:

1. Develop using development cases only; write down all iterations.
2. Have new scenario families/labels authored and reviewed separately.
3. Freeze the new protocol, source, model and dataset hashes before opening tests.
4. Run once with raw model results, guard outcomes and baseline scored separately.
5. Preserve failures and interruptions, and report family-level limitations.

The original V1 evaluation script requires its original source hashes and is
retained as historical code. Current V2 report reproduction requires the pinned
local model manifest even though aggregating saved results performs no inference.
Use the preserved source snapshots to investigate a historical environment;
do not overwrite its records to make a new run appear identical.
