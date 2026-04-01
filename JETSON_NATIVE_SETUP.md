# Jetson Native Setup (No Docker)

This guide runs Social Dynamics AI directly on Jetson (without Docker), tuned for low memory devices like Jetson Nano 2GB.

## 1) Pre-checks

Run on Jetson terminal:

```bash
uname -a
cat /etc/nv_tegra_release || true
python3 --version
```

You need:
- NVIDIA Jetson with working camera
- Python 3.8.18 (or install in Step 4)
- Internet access for package installation

## 2) System optimization for 2GB Nano

Enable max performance and add swap to reduce out-of-memory crashes.

```bash
sudo nvpmodel -m 0
sudo jetson_clocks
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
free -h
```

## 3) Install system dependencies

```bash
sudo apt update
sudo apt install -y \
  git curl wget build-essential pkg-config \
  libbz2-dev libssl-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev \
  xz-utils tk-dev \
  libopenblas-dev libblas-dev liblapack-dev gfortran \
  libjpeg-dev zlib1g-dev libpython3-dev \
  libopenmpi-dev libomp-dev \
  python3-venv python3-pip
```

## 4) Prepare Python 3.8.18 environment

If your Jetson already has Python 3.8.x, skip to Step 5.

If not, install Python 3.8.18 via pyenv:

```bash
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

pyenv install 3.8.18
pyenv virtualenv 3.8.18 social-ai-3.8
pyenv activate social-ai-3.8
python --version
python -c "import bz2, ssl, lzma; print('python stdlib compression/ssl modules OK')"
```

## 5) Clone project

```bash
cd ~
git clone https://github.com/Nency02/social-dynamics-ai_mini.git social-dynamics-ai
cd social-dynamics-ai
```

If you already copied the project manually, just `cd` into it.

## 6) Create and activate virtual environment

From project root:

```bash
python3.8 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

## 7) Install Jetson-compatible PyTorch first

Important: on Jetson, install NVIDIA-compatible PyTorch wheel first, then install the project requirements.

1. Identify your JetPack version:

```bash
cat /etc/nv_tegra_release
```

2. Install matching torch/torchvision wheel from NVIDIA Jetson PyTorch releases.

Use NVIDIA official instructions for your exact JetPack + Python 3.8 combo:
- https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/70
- https://docs.nvidia.com/deeplearning/frameworks/install-pytorch-jetson-platform/

3. Verify torch:

```bash
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

## 8) Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

If `ultralytics` tries to upgrade torch, reinstall your Jetson torch wheel afterward.

## 9) Install frontend dependencies (optional, for local UI on Jetson)

```bash
cd ../frontend
npm install
```

## 10) Run backend API and vision pipeline (native)

Open terminal A:

```bash
cd ~/social-dynamics-ai/backend
source ../.venv/bin/activate
python api.py
```

Open terminal B:

```bash
cd ~/social-dynamics-ai/backend
source ../.venv/bin/activate

export YOLO_POSE_MODEL=yolov8n-pose.pt
export YOLO_IMGSZ=320
export YOLO_MAX_DET=8
export YOLO_CONF=0.25
export YOLO_IOU=0.50
export YOLO_HALF=1
export YOLO_DEVICE=cuda:0

python main.py
```

If CUDA is unavailable or memory is too tight:

```bash
export YOLO_DEVICE=cpu
export YOLO_HALF=0
python main.py
```

## 11) Run frontend

Open terminal C:

```bash
cd ~/social-dynamics-ai/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Access from another device browser:

```text
http://JETSON_IP:5173
http://JETSON_IP:8000/data
http://JETSON_IP:8000/docs
```

## 12) Camera troubleshooting

List camera devices:

```bash
ls /dev/video*
```

If needed, select camera index:

```bash
export CAMERA_INDEX=0
python main.py
```

## 13) Performance tips for 2GB

- Keep `YOLO_IMGSZ=320`.
- Keep `YOLO_MAX_DET` between `4` and `8`.
- Close browser tabs and other apps while running inference.
- Keep swap enabled.
- If FPS drops, reduce `YOLO_MAX_DET` first.

## 14) Fix `ModuleNotFoundError: No module named '_bz2'`

This means Python was built without bzip2 headers installed.

Run:

```bash
sudo apt update
sudo apt install -y libbz2-dev bzip2

# If you used pyenv, rebuild Python after installing headers
pyenv uninstall -f 3.8.18
pyenv install 3.8.18

# Recreate venv and reinstall deps
cd ~/social-dynamics-ai
rm -rf .venv
python3.8 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
cd backend
pip install -r requirements.txt

# Verify fix
python -c "import bz2; print('bz2 OK')"
```

## 15) Fix `import-im6.q16` error when testing torch

If you run this in terminal:

```bash
import torch
```

Linux executes the ImageMagick `import` command, not Python.

Use one of these instead:

```bash
python -c "import torch; print(torch.__version__)"
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

Or open Python REPL first:

```bash
python
>>> import torch
```

## 16) Final one-shot recovery (bz2 + venv + run)

If you want one complete recovery path, run this block exactly:

```bash
sudo apt update
sudo apt install -y libbz2-dev bzip2 libssl-dev zlib1g-dev liblzma-dev

cd ~/social-dynamics-ai_mini

# If pyenv is used for Python 3.8.18, rebuild Python so _bz2 is compiled
if command -v pyenv >/dev/null 2>&1; then
  pyenv uninstall -f 3.8.18 || true
  pyenv install 3.8.18
fi

rm -rf .venv
python3.8 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# Install Jetson-compatible torch first (from NVIDIA docs for your JetPack), then project deps
cd backend
pip install -r requirements.txt

python -c "import bz2; print('bz2 OK')"
python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
python -c "import ultralytics; print('ultralytics OK')"

export YOLO_POSE_MODEL=yolov8n-pose.pt
export YOLO_IMGSZ=320
export YOLO_MAX_DET=8
export YOLO_CONF=0.25
export YOLO_IOU=0.50
export YOLO_HALF=1
export YOLO_DEVICE=cuda:0

python main.py
```

If CUDA is false, run CPU mode:

```bash
export YOLO_DEVICE=cpu
export YOLO_HALF=0
python main.py
```

## 17) Quick start block (copy/paste)

```bash
cd ~/social-dynamics-ai
python3.8 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
cd backend
pip install -r requirements.txt
python api.py
```

In another terminal:

```bash
cd ~/social-dynamics-ai/backend
source ../.venv/bin/activate
export YOLO_POSE_MODEL=yolov8n-pose.pt
export YOLO_IMGSZ=320
export YOLO_MAX_DET=8
export YOLO_CONF=0.25
export YOLO_IOU=0.50
export YOLO_HALF=1
export YOLO_DEVICE=cuda:0
python main.py
```