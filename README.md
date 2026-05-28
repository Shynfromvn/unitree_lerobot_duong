# unitree_lerobot_duong

Linux-first workflow for training and evaluating a Unitree G1 Dex3 HeadcamOnly ACT policy with LeRobot.

This repository is based on `unitreerobotics/unitree_lerobot` and keeps the original LeRobot training entrypoint:

```text
lerobot/src/lerobot/scripts/lerobot_train.py
```

The local project-specific dataset contract is:

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

All commands below are for Ubuntu/Linux with bash or zsh. Do not use PowerShell syntax on the Ubuntu training machine.

## 1. Expected Folder Layout

Use this layout:

```text
~/work/unitree_lerobot_duong/
  unitree_lerobot/
  unitree_sdk2_python/
  datasets/
    G1_Dex3_PickApple_Dataset/
    G1_Dex3_PickApple_Dataset_HeadcamOnly/
```

Clone the project:

```bash
mkdir -p ~/work/unitree_lerobot_duong
cd ~/work/unitree_lerobot_duong

git clone --recurse-submodules https://github.com/Shynfromvn/unitree_lerobot_duong.git unitree_lerobot
cd unitree_lerobot
git submodule update --init --recursive
```

## 2. Create Environment

Create and activate the conda environment:

```bash
conda create -n unitree_lerobot -c conda-forge python=3.10 pinocchio "ffmpeg>=7,<8" -y
conda activate unitree_lerobot
```

Install LeRobot and this package from the repo root:

```bash
cd ~/work/unitree_lerobot_duong/unitree_lerobot

cd lerobot
pip install -e .

cd ..
pip install -e .
```

## 3. CUDA Setup

### Standard CUDA Check

Run:

```bash
python -c 'import torch; print(torch.__version__, torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda")'
```

### RTX PRO 6000 Blackwell

On the Ubuntu machine with `NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition`, the working setup is PyTorch CUDA 12.8. This fixes the `sm_120 is not compatible` and `no kernel image is available for execution on the device` errors.

```bash
conda activate unitree_lerobot

pip uninstall -y torch torchvision torchaudio
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

Verify with an actual CUDA operation:

```bash
python -c 'import torch; print(torch.__version__, torch.version.cuda); print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_capability(0)); x=torch.randn(512,512,device="cuda"); y=x@x; torch.cuda.synchronize(); print("cuda ok")'
```

Expected:

```text
2.7.1+cu128 12.8
NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition
(12, 0)
cuda ok
```

## 4. TorchCodec and FFmpeg

This project uses LeRobot dataset video decoding. In this repo version the default backend can be `torchcodec`.

Install compatible TorchCodec and runtime libraries:

```bash
conda activate unitree_lerobot

conda install -y --override-channels -c conda-forge "ffmpeg>=7,<8"
pip uninstall -y torchcodec
pip install torchcodec==0.5 --index-url https://download.pytorch.org/whl/cu128
pip install --force-reinstall nvidia-cuda-nvrtc-cu12==12.8.61
pip install -U nvidia-npp-cu12
```

Set library path for the current shell:

```bash
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$(python -c 'import site,glob; print(":".join(glob.glob(site.getsitepackages()[0]+"/nvidia/*/lib")))'):$LD_LIBRARY_PATH"
```

Check FFmpeg and TorchCodec:

```bash
ffmpeg -version | head -n 3
ls "$CONDA_PREFIX"/lib/libavutil.so*
find "$(python -c 'import site; print(site.getsitepackages()[0])')" -name 'libnppicc.so.12'
python -c 'import torchcodec; from torchcodec.decoders import VideoDecoder; print("torchcodec ok")'
```

Expected FFmpeg version:

```text
ffmpeg version 7.x
```

Expected library:

```text
libavutil.so.59
```

Do not install plain `ffmpeg<8`; conda may choose `ffmpeg 2.8.6`, which is too old for TorchCodec.

## 5. Unitree SDK for Simulation or Real Robot

Install `unitree_sdk2_python` in the same conda env:

```bash
cd ~/work/unitree_lerobot_duong

git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python

conda activate unitree_lerobot
pip install -e .
```

Verify:

```bash
python -c 'import unitree_sdk2py; import cyclonedds; import cv2; print("unitree sdk ok")'
```

## 6. Define Dataset Paths

Run these from the repository root:

```bash
cd ~/work/unitree_lerobot_duong/unitree_lerobot

