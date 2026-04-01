import os
from pathlib import Path

import torch

_MODEL = None
_YOLO_IMPORT_ERROR = None
_WARNED_FALLBACK = False


def _get_model():
    """Load the pose model once (lazy) to reduce startup and test overhead."""
    global _YOLO_IMPORT_ERROR
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    try:
        from ultralytics import YOLO
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        _YOLO_IMPORT_ERROR = exc
        return None

    default_model = Path(__file__).resolve().parents[1] / "yolov8n-pose.pt"
    model_source = os.getenv("YOLO_POSE_MODEL", str(default_model))
    _MODEL = YOLO(model_source)
    return _MODEL


def detect_pose(frame):
    """Run lightweight pose detection tuned for low-memory Jetson devices."""
    global _WARNED_FALLBACK
    model = _get_model()
    if model is None:
        if not _WARNED_FALLBACK:
            print(
                "[WARN] Ultralytics model unavailable. Running in fallback mode with no pose detections. "
                f"Import error: {_YOLO_IMPORT_ERROR}"
            )
            _WARNED_FALLBACK = True
        return []

    use_cuda = torch.cuda.is_available() and os.getenv("YOLO_DEVICE", "cuda:0").startswith("cuda")
    device = os.getenv("YOLO_DEVICE", "cuda:0" if use_cuda else "cpu")

    conf = float(os.getenv("YOLO_CONF", "0.25"))
    iou = float(os.getenv("YOLO_IOU", "0.50"))
    imgsz = int(os.getenv("YOLO_IMGSZ", "320"))
    max_det = int(os.getenv("YOLO_MAX_DET", "8"))
    use_half = os.getenv("YOLO_HALF", "1") == "1" and device.startswith("cuda")

    results = model(
        frame,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        max_det=max_det,
        device=device,
        half=use_half,
        verbose=False,
    )
    return results