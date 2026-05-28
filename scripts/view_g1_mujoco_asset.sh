#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_ROOT/unitree_lerobot/eval_robot/assets/g1/g1_body29_hand14.xml}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "MuJoCo model not found: $MODEL_PATH" >&2
  exit 1
fi

python -c 'import mujoco, mujoco.viewer; print("mujoco ok")' >/dev/null

echo "Opening MuJoCo viewer with:"
echo "$MODEL_PATH"
echo
echo "This is only a model viewer. It is not the DDS simulator required by eval_g1_sim.py."

MODEL_PATH="$MODEL_PATH" python -c 'import os, mujoco.viewer; mujoco.viewer.launch_from_path(os.environ["MODEL_PATH"])'
