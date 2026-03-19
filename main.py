"""
main.py  -  Social Dynamics AI - Real-time pipeline

ESC to quit.
"""

import cv2
import json
import os
import time
from collections import deque

from src.behavior.scoring import analyze_social_dynamics
from src.vision.pose import detect_pose
from src.vision.keypoints import assign_track_ids, extract_keypoints
from src.vision.Overlay import render_frame


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_JSON      = "outputs/keypoints.json"
JSON_EVERY_N     = 5       # write JSON every N frames (reduce I/O)
CAMERA_INDEX     = 0
FPS_WINDOW       = 30      # rolling window size for FPS smoothing


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
os.makedirs("outputs", exist_ok=True)

cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open camera at index {CAMERA_INDEX}")

frame_id     = 0
tracker_state = {"next_track_id": 0, "tracks": {}, "previous_centers": {}}
fps_history   = deque(maxlen=FPS_WINDOW)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    t0 = time.perf_counter()

    ret, frame = cap.read()
    if not ret:
        print("[WARN] Frame read failed – retrying…")
        continue

    frame_id += 1

    # ---- Vision ----
    results = detect_pose(frame)
    people  = extract_keypoints(results)
    people  = assign_track_ids(people, tracker_state)

    # ---- Behavior analysis ----
    people, group_metrics = analyze_social_dynamics(people)

    # ---- FPS ----
    elapsed = time.perf_counter() - t0
    fps_history.append(1.0 / elapsed if elapsed > 0 else 0.0)
    fps = sum(fps_history) / len(fps_history)

    # ---- Render ----
    annotated = frame.copy()
    annotated = render_frame(annotated, people, group_metrics, fps=fps)

    cv2.imshow("Social Dynamics AI", annotated)

    # ---- JSON export (throttled) ----
    if frame_id % JSON_EVERY_N == 0:
        export_people = [
            {k: v for k, v in p.items() if k != "behavior_features"}
            for p in people
        ]
        payload = {
            "schema_version": "1.1.0",
            "frame_id":       frame_id,
            "timestamp":      time.time(),
            "fps":            round(fps, 2),
            "group_metrics":  group_metrics,
            "people":         export_people,
        }
        with open(OUTPUT_JSON, "w") as f:
            json.dump(payload, f, indent=2)

    if cv2.waitKey(1) == 27:   # ESC
        break


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
cap.release()
cv2.destroyAllWindows()
print(f"[INFO] Processed {frame_id} frames.")