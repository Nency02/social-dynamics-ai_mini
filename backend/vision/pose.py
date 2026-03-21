from pathlib import Path
from ultralytics import YOLO

MODEL_PATH = Path(__file__).resolve().parents[1] / "yolov8n-pose.pt"
model = YOLO(str(MODEL_PATH))

def detect_pose(frame):
    # Slightly lower confidence and suppress verbose logs for steadier classroom recall.
    results = model(frame, conf=0.15, iou=0.55, verbose=False)
    return results