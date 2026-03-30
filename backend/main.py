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
from behavior.roles import assign_roles
from vision.pose import detect_pose
from vision.keypoints import assign_track_ids, extract_keypoints
from vision.Overlay import render_frame


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_JSON      = os.path.join(os.path.dirname(__file__), "outputs", "keypoints.json")
LIVE_DATA_JSON   = os.path.join(os.path.dirname(__file__), "outputs", "live_data.json")
JSON_EVERY_N     = 5       # write JSON every N frames (reduce I/O)
FPS_WINDOW       = 30      # rolling window size for FPS smoothing


def _open_camera():
    """Open a camera, preferring external webcams on Windows."""
    env_camera = os.getenv("CAMERA_INDEX")
    if env_camera is not None:
        try:
            candidates = [int(env_camera)]
        except ValueError as exc:
            raise RuntimeError("CAMERA_INDEX must be an integer") from exc
    else:
        # External USB webcams commonly appear on index 1+ while built-ins are index 0.
        candidates = [1, 2, 0]

    for idx in candidates:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            continue

        ok, _ = cap.read()
        if ok:
            print(f"[INFO] Using camera index {idx}")
            return cap

        cap.release()

    raise RuntimeError(
        f"Cannot open any camera. Tried indices: {candidates}. "
        "Set CAMERA_INDEX to your webcam index if needed."
    )


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
            "detailed_role": old_role,
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
                    "detailed_role": "Inferred",
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

cap = _open_camera()

frame_id     = 0
tracker_state = {"next_track_id": 0, "tracks": {}, "previous_centers": {}}
fps_history   = deque(maxlen=FPS_WINDOW)

# Temporal smoothing: keep a rolling history of scores per track_id.
# Speaker role requires sustained activity — not a single noisy frame.
SCORE_HISTORY_LEN = 8   # smooth over last N frames (~0.5s at 15fps)
score_history: dict = {}  # track_id -> deque of (dom, act, eng) tuples


def _smooth_scores(people, history: dict, window: int = SCORE_HISTORY_LEN):
    """
    Replace per-person scores with a rolling average over recent frames.
    This prevents a single noisy frame from triggering Speaker.
    """
    for person in people:
        tid = person.get("track_id")
        if tid is None:
            continue
        if tid not in history:
            history[tid] = deque(maxlen=window)

        history[tid].append((
            person.get("dominance_score", 0.0),
            person.get("activity_score",  0.0),
            person.get("engagement_score", 0.0),
        ))

        if len(history[tid]) >= 2:   # only smooth once we have data
            doms, acts, engs = zip(*history[tid])
            person["dominance_score"]  = round(sum(doms) / len(doms), 4)
            person["activity_score"]   = round(sum(acts) / len(acts), 4)
            person["engagement_score"] = round(sum(engs) / len(engs), 4)
    return people


def _prune_score_history(history: dict, tracker_state: dict):
    """Remove score history for tracks that are no longer active."""
    active_tracks = set((tracker_state.get("tracks") or {}).keys())
    stale_ids = [tid for tid in history.keys() if tid not in active_tracks]
    for tid in stale_ids:
        history.pop(tid, None)


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
    _prune_score_history(score_history, tracker_state)

    # ---- Behavior analysis ----
    people, group_metrics = analyze_social_dynamics(people)

    # ---- Temporal smoothing (prevents single-frame noise triggering Speaker) ----
    people = _smooth_scores(people, score_history)

    # ---- Re-run role assignment on smoothed scores ----
    assign_roles(people)

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