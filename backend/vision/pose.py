import os
from pathlib import Path

import cv2
import numpy as np
import torch

_MODEL = None
_YOLO_IMPORT_ERROR = None
_WARNED_FALLBACK = False
_HOG = None


def _get_hog_detector():
    global _HOG
    if _HOG is not None:
        return _HOG
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    _HOG = hog
    return _HOG


def _synthetic_keypoints_from_bbox(x1, y1, x2, y2):
    """Create approximate COCO-like keypoints from a person box for fallback scoring."""
    w = max(1.0, float(x2 - x1))
    h = max(1.0, float(y2 - y1))
    cx = float(x1) + w * 0.5

    points = [(0.0, 0.0)] * 17
    # Face
    points[0] = (cx, y1 + h * 0.12)            # nose
    points[1] = (cx - w * 0.05, y1 + h * 0.11) # left eye
    points[2] = (cx + w * 0.05, y1 + h * 0.11) # right eye
    # Shoulders
    points[5] = (cx - w * 0.18, y1 + h * 0.28)
    points[6] = (cx + w * 0.18, y1 + h * 0.28)
    # Elbows
    points[7] = (cx - w * 0.24, y1 + h * 0.45)
    points[8] = (cx + w * 0.24, y1 + h * 0.45)
    # Wrists
    points[9] = (cx - w * 0.30, y1 + h * 0.62)
    points[10] = (cx + w * 0.30, y1 + h * 0.62)
    # Hips
    points[11] = (cx - w * 0.14, y1 + h * 0.58)
    points[12] = (cx + w * 0.14, y1 + h * 0.58)

    return [[round(px, 2), round(py, 2)] for px, py in points]


def _fallback_people_from_frame(frame):
    """Return person-like detections without Ultralytics (OpenCV HOG fallback)."""
    hog = _get_hog_detector()
    max_det = int(os.getenv("YOLO_MAX_DET", "8"))

    # HOG expects grayscale for better performance on low-power devices.
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    boxes, weights = hog.detectMultiScale(
        gray,
        winStride=(8, 8),
        padding=(8, 8),
        scale=1.05,
    )

    people = []
    if len(boxes) == 0:
        return people

    weights_arr = np.array(weights).reshape(-1) if len(weights) else np.zeros(len(boxes), dtype=np.float32)
    order = np.argsort(-weights_arr)

    for rank, idx in enumerate(order[:max_det]):
        x, y, w, h = boxes[int(idx)]
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + w), int(y + h)

        # Clamp confidence into a display-friendly [0, 1] range.
        conf = float(weights_arr[int(idx)]) if len(weights_arr) > int(idx) else 0.4
        conf = max(0.05, min(0.99, conf / 2.0))

        kps = _synthetic_keypoints_from_bbox(x1, y1, x2, y2)
        people.append(
            {
                "id": rank,
                "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
                "confidence": round(conf, 4),
                "keypoints": kps,
                "keypoint_confidence": [round(conf, 4)] * 17,
                "orientation_angle_deg": 0.0,
                "fallback": True,
            }
        )

    return people


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
                "[WARN] Ultralytics unavailable. Running OpenCV fallback detector (approximate boxes/keypoints). "
                f"Import error: {_YOLO_IMPORT_ERROR}"
            )
            _WARNED_FALLBACK = True
        return _fallback_people_from_frame(frame)

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