PROJECT_ROOT="$(pwd)"
DATASET_PARENT="$(dirname "$PROJECT_ROOT")/datasets"
DATASET_REPO_ID="G1_Dex3_PickApple_Dataset_HeadcamOnly"
DATASET_DIR="$DATASET_PARENT/$DATASET_REPO_ID"
SOURCE_DATASET_REPO_ID="unitreerobotics/G1_Dex3_PickApple_Dataset"
SOURCE_DATASET_NAME="G1_Dex3_PickApple_Dataset"
SOURCE_DATASET_DIR="$DATASET_PARENT/$SOURCE_DATASET_NAME"
ROBOT_TYPE="Unitree_G1_Dex3_HeadcamOnly"

mkdir -p "$DATASET_PARENT"
export PROJECT_ROOT DATASET_PARENT DATASET_REPO_ID DATASET_DIR SOURCE_DATASET_REPO_ID SOURCE_DATASET_NAME SOURCE_DATASET_DIR ROBOT_TYPE
```

Check:

```bash
echo "$DATASET_DIR"
```

Expected:

```text
/home/<user>/work/unitree_lerobot_duong/datasets/G1_Dex3_PickApple_Dataset_HeadcamOnly
```

## 7. Download and Generate HeadcamOnly Dataset

If Hugging Face requires authentication:

```bash
huggingface-cli login
```

Download the source dataset:

```bash
python -c 'import os; from huggingface_hub import snapshot_download; snapshot_download(repo_id=os.environ["SOURCE_DATASET_REPO_ID"], repo_type="dataset", local_dir=os.environ["SOURCE_DATASET_DIR"])'
```

Generate the HeadcamOnly dataset:

```bash
python unitree_lerobot/utils/create_headcam_only_dataset.py \
  --src-dir "$SOURCE_DATASET_DIR" \
  --dst-dir "$DATASET_DIR" \
  --source-video-key observation.images.cam_left_high \
  --target-video-key observation.images.head_cam \
  --overwrite
```

This converts:

```text
observation.images.cam_left_high -> observation.images.head_cam
```

## 8. Verify Dataset Metadata

Run this as one line:

```bash
python -c 'import json,pathlib; p=pathlib.Path("'"$DATASET_DIR"'")/"meta/info.json"; info=json.loads(p.read_text()); print(info["codebase_version"]); print(info["robot_type"]); print([k for k in info["features"] if k.startswith("observation.images.")]); print(info["features"]["observation.state"]["shape"]); print(info["features"]["action"]["shape"])'
```

Expected:

```text
v3.0
Unitree_G1_Dex3_HeadcamOnly
['observation.images.head_cam']
[28]
[28]
```

If the command tries to read `meta/info.json` without the full dataset path, `DATASET_DIR` is empty in that shell. Re-run Section 6.

## 9. Train Test on 5 Episodes

Use this before full training. The quotes around `--dataset.episodes='[0,1,2,3,4]'` are required in zsh.

```bash
cd ~/work/unitree_lerobot_duong/unitree_lerobot/lerobot

TRAIN_STEPS=200

python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id="$DATASET_REPO_ID" \
  --dataset.root="$DATASET_DIR" \
  --dataset.episodes='[0,1,2,3,4]' \
  --policy.push_to_hub=false \
  --policy.type=act \
  --policy.device=cuda \
  --steps="$TRAIN_STEPS" \
  --batch_size=4 \
  --num_workers=0 \
  --save_freq="$TRAIN_STEPS" \
  --eval_freq=0
```

Expected log markers:

```text
dataset.num_episodes=5
Start offline training on a fixed dataset
step:200
Checkpoint policy after step 200
```

## 10. Full Training

Full training uses the full dataset by omitting `--dataset.episodes`.

The repo default is `steps=100000`. Do not pass `--steps` if you want the default.

```bash
cd ~/work/unitree_lerobot_duong/unitree_lerobot/lerobot

python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id="$DATASET_REPO_ID" \
  --dataset.root="$DATASET_DIR" \
  --policy.push_to_hub=false \
  --policy.type=act \
  --policy.device=cuda \
  --eval_freq=0
