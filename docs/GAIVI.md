# Running model checks on USF GAIVI

GAIVI is USF's GPU cluster. The class allocation is node GPU42 in the
`ClsGenAI` partition, with 100 GB each in `/home`, `/data` and `/general`.
GitHub keeps running the model-free tests; GAIVI runs the real models.
Results are development observations, not held-out evidence. Every job names
a runtime profile (`RUNTIME=compaction-gaivi-cuda` for float16 with SDPA, as
the compaction project ran, or `cuda-bfloat16-eager`); neither matches the
frozen Apple MPS float16 run exactly, and the profile is recorded with the results.

GAIVI rules that shape these steps: connect through the USF GlobalProtect VPN;
anything over 10 minutes, 1 CPU core or 2 GB memory on the login node must run
as a SLURM job; never SSH into compute nodes; no `sudo`; storage is not backed
up; accounts inactive for 6 months are removed. See the
[GAIVI documentation](https://docs.gaivi.cse.usf.edu/).

## 1. Log in and clone

```sh
ssh <NetID>@gaivi.cse.usf.edu
git clone https://github.com/MayFairMI6/apron-lens.git
cd apron-lens
```

The repository is private: authenticate with a GitHub personal access token or
an SSH key added to your GitHub account.

## 2. Keep weights in /data

All five models need about 69 GB, so store them in `/data`, not `/home`, and
link them into the checkout:

```sh
mkdir -p /data/<your folder>/apron-lens-models
ln -s /data/<your folder>/apron-lens-models models
```

Check your `/data` folder name with `ls /data` or the GAIVI documentation.

## 3. Create the Python environments (inside a job)

Installing PyTorch takes longer than the login node allows, so open an
interactive job first:

```sh
srun --partition=ClsGenAI --cpus-per-task=2 --mem=8G --time=01:00:00 --pty bash
conda create -y -n apronlens python=3.12
conda activate apronlens
python -m pip install -r requirements-qwen.lock.txt
```

That environment runs the evaluated `qwen2.5-vl-3b` and the Qwen3-VL candidates.
For `qwen3.5-9b` and `gemma-4-e4b`, which need transformers 5, make a second
environment. Three GAIVI details shape how (found on GPU42, October 2026):

- The `/home` quota is small; PyTorch alone fills it. Keep this environment,
  and the pip, conda and Hugging Face caches, in your `/data` folder.
- GPU42's driver (530) supports CUDA 12.x only, while PyPI's default PyTorch
  wheels are built for CUDA 13. Install the `cu126` build.
- Compute nodes keep dropping long downloads, such as the 400 MB CUDA wheels.
  Fetch the wheels on the login node, where downloads complete, then install
  them in a job.

On the login node (each step takes a few minutes):

```sh
DATA=/data/<your folder>
mkdir -p $DATA/wheels-cu126 $DATA/logs
export PIP_CACHE_DIR=$DATA/pip-cache CONDA_PKGS_DIRS=$DATA/conda-pkgs
conda create -y -q -p $DATA/conda-envs/wheel-fetch python=3.12
PY=$DATA/conda-envs/wheel-fetch/bin/python
$PY -m pip download -d $DATA/wheels-cu126 --index-url https://download.pytorch.org/whl/cu126 "torch>=2.6,<3" "torchvision>=0.21,<1"
ls $DATA/wheels-cu126 | grep ^torch   # pin these exact versions in the next line
printf "torch==<version>+cu126\ntorchvision==<version>+cu126\n" > $DATA/wheels-cu126/constraints.txt
$PY -m pip download -d $DATA/wheels-cu126 --find-links $DATA/wheels-cu126 -c $DATA/wheels-cu126/constraints.txt -r requirements-candidates.txt
```

Then build the environment and download both models in one job:

```sh
sbatch --export=ALL,DATA=$DATA --output=$DATA/logs/slurm-%x-%j.out scripts/gaivi/setup_candidates.sbatch
```

The job prints the torch version and whether CUDA is available; use
`PYTHON=$DATA/conda-envs/apronlens-candidates/bin/python` when submitting runs
for these two models.

Exit the interactive job with `exit` when done.

## 4. Download weights (a job)

Activate the environment that will use the models, then submit from the
repository root. `--export=ALL` passes the active environment to the job.

```sh
conda activate apronlens
sbatch --export=ALL,MODELS="qwen2.5-vl-3b qwen3-vl-4b qwen3-vl-8b" scripts/gaivi/download_models.sbatch
# for the candidate models, from the apronlens-candidates environment:
sbatch --export=ALL,MODELS="qwen3.5-9b gemma-4-e4b" scripts/gaivi/download_models.sbatch
```

Each model lands in `models/<name>/` with a manifest pinning its exact revision.
If the job cannot reach huggingface.co, compute nodes may lack internet access;
ask GAIVI support (Bellini-CollegeLRICS@usf.edu) for the recommended route.

## 5. Run a development check (a GPU job)

```sh
conda activate apronlens
sbatch --export=ALL,MODEL=qwen3-vl-4b,SUITE=smoke,RUNTIME=compaction-gaivi-cuda scripts/gaivi/model_check.sbatch
squeue -u $USER
```

`SUITE=dev` runs the 24 development questions. For `qwen3.5-9b` or
`gemma-4-e4b`, activate `apronlens-candidates` before `sbatch`. The job log is
`slurm-apronlens-check-<job id>.out`; results go to
`work/gaivi/<model>-<suite>-<job id>-r<restart>/`, with `summary.json`
recording the model revision, GPU, number type and transformers version.

GAIVI may preempt a job; it is requeued and restarts into a new results folder,
so an interrupted attempt is kept rather than overwritten.

## 6. Conversation and perception runs (GPU jobs)

These run `scripts/run_conversation_smoke.py` (25 development turns through
the `/conversation` turn handler) and `scripts/run_visual_perception_check.py`
(18 prop judgements against authored ground truth) on a GAIVI GPU. Both use
development data only.

GAIVI has no Unity, so first copy the evidence renders from the Mac. They come
from `VisualCaptureVerification.SaveObservationSamples`:

```sh
scp work/visual-observation-*.png <NetID>@gaivi.cse.usf.edu:<repo>/work/
```

Use GAIVI only for distinct runs: a combination of model, method version
(prompt and referent rule) and data that hasn't been run already. Rerunning a
model counts as distinct only when the method or data changed. These have
already run on the Mac (`apronlens-v2-mps`) and shouldn't be repeated:

| Run | Model | Method | Result |
|---|---|---|---|
| 25 conversation turns | `qwen2.5-vl-3b` | prompt v4, `referent-rule-v2` | 15/25 |
| 25 conversation turns | `qwen3-vl-8b` | prompt v4, `referent-rule-v2` | 22/25 |
| Perception check (18 judgements) | `qwen3-vl-8b` | redesigned props, v4 legend | 11/18 plain, 12/18 with legend |
| Perception check (18 judgements) | `qwen3-vl-4b` | v4 legend | 9/18 plain, 11/18 with legend |
| Perception check (18 judgements) | `qwen2.5-vl-3b` | v4 legend | 0/18 plain, 9/18 with legend |
| 16 family turns, images on / off | `qwen2.5-vl-3b`, `qwen3-vl-4b`, `qwen3-vl-8b` | prompt v4 | 3, 5, 8 of 16 (both) |
| 16 family turns, images on / off | `qwen2.5-vl-3b` | prompt v5 | 5/16, 4/16 |
| 16 family turns, images on / off | `qwen3-vl-4b` | prompt v5 | 12/16, 11/16 |
| 16 family turns, images on / off | `qwen3-vl-8b` | prompt v5 | 11/16, 12/16 |

Not yet run with this method: `qwen3.5-9b` and `gemma-4-e4b` (the
`apronlens-candidates` environment, which has transformers 5; step 3 builds it
and downloads both).

Then, with the environment for the model active:

```sh
conda activate apronlens-candidates
sbatch --export=ALL,MODEL=qwen3.5-9b,RUNTIME=compaction-gaivi-cuda scripts/gaivi/conversation_smoke.sbatch
sbatch --export=ALL,MODEL=qwen3.5-9b,RUNTIME=compaction-gaivi-cuda scripts/gaivi/perception_check.sbatch
```

The development families (`scripts/run_conversation_families.py`, images on
and then off, in one job):

```sh
sbatch --export=ALL,MODEL=qwen3.5-9b,RUNTIME=compaction-gaivi-cuda,PYTHON=$DATA/conda-envs/apronlens-candidates/bin/python scripts/gaivi/conversation_families.sbatch
```

`MODEL` has no default, so a job can't repeat a completed run by accident. Add
each finished run to the table above.

Results go to `work/gaivi/conversation-…json` and `work/gaivi/perception-…json`.
Each records the runtime, the commit (and whether the checkout had uncommitted
changes) and the host. A preempted attempt writes its own file; nothing is
overwritten. Without the renders, the conversation run skips its two image
turns and the perception job stops with a message.

Compare GAIVI and Mac results only within the same runtime profile. The frozen
V2 results ran on Apple MPS in float16, which neither CUDA profile matches
exactly.

## 7. Bring results back

Copy the results folder to your computer (`scp -r`), or commit it on a branch
and open a pull request. Keep raw results and failures; do not rerun until a
model passes.
