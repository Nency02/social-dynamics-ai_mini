import math


LEFT_SHOULDER_INDEX = 5
RIGHT_SHOULDER_INDEX = 6


def calculate_shoulder_angle(person_keypoints):
    """Return torso orientation angle in degrees based on shoulder line."""
    if len(person_keypoints) <= RIGHT_SHOULDER_INDEX:
        return None

    left = person_keypoints[LEFT_SHOULDER_INDEX]
    right = person_keypoints[RIGHT_SHOULDER_INDEX]

    # Missing keypoints are commonly returned as zeros.
    if (left[0] == 0 and left[1] == 0) or (right[0] == 0 and right[1] == 0):
        return None

    dx = float(right[0] - left[0])
    dy = float(right[1] - left[1])
    angle_deg = math.degrees(math.atan2(dy, dx))
    return round(angle_deg, 2)


def _compute_person_center(person):
    """Compute a robust center point used for frame-to-frame matching."""
    bbox = person.get("bbox_xyxy")
    if bbox and len(bbox) == 4:
        x1, y1, x2, y2 = bbox
        return ((float(x1) + float(x2)) / 2.0, (float(y1) + float(y2)) / 2.0)

    keypoints = person.get("keypoints") or []
    if len(keypoints) > RIGHT_SHOULDER_INDEX:
        left = keypoints[LEFT_SHOULDER_INDEX]
        right = keypoints[RIGHT_SHOULDER_INDEX]
        if not ((left[0] == 0 and left[1] == 0) or (right[0] == 0 and right[1] == 0)):
            return ((float(left[0]) + float(right[0])) / 2.0, (float(left[1]) + float(right[1])) / 2.0)

    if keypoints:
        valid = [(float(x), float(y)) for x, y in keypoints if not (x == 0 and y == 0)]
        if valid:
            avg_x = sum(p[0] for p in valid) / len(valid)
            avg_y = sum(p[1] for p in valid) / len(valid)
            return (avg_x, avg_y)

    return None


