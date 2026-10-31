#!/bin/bash
# Conversation development run (scripts/run_conversation_smoke.py) of one local model on a GAIVI GPU.
# Development data only; never reads held-out answers or the v1 question/gold file.
# Usage, from the repository root with the model environment active:
#   sbatch --export=ALL,MODEL=qwen3-vl-8b,RUNTIME=compaction-gaivi-cuda scripts/gaivi/conversation_smoke.sbatch
# RUNTIME is required: compaction-gaivi-cuda (float16, sdpa) or cuda-bfloat16-eager. Results record it,
# the commit and the host; runs on different runtimes must not be pooled in one comparison.
# The two image turns need Unity renders, which GAIVI cannot make; copy them from the Mac first:
#   scp work/visual-observation-24s.png work/visual-observation-dev02-20s.png <NetID>@gaivi.cse.usf.edu:<repo>/work/
# Without them the image turns are skipped and the log says so.
#SBATCH --job-name=apronlens-conversation
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
MODEL="${MODEL:-qwen3-vl-8b}"
RUNTIME="${RUNTIME:?set RUNTIME to a runtime profile, e.g. compaction-gaivi-cuda}"
nvidia-smi --query-gpu=name,memory.total --format=csv
# A preempted job restarts from the top; each attempt writes its own file, and the script never overwrites one.
output="work/gaivi/conversation-${MODEL}-${RUNTIME}-${SLURM_JOB_ID}-r${SLURM_RESTART_COUNT:-0}.json"
"$PYTHON" scripts/run_conversation_smoke.py --model "$MODEL" --profile "$RUNTIME" --output "$output"
echo "Results: $output"
