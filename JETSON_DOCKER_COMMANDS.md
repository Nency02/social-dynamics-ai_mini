# Jetson Nano 2GB Docker Runbook (Social Dynamics AI)

This is a zero-to-run command guide to run the project on Jetson using Docker.

## Step 1: Install Docker on Jetson

```bash
sudo apt update
sudo apt install docker.io -y
```

Start and enable Docker:

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

Add your user to docker group:

```bash
sudo usermod -aG docker $USER
```

Reboot once:

```bash
sudo reboot
```

## Step 2: Install NVIDIA container runtime

```bash
sudo apt install nvidia-container-toolkit -y
sudo systemctl restart docker
```

Check runtime:

```bash
docker info | grep -i runtime
```

## Step 3: Prepare project folder

On Jetson:

```bash
mkdir -p ~/social-dynamics-ai
cd ~/social-dynamics-ai
```

Copy from laptop/PC:

```bash
scp -r /path/to/social-dynamics-ai <jetson-user>@<jetson-ip>:~/social-dynamics-ai
```

Or clone directly:

```bash
git clone <your-repo-url> ~/social-dynamics-ai
cd ~/social-dynamics-ai
```

## Step 4: Create Dockerfile for backend

Create `backend/Dockerfile` with this content:

```dockerfile
FROM nvcr.io/nvidia/l4t-ml:r32.7.1-py3

WORKDIR /app

COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]
```

Why this base image:

- CUDA-ready for Jetson
- Jetson-optimized dependencies
- Includes PyTorch stack for AI workloads

## Step 5: Build Docker image

From `backend` folder:

```bash
cd ~/social-dynamics-ai/backend
docker build -t social-ai .
```

## Step 6: Run container with GPU and camera

```bash
docker run -it --rm \
  --runtime nvidia \
  --network host \
  -e YOLO_POSE_MODEL=yolov8n-pose.pt \
  -e YOLO_IMGSZ=320 \
  -e YOLO_MAX_DET=8 \
  -e YOLO_CONF=0.25 \
  -e YOLO_IOU=0.50 \
  -e YOLO_HALF=1 \
  -e YOLO_DEVICE=cuda:0 \
  --device /dev/video0 \
  social-ai
```

Flag meanings:

- `--runtime nvidia`: enables GPU inside container
- `--device /dev/video0`: gives camera access
- `--network host`: exposes API on Jetson host network

## Step 7: Run API for dashboard

If you need API mode instead of `main.py` default command:

```bash
cd ~/social-dynamics-ai/backend
docker run -it --rm \
  --runtime nvidia \
  --network host \
  -e YOLO_POSE_MODEL=yolov8n-pose.pt \
  -e YOLO_IMGSZ=320 \
  -e YOLO_MAX_DET=8 \
  -e YOLO_CONF=0.25 \
  -e YOLO_IOU=0.50 \
  -e YOLO_HALF=1 \
  -e YOLO_DEVICE=cuda:0 \
  --device /dev/video0 \
  -w /app \
  social-ai \
  uvicorn api:app --host 0.0.0.0 --port 8000
```

Open from browser:

```text
http://JETSON_IP:8000/data
http://JETSON_IP:8000/docs
```

## Common issues and fixes

Camera not detected:

```bash
ls /dev/video*
```

Then use the correct device mapping in `docker run`.

Permission denied on camera:

```bash
sudo chmod 666 /dev/video0
```

GPU runtime not available:

```bash
docker info | grep -i runtime
```

If `nvidia` is missing, reinstall toolkit and restart Docker.

## End-to-end flow

```text
Jetson Camera -> Docker Container -> YOLO Pose Detection -> Behavior Analysis -> API -> Dashboard
```

## Lightweight model notes (2GB Nano)

- Keep `YOLO_IMGSZ=320` for lower RAM usage.
- Keep `YOLO_MAX_DET` small (for example `6` to `8`) if many false detections appear.
- If GPU memory is very tight, set `YOLO_HALF=0` and `YOLO_DEVICE=cpu`.

## Quick command block (copy/paste)

```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
sudo apt install nvidia-container-toolkit -y
sudo systemctl restart docker
docker info | grep -i runtime
mkdir -p ~/social-dynamics-ai
cd ~/social-dynamics-ai/backend
docker build -t social-ai .
docker run -it --rm --runtime nvidia --network host --device /dev/video0 social-ai
```
