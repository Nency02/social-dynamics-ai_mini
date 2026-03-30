import math

# COCO keypoint indices
NOSE_INDEX = 0
LEFT_EYE_INDEX = 1
RIGHT_EYE_INDEX = 2
LEFT_SHOULDER_INDEX = 5
RIGHT_SHOULDER_INDEX = 6
LEFT_ELBOW_INDEX = 7
RIGHT_ELBOW_INDEX = 8
LEFT_WRIST_INDEX = 9
RIGHT_WRIST_INDEX = 10
LEFT_HIP_INDEX = 11
RIGHT_HIP_INDEX = 12


def _is_valid(pt):
    return pt is not None and len(pt) >= 2 and not (pt[0] == 0 and pt[1] == 0)


def _dist(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _normalize(v, lo, hi):
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (float(v) - lo) / (hi - lo)))


def _person_center(person):
    bbox = person.get("bbox_xyxy")
    if bbox and len(bbox) == 4:
        return (
            (float(bbox[0]) + float(bbox[2])) / 2.0,
            (float(bbox[1]) + float(bbox[3])) / 2.0,
        )

    kps = person.get("keypoints") or []
    valid = [(float(x), float(y)) for x, y in kps if not (x == 0 and y == 0)]
    if not valid:
        return None
    return (
        sum(p[0] for p in valid) / len(valid),
        sum(p[1] for p in valid) / len(valid),
    )


def _shoulder_midpoint(kps):
    if len(kps) <= RIGHT_SHOULDER_INDEX:
        return None
    left = kps[LEFT_SHOULDER_INDEX]
    right = kps[RIGHT_SHOULDER_INDEX]
    if not (_is_valid(left) and _is_valid(right)):
        return None
    return (
        (float(left[0]) + float(right[0])) / 2.0,
        (float(left[1]) + float(right[1])) / 2.0,
    )


def _gesture_activity(kps):
    if len(kps) <= RIGHT_WRIST_INDEX:
        return 0.0

    score, votes = 0.0, 0
    pairs = [
        (LEFT_SHOULDER_INDEX, LEFT_WRIST_INDEX),
        (RIGHT_SHOULDER_INDEX, RIGHT_WRIST_INDEX),
    ]
    for sh_idx, wr_idx in pairs:
        shoulder = kps[sh_idx] if len(kps) > sh_idx else None
        wrist = kps[wr_idx]
        if _is_valid(shoulder) and _is_valid(wrist):
            votes += 1
            delta_y = float(shoulder[1]) - float(wrist[1])
            if delta_y > 0:
                score += 1.0
            elif delta_y > -40:
                score += 0.4
    return score / float(votes) if votes else 0.0


def _arm_spread(kps):
    if len(kps) <= RIGHT_WRIST_INDEX:
        return 0.0

    left_shoulder = kps[LEFT_SHOULDER_INDEX] if len(kps) > LEFT_SHOULDER_INDEX else None
    right_shoulder = kps[RIGHT_SHOULDER_INDEX] if len(kps) > RIGHT_SHOULDER_INDEX else None
    left_wrist = kps[LEFT_WRIST_INDEX]
    right_wrist = kps[RIGHT_WRIST_INDEX]

    if not (_is_valid(left_shoulder) and _is_valid(right_shoulder)):
        return 0.0

    shoulder_width = _dist(left_shoulder, right_shoulder)
    if shoulder_width < 5:
        return 0.0

    total, count = 0.0, 0
    if _is_valid(left_wrist):
        total += abs(float(left_wrist[0]) - float(left_shoulder[0]))
        count += 1
    if _is_valid(right_wrist):
        total += abs(float(right_wrist[0]) - float(right_shoulder[0]))
        count += 1

    return _normalize(total / count, 0, shoulder_width * 1.5) if count else 0.0


def _body_lean(kps):
    if len(kps) <= RIGHT_SHOULDER_INDEX:
        return 0.0
    left = kps[LEFT_SHOULDER_INDEX]
    right = kps[RIGHT_SHOULDER_INDEX]
    if not (_is_valid(left) and _is_valid(right)):
        return 0.0

    angle_deg = abs(
        math.degrees(
            math.atan2(float(right[1]) - float(left[1]), float(right[0]) - float(left[0]))
        )
    )
    return min(1.0, angle_deg / 45.0)


