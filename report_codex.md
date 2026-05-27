# Codex report: G1 Dex3 HeadcamOnly workflow

Date: 2026-05-27

This report records the practical changes made for training with the generated dataset:

```text
G1_Dex3_PickApple_Dataset_HeadcamOnly
```

The goal is to keep the repository GitHub-friendly: no local absolute drive paths, no extra train wrapper, and one consistent workflow that a teammate can copy from `README.md` after cloning.

## Final dataset contract

The training/eval workflow uses this LeRobot dataset contract:

```text
source dataset:       unitreerobotics/G1_Dex3_PickApple_Dataset
local dataset id:     G1_Dex3_PickApple_Dataset_HeadcamOnly
robot type:           Unitree_G1_Dex3_HeadcamOnly
camera key:           observation.images.head_cam
source camera key:    observation.images.cam_left_high
state shape:          [28]
action shape:         [28]
fps:                  30
LeRobot format:       v3.0
```

Important naming decision:

```text
observation.images.head_cam
```

This is the camera key agreed by the team. All load, train, eval, and replay commands must stay aligned with this key through the generated dataset metadata.

## Canonical path variables

The README now avoids hard-coded local paths. It derives the dataset path from the repo location:

```powershell
$PROJECT_ROOT = (Get-Location).Path
$DATASET_PARENT = Join-Path (Split-Path $PROJECT_ROOT -Parent) "datasets"
$DATASET_REPO_ID = "G1_Dex3_PickApple_Dataset_HeadcamOnly"
$DATASET_DIR = Join-Path $DATASET_PARENT $DATASET_REPO_ID
$SOURCE_DATASET_REPO_ID = "unitreerobotics/G1_Dex3_PickApple_Dataset"
$SOURCE_DATASET_NAME = "G1_Dex3_PickApple_Dataset"
$SOURCE_DATASET_DIR = Join-Path $DATASET_PARENT $SOURCE_DATASET_NAME
```

Meaning:

- `$DATASET_PARENT`: folder containing datasets.
- `$DATASET_DIR`: actual LeRobot dataset root passed to `--dataset.root` and `--root`.
- `$SOURCE_DATASET_DIR`: downloaded original multi-camera dataset.

The important bug avoided here:

```text
Wrong: --dataset.root=<parent datasets folder>
Right: --dataset.root=<actual HeadcamOnly dataset folder>
```

If the root points to the parent folder, LeRobot looks for `meta/info.json` in the wrong place, then falls back to Hugging Face and returns 404 for the local-only dataset id.

## Files changed

### 1. `README.md`

Purpose:

- Make the HeadcamOnly workflow executable from a fresh clone.
- Keep the original repo style and original LeRobot entrypoints.
- Avoid machine-specific paths so the repo can be pushed to GitHub.
- Document the exact sequence that worked locally.

Main changes:

- Updated conda setup to the working combined command:

```powershell
conda create -n unitree_lerobot -c conda-forge python=3.10 pinocchio ffmpeg -y
conda activate unitree_lerobot
```

Why:

- Installing `python`, `pinocchio`, and `ffmpeg` together from `conda-forge` avoids the dependency conflicts seen with separate installs.

