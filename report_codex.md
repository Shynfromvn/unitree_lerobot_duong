# Codex report: HeadcamOnly training workflow

Date: 2026-05-27

## Summary

I updated the project so the new G1 Dex3 headcam-only dataset can be used through the repository's existing README workflow, without requiring a separate train script or a separate validator script.

The main design decision was:

```text
Use README.md as the single source of truth for load -> convert -> train -> eval -> replay.
```

This avoids having multiple ways to run the same pipeline. It also makes the instructions suitable for publishing to GitHub because the commands no longer contain machine-specific absolute paths such as a local drive path.

## Dataset contract used by the workflow

The workflow is built around this dataset identity:

```text
dataset repo id: G1_Dex3_PickApple_Dataset_HeadcamOnly
robot type:      Unitree_G1_Dex3_HeadcamOnly
camera key:      observation.images.head_cam
state shape:     [28]
action shape:    [28]
fps:             30
```

The dataset root is intentionally not hard-coded. In README, it is derived from the current repo location:

```powershell
$PROJECT_ROOT = (Get-Location).Path
$DATASET_ROOT = (Resolve-Path (Join-Path $PROJECT_ROOT "..\datasets")).Path
$DATASET_REPO_ID = "G1_Dex3_PickApple_Dataset_HeadcamOnly"
$ROBOT_TYPE = "Unitree_G1_Dex3_HeadcamOnly"
```

If someone clones the repo elsewhere, they only need to place `datasets/` next to the repo or override `$DATASET_ROOT`.

## Execution pipeline

Run this pipeline from a fresh shell. It follows the repository README flow and uses the existing LeRobot scripts directly.

### 1. Create and activate environment

```powershell
conda create -n unitree_lerobot -c conda-forge python=3.10 pinocchio ffmpeg -y
conda activate unitree_lerobot
```

This solves `python`, `pinocchio`, and `ffmpeg` together from `conda-forge`, which avoids dependency conflicts seen when installing them in separate steps.

### 2. Install project packages

Run from the repository root:

```powershell
$PROJECT_ROOT = (Get-Location).Path

cd (Join-Path $PROJECT_ROOT "unitree_lerobot\lerobot")
pip install -e .

cd $PROJECT_ROOT
pip install -e .
```

### 3. Define dataset variables once

Default layout:

```text
parent-folder/
  datasets/
    G1_Dex3_PickApple_Dataset_HeadcamOnly/
  unitree_lerobot/
```

PowerShell variables:

```powershell
$PROJECT_ROOT = (Get-Location).Path
$DATASET_ROOT = Join-Path (Split-Path $PROJECT_ROOT -Parent) "datasets"
$DATASET_REPO_ID = "G1_Dex3_PickApple_Dataset_HeadcamOnly"
$SOURCE_DATASET_REPO_ID = "unitreerobotics/G1_Dex3_PickApple_Dataset"
$SOURCE_DATASET_NAME = "G1_Dex3_PickApple_Dataset"
$ROBOT_TYPE = "Unitree_G1_Dex3_HeadcamOnly"

New-Item -ItemType Directory -Force $DATASET_ROOT | Out-Null
```

If your dataset is not next to the repo, override only this:

```powershell
$DATASET_ROOT = "<path-to-folder-containing-G1_Dex3_PickApple_Dataset_HeadcamOnly>"
```

### 4. Download source dataset on a new machine

Use this when the GitHub repo does not include `datasets/`.

`$SOURCE_DATASET_REPO_ID` points to the Hugging Face dataset repo that contains the original multi-camera G1 Dex3 PickApple dataset. Keep `$SOURCE_DATASET_NAME` as the local folder name.

```powershell
$SOURCE_DATASET_DIR = Join-Path $DATASET_ROOT $SOURCE_DATASET_NAME

# Run this first if the source dataset is private:
# huggingface-cli login

python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id=r'$SOURCE_DATASET_REPO_ID', repo_type='dataset', local_dir=r'$SOURCE_DATASET_DIR')"
```

Expected source dataset layout after download:

```text
datasets/
  G1_Dex3_PickApple_Dataset/
    data/
    meta/
    videos/
```

The source dataset must contain this camera feature:

```text
observation.images.cam_left_high
```

That source camera is copied into the training camera:

```text
observation.images.cam_left_high -> observation.images.head_cam
```

### 5. Convert source dataset to HeadcamOnly

This step creates the dataset used by training:

```powershell
$SOURCE_DATASET_DIR = Join-Path $DATASET_ROOT $SOURCE_DATASET_NAME
$TARGET_DATASET_DIR = Join-Path $DATASET_ROOT $DATASET_REPO_ID

python unitree_lerobot/utils/create_headcam_only_dataset.py `
    --src-dir "$SOURCE_DATASET_DIR" `
    --dst-dir "$TARGET_DATASET_DIR" `
    --source-video-key observation.images.cam_left_high `
    --target-video-key observation.images.head_cam `
    --overwrite
