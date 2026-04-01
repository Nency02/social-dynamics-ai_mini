# Social Dynamics AI

Real-time classroom discussion analytics using pose estimation, behavior scoring, and a live React dashboard.

## What This Project Does

- Detects multiple people from a camera feed using YOLOv8 pose estimation
- Tracks people across frames with stable IDs
- Computes behavior signals (gesture, posture, proximity, centrality, facing)
- Produces participation metrics and social roles per participant
- Serves live metrics via FastAPI
- Visualizes results in a modern frontend dashboard

## Project Structure

```text
social-dynamics-ai/
  backend/
    api.py
    main.py
    requirements.txt
    yolov8n-pose.pt
    behavior/
    vision/
    outputs/
  frontend/
    package.json
    src/
    public/
  start_system.bat
  start_system.sh
  README.md
```

## Prerequisites

- Python 3.8.18+
- Node.js 18+
- A working webcam

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run Locally

Run each service in a separate terminal.

### 1) Start API server

```bash
cd backend
python api.py
```

### 2) Start vision pipeline

```bash
cd backend
python main.py
```

For Jetson Nano 2GB (recommended lightweight settings):

```bash
cd backend
export YOLO_POSE_MODEL=yolov8n-pose.pt
export YOLO_IMGSZ=320
export YOLO_MAX_DET=8
export YOLO_CONF=0.25
export YOLO_IOU=0.50
export YOLO_HALF=1
export YOLO_DEVICE=cuda:0
python main.py
```

If CUDA is unavailable, use:

```bash
export YOLO_DEVICE=cpu
export YOLO_HALF=0
```

If you want to force a specific webcam (for example, your external USB camera), set
`CAMERA_INDEX` before running:

```bash
# Windows (PowerShell)
$env:CAMERA_INDEX=1
python main.py
```

### 3) Start frontend

```bash
cd frontend
npm run dev
```

Open the URL shown by Vite (commonly `http://localhost:5173` or `http://localhost:5174`).

## Testing

### Backend tests

```bash
cd backend
pytest -q
```

Includes comprehensive tests for:
- Person tracking stability (persistence when off-frame, no ID switching)
- Behavior attribution accuracy (gesture/activity not misattributed to nearby people)
- Scoring correctness (participation aggregation, role assignment)
- API robustness (health checks, missing data handling)

### Frontend build check

```bash
cd frontend
npm run build
```

## Continuous Integration

- GitHub Actions runs backend tests and frontend build on pull requests and pushes to `main`.
- Workflow file: `.github/workflows/ci.yml`

## API

### `GET /health`

Returns service health.

### `GET /data`

Returns live classroom analytics in this shape:

```json
{
  "timestamp": 1710951234.567,
  "total_students": 3,
  "students": [
    {
      "student_id": 0,
      "role": "Active",
      "participation_score": 0.74
    }
  ],
  "metrics": {
    "most_active_student": 0,
    "participation_level": 0.51,
    "discussion_balance": 0.67
  }
}
```

## Notes

- Runtime JSON files are written to `backend/outputs/`.
- Default pose model is `yolov8n-pose.pt` and can be changed with `YOLO_POSE_MODEL`.
- Inference can be tuned with `YOLO_IMGSZ`, `YOLO_MAX_DET`, `YOLO_CONF`, `YOLO_IOU`, `YOLO_HALF`, and `YOLO_DEVICE`.
- Jetson setup guides:
  - Docker: `JETSON_DOCKER_COMMANDS.md`
  - Native (no Docker): `JETSON_NATIVE_SETUP.md`
- Participation and role labeling are heuristic and intended for classroom analytics prototypes.
- For best detection quality, use stable lighting and keep all participants visible.

## Person Tracking & Behavior Attribution

**Tracking stability improvements:**
- Multi-factor matching: Combines position distance + pose (shoulder angle) consistency to prevent misidentification
- Extended persistence: Tracks maintain identity for up to 36 frames during occlusion/out-of-frame, then re-acquire on re-entry
- Pose validation: Rejects matches where two people have opposite body orientations, preventing swaps

**Behavior attribution safeguards:**
- Each person's gesture/activity is computed only from their own keypoints
- Proximity-based features (facing, group centrality) properly isolate per-person calculations
- All behavior scores are attributed to the correct track_id via validated matching

**Testing coverage:**
- `tests/test_tracking.py`: Validates tracking persistence, cross-identification prevention, and pose matching
- `tests/test_scoring.py`: Verifies participation averages include all detected people
- `tests/test_api.py`: Ensures API returns accurate data in all scenarios