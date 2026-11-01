#!/bin/bash
# Conversation families (scripts/run_conversation_families.py) of one local model on a GAIVI GPU,
# with and without evidence images, scored against the development labels.
# Usage, from the repository root with the model environment active:
#   sbatch --export=ALL,MODEL=qwen3.5-9b,RUNTIME=compaction-gaivi-cuda scripts/gaivi/conversation_families.sbatch
# Use GAIVI only for distinct runs (docs/GAIVI.md section 6). MODEL and RUNTIME have no defaults.
# The image turns need two Unity renders, which GAIVI cannot make; copy them from the Mac first:
#   scp work/visual-observation-24s.png work/visual-observation-dev05-20s.png gaivi:<repo>/work/
# The images-on run refuses to start without them.
#SBATCH --job-name=apronlens-families
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
MODEL="${MODEL:?set MODEL to a model not already run with this method; see docs/GAIVI.md section 6}"
RUNTIME="${RUNTIME:?set RUNTIME to a runtime profile, e.g. compaction-gaivi-cuda}"
nvidia-smi --query-gpu=name,memory.total --format=csv
for IMAGES in on off; do
  # Each attempt and condition writes its own file; nothing is overwritten.
  output="work/gaivi/families-${MODEL}-${RUNTIME}-images-${IMAGES}-${SLURM_JOB_ID}-r${SLURM_RESTART_COUNT:-0}.json"
  "$PYTHON" scripts/run_conversation_families.py --model "$MODEL" --profile "$RUNTIME" --images "$IMAGES" --output "$output"
  echo "Results: $output"
done