```

Important:

- `--overwrite` replaces an existing generated HeadcamOnly dataset.
- Do not point `--src-dir` and `--dst-dir` to the same folder.
- `unitree_lerobot/utils/create_headcam_only_dataset.py` must be committed to GitHub with the repo, otherwise a fresh clone cannot run this conversion.
- `$SOURCE_DATASET_REPO_ID` is set to `unitreerobotics/G1_Dex3_PickApple_Dataset`, the original multi-camera dataset on Hugging Face.

### 6. Check converted dataset metadata

```powershell
python -c "from pathlib import Path; import json; root=Path(r'$DATASET_ROOT') / '$DATASET_REPO_ID'; info=json.loads((root/'meta/info.json').read_text()); print(info['codebase_version']); print(info['robot_type']); print([k for k in info['features'] if k.startswith('observation.images.')]); print(info['features']['observation.state']['shape'], info['features']['action']['shape'])"
```

Expected:

```text
v3.0
Unitree_G1_Dex3_HeadcamOnly
['observation.images.head_cam']
[28] [28]
```

### 7. Optional: visualize one episode

```powershell
cd (Join-Path $PROJECT_ROOT "unitree_lerobot\lerobot")

python src/lerobot/scripts/lerobot_dataset_viz.py `
    --repo-id "$DATASET_REPO_ID" `
    --root "$DATASET_ROOT" `
    --episode-index 0
```

### 8. Smoke test training

Run one step before long training:

```powershell
python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_ROOT" `
    --policy.push_to_hub=false `
    --policy.type=act `
    --steps=1 `
    --batch_size=1 `
    --num_workers=0 `
    --eval_freq=0 `
    --save_checkpoint=false
```

### 9. Start training

```powershell
python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_ROOT" `
    --policy.push_to_hub=false `
    --policy.type=act `
    --eval_freq=0
```

### 10. Evaluate trained policy on dataset

Replace `<run>` and `<step>` with your output checkpoint path.

```powershell
cd $PROJECT_ROOT

python unitree_lerobot/eval_robot/eval_g1_dataset.py `
    --policy.path="unitree_lerobot/lerobot/outputs/train/<run>/checkpoints/<step>/pretrained_model" `
    --repo_id=$DATASET_REPO_ID `
    --root="$DATASET_ROOT" `
    --episodes=0 `
    --frequency=30 `
    --arm="G1_29" `
    --ee="dex3" `
    --visualization=true `
    --send_real_robot=false
```

### 11. Optional: replay dataset

```powershell
python unitree_lerobot/eval_robot/replay_robot.py `
    --repo_id=$DATASET_REPO_ID `
    --root="$DATASET_ROOT" `
    --episodes=0 `
    --frequency=30 `
    --arm="G1_29" `
    --ee="dex3" `
    --visualization=true
```

### 12. If converting new raw JSON later

Only use this when you have raw Unitree JSON data, not for the existing LeRobot dataset.

```powershell
$RAW_DATA_ROOT = "<path-to-raw-json-dataset>"

python unitree_lerobot/utils/convert_unitree_json_to_lerobot.py `
    --raw-dir "$RAW_DATA_ROOT" `
    --repo-id "$DATASET_REPO_ID" `
    --robot_type "$ROBOT_TYPE"
```

## Files changed

### 1. `README.md`

Purpose:

- Make the headcam-only dataset usable from the official repo workflow.
- Keep one shared set of variables for all stages.
- Remove hard-coded local paths so the README is GitHub-safe.
- Avoid introducing a second train entrypoint.

Sections changed:

```text
2.1 Load Datasets
2.4.2 Conversion
3 Training
4 Real-World Testing
5 Replay Datasets On Robot
```

#### Section 2.1: Load Datasets

What was added:

- A shared portable variable block:

```powershell
$PROJECT_ROOT = (Get-Location).Path
$DATASET_ROOT = (Resolve-Path (Join-Path $PROJECT_ROOT "..\datasets")).Path
$DATASET_REPO_ID = "G1_Dex3_PickApple_Dataset_HeadcamOnly"
$ROBOT_TYPE = "Unitree_G1_Dex3_HeadcamOnly"
```

- A Python snippet that loads the local dataset through `LeRobotDataset`.
- Expected metadata for quick validation.
- A local visualization command using the same variables.

Why:

- The original README only showed the public Hugging Face dataset.
- Your new dataset is local, so users need both `repo_id` and `root`.
- Using shared variables prevents later commands from drifting.

#### Section 2.4.2: Conversion

What was added:

```powershell
$RAW_DATA_ROOT = "<path-to-raw-json-dataset>"

python unitree_lerobot/utils/convert_unitree_json_to_lerobot.py `
    --raw-dir "$RAW_DATA_ROOT" `
    --repo-id "$DATASET_REPO_ID" `
    --robot_type "$ROBOT_TYPE"
```

Why:

- `constants.py` now contains `Unitree_G1_Dex3_HeadcamOnly`.
- New raw JSON conversions should use the same robot type and produce `observation.images.head_cam`.
- The raw data path is a placeholder instead of a local machine path.

#### Section 3: Training

What was added:

```powershell
cd (Join-Path $PROJECT_ROOT "unitree_lerobot\lerobot")

python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_ROOT" `
    --policy.push_to_hub=false `
    --policy.type=act `
    --eval_freq=0
