#!/bin/bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_root"
exec "$project_root/.venv-qwen/bin/python" -m backend.server "$@"
