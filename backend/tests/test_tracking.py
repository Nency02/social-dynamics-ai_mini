"""
Tests for tracking stability and preventing cross-person behavior attribution.
"""

import math
from vision.keypoints import assign_track_ids, _compute_person_center, _distance, _pose_similarity
from behavior.features import build_behavior_features


def create_mock_person(track_id, center_x, center_y, orientation_angle=0.0, gesture_activity=0.0):
    """Create a mock person for testing."""
    # Create 17 keypoints (COCO format)
    keypoints = [[0, 0] for _ in range(17)]
    
    # Set shoulder positions for orientation
    left_sh_idx, right_sh_idx = 5, 6
    keypoints[left_sh_idx] = [center_x - 15, center_y]
    keypoints[right_sh_idx] = [center_x + 15, center_y]
    
    # Set arm keypoints to encode gesture activity
    if gesture_activity > 0.5:
        # Raised arms = hand above shoulder
        keypoints[9] = [center_x - 10, center_y - 30]  # left wrist
        keypoints[10] = [center_x + 10, center_y - 30]  # right wrist
    else:
        # Lowered arms
        keypoints[9] = [center_x - 10, center_y + 40]
        keypoints[10] = [center_x + 10, center_y + 40]
    
    # Set nose for facing
    keypoints[0] = [center_x, center_y - 20]
    
    return {
        "track_id": track_id,
        "bbox_xyxy": [center_x - 30, center_y - 40, center_x + 30, center_y + 60],
        "keypoints": keypoints,
        "orientation_angle_deg": orientation_angle,
    }


def test_track_persistence_on_out_of_frame():
    """Ensure track ID persists when person temporarily leaves frame."""
    tracker_state = {"next_track_id": 0, "tracks": {}, "previous_centers": {}}
    
    # Frame 1: Person at (100, 100)
    people_frame1 = [create_mock_person(None, 100, 100, orientation_angle=30.0)]
    result = assign_track_ids(people_frame1, tracker_state)
    track_id_frame1 = result[0]["track_id"]
    assert track_id_frame1 == 0
    
    # Frame 2-20: Person out of frame
    for _ in range(20):
        result = assign_track_ids([], tracker_state)
    
    # Frame 21: Person re-enters at (100, 105) - should keep ID 0
    people_frame21 = [create_mock_person(None, 100, 105, orientation_angle=31.0)]
    result = assign_track_ids(people_frame21, tracker_state)
    track_id_reentry = result[0]["track_id"]
    
    assert track_id_reentry == track_id_frame1, \
        f"Track ID changed after re-entry: was {track_id_frame1}, now {track_id_reentry}"


def test_no_cross_identification_when_people_swap():
    """Prevent track swaps when two people pass each other."""
    tracker_state = {"next_track_id": 0, "tracks": {}, "previous_centers": {}}
    
    # Frame 1: Person A at (100, 100), Person B at (200, 100)
    person_a = create_mock_person(None, 100, 100, orientation_angle=0.0)
    person_b = create_mock_person(None, 200, 100, orientation_angle=180.0)
    result = assign_track_ids([person_a, person_b], tracker_state)
    
    id_a_frame1 = next(p for p in result if abs(p["bbox_xyxy"][0] - 70) < 5)["track_id"]
    id_b_frame1 = next(p for p in result if abs(p["bbox_xyxy"][0] - 170) < 5)["track_id"]
    
    # Frame 2: They've moved closer but NOT swapped (still same people)
    person_a_moved = create_mock_person(None, 120, 100, orientation_angle=5.0)
    person_b_moved = create_mock_person(None, 180, 100, orientation_angle=175.0)
    result = assign_track_ids([person_a_moved, person_b_moved], tracker_state)
    
    id_a_frame2 = next(p for p in result if abs(p["bbox_xyxy"][0] - 90) < 5)["track_id"]
    id_b_frame2 = next(p for p in result if abs(p["bbox_xyxy"][0] - 150) < 5)["track_id"]
    
    # IDs should be stable despite proximity
    assert id_a_frame2 == id_a_frame1, "Person A track ID changed during movement"
    assert id_b_frame2 == id_b_frame1, "Person B track ID changed during movement"


def test_gesture_not_attributed_to_nearby_person():
    """Ensure gesture from person A doesn't get attributed to nearby person B."""
    # Person A with raised arms (gesture_activity=1.0)
    person_a = create_mock_person(track_id=0, center_x=100, center_y=100, gesture_activity=1.0)
    
    # Person B right next to A, arms down (gesture_activity=0.0)
    person_b = create_mock_person(track_id=1, center_x=140, center_y=100, gesture_activity=0.0)
    
    # Build features for both
    features = build_behavior_features([person_a, person_b])
    
    # Find features for each person
    feat_a = next(f for f in features if f["track_id"] == 0)
    feat_b = next(f for f in features if f["track_id"] == 1)
    
    # Person A should have high gesture activity
    assert feat_a["gesture_activity"] > 0.5, \
        f"Person A gesture_activity too low: {feat_a['gesture_activity']}"
    
    # Person B should have low gesture activity (not inherit from A)
    assert feat_b["gesture_activity"] < 0.3, \
        f"Person B wrongly attributed gesture from A: {feat_b['gesture_activity']}"


def test_pose_similarity_computation():
    """Verify pose similarity correctly rejects mismatched people."""
    # Same orientation (0 degrees)
    sim_same = _pose_similarity(0.0, 5.0, angle_threshold_deg=45.0)
    assert sim_same > 0.8, f"Similar poses should score high: {sim_same}"
    
    # Opposite orientations (0 vs 180)
    sim_opposite = _pose_similarity(0.0, 180.0, angle_threshold_deg=45.0)
    assert sim_opposite < 0.3, f"Opposite poses should score low: {sim_opposite}"
    
    # Wraparound: 179 vs -179 should be similar
    sim_wraparound = _pose_similarity(179.0, -179.0, angle_threshold_deg=45.0)
    assert sim_wraparound > 0.8, f"Wraparound poses should match: {sim_wraparound}"


def test_distance_to_same_person_is_low():
    """Verify centroid distance is correctly computed."""
    tracker_state = {"next_track_id": 0, "tracks": {}, "previous_centers": {}}
    
    # Frame 1: Person at (100, 100)
    person = create_mock_person(None, 100, 100)
    assign_track_ids([person], tracker_state)
    
    # Frame 2: Same person moves slightly to (102, 101)
    person_moved = create_mock_person(None, 102, 101)
    result = assign_track_ids([person_moved], tracker_state)
    
    # Should still have same track ID
    assert result[0]["track_id"] == 0, "Same person should retain track ID despite small movement"