- Added CUDA verification and a compatible CUDA wheel example:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda)"
pip install --upgrade torch==2.6.0+cu121 torchvision==0.21.0+cu121 torchaudio==2.6.0+cu121 --index-url https://download.pytorch.org/whl/cu121
```

Why:

- The earlier CPU-only setup made training run on CPU.
- `torchvision` must stay compatible with LeRobot (`>=0.21`, `<0.23`), so the README avoids the incompatible `torchvision==0.20.1` combination.

- Added a dedicated copy-run section:

```text
1.3 G1 Dex3 HeadcamOnly Copy-Run Pipeline
```

This section contains:

- shared path variables;
- source dataset download from Hugging Face;
- HeadcamOnly conversion;
- metadata verification;
- 5-episode train-test;
- full-data train command;
- eval command using the saved checkpoint.

Why:

- The team can clone the repo, open README, and run one coherent workflow without reconstructing the steps from chat.

- Replaced older `$DATASET_ROOT` usage with:

```powershell
$DATASET_PARENT
$DATASET_DIR
```

Why:

- `$DATASET_ROOT` was ambiguous and caused an actual train error when it pointed to the parent `datasets/` folder.
- `$DATASET_DIR` is explicit: it is the real LeRobot dataset folder containing `meta/info.json`.

- Added Windows checkpoint note:

```text
WinError 1314
```

Why:

- On Windows VS Code terminals, LeRobot may save the real checkpoint and then fail when creating `checkpoints/last`, because symlink creation needs Developer Mode or admin privileges.
- The real usable model path is still:

```text
outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model
```

Effect:

- Teammates know that Ubuntu/Linux full training should save normally.
- Windows users know how to interpret the symlink error and where the real model is.

### 2. `unitree_lerobot/eval_robot/eval_g1_dataset.py`

Purpose:

- Make dataset evaluation use the local dataset path passed in the command.

Change:

```python
dataset = LeRobotDataset(repo_id=cfg.repo_id, root=cfg.root)
```

Before:

```python
dataset = LeRobotDataset(repo_id=cfg.repo_id)
```

Why:

- The script accepted `--root`, but ignored it.
- With local repo id `G1_Dex3_PickApple_Dataset_HeadcamOnly`, the script tried to load from:

```text
~/.cache/huggingface/lerobot/G1_Dex3_PickApple_Dataset_HeadcamOnly
```

and then from Hugging Face, which failed with 404 because this generated dataset is local.

Effect:

- This command now evaluates against the same local dataset used for training:

```powershell
python unitree_lerobot/eval_robot/eval_g1_dataset.py `
    --policy.path="$POLICY_PATH" `
    --repo_id=$DATASET_REPO_ID `
    --root="$DATASET_DIR" `
    --episodes=0 `
    --frequency=30 `
    --arm="G1_29" `
    --ee="dex3" `
    --visualization=true `
    --send_real_robot=false
```

### 3. `.gitignore`

Purpose:

- Keep generated and local-heavy files out of GitHub.

Current relevant behavior:

```text
__pycache__/
.pytest_cache/
.ruff_cache/
unitree_sdk2_python/
/data/
/datasets/
*.mp4
*.h5
*.parquet
/outputs/
/wandb/
/checkpoints/
*.pt
*.pth
*.exe
figure.png
```

Change made in the latest pass:

```text
*.exe
```

Why:

- Local Windows installers such as Anaconda/Miniforge should not be pushed to GitHub.
- Dataset folders, generated videos, checkpoints, and train outputs are intentionally excluded because they are large and machine-specific.

Effect:

- The GitHub repo stays small and reproducible.
- Teammates regenerate data/checkpoints using README instead of pulling local artifacts from git.

### 4. `report_codex.md`

Purpose:

- Record the modifications, decisions, failure modes, and final commands.
- Serve as a change log between the original repo workflow and the HeadcamOnly workflow.

Change:

- Rewritten into this structured report.
- Removed stale wording that said only docs changed.
- Added the actual eval fix, checkpoint behavior, and fresh-clone pipeline.

## Files checked but not changed in the latest pass

### `unitree_lerobot/utils/create_headcam_only_dataset.py`

Status:

- Kept.
- Required by the fresh-clone workflow.

Role:

- Copies the original LeRobot dataset tree.
- Removes other image streams from metadata.
- Rewrites:

```text
meta/info.json
meta/stats.json
meta/episodes/*.parquet
videos/observation.images.head_cam/
```

Main transformation:

```text
observation.images.cam_left_high -> observation.images.head_cam
```

Why keep it:

- The GitHub repo does not contain dataset files.
- A teammate must be able to download the source Hugging Face dataset and regenerate `G1_Dex3_PickApple_Dataset_HeadcamOnly`.

### `unitree_lerobot/utils/constants.py`

Status:

- Checked as part of the workflow.
- Not changed in the latest pass.

Required config:

```python
"Unitree_G1_Dex3_HeadcamOnly": G1_DEX3_HEADCAM_ONLY_CONFIG
```

Expected behavior:

```text
cameras = ['head_cam']
camera_to_image_key = {'color_0': 'head_cam'}
motor count = 28
```

Why it matters:

- If converting future raw Unitree JSON data, this robot type should generate the same camera naming convention as the current dataset.
- For the already-generated LeRobot dataset, training mainly uses `meta/info.json`, but this config keeps future conversions consistent.

## Files intentionally removed or not kept

These temporary files are not present now:

```text
train_headcamonly_act.ps1
validate_headcamonly_dataset.py
```

Reason:

- They created a second workflow outside README.
- The final approach uses the existing LeRobot scripts directly:

```text
lerobot/src/lerobot/scripts/lerobot_train.py
unitree_lerobot/eval_robot/eval_g1_dataset.py
unitree_lerobot/eval_robot/replay_robot.py
```

