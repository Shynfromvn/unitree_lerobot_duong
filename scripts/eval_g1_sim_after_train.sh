#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DATASET_PARENT="${DATASET_PARENT:-$(dirname "$PROJECT_ROOT")/datasets}"
DATASET_REPO_ID="${DATASET_REPO_ID:-G1_Dex3_PickApple_Dataset_HeadcamOnly}"
DATASET_DIR="${DATASET_DIR:-$DATASET_PARENT/$DATASET_REPO_ID}"

ARM="${ARM:-G1_29}"
EE="${EE:-dex3}"
FREQUENCY="${FREQUENCY:-30}"
IMAGE_HOST="${IMAGE_HOST:-127.0.0.1}"
MAX_EPISODES="${MAX_EPISODES:-1200}"
SAVE_DATA="${SAVE_DATA:-false}"
TASK_DIR="${TASK_DIR:-$PROJECT_ROOT/data/sim_eval}"
VISUALIZATION="${VISUALIZATION:-true}"
RENAME_MAP="${RENAME_MAP:-{\"observation.images.cam_left_high\":\"observation.images.head_cam\"}}"

if [[ -n "${CONDA_PREFIX:-}" ]]; then
  NVIDIA_LIBS="$(python -c 'import site,glob; print(":".join(glob.glob(site.getsitepackages()[0]+"/nvidia/*/lib")))')"
  export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$NVIDIA_LIBS:${LD_LIBRARY_PATH:-}"
fi

if [[ -z "${POLICY_PATH:-}" ]]; then
  POLICY_PATH="$(
    find "$PROJECT_ROOT/lerobot/outputs/train" -path "*/checkpoints/*/pretrained_model" -type d 2>/dev/null \
      | while read -r path; do
          if [[ -f "$path/model.safetensors" || -f "$path/pytorch_model.bin" ]]; then
            stat -c '%Y %n' "$path"
          fi
        done \
      | sort -nr \
      | head -n 1 \
      | cut -d' ' -f2-
  )"
fi

if [[ -z "${POLICY_PATH:-}" ]]; then
  echo "No policy checkpoint found. Set POLICY_PATH=/path/to/pretrained_model." >&2
  exit 1
fi

if [[ ! -d "$POLICY_PATH" ]]; then
  echo "POLICY_PATH does not exist: $POLICY_PATH" >&2
  exit 1
fi

if [[ ! -f "$DATASET_DIR/meta/info.json" ]]; then
  echo "Dataset metadata not found: $DATASET_DIR/meta/info.json" >&2
  echo "Set DATASET_DIR or regenerate the HeadcamOnly dataset first." >&2
  exit 1
fi

echo "Project root: $PROJECT_ROOT"
echo "Dataset:      $DATASET_DIR"
echo "Policy:       $POLICY_PATH"
echo "Image host:   $IMAGE_HOST"
echo "Arm/EE:       $ARM / $EE"
echo
echo "Before pressing 's' in eval_g1_sim.py, make sure the simulator is already running and publishes DDS/image data."
echo "This repository provides G1 MJCF/URDF assets, but eval_g1_sim.py itself talks to an external Unitree simulator over DDS and image_server."
echo

cd "$PROJECT_ROOT"

python unitree_lerobot/eval_robot/eval_g1_sim.py \
  --policy.path="$POLICY_PATH" \
  --repo_id="$DATASET_REPO_ID" \
  --root="$DATASET_DIR" \
  --episodes=0 \
  --frequency="$FREQUENCY" \
  --arm="$ARM" \
  --ee="$EE" \
  --visualization="$VISUALIZATION" \
  --save_data="$SAVE_DATA" \
  --task_dir="$TASK_DIR" \
  --max_episodes="$MAX_EPISODES" \
  --image_host="$IMAGE_HOST" \
  --rename_map="$RENAME_MAP" \
  "$@"
