import os

import torch
from ultralytics import YOLO

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = YOLO(os.getenv("YOLO_DETECT_MODEL", "yolov8n.pt"))
    return _MODEL


def detect_person(frame):
    model = _get_model()
    use_cuda = torch.cuda.is_available() and os.getenv("YOLO_DEVICE", "cuda:0").startswith("cuda")
    device = os.getenv("YOLO_DEVICE", "cuda:0" if use_cuda else "cpu")
    imgsz = int(os.getenv("YOLO_IMGSZ", "320"))
    use_half = os.getenv("YOLO_HALF", "1") == "1" and device.startswith("cuda")
    results = model(frame, imgsz=imgsz, device=device, half=use_half, verbose=False)
    return results
    