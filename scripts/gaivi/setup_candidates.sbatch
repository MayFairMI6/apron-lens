#!/bin/bash
# The apronlens-candidates environment (transformers 5, for qwen3.5-9b and gemma-4-e4b) and their weights.
# Usage, from the repository root, after fetching the wheels on the login node (docs/GAIVI.md section 3):
#   sbatch --export=ALL,DATA=/data/<your folder> --output=/data/<your folder>/logs/slurm-%x-%j.out \
#     scripts/gaivi/setup_candidates.sbatch
# The environment and every cache live under DATA: the home quota is too small for PyTorch.
#SBATCH --job-name=apronlens-setup
#SBATCH --partition=ClsGenAI
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=03:00:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
DATA="${DATA:?set DATA to your /data folder}"
ENV="$DATA/conda-envs/apronlens-candidates"
WHEELS="$DATA/wheels-cu126"
export PIP_CACHE_DIR="$DATA/pip-cache" HF_HOME="$DATA/hf-cache" CONDA_PKGS_DIRS="$DATA/conda-pkgs"
if [ ! -x "$ENV/bin/python" ]; then "${CONDA:-conda}" create -y -q -p "$ENV" python=3.12; fi
# Install from the wheels fetched on the login node; fall back to the index only for anything missing.
pip_args=(-q --find-links "$WHEELS" -c "$WHEELS/constraints.txt" -r requirements-candidates.txt)
"$ENV/bin/python" -m pip install --no-index "${pip_args[@]}" || "$ENV/bin/python" -m pip install --resume-retries 20 "${pip_args[@]}"
"$ENV/bin/python" -c "import torch, transformers; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0), 'transformers', transformers.__version__)"
for model in qwen3.5-9b gemma-4-e4b; do
  downloaded=0
  for attempt in 1 2 3 4 5 6; do
    if "$ENV/bin/python" -m backbone.download --model "$model"; then downloaded=1; break; fi
    echo "download $model attempt $attempt failed; retrying"; sleep 20
  done
  # A model that never downloaded leaves the environment unusable for its runs: fail the job.
  if [ "$downloaded" -ne 1 ]; then echo "download $model failed after 6 attempts" >&2; exit 1; fi
done
du -shL models/*/