Also removed:

```text
__pycache__/
```

Reason:

- Python cache generated by imports/tests.
- It is not source code and should not be committed.

## Verified execution results

### Dataset metadata

The generated dataset was checked and matched the target contract:

```text
codebase_version: v3.0
robot_type: Unitree_G1_Dex3_HeadcamOnly
image keys: ['observation.images.head_cam']
observation.state shape: [28]
action shape: [28]
```

Conclusion:

```text
The generated dataset is already in LeRobot v3.0 format.
```

### One-step smoke test

Command type:

```text
5 episodes, 1 train step, no checkpoint
```

Expected success markers:

```text
Creating dataset
Creating policy
dataset.num_episodes=5
Start offline training on a fixed dataset
End of training
```

Purpose:

- Validate dataset path.
- Validate metadata shape.
- Validate policy construction.
- Avoid checkpoint/symlink issues during the first test.

### 5-episode checkpoint test

Command type:

```text
5 episodes, 200 steps, batch size 4, CUDA, checkpoint at final step
```

Observed success markers:

```text
policy.device='cuda'
dataset.num_episodes=5
step:200
Checkpoint policy after step 200
```

Observed Windows-only issue:

```text
OSError: [WinError 1314] A required privilege is not held by the client
```

Interpretation:

- Training reached step 200.
- The real checkpoint folder was created before LeRobot tried to create `checkpoints/last`.
- The error is caused by Windows symlink permissions, not by the dataset or model.

Recommended handling:

- On Ubuntu/Linux: train normally.
- On Windows: enable Developer Mode for clean symlink creation, or use the real checkpoint path directly.

## Standard commands to keep using

Run from repository root unless the command changes directory.

### 1. Environment

```powershell
conda create -n unitree_lerobot -c conda-forge python=3.10 pinocchio ffmpeg -y
conda activate unitree_lerobot

cd unitree_lerobot/lerobot
pip install -e .

cd ../..
pip install -e .
```

### 2. Shared variables

```powershell
$PROJECT_ROOT = (Get-Location).Path
$DATASET_PARENT = Join-Path (Split-Path $PROJECT_ROOT -Parent) "datasets"
$DATASET_REPO_ID = "G1_Dex3_PickApple_Dataset_HeadcamOnly"
$DATASET_DIR = Join-Path $DATASET_PARENT $DATASET_REPO_ID
$SOURCE_DATASET_REPO_ID = "unitreerobotics/G1_Dex3_PickApple_Dataset"
$SOURCE_DATASET_NAME = "G1_Dex3_PickApple_Dataset"
$SOURCE_DATASET_DIR = Join-Path $DATASET_PARENT $SOURCE_DATASET_NAME

New-Item -ItemType Directory -Force $DATASET_PARENT | Out-Null
```

### 3. Download and convert data

```powershell
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id=r'$SOURCE_DATASET_REPO_ID', repo_type='dataset', local_dir=r'$SOURCE_DATASET_DIR')"

python unitree_lerobot/utils/create_headcam_only_dataset.py `
    --src-dir "$SOURCE_DATASET_DIR" `
    --dst-dir "$DATASET_DIR" `
    --source-video-key observation.images.cam_left_high `
    --target-video-key observation.images.head_cam `
    --overwrite
```

### 4. Verify metadata

```powershell
$INFO_PATH = Join-Path $DATASET_DIR "meta\info.json"
$INFO = Get-Content $INFO_PATH -Raw | ConvertFrom-Json

$INFO.codebase_version
$INFO.robot_type
$INFO.features.PSObject.Properties.Name | Where-Object { $_ -like "observation.images.*" }
$INFO.features."observation.state".shape
$INFO.features.action.shape
```

### 5. Train-test on 5 episodes

```powershell
cd (Join-Path $PROJECT_ROOT "unitree_lerobot\lerobot")

$TRAIN_STEPS = 200

python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_DIR" `
    --dataset.episodes=[0,1,2,3,4] `
    --policy.push_to_hub=false `
    --policy.type=act `
    --policy.device=cuda `
    --steps=$TRAIN_STEPS `
    --batch_size=4 `
    --num_workers=0 `
    --save_freq=$TRAIN_STEPS `
    --eval_freq=0
```

### 6. Full-data train

```powershell
$TRAIN_STEPS = 100000

