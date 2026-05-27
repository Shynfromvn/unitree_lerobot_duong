"""
Create a LeRobot dataset with a single fake head camera.

The new camera is copied from an existing camera stream, by default:
observation.images.cam_left_high -> observation.images.head_cam
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd


DEFAULT_SOURCE_VIDEO_KEY = "observation.images.cam_left_high"
DEFAULT_TARGET_VIDEO_KEY = "observation.images.head_cam"


def _is_image_feature(name: str) -> bool:
    return "observation.images." in name


def _copy_base_tree(src_dir: Path, dst_dir: Path, overwrite: bool) -> None:
    if dst_dir.exists():
        has_content = any(dst_dir.iterdir())
        if has_content and not overwrite:
            raise FileExistsError(
                f"{dst_dir} already exists and is not empty. Re-run with --overwrite if you want to replace it."
            )
        if has_content:
            shutil.rmtree(dst_dir)

    ignore = shutil.ignore_patterns(".cache", "videos")
    shutil.copytree(src_dir, dst_dir, ignore=ignore, dirs_exist_ok=True)


def _rewrite_info_json(
    dst_dir: Path,
    source_video_key: str,
    target_video_key: str,
) -> None:
    info_path = dst_dir / "meta" / "info.json"
    with info_path.open("r", encoding="utf-8") as f:
        info = json.load(f)

    features = info["features"]
    if source_video_key not in features:
        raise KeyError(f"{source_video_key} was not found in {info_path}")

    new_features = {}
    for key, value in features.items():
        if key == source_video_key:
            new_features[target_video_key] = value
        elif _is_image_feature(key):
            continue
        else:
            new_features[key] = value

    info["features"] = new_features

    with info_path.open("w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)
        f.write("\n")


def _rewrite_stats_json(
    dst_dir: Path,
    source_video_key: str,
    target_video_key: str,
) -> None:
    stats_path = dst_dir / "meta" / "stats.json"
    with stats_path.open("r", encoding="utf-8") as f:
        stats = json.load(f)

    if source_video_key not in stats:
        raise KeyError(f"{source_video_key} was not found in {stats_path}")

    new_stats = {}
    for key, value in stats.items():
        if key == source_video_key:
            new_stats[target_video_key] = value
        elif _is_image_feature(key):
            continue
        else:
            new_stats[key] = value

    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(new_stats, f, indent=4)
        f.write("\n")


def _rewrite_episode_metadata(
    dst_dir: Path,
    source_video_key: str,
    target_video_key: str,
) -> None:
    episodes_dir = dst_dir / "meta" / "episodes"
    for parquet_path in episodes_dir.rglob("*.parquet"):
        df = pd.read_parquet(parquet_path)

        rename_columns = {}
        drop_columns = []
        for column in df.columns:
            if source_video_key in column:
                rename_columns[column] = column.replace(source_video_key, target_video_key)
            elif _is_image_feature(column):
                drop_columns.append(column)

        df = df.drop(columns=drop_columns).rename(columns=rename_columns)
        df.to_parquet(parquet_path, index=False)


def _copy_headcam_videos(
    src_dir: Path,
    dst_dir: Path,
    source_video_key: str,
    target_video_key: str,
) -> None:
    src_videos = src_dir / "videos" / source_video_key
    dst_videos = dst_dir / "videos" / target_video_key

    if not src_videos.exists():
        raise FileNotFoundError(f"Source video folder does not exist: {src_videos}")

    shutil.copytree(src_videos, dst_videos)


def _write_readme(dst_dir: Path, source_video_key: str, target_video_key: str) -> None:
    readme_path = dst_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "---",
                "license: apache-2.0",
                "task_categories:",
                "- robotics",
                "tags:",
                "- LeRobot",
                "- headcam-only",
                "configs:",
                "- config_name: default",
                "  data_files: data/*/*.parquet",
                "---",
                "",
                "# G1 Dex3 PickApple HeadcamOnly",
                "",
                "This dataset is derived from the original G1 Dex3 PickApple dataset.",
                f"The only image feature is `{target_video_key}`, copied from `{source_video_key}`.",
                "State, action, task, episode, and frame metadata are preserved.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def create_headcam_only_dataset(
    src_dir: Path,
    dst_dir: Path,
    source_video_key: str = DEFAULT_SOURCE_VIDEO_KEY,
    target_video_key: str = DEFAULT_TARGET_VIDEO_KEY,
    overwrite: bool = False,
) -> None:
    src_dir = src_dir.resolve()
    dst_dir = dst_dir.resolve()

    if not src_dir.exists():
        raise FileNotFoundError(f"Source dataset does not exist: {src_dir}")
    if src_dir == dst_dir:
        raise ValueError("Source and destination directories must be different.")

    _copy_base_tree(src_dir, dst_dir, overwrite=overwrite)
    _rewrite_info_json(dst_dir, source_video_key, target_video_key)
    _rewrite_stats_json(dst_dir, source_video_key, target_video_key)
    _rewrite_episode_metadata(dst_dir, source_video_key, target_video_key)
    _copy_headcam_videos(src_dir, dst_dir, source_video_key, target_video_key)
    _write_readme(dst_dir, source_video_key, target_video_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src-dir", type=Path, required=True, help="Source LeRobot dataset directory.")
    parser.add_argument("--dst-dir", type=Path, required=True, help="Destination dataset directory.")
    parser.add_argument("--source-video-key", default=DEFAULT_SOURCE_VIDEO_KEY)
    parser.add_argument("--target-video-key", default=DEFAULT_TARGET_VIDEO_KEY)
    parser.add_argument("--overwrite", action="store_true", help="Replace destination if it is not empty.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    create_headcam_only_dataset(
        src_dir=args.src_dir,
        dst_dir=args.dst_dir,
        source_video_key=args.source_video_key,
        target_video_key=args.target_video_key,
        overwrite=args.overwrite,
    )
    print(f"Created headcam-only dataset at: {args.dst_dir}")


if __name__ == "__main__":
    main()
