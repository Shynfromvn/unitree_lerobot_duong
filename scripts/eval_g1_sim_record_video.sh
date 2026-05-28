#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TASK_DIR="${TASK_DIR:-$PROJECT_ROOT/data/sim_eval_recordings}"
MAX_EPISODES="${MAX_EPISODES:-900}"
FREQUENCY="${FREQUENCY:-30}"
CAMERA="${CAMERA:-color_0}"
VIDEO_OUTPUT="${VIDEO_OUTPUT:-}"

mkdir -p "$TASK_DIR"

echo "Recording sim eval frames to: $TASK_DIR"
echo "The eval loop will save the episode when it succeeds or when max_episodes is reached."
echo "Default max_episodes=$MAX_EPISODES at ${FREQUENCY}Hz gives about $((MAX_EPISODES / FREQUENCY)) seconds."
echo

set +e
SAVE_DATA=true \
TASK_DIR="$TASK_DIR" \
MAX_EPISODES="$MAX_EPISODES" \
FREQUENCY="$FREQUENCY" \
bash "$SCRIPT_DIR/eval_g1_sim_after_train.sh"
eval_status=$?
set -e

if [[ "$eval_status" -ne 0 ]]; then
  echo "eval_g1_sim exited with status $eval_status. Trying to convert any frames that were flushed."
fi

if [[ -n "$VIDEO_OUTPUT" ]]; then
  python "$SCRIPT_DIR/episode_frames_to_video.py" \
    --task-dir "$TASK_DIR" \
    --camera "$CAMERA" \
    --fps "$FREQUENCY" \
    --output "$VIDEO_OUTPUT"
else
  python "$SCRIPT_DIR/episode_frames_to_video.py" \
    --task-dir "$TASK_DIR" \
    --camera "$CAMERA" \
    --fps "$FREQUENCY"
fi
