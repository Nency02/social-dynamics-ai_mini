import os

import torch

_MODEL = None
_YOLO_IMPORT_ERROR = None
_WARNED_FALLBACK = False


def _get_model():
    global _YOLO_IMPORT_ERROR
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    try:
        from ultralytics import YOLO
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        _YOLO_IMPORT_ERROR = exc
        return None

    _MODEL = YOLO(os.getenv("YOLO_DETECT_MODEL", "yolov8n.pt"))
    return _MODEL


def detect_person(frame):
    global _WARNED_FALLBACK
    model = _get_model()
    if model is None:
        if not _WARNED_FALLBACK:
            print(
                "[WARN] Ultralytics detect model unavailable. Returning empty detections. "
                f"Import error: {_YOLO_IMPORT_ERROR}"
            )
            _WARNED_FALLBACK = True
        return []

    use_cuda = torch.cuda.is_available() and os.getenv("YOLO_DEVICE", "cuda:0").startswith("cuda")
    device = os.getenv("YOLO_DEVICE", "cuda:0" if use_cuda else "cpu")
    imgsz = int(os.getenv("YOLO_IMGSZ", "320"))
    use_half = os.getenv("YOLO_HALF", "1") == "1" and device.startswith("cuda")
    results = model(frame, imgsz=imgsz, device=device, half=use_half, verbose=False)
    return results
    