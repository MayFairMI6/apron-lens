#!/bin/bash
# Download pinned model weights on GAIVI inside a job (login nodes stop tasks over 10 minutes).
# Usage, from the repository root with the model environment active:
#   sbatch --export=ALL,MODELS="qwen2.5-vl-3b qwen3-vl-4b" scripts/gaivi/download_models.sbatch
#SBATCH --job-name=apronlens-download
#SBATCH --partition=ClsGenAI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=slurm-%x-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
PYTHON="${PYTHON:-python}"
for model in ${MODELS:-qwen2.5-vl-3b}; do
  "$PYTHON" -m backbone.download --model "$model"
done
du -sh models/*/ 2>/dev/null || true
