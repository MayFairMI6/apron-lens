#!/bin/bash
# Development check of one model on a GAIVI GPU. Never reads the fresh/held-out question sets.
# Usage, from the repository root with the model environment active:
#   sbatch --export=ALL,MODEL=qwen3-vl-4b,SUITE=smoke scripts/gaivi/model_check.sbatch
#SBATCH --job-name=apronlens-check
#SBATCH --partition=ClsGenAI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-task=1
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --requeue
#SBATCH --output=slurm-%x-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
PYTHON="${PYTHON:-python}"
MODEL="${MODEL:-qwen2.5-vl-3b}"
SUITE="${SUITE:-smoke}"
nvidia-smi --query-gpu=name,memory.total --format=csv
# A preempted job restarts from the top; each attempt gets its own folder because
# run_model_check.py never overwrites an earlier run.
output="work/gaivi/${MODEL}-${SUITE}-${SLURM_JOB_ID}-r${SLURM_RESTART_COUNT:-0}"
"$PYTHON" scripts/run_model_check.py --suite "$SUITE" --model "$MODEL" --output "$output"
echo "Results: $output"