def _distance(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.hypot(dx, dy)


def _pose_similarity(orientation1, orientation2, angle_threshold_deg=45.0):
    """Check if two orientations are similar (same person likely maintains pose direction)."""
    if orientation1 is None or orientation2 is None:
        return 1.0  # Unknown, assume okay
    
    diff = abs(float(orientation1) - float(orientation2))
    # Handle wraparound (180 and -180 are same)
    if diff > 180:
        diff = 360 - diff
    
    return 1.0 - min(1.0, diff / angle_threshold_deg)


def _compute_match_score(det_center, det_orientation, track_data, position_weight=0.6, pose_weight=0.4):
    """
    Compute match quality: position distance + pose consistency.
    Returns score in [0, 1] where 1 is perfect match.
    """
    if det_center is None or track_data.get("center") is None:
        return 0.0
    
    # Normalize position distance to [0, 1] penalty
    dist = _distance(det_center, track_data["center"])
    max_dist = 250.0  # Beyond this, score is nearly 0
    position_score = max(0.0, 1.0 - (dist / max_dist))
    
    # Pose consistency score
    pose_score = _pose_similarity(det_orientation, track_data.get("orientation_angle_deg"))
    
    # Combined score: favor position but validate pose
    match_score = position_weight * position_score + pose_weight * pose_score
    return match_score


def assign_track_ids(people, tracker_state, max_match_distance=180.0, max_missed_frames=36):
    """
    Assign stable track IDs with pose validation to prevent identity switches.
    
    Improvements:
    - Uses pose (shoulder angle) consistency to reject poor matches
    - Increases missed frame tolerance (36 instead of 24) for longer occlusions
    - Matches by combined score (position + pose) instead of distance alone
    """
    tracks = tracker_state.get("tracks", {})
    next_track_id = tracker_state.get("next_track_id", 0)

    # Backward compatibility with earlier tracker state format.
    if not tracks and tracker_state.get("previous_centers"):
        legacy_centers = tracker_state.get("previous_centers", {})
        tracks = {
            track_id: {"center": center, "orientation_angle_deg": None, "missed": 0}
            for track_id, center in legacy_centers.items()
        }

    detection_centers = []
    detection_orientations = []
    for person in people:
        detection_centers.append(_compute_person_center(person))
        detection_orientations.append(person.get("orientation_angle_deg"))

    # Build all candidate matches by match quality (position + pose)
    candidates = []
    for det_idx, det_center in enumerate(detection_centers):
        if det_center is None:
            continue

        for track_id, track_data in tracks.items():
            score = _compute_match_score(
                det_center, 
                detection_orientations[det_idx],
                track_data,
                position_weight=0.6,
                pose_weight=0.4
            )
            
            # Only consider matches with reasonable score
            if score > 0.15:
                candidates.append((score, det_idx, track_id))

    # Sort by score descending (best matches first)
    candidates.sort(key=lambda x: -x[0])

    matched_detection_to_track = {}
    used_tracks = set()
    for score, det_idx, track_id in candidates:
        if det_idx in matched_detection_to_track or track_id in used_tracks:
            continue
        matched_detection_to_track[det_idx] = track_id
        used_tracks.add(track_id)

    matched_tracks = set()

    for det_idx, person in enumerate(people):
        center = detection_centers[det_idx]
        orientation = detection_orientations[det_idx]
        assigned_track_id = None

        if det_idx in matched_detection_to_track:
            assigned_track_id = matched_detection_to_track[det_idx]
            matched_tracks.add(assigned_track_id)
            if center is not None:
                tracks[assigned_track_id]["center"] = center
            tracks[assigned_track_id]["orientation_angle_deg"] = orientation
            tracks[assigned_track_id]["missed"] = 0

        if assigned_track_id is None:
            assigned_track_id = next_track_id
            next_track_id += 1
            tracks[assigned_track_id] = {
                "center": center,
                "orientation_angle_deg": orientation,
                "missed": 0
            }

        person["track_id"] = int(assigned_track_id)
        if center is not None:
            tracks[assigned_track_id]["center"] = center

    # Keep unmatched tracks alive longer to handle occlusions and re-entry
    active_tracks = {}
    for track_id, track_data in tracks.items():
        if track_id not in matched_tracks:
            track_data["missed"] = int(track_data.get("missed", 0)) + 1

        if int(track_data.get("missed", 0)) <= max_missed_frames:
            active_tracks[track_id] = track_data

    tracker_state["tracks"] = active_tracks
    tracker_state["previous_centers"] = {
        track_id: data["center"]
        for track_id, data in active_tracks.items()
        if data.get("center") is not None
    }
    tracker_state["next_track_id"] = next_track_id
    return people


def extract_keypoints(results):
    people = []

    for r in results:
        if r.keypoints is not None:
            keypoints = r.keypoints.xy.cpu().numpy()
            keypoint_conf = None
            if r.keypoints.conf is not None:
                keypoint_conf = r.keypoints.conf.cpu().numpy()

            boxes_xyxy = None
            boxes_conf = None
            if r.boxes is not None and r.boxes.xyxy is not None:
                boxes_xyxy = r.boxes.xyxy.cpu().numpy()
                boxes_conf = r.boxes.conf.cpu().numpy()

            for i, person in enumerate(keypoints):
                orientation_angle_deg = calculate_shoulder_angle(person)

                bbox_xyxy = None
                confidence = None
                if boxes_xyxy is not None and i < len(boxes_xyxy):
                    bbox_xyxy = boxes_xyxy[i].tolist()
                    confidence = round(float(boxes_conf[i]), 4)

                person_keypoint_conf = None
                if keypoint_conf is not None and i < len(keypoint_conf):
                    person_keypoint_conf = keypoint_conf[i].tolist()

                people.append({
                    "id": i,
                    "bbox_xyxy": bbox_xyxy,
                    "confidence": confidence,
                    "keypoints": person.tolist(),
                    "keypoint_confidence": person_keypoint_conf,
                    "orientation_angle_deg": orientation_angle_deg
                })

    return people