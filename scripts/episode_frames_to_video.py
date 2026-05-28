#!/usr/bin/env python3
import argparse
from pathlib import Path

import cv2


def latest_episode(task_dir: Path) -> Path:
    episodes = sorted([p for p in task_dir.iterdir() if p.is_dir() and p.name.startswith("episode_")])
    if not episodes:
        raise FileNotFoundError(f"No episode_* directories found under {task_dir}")
    return episodes[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert an eval_g1_sim saved episode camera frames to MP4.")
    parser.add_argument("--task-dir", type=Path, required=True, help="Directory containing episode_* folders.")
    parser.add_argument("--episode-dir", type=Path, default=None, help="Specific episode directory. Defaults to latest.")
    parser.add_argument("--camera", default="color_0", help="Camera suffix saved by EpisodeWriter, e.g. color_0.")
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    task_dir = args.task_dir.expanduser().resolve()
    episode_dir = args.episode_dir.expanduser().resolve() if args.episode_dir else latest_episode(task_dir)
    color_dir = episode_dir / "colors"
    if not color_dir.is_dir():
        raise FileNotFoundError(f"Missing colors directory: {color_dir}")

    frames = sorted(color_dir.glob(f"*_{args.camera}.jpg"))
    if not frames:
        raise FileNotFoundError(f"No frames matching '*_{args.camera}.jpg' in {color_dir}")

    first = cv2.imread(str(frames[0]))
    if first is None:
        raise RuntimeError(f"Could not read first frame: {frames[0]}")

    height, width = first.shape[:2]
    output = args.output.expanduser().resolve() if args.output else episode_dir / f"{episode_dir.name}_{args.camera}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer: {output}")

    written = 0
    for frame_path in frames:
        frame = cv2.imread(str(frame_path))
        if frame is None:
            continue
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))
        writer.write(frame)
        written += 1

    writer.release()
    print(f"Wrote {written} frames at {args.fps:g} fps: {output}")


if __name__ == "__main__":
    main()
