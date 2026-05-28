# Codex Change Report

Date: 2026-05-28

Scope:

- Align this fork with the practical Linux/zsh workflow used on the Ubuntu training machine.
- Keep the original Unitree/LeRobot training entrypoint.
- Document code changes separately from run commands.

References checked:

- Upstream repo: https://github.com/unitreerobotics/unitree_lerobot
- Project repo remote: https://github.com/Shynfromvn/unitree_lerobot_duong.git
- PyTorch install selector: https://pytorch.org/get-started/locally/
- TorchCodec README: https://github.com/pytorch/torchcodec

## Difference From Upstream

This fork keeps the upstream Unitree/LeRobot architecture, but adds a project-specific HeadcamOnly workflow and fixes local evaluation paths for that workflow.

### Kept From Upstream

- The original LeRobot training entrypoint remains:

```text
lerobot/src/lerobot/scripts/lerobot_train.py
```

- The original Unitree eval entrypoints remain:

```text
unitree_lerobot/eval_robot/eval_g1.py
unitree_lerobot/eval_robot/eval_g1_sim.py
unitree_lerobot/eval_robot/eval_g1_dataset.py
unitree_lerobot/eval_robot/replay_robot.py
```

- The G1 URDF/MJCF assets are still used as robot description assets:

```text
unitree_lerobot/eval_robot/assets/g1/
```

- Simulation eval is still designed around Unitree simulator communication through DDS and image server, as in upstream documentation for `unitree_sim_isaaclab`.

### Added or Changed in This Fork

| Area | Upstream behavior | This fork behavior | Reason |
| --- | --- | --- | --- |
| Dataset workflow | Uses Unitree public dataset ids directly in examples. | Adds local `G1_Dex3_PickApple_Dataset_HeadcamOnly` workflow. | Train on one head camera stream matching the project dataset. |
| Camera key | Public examples commonly use original camera keys. | Standardizes policy input to `observation.images.head_cam`. | Keeps training, eval, and generated metadata aligned. |
| Dataset generation | No dedicated HeadcamOnly copy workflow in upstream README. | Documents and keeps `create_headcam_only_dataset.py`. | Reproducibly generate the local dataset from the source Hugging Face dataset. |
| README commands | Upstream has generic bash examples and this fork previously mixed PowerShell/Linux. | README is now Linux/zsh-first. | The active training machine is Ubuntu/Linux and previous PowerShell blocks failed in zsh. |
| `eval_g1_dataset.py` | Accepted `--root` in config but loaded dataset by `repo_id` only. | Loads `LeRobotDataset(repo_id=cfg.repo_id, root=cfg.root)`. | Required for local-only datasets. |
| `eval_g1_sim.py` image API | Had older image shared-memory expectations. | Uses current `setup_image_client()` return shape `(image_client, image_config)`. | Matches current `make_robot.py`. |
| `eval_g1_sim.py` dataset loading | Loaded dataset by `repo_id` only. | Loads dataset with `root=cfg.root`. | Required for local HeadcamOnly metadata and initial pose. |
| Sim image host | Not exposed in `EvalRealConfig`. | Adds `image_host` config field. | Allows `--image_host=127.0.0.1` or remote sim host. |
| Eval helper | No wrapper script for post-training sim eval. | Adds `scripts/eval_g1_sim_after_train.sh`. | Auto-resolves paths/checkpoint and runs the correct eval command. |
| Sim video review | No local helper to turn saved sim frames into an MP4. | Adds `scripts/eval_g1_sim_record_video.sh` and `scripts/episode_frames_to_video.py`. | Lets the policy be reviewed visually before trying the real robot. |
| MuJoCo handling | Asset README says MJCF can be opened in MuJoCo viewer. | Adds `scripts/view_g1_mujoco_asset.sh` and clarifies it is only visualization. | Prevents confusing MJCF viewer with DDS sim eval. |
| Blackwell GPU setup | Not project-specific. | Documents `torch==2.7.1+cu128` for `sm_120`. | Fixes RTX PRO 6000 Blackwell CUDA kernel support. |
| TorchCodec setup | Upstream generic dependency flow. | Documents `torchcodec==0.5+cu128`, FFmpeg 7, NPP/NVRTC libs. | Fixes video decode on the Ubuntu training machine. |

### Current Fork-Specific Files

These are project-specific and should be maintained when rebasing from upstream:

```text
README.md
report_codex.md
scripts/eval_g1_sim_after_train.sh
scripts/eval_g1_sim_record_video.sh
scripts/episode_frames_to_video.py
scripts/view_g1_mujoco_asset.sh
unitree_lerobot/utils/create_headcam_only_dataset.py
```

These source-code changes are also fork-specific unless upstream later makes equivalent fixes:

```text
unitree_lerobot/eval_robot/eval_g1_dataset.py
unitree_lerobot/eval_robot/eval_g1_sim.py
unitree_lerobot/eval_robot/utils/sim_savedata_utils.py
unitree_lerobot/utils/constants.py
```

## Final Workflow Contract

Dataset:

```text
source dataset:    unitreerobotics/G1_Dex3_PickApple_Dataset
local dataset id:  G1_Dex3_PickApple_Dataset_HeadcamOnly
robot type:        Unitree_G1_Dex3_HeadcamOnly
camera key:        observation.images.head_cam
source camera:     observation.images.cam_left_high
state shape:       [28]
action shape:      [28]
fps:               30
LeRobot format:    v3.0
```

Training entrypoint:

```text
lerobot/src/lerobot/scripts/lerobot_train.py
```

Main Ubuntu path layout:

```text
~/work/unitree_lerobot_duong/
  unitree_lerobot/
  unitree_sdk2_python/
  datasets/
```

## Files Changed

### 1. README.md

Change:

- Replaced the mixed upstream/PowerShell-heavy README with a Linux-first project README.
- Kept links to upstream Unitree, this fork, Unitree SDK, PyTorch, and TorchCodec.
- Removed PowerShell commands from the primary workflow because they caused actual zsh errors:

```text
zsh: no matches found: (Get-Location).Path
zsh: command not found: Join-Path
bquote>
```

New README structure:

```text
1. Expected Folder Layout
2. Create Environment
3. CUDA Setup
4. TorchCodec and FFmpeg
5. Unitree SDK for Simulation or Real Robot
6. Define Dataset Paths
7. Download and Generate HeadcamOnly Dataset
8. Verify Dataset Metadata
9. Train Test on 5 Episodes
10. Full Training
11. Checkpoint Location
12. Evaluate Checkpoint on Dataset
13. Run Checkpoint in Unitree Simulation
14. Replay Dataset on Robot
15. Troubleshooting
```

Reason:

- The target machine is Ubuntu/Linux with zsh/bash, not Windows PowerShell.
- The successful commands require Linux quoting and line continuation:

```bash
--dataset.episodes='[0,1,2,3,4]'
\
```

not:

```powershell
--dataset.episodes=[0,1,2,3,4]
`
```

Important README additions:

- Canonical dataset variables:

```bash
PROJECT_ROOT="$(pwd)"
DATASET_PARENT="$(dirname "$PROJECT_ROOT")/datasets"
DATASET_REPO_ID="G1_Dex3_PickApple_Dataset_HeadcamOnly"
DATASET_DIR="$DATASET_PARENT/$DATASET_REPO_ID"
SOURCE_DATASET_REPO_ID="unitreerobotics/G1_Dex3_PickApple_Dataset"
SOURCE_DATASET_DIR="$DATASET_PARENT/G1_Dex3_PickApple_Dataset"
```

- One-line metadata verification command, avoiding heredoc `PY` because the shell session previously got stuck at `heredoc>` when the terminator was indented.
- Blackwell GPU setup:

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

- TorchCodec runtime notes:

```text
torch 2.7.1+cu128
torchcodec 0.5+cu128
ffmpeg 7.x
libavutil.so.59
libnppicc.so.12
```

- Full training command now omits `--dataset.episodes`.
- Full training command also omits `--steps` by default, because repo config already defines `steps=100000`.
- A higher-throughput optional command uses:

```bash
--batch_size=64
--num_workers=4
```

Reason for batch guidance:

- The Ubuntu GPU had about 98 GB VRAM.
- Current ACT training with small batch used only about 3 GB.
- `batch_size=64` is a reasonable first step; `96` can be tried if stable, `48` or `32` if out of memory.

### 2. unitree_lerobot/eval_robot/eval_g1_dataset.py

Change:

```python
dataset = LeRobotDataset(repo_id=cfg.repo_id, root=cfg.root)
```

Previous behavior:

```python
dataset = LeRobotDataset(repo_id=cfg.repo_id)
```

Reason:

- The script accepted `--root`, but did not use it.
- The project dataset id is local-only:

```text
G1_Dex3_PickApple_Dataset_HeadcamOnly
```

- Without `root=cfg.root`, LeRobot could look in the cache or Hugging Face instead of the generated local dataset.

Effect:

- Dataset evaluation now uses the same dataset root as training:

```bash
--repo_id="$DATASET_REPO_ID"
--root="$DATASET_DIR"
```

### 3. unitree_lerobot/eval_robot/eval_g1_sim.py

Change 1: Use current image client API.

```python
image_client, camera_config = image_info
observation, current_arm_q = process_images_and_observations(image_client, camera_config, arm_ctrl)
```

Previous code expected old shared-memory fields:

```text
tv_img_array
wrist_img_array
tv_img_shape
wrist_img_shape
is_binocular
has_wrist_cam
```

Reason:

- `make_robot.setup_image_client(cfg)` currently returns:

```text
(image_client, image_config)
```

- `eval_g1_sim.py` was still written for the older return shape.

Change 2: Close the current image client correctly.

```python
image_client, _ = image_info
image_client.close()
```

Reason:

- The old cleanup helper expected shared-memory resources and was no longer correct for the current image client object.

Change 2b: Close `EpisodeWriter` when recording sim data.

```python
if "episode_writer" in locals() and episode_writer:
    episode_writer.close()
