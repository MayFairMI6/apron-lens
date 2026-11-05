#!/bin/bash
#SBATCH --job-name=airfield-review-lora
#SBATCH --partition=ClsGenAI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-task=1
#SBATCH --mem=48G
#SBATCH --time=06:00:00
set -euo pipefail
RUN_ROOT=/data/aravindav/airfieldlens-review-lora
cd "$RUN_ROOT/repo"
export PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
PYTHON="$RUN_ROOT/env2/bin/python"
# Each command fails closed. No training if loading/backward/reload fails;
# no sealed evaluation unless fixed training and validation selection complete.
"$PYTHON" -m experiments.typed_review_lora.gpu_preflight --model "$RUN_ROOT/model" --data "$RUN_ROOT/data-v2" --out "$RUN_ROOT/full-smoke.json"
"$PYTHON" -m experiments.typed_review_lora.train --model "$RUN_ROOT/model" --data "$RUN_ROOT/data-v2" --out "$RUN_ROOT/run-v1" --approval "$RUN_ROOT/approval.json" --smoke "$RUN_ROOT/full-smoke.json"
# After independent selection-lock review, run separately:
# "$PYTHON" -m experiments.typed_review_lora.evaluate --model "$RUN_ROOT/model" --data "$RUN_ROOT/data-v2" --training "$RUN_ROOT/run-v1" --out "$RUN_ROOT/evaluation-v1"