def _head_tilt(kps):
    if len(kps) <= RIGHT_EYE_INDEX:
        return 0.0
    left_eye = kps[LEFT_EYE_INDEX]
    right_eye = kps[RIGHT_EYE_INDEX]
    if not (_is_valid(left_eye) and _is_valid(right_eye)):
        return 0.0

    angle = abs(
        math.degrees(
            math.atan2(
                float(right_eye[1]) - float(left_eye[1]),
                float(right_eye[0]) - float(left_eye[0]),
            )
        )
    )
    return _normalize(angle, 0, 30)


def _facing_engagement(person, people):
    """
    Compute how much a person is oriented toward the group center.
    Prevents cross-identification by only considering valid keypoints from THIS person's skeleton.
    """
    kps = person.get("keypoints") or []
    if not kps:
        return 0.0

    nose = kps[NOSE_INDEX] if len(kps) > NOSE_INDEX else None
    shoulder_mid = _shoulder_midpoint(kps)
    if not (_is_valid(nose) and shoulder_mid is not None):
        return 0.0

    # Facing direction is ONLY from this person's nose and shoulders
    facing = (float(nose[0]) - shoulder_mid[0], float(nose[1]) - shoulder_mid[1])
    facing_norm = math.hypot(*facing)
    if facing_norm < 1e-6:
        return 0.0

    center = _person_center(person)
    if center is None:
        return 0.0

    alignments = []
    for other in people:
        if other.get("track_id") == person.get("track_id"):
            continue
        other_center = _person_center(other)
        if other_center is None:
            continue

        to_other = (other_center[0] - center[0], other_center[1] - center[1])
        d = math.hypot(*to_other)
        if d < 1e-6:
            continue

        cosine = (facing[0] * to_other[0] + facing[1] * to_other[1]) / (facing_norm * d)
        alignments.append(max(0.0, cosine))

    return sum(alignments) / len(alignments) if alignments else 0.0


def _proximity_density(person_idx, centers, threshold=220.0):
    center = centers[person_idx]
    if center is None:
        return 0.0

    nearby = sum(
        1
        for i, other_center in enumerate(centers)
        if i != person_idx and other_center is not None and _dist(center, other_center) <= threshold
    )
    max_possible = max(1, len(centers) - 1)
    return nearby / max_possible


def _group_centrality(person_idx, centers):
    valid = [c for c in centers if c is not None]
    if len(valid) < 2:
        return 1.0

    group_center = (
        sum(c[0] for c in valid) / len(valid),
        sum(c[1] for c in valid) / len(valid),
    )
    center = centers[person_idx]
    if center is None:
        return 0.0

    max_d = max(_dist(v, group_center) for v in valid)
    if max_d < 1e-6:
        return 1.0

    return 1.0 - _normalize(_dist(center, group_center), 0, max_d)


def build_behavior_features(people):
    if not people:
        return []

    centers = [_person_center(person) for person in people]

    pairwise = [
        _dist(centers[i], centers[j])
        for i in range(len(centers))
        for j in range(i + 1, len(centers))
        if centers[i] is not None and centers[j] is not None
    ]
    scene_scale = max(max(pairwise), 200.0) if pairwise else 400.0

    features = []
    for idx, person in enumerate(people):
        kps = person.get("keypoints") or []
        center = centers[idx]

        dists = [
            _dist(center, centers[j])
            for j in range(len(centers))
            if j != idx and centers[j] is not None and center is not None
        ]
        mean_dist = sum(dists) / len(dists) if dists else scene_scale

        features.append(
            {
                "track_id": person.get("track_id"),
                "orientation_angle_deg": person.get("orientation_angle_deg"),
                "gesture_activity": round(_gesture_activity(kps), 4),
                "arm_spread": round(_arm_spread(kps), 4),
                "body_lean": round(_body_lean(kps), 4),
                "head_tilt": round(_head_tilt(kps), 4),
                "facing_engagement": round(_facing_engagement(person, people), 4),
                "group_distance": round(_normalize(mean_dist, 0, scene_scale), 4),
                "proximity_density": round(_proximity_density(idx, centers), 4),
                "group_centrality": round(_group_centrality(idx, centers), 4),
            }
        )

    return features