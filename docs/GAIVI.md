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
For `qwen3.5-9b` and `gemma-4-e4b`, which need transformers 5, make a second one:

```sh
conda create -y -n apronlens-candidates python=3.12
conda activate apronlens-candidates
python -m pip install -r requirements-candidates.txt
```

Exit the interactive job with `exit` when done.

## 4. Download weights (a job)

Activate the environment that will use the models, then submit from the
repository root. `--export=ALL` passes the active environment to the job.

```sh
conda activate apronlens
sbatch --export=ALL,MODELS="qwen2.5-vl-3b qwen3-vl-4b qwen3-vl-8b" scripts/gaivi/download_models.sbatch
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

## 6. Bring results back

Copy the results folder to your computer (`scp -r`), or commit it on a branch
and open a pull request. Keep raw results and failures; do not rerun until a
model passes.