```

Also added a one-step smoke test:

```powershell
python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_ROOT" `
    --policy.push_to_hub=false `
    --policy.type=act `
    --steps=1 `
    --batch_size=1 `
    --num_workers=0 `
    --eval_freq=0 `
    --save_checkpoint=false
```

Why:

- This keeps training on the original LeRobot train script.
- No extra wrapper script is needed.
- `--dataset.root` makes the local dataset explicit.
- `--eval_freq=0` avoids creating an eval environment for offline dataset training.

#### Section 4: Real-World Testing

What was added:

```powershell
python unitree_lerobot/eval_robot/eval_g1_dataset.py `
    --policy.path="unitree_lerobot/lerobot/outputs/train/<run>/checkpoints/<step>/pretrained_model" `
    --repo_id=$DATASET_REPO_ID `
    --root="$DATASET_ROOT" `
    --episodes=0 `
    --frequency=30 `
    --arm="G1_29" `
    --ee="dex3" `
    --visualization=true `
    --send_real_robot=false
```

Why:

- Evaluation should point to the same dataset identity used during training.
- Keeping `--repo_id` and `--root` aligned prevents accidental evaluation against the old Hugging Face dataset.

#### Section 5: Replay Datasets On Robot

What was added:

```powershell
python unitree_lerobot/eval_robot/replay_robot.py `
    --repo_id=$DATASET_REPO_ID `
    --root="$DATASET_ROOT" `
    --episodes=0 `
    --frequency=30 `
    --arm="G1_29" `
    --ee="dex3" `
    --visualization=true
```

Why:

- Replay now uses the same dataset variables as load/train/eval.

### 2. `unitree_lerobot/utils/constants.py`

Status:

- This file had already been edited before this report update.
- I did not rewrite it in this pass.
- I verified the new robot type can be imported and matches the headcam-only dataset.

Relevant config:

```python
"Unitree_G1_Dex3_HeadcamOnly": G1_DEX3_HEADCAM_ONLY_CONFIG
```

Expected behavior:

```text
cameras = ['head_cam']
camera_to_image_key = {'color_0': 'head_cam'}
motor count = 28
```

Why this matters:

- Conversion from raw JSON uses `ROBOT_CONFIGS[robot_type]`.
- Training from an already-converted LeRobot dataset mainly depends on dataset metadata, but future conversions need this robot type to generate the same camera key.

### 3. `report_codex.md`

Purpose:

- Explain what changed and why.
- Record the final workflow decision.
- Record verification results and current environment blockers.

## Files intentionally not kept

These files were created in an earlier approach and then removed:

```text
train_headcamonly_act.ps1
unitree_lerobot/utils/validate_headcamonly_dataset.py
```

Reason:

- They created a second workflow outside the README.
- The user explicitly wanted to follow the repo README and minimize extra files.
- The final approach uses existing repo scripts directly.

## File not modified

```text
unitree_lerobot/utils/create_headcam_only_dataset.py
```

Status:

- I did not modify or delete it.
- It is required for the fresh-clone workflow that regenerates the HeadcamOnly dataset from the original multi-camera dataset.
- It is tracked by git in the current repository state.

## Verification performed

### Dataset metadata check

Checked with Python stdlib, without depending on LeRobot training dependencies.

Result:

```text
robot_type: Unitree_G1_Dex3_HeadcamOnly
image keys: ['observation.images.head_cam']
state/action shape: [28] [28]
```

### Robot config check

Checked:

```powershell
python -c "from unitree_lerobot.utils.constants import ROBOT_CONFIGS; c=ROBOT_CONFIGS['Unitree_G1_Dex3_HeadcamOnly']; print(c.cameras); print(c.camera_to_image_key); print(len(c.motors))"
```

Result:

```text
['head_cam']
{'color_0': 'head_cam'}
28
```

### README hard-code check

Checked for local machine paths in README.

Result:

```text
No hard-coded local drive path remains in README.
```

The README still contains placeholders such as:

```text
<path-to-raw-json-dataset>
```

That is intentional.

## Current environment blocker

The code path is prepared, but the current Python environment is missing LeRobot training dependencies.

Observed missing packages:

```text
torchvision
accelerate
draccus
safetensors
einops
diffusers
```

Earlier smoke test stopped at:

```text
ModuleNotFoundError: No module named 'accelerate'
```

After installing dependencies, the recommended first run is still the README smoke test:

```powershell
python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_ROOT" `
    --policy.push_to_hub=false `
    --policy.type=act `
    --steps=1 `
    --batch_size=1 `
    --num_workers=0 `
    --eval_freq=0 `
    --save_checkpoint=false
```

## Current git status context

Expected relevant status after this work:

```text
M .gitignore
M README.md
M report_codex.md
```

Notes:

- `.gitignore`: modified in the current working tree outside the README/report changes; keep it if you want datasets, videos, and training outputs excluded from GitHub.
- `README.md`: updated by Codex to document the portable workflow.
- `report_codex.md`: updated by Codex.
- `unitree_lerobot/utils/create_headcam_only_dataset.py`: tracked utility required by the fresh-clone data regeneration flow.
