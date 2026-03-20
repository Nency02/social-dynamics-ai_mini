from src.behavior.features import build_behavior_features
from src.behavior.roles import assign_roles


def _c(v):
    return max(0.0, min(1.0, float(v)))


def _r4(v):
    return round(float(v), 4)


def analyze_social_dynamics(people):
    """
    Compute per-person behavioral scores and group-level metrics.

    Returns
    -------
    people        : list[dict]  - each person augmented with score fields
    group_metrics : dict        - cohesion, spread, avg_engagement, etc.
    """
    if not people:
        return people, {
            "group_cohesion": 0.0,
            "group_spread": 0.0,
            "avg_engagement": 0.0,
            "num_people": 0,
        }

    feature_rows = build_behavior_features(people)
    fmap = {row["track_id"]: row for row in feature_rows}

    engagement_scores = []
    dominance_scores = []

    for person in people:
        f = fmap.get(person.get("track_id"), {})

        gesture = f.get("gesture_activity", 0.0)
        arm_spread = f.get("arm_spread", 0.0)
        facing = f.get("facing_engagement", 0.0)
        proximity = f.get("proximity_density", 0.0)
        centrality = f.get("group_centrality", 0.0)
        dist_close = 1.0 - f.get("group_distance", 1.0)
        body_lean = f.get("body_lean", 0.0)

        engagement_score = _c(
            0.25 * facing
            + 0.20 * dist_close
            + 0.25 * gesture          # Boosted from 0.15 to emphasize talking/gesturing
            + 0.15 * proximity
            + 0.15 * centrality
        )

        dominance_score = _c(
            0.60 * gesture            # Boosted from 0.50 - gesture is key for speaker
            + 0.15 * arm_spread       # Reduced from 0.20
            + 0.10 * centrality       # Reduced from 0.15
            + 0.10 * facing
            + 0.05 * dist_close
        )

        activity_score = _c(
            0.50 * gesture
            + 0.30 * arm_spread
            + 0.20 * body_lean
        )

        participation_score = _c((engagement_score + dominance_score) / 2.0)

        person["behavior_features"] = f
        person["engagement_score"] = _r4(engagement_score)
        person["dominance_score"] = _r4(dominance_score)
        person["activity_score"] = _r4(activity_score)
        person["participation_score"] = _r4(participation_score)

        engagement_scores.append(engagement_score)
        dominance_scores.append(dominance_score)

    assign_roles(people)

    n = len(engagement_scores)
    avg_eng = sum(engagement_scores) / n if n else 0.0

    if n > 1:
        variance = sum((e - avg_eng) ** 2 for e in engagement_scores) / n
        cohesion = _c(avg_eng * (1.0 - min(1.0, variance * 4.0)))
    else:
        cohesion = avg_eng

    spread_values = [
        fmap.get(p.get("track_id"), {}).get("group_distance", 0.5)
        for p in people
    ]
    group_spread = _c(sum(spread_values) / len(spread_values)) if spread_values else 0.0

    group_metrics = {
        "group_cohesion": _r4(cohesion),
        "group_spread": _r4(group_spread),
        "avg_engagement": _r4(avg_eng),
        "num_people": n,
    }

    return people, group_metrics