python src/lerobot/scripts/lerobot_train.py `
    --dataset.repo_id=$DATASET_REPO_ID `
    --dataset.root="$DATASET_DIR" `
    --policy.push_to_hub=false `
    --policy.type=act `
    --policy.device=cuda `
    --steps=$TRAIN_STEPS `
    --save_freq=$TRAIN_STEPS `
    --eval_freq=0
```

Do not include this in full training:

```text
--dataset.episodes=[0,1,2,3,4]
```

### 7. Evaluate checkpoint

```powershell
cd $PROJECT_ROOT

$POLICY_PATH = "unitree_lerobot/lerobot/outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model"

python unitree_lerobot/eval_robot/eval_g1_dataset.py `
    --policy.path="$POLICY_PATH" `
    --repo_id=$DATASET_REPO_ID `
    --root="$DATASET_DIR" `
    --episodes=0 `
    --frequency=30 `
    --arm="G1_29" `
    --ee="dex3" `
    --visualization=true `
    --send_real_robot=false
```

## Ubuntu/Linux copy-run block

Use this on the GPU Ubuntu machine from the repository root. It is the bash equivalent of the PowerShell workflow above.

```bash
PROJECT_ROOT="$(pwd)"
DATASET_PARENT="$(dirname "$PROJECT_ROOT")/datasets"
DATASET_REPO_ID="G1_Dex3_PickApple_Dataset_HeadcamOnly"
DATASET_DIR="$DATASET_PARENT/$DATASET_REPO_ID"
SOURCE_DATASET_REPO_ID="unitreerobotics/G1_Dex3_PickApple_Dataset"
SOURCE_DATASET_NAME="G1_Dex3_PickApple_Dataset"
SOURCE_DATASET_DIR="$DATASET_PARENT/$SOURCE_DATASET_NAME"

mkdir -p "$DATASET_PARENT"

export SOURCE_DATASET_REPO_ID SOURCE_DATASET_DIR
python -c 'import os; from huggingface_hub import snapshot_download; snapshot_download(repo_id=os.environ["SOURCE_DATASET_REPO_ID"], repo_type="dataset", local_dir=os.environ["SOURCE_DATASET_DIR"])'

python unitree_lerobot/utils/create_headcam_only_dataset.py \
    --src-dir "$SOURCE_DATASET_DIR" \
    --dst-dir "$DATASET_DIR" \
    --source-video-key observation.images.cam_left_high \
    --target-video-key observation.images.head_cam \
    --overwrite

cd "$PROJECT_ROOT/unitree_lerobot/lerobot"

TRAIN_STEPS=200
python src/lerobot/scripts/lerobot_train.py \
    --dataset.repo_id="$DATASET_REPO_ID" \
    --dataset.root="$DATASET_DIR" \
    --dataset.episodes=[0,1,2,3,4] \
    --policy.push_to_hub=false \
    --policy.type=act \
    --policy.device=cuda \
    --steps="$TRAIN_STEPS" \
    --batch_size=4 \
    --num_workers=0 \
    --save_freq="$TRAIN_STEPS" \
    --eval_freq=0

TRAIN_STEPS=100000
python src/lerobot/scripts/lerobot_train.py \
    --dataset.repo_id="$DATASET_REPO_ID" \
    --dataset.root="$DATASET_DIR" \
    --policy.push_to_hub=false \
    --policy.type=act \
    --policy.device=cuda \
    --steps="$TRAIN_STEPS" \
    --save_freq="$TRAIN_STEPS" \
    --eval_freq=0
```

Evaluation after Linux training:

```bash
cd "$PROJECT_ROOT"
POLICY_PATH="unitree_lerobot/lerobot/outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model"

python unitree_lerobot/eval_robot/eval_g1_dataset.py \
    --policy.path="$POLICY_PATH" \
    --repo_id="$DATASET_REPO_ID" \
    --root="$DATASET_DIR" \
    --episodes=0 \
    --frequency=30 \
    --arm="G1_29" \
    --ee="dex3" \
    --visualization=true \
    --send_real_robot=false
```

## Current git status expectation

Expected relevant modified files before commit:

```text
M .gitignore
M README.md
M report_codex.md
M unitree_lerobot/eval_robot/eval_g1_dataset.py
```

Recommended commit scope:

```powershell
git add .gitignore README.md report_codex.md unitree_lerobot/eval_robot/eval_g1_dataset.py
git commit -m "Document and fix G1 Dex3 HeadcamOnly training workflow"
```

Do not commit:

```text
datasets/
outputs/
checkpoints/
videos/
__pycache__/
*.exe
```