```

For the RTX PRO 6000 Blackwell machine, a practical higher-throughput command is:

```bash
python src/lerobot/scripts/lerobot_train.py \
  --dataset.repo_id="$DATASET_REPO_ID" \
  --dataset.root="$DATASET_DIR" \
  --policy.push_to_hub=false \
  --policy.type=act \
  --policy.device=cuda \
  --batch_size=64 \
  --num_workers=4 \
  --eval_freq=0
```

If stable and GPU memory is still low, try `--batch_size=96`. If out of memory, use `--batch_size=48` or `--batch_size=32`.

Monitor:

```bash
watch -n 1 nvidia-smi
```

## 11. Checkpoint Location

Checkpoints are saved under:

```text
lerobot/outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model
```

Example:

```bash
POLICY_PATH="$PROJECT_ROOT/lerobot/outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model"
```

## 12. Evaluate Checkpoint on Dataset

Run from repo root:

```bash
cd "$PROJECT_ROOT"

POLICY_PATH="$PROJECT_ROOT/lerobot/outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model"

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

When prompted, enter:

```text
s
```

## 13. Run Checkpoint in Unitree Simulation

Start the Unitree simulation and image server first. Then run:

```bash
cd "$PROJECT_ROOT"

POLICY_PATH="$PROJECT_ROOT/lerobot/outputs/train/<date>/<run>_act/checkpoints/<step>/pretrained_model"

python unitree_lerobot/eval_robot/eval_g1_sim.py \
  --policy.path="$POLICY_PATH" \
  --repo_id="$DATASET_REPO_ID" \
  --root="$DATASET_DIR" \
  --episodes=0 \
  --frequency=30 \
  --arm="G1_29" \
  --ee="dex3" \
  --visualization=true \
  --save_data=false \
  --task_dir="./data" \
  --max_episodes=1200 \
  --image_host="127.0.0.1" \
  --rename_map='{"observation.images.cam_left_high":"observation.images.head_cam"}'
```

Change `--image_host` if the image server is on another machine.

The rename map is required because the trained policy expects:

```text
observation.images.head_cam
```

while the current simulation image processing emits:

```text
observation.images.cam_left_high
```

When prompted, enter:

```text
s
```

## 14. Replay Dataset on Robot

```bash
cd "$PROJECT_ROOT"

python unitree_lerobot/eval_robot/replay_robot.py \
  --repo_id="$DATASET_REPO_ID" \
  --root="$DATASET_DIR" \
  --episodes=0 \
  --frequency=30 \
  --arm="G1_29" \
  --ee="dex3" \
  --visualization=true
```

## 15. Troubleshooting

### zsh shows `bquote>`

You pasted PowerShell backticks into zsh. Press `Ctrl+C` and use Linux line continuation `\`.

Wrong in zsh:

```text
`
```

Right in zsh:

```text
\
```

### `Repo id ...: ''`

The dataset repo variable is empty. Re-run Section 6 before downloading:

```bash
echo "$SOURCE_DATASET_REPO_ID"
echo "$SOURCE_DATASET_DIR"
```

### `FileNotFoundError: meta/info.json`

`DATASET_DIR` is empty or points to the wrong folder. Re-run Section 6 and check:

```bash
ls "$DATASET_DIR/meta/info.json"
```

### `sm_120 is not compatible` or `no kernel image is available`

Install PyTorch CUDA 12.8 as shown in Section 3.

### `Could not load libtorchcodec`

Check:

```bash
ffmpeg -version | head -n 3
ls "$CONDA_PREFIX"/lib/libavutil.so*
find "$(python -c 'import site; print(site.getsitepackages()[0])')" -name 'libnppicc.so.12'
```

The working target is:

```text
torch 2.7.1+cu128
torchcodec 0.5+cu128
ffmpeg 7.x
libavutil.so.59
libnppicc.so.12
```

### SSH or tmux training

Use tmux for long runs:

```bash
tmux new -s train_lerobot
```

Detach:

```text
Ctrl+B then D
```

Reattach:

```bash
tmux attach -t train_lerobot
```

## References

- Upstream Unitree repository: https://github.com/unitreerobotics/unitree_lerobot
- Project repository: https://github.com/Shynfromvn/unitree_lerobot_duong
- Unitree SDK: https://github.com/unitreerobotics/unitree_sdk2_python
- PyTorch install selector: https://pytorch.org/get-started/locally/
- TorchCodec README: https://github.com/pytorch/torchcodec
