#!/bin/bash
# Visual perception check (scripts/run_visual_perception_check.py) of one local model on a GAIVI GPU.
# Development scenarios only; scored against authored ground truth.
# Usage, from the repository root with the model environment active:
#   sbatch --export=ALL,MODEL=qwen3-vl-8b,RUNTIME=compaction-gaivi-cuda scripts/gaivi/perception_check.sbatch
# RUNTIME is required: compaction-gaivi-cuda (float16, sdpa) or cuda-bfloat16-eager. Results record it,
# the commit and the host.
# The check needs the six Unity renders from VisualCaptureVerification.SaveObservationSamples, which
# GAIVI cannot make; copy them from the Mac first:
#   scp work/visual-observation-*.png <NetID>@gaivi.cse.usf.edu:<repo>/work/
#SBATCH --job-name=apronlens-perception
#SBATCH --partition=ClsGenAI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-task=1
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --requeue
#SBATCH --output=slurm-%x-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
PYTHON="${PYTHON:-python}"
MODEL="${MODEL:-qwen3-vl-8b}"
RUNTIME="${RUNTIME:?set RUNTIME to a runtime profile, e.g. compaction-gaivi-cuda}"
for t in 24s 29s 31s dev02-20s dev02-27s dev02-33s; do
  [ -f "work/visual-observation-$t.png" ] || { echo "Missing work/visual-observation-$t.png: copy the Unity renders from the Mac (see the header)." >&2; exit 2; }
done
nvidia-smi --query-gpu=name,memory.total --format=csv
output="work/gaivi/perception-${MODEL}-${RUNTIME}-${SLURM_JOB_ID}-r${SLURM_RESTART_COUNT:-0}.json"
"$PYTHON" scripts/run_visual_perception_check.py --model "$MODEL" --profile "$RUNTIME" --output "$output"
echo "Results: $output"
