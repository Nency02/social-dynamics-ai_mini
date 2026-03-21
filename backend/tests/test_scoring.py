from behavior.scoring import analyze_social_dynamics


def test_analyze_social_dynamics_empty_people_returns_zero_metrics():
    people, group_metrics = analyze_social_dynamics([])

    assert people == []
    assert group_metrics == {
        "group_cohesion": 0.0,
        "group_spread": 0.0,
        "avg_engagement": 0.0,
        "num_people": 0,
    }


def test_avg_participation_uses_all_people(monkeypatch):
    # Keep role assignment deterministic and focused on score aggregation.
    monkeypatch.setattr("behavior.scoring.assign_roles", lambda people: people)
    monkeypatch.setattr(
        "behavior.scoring.build_behavior_features",
        lambda people: [
            {
                "track_id": 1,
                "gesture_activity": 1.0,
                "arm_spread": 1.0,
                "facing_engagement": 1.0,
                "proximity_density": 1.0,
                "group_centrality": 1.0,
                "group_distance": 0.0,
                "body_lean": 1.0,
                "head_tilt": 1.0,
            },
            {
                "track_id": 2,
                "gesture_activity": 0.0,
                "arm_spread": 0.0,
                "facing_engagement": 0.0,
                "proximity_density": 0.0,
                "group_centrality": 0.0,
                "group_distance": 1.0,
                "body_lean": 0.0,
                "head_tilt": 0.0,
            },
        ],
    )

    people = [{"track_id": 1}, {"track_id": 2}]
    scored_people, group_metrics = analyze_social_dynamics(people)

    p1 = next(p for p in scored_people if p["track_id"] == 1)["participation_score"]
    p2 = next(p for p in scored_people if p["track_id"] == 2)["participation_score"]

    expected_avg = round((p1 + p2) / 2, 4)
    assert group_metrics["avg_participation"] == expected_avg
