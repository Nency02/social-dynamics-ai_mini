"""
main.py  -  Social Dynamics AI - Real-time pipeline

ESC to quit.
"""

import cv2
import json
import os
import time
from collections import deque

from behavior.scoring import analyze_social_dynamics
from vision.pose import detect_pose
from vision.keypoints import assign_track_ids, extract_keypoints
from vision.Overlay import render_frame


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_JSON      = os.path.join(os.path.dirname(__file__), "outputs", "keypoints.json")
LIVE_DATA_JSON   = os.path.join(os.path.dirname(__file__), "outputs", "live_data.json")
JSON_EVERY_N     = 5       # write JSON every N frames (reduce I/O)
CAMERA_INDEX     = 0
FPS_WINDOW       = 30      # rolling window size for FPS smoothing


def _normalize_role(old_role):
    """Convert detailed roles to simplified classroom roles."""
    if old_role == "Speaker":
        return "Active"
    elif old_role in ["Listener", "Engaged"]:
        return "Moderate"
    else:  # Peripheral, Isolated
        return "Passive"


def _create_live_data(people, group_metrics, tracker_state=None):
    """Create classroom discussion analyzer output format."""
    # Map students with roles
    students = []
    detected_ids = set()
    for person in people:
        old_role = person.get("social_role", "Peripheral")
        track_id = person.get("track_id")
        detected_ids.add(track_id)
        students.append({
            "student_id": track_id,
            "role": _normalize_role(old_role),
            "participation_score": person.get("participation_score", 0.0),
        })

    # Keep recently tracked participants visible for short detector dropouts.
    inferred_students = []
    if tracker_state is not None:
        tracks = tracker_state.get("tracks", {})
        for track_id, track_data in tracks.items():
            if track_id in detected_ids:
                continue
            missed = int(track_data.get("missed", 0))
            if missed <= 8:
                inferred_students.append({
                    "student_id": int(track_id),
                    "role": "Passive",
                    "participation_score": 0.0,
                    "inferred": True,
                })

    students.extend(inferred_students)

    # Calculate metrics
    detected_students = [s for s in students if not s.get("inferred")]

    if detected_students:
        most_active = max(detected_students, key=lambda s: s["participation_score"])
        most_active_id = most_active["student_id"]
        scores = [s["participation_score"] for s in detected_students]
        mean_participation = sum(scores) / len(scores)

        # Ratio of students participating above a minimum practical threshold.
        active_ratio = sum(1 for s in scores if s >= 0.25) / len(scores)

        # Blend magnitude (mean score) with spread of active contributors.
        participation_level = max(0.0, min(1.0, 0.65 * mean_participation + 0.35 * active_ratio))
        participation_level = participation_level ** 0.85

        # Discussion balance: how evenly distributed participation is (inverse of variance)
        if len(scores) > 1:
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            equality = max(0.0, min(1.0, 1.0 - min(1.0, variance * 5.0)))

            # Uniformly low participation should not report as perfectly balanced.
            intensity = max(0.0, min(1.0, mean / 0.6))
            discussion_balance = max(0.0, min(1.0, 0.70 * equality + 0.30 * intensity))
        else:
            discussion_balance = participation_level
    else:
        most_active_id = None
        participation_level = 0.0
        discussion_balance = 0.0

    return {
        "timestamp": time.time(),
        "total_students": len(students),
        "students": students,
        "metrics": {
            "most_active_student": most_active_id,
            "participation_level": round(participation_level, 4),
            "discussion_balance": round(discussion_balance, 4),
        },
    }


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs"), exist_ok=True)

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
   # ---- Behavior analysis ----
    people, group_metrics = analyze_social_dynamics(people)

    # DEBUG: Print scores to console
    for p in people:
        print(f"ID:{p.get('track_id')} | Role:{p.get('social_role')} | "
            f"Eng:{p.get('engagement_score'):.3f} | "
            f"Dom:{p.get('dominance_score'):.3f} | "
            f"Act:{p.get('activity_score'):.3f}")

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
        # Original detailed output
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

        # Classroom discussion analyzer format
        live_data = _create_live_data(people, group_metrics, tracker_state=tracker_state)
        with open(LIVE_DATA_JSON, "w") as f:
            json.dump(live_data, f, indent=2)

    if cv2.waitKey(1) == 27:   # ESC
        break


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
cap.release()
cv2.destroyAllWindows()
print(f"[INFO] Processed {frame_id} frames.")