```

Reason:

- When `--save_data=true`, `EpisodeWriter` saves camera frames and `data.json` in a background worker.
- Closing it in `finally` flushes queued frames and writes the episode metadata before the process exits.
- This is required for reliable post-run video conversion, especially when stopping eval manually after observing enough behavior.

Change 3: Use the local dataset root.

```python
dataset = LeRobotDataset(repo_id=cfg.repo_id, root=cfg.root)
```

Reason:

- Simulation needs the dataset metadata and initial state from the same local HeadcamOnly dataset as training.

### 4. unitree_lerobot/eval_robot/utils/sim_savedata_utils.py

Change:

```python
image_host: str = "192.168.123.164"
```

Reason:

- `make_robot.setup_image_client(args)` reads:

```python
args.image_host
```

- The config class did not expose this field, so the simulation command could not cleanly pass the image server host.

Effect:

- Simulation can now run with:

```bash
--image_host="127.0.0.1"
```

or another host IP if the image server runs on a different machine.

### 5. scripts/eval_g1_sim_after_train.sh

Change:

- Added a Linux helper script for running `eval_g1_sim.py` after training completes.

What it does:

- Derives `PROJECT_ROOT` from the script location.
- Uses the standard project dataset variables:

```bash
DATASET_REPO_ID=G1_Dex3_PickApple_Dataset_HeadcamOnly
DATASET_DIR=<parent>/datasets/G1_Dex3_PickApple_Dataset_HeadcamOnly
```

- Uses `POLICY_PATH` if provided.
- If `POLICY_PATH` is not provided, finds the newest local checkpoint matching:

```text
lerobot/outputs/train/*/*_act/checkpoints/*/pretrained_model
```

- Checks that:

```text
$POLICY_PATH
$DATASET_DIR/meta/info.json
```

exist before starting eval.

- Sets `LD_LIBRARY_PATH` from `CONDA_PREFIX` and Python `nvidia/*/lib` folders when available.
- Runs `unitree_lerobot/eval_robot/eval_g1_sim.py` with:

```bash
--image_host="$IMAGE_HOST"
--rename_map='{"observation.images.cam_left_high":"observation.images.head_cam"}'
```

Reason:

- The trained checkpoint can be produced on a separate SSH machine.
- The eval machine needs one stable command that checks paths and runs the correct simulation eval command.
- It also documents that `eval_g1_sim.py` requires an already-running external simulator and image server.

Important clarification:

- This script does not start MuJoCo or IsaacLab.
- It starts only the policy eval client.
- The simulator must already publish the Unitree DDS topics and camera image stream.

### 6. scripts/view_g1_mujoco_asset.sh

Change:

- Added a small MuJoCo asset viewer script for:

```text
unitree_lerobot/eval_robot/assets/g1/g1_body29_hand14.xml
```

Reason:

- The repo includes G1 MJCF/URDF assets.
- The asset README says the MJCF can be opened in MuJoCo viewer.
- This helps inspect the robot model, but it is not the same as running `eval_g1_sim.py`.

Important clarification:

- MuJoCo viewer is model visualization only in this repo.
- `eval_g1_sim.py` is wired to Unitree DDS/image-server simulation interfaces, not a local MuJoCo step loop.

### 7. scripts/eval_g1_sim_record_video.sh

Change:

- Added a Linux helper script for recording one simulation eval run and converting the saved frames to MP4.

What it does:

- Runs `scripts/eval_g1_sim_after_train.sh` with:

```bash
SAVE_DATA=true
TASK_DIR="$PROJECT_ROOT/data/sim_eval_recordings"
MAX_EPISODES=900
FREQUENCY=30
```

- Converts the latest saved episode to MP4 through `scripts/episode_frames_to_video.py`.
- Keeps trying conversion even if the eval process exits non-zero, so flushed frames can still become a video after a manual stop or sim-side interruption.

Reason:

- The user needs to inspect policy behavior in simulation as a video before deploying to the real robot.
- Upstream `eval_g1_sim.py` saves episode images/data but does not provide a one-command MP4 review workflow.

Output:

```text
data/sim_eval_recordings/episode_XXXX/episode_XXXX_color_0.mp4
```

### 8. scripts/episode_frames_to_video.py

Change:

- Added a small OpenCV utility that converts `EpisodeWriter` JPEG frames to MP4.

Input:

```text
<task_dir>/episode_XXXX/colors/*_color_0.jpg
```

Default output:

```text
<task_dir>/episode_XXXX/episode_XXXX_color_0.mp4
```

Reason:

- `EpisodeWriter` saves image frames, not an MP4.
- The MP4 is the convenient review artifact for comparing model behavior before real-robot testing.

### 9. unitree_lerobot/utils/create_headcam_only_dataset.py

Status:

- Kept as a required project utility.

Role:

- Copies the original multi-camera LeRobot dataset.
- Keeps only:

```text
observation.images.head_cam
```

- Maps:

```text
observation.images.cam_left_high -> observation.images.head_cam
```

Reason:

- Dataset files are not committed.
- A new Linux machine must be able to regenerate the local training dataset from the source Hugging Face dataset.

### 10. unitree_lerobot/utils/constants.py

Status:

- Kept with project-specific robot config support.

Required logical config:

```text
Unitree_G1_Dex3_HeadcamOnly
cameras = ['head_cam']
state/action dim = 28
```

Reason:

- Future raw Unitree JSON conversions must produce the same camera key used by the training dataset.

### 11. .gitignore

Purpose:

- Keep generated artifacts out of git.

Relevant ignored outputs:

```text
datasets/
outputs/
checkpoints/
videos/
__pycache__/
*.mp4
*.h5
*.parquet
*.pt
*.pth
*.exe
```

Reason:

- Datasets, checkpoints, videos, and local installers are large or machine-specific.
- They should be regenerated or downloaded using README commands.

## Run Commands Now Documented in README

The README now contains the canonical Linux commands for:

- Environment creation.
- Blackwell CUDA setup.
- TorchCodec and FFmpeg setup.
- Unitree SDK installation.
- Dataset variable setup.
- Dataset download and HeadcamOnly conversion.
- Metadata verification.
- 5-episode train test.
- Full train without explicit `--steps`.
- Full train with optional higher batch size.
- Dataset evaluation.
- Simulation evaluation with `--image_host` and `--rename_map`.
- Simulation recording to MP4 with `scripts/eval_g1_sim_record_video.sh`.
- Dataset replay.

## Important Lessons Captured

### Do not paste PowerShell into zsh

PowerShell syntax that failed on Ubuntu:

```powershell
$PROJECT_ROOT = (Get-Location).Path
Join-Path
New-Item
`
```

Linux replacement:

```bash
PROJECT_ROOT="$(pwd)"
DATASET_DIR="$DATASET_PARENT/$DATASET_REPO_ID"
mkdir -p "$DATASET_PARENT"
\
```

### Quote episodes in zsh

Use:

```bash
--dataset.episodes='[0,1,2,3,4]'
```

Reason:

- zsh treats square brackets as glob syntax if not quoted.

### Full training uses all episodes by omission

Do not pass:

```bash
--dataset.episodes='[0,1,2,3,4]'
```

for full training.

### Explicit steps are optional

The repo config defines:

```text
steps = 100000
```

So full training can omit `--steps`.

### Blackwell requires CUDA 12.8 PyTorch

Working CUDA check:

```text
torch 2.7.1+cu128
cuda 12.8
capability (12, 0)
cuda ok
```

This fixes:

```text
sm_120 is not compatible
no kernel image is available for execution on the device
```

### TorchCodec requires compatible FFmpeg and CUDA runtime libs

Avoid:

```bash
conda install "ffmpeg<8"
```

because it may install:

```text
ffmpeg 2.8.6
```

Use:

```bash
conda install -y --override-channels -c conda-forge "ffmpeg>=7,<8"
```

Expected:

```text
libavutil.so.59
libnppicc.so.12
```

## Current Recommended Commit Scope

After this documentation pass:

```bash
git add README.md report_codex.md \
  unitree_lerobot/eval_robot/eval_g1_sim.py \
  scripts/eval_g1_sim_after_train.sh \
  scripts/eval_g1_sim_record_video.sh \
  scripts/episode_frames_to_video.py \
  scripts/view_g1_mujoco_asset.sh
git commit -m "Add Linux G1 Dex3 sim eval recording workflow"
```

If code changes from earlier are not already committed, include:

```bash
git add unitree_lerobot/eval_robot/eval_g1_dataset.py
git add unitree_lerobot/eval_robot/eval_g1_sim.py
git add unitree_lerobot/eval_robot/utils/sim_savedata_utils.py
```

Do not commit:

```text
../unitree_sdk2_python/
datasets/
outputs/
checkpoints/
videos/
```
