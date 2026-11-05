#!/bin/bash
#SBATCH --job-name=airfield-lora-probe
#SBATCH --partition=ClsGenAI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:15:00
set -euo pipefail
cd /data/aravindav/airfieldlens-review-lora/repo
export PYTHONUNBUFFERED=1
/data/aravindav/airfieldlens-review-lora/env2/bin/python -m experiments.typed_review_lora.gpu_preflight
