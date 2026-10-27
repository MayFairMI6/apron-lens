#!/bin/bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
editor_path="${UNITY_EDITOR:-$project_root/work/unity-editor/Unity.app/Contents/MacOS/Unity}"
mkdir -p "$project_root/work"
"$editor_path" -batchmode -nographics -quit -buildTarget Android \
  -projectPath "$project_root/unity/SurfaceSafetyCoach" \
  -executeMethod MilestoneBuild.Android \
  -logFile "$project_root/work/unity-android-build.log"
