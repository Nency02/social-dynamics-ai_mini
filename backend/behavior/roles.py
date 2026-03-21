"""
Social role classification.

Roles (in rough dominance order):
  Speaker    - most active, gesturing, central; leading the interaction
  Listener   - highly engaged and attentive but not doing most of the talking
  Engaged    - moderate two-way involvement
  Peripheral - present but on the edge of interaction
  Isolated   - far from the group or minimally responsive
"""


def assign_roles(people_with_scores):
    if not people_with_scores:
        return people_with_scores

    # Single-person scenes have no social proximity signal; classify using
    # activity and self-engagement so the label is still meaningful.
    if len(people_with_scores) == 1:
        p = people_with_scores[0]
        engagement = p.get("engagement_score", 0.0)
        dominance = p.get("dominance_score", 0.0)
        activity = p.get("activity_score", 0.0)

        # LOWERED THRESHOLDS: Was 0.30, 0.28, 0.22 - now more permissive
        if activity >= 0.10 or dominance >= 0.10 or engagement >= 0.08:
            p["social_role"] = "Engaged"
        else:
            p["social_role"] = "Peripheral"
        return people_with_scores

    # Rank by speaking propensity, not dominance alone.
    ranked = sorted(
        people_with_scores,
        key=lambda p: (
            0.50 * p.get("dominance_score", 0.0)
            + 0.30 * p.get("activity_score", 0.0)
            + 0.20 * p.get("engagement_score", 0.0)
        ),
        reverse=True,
    )

    speaker_ids = set()
    if ranked:
        top = ranked[0]
        top_dom = top.get("dominance_score", 0.0)
        top_act = top.get("activity_score", 0.0)
        top_eng = top.get("engagement_score", 0.0)

        # Speaker requires clear evidence, not just slight movement.
        if (top_dom >= 0.24 and top_act >= 0.22) or (top_dom >= 0.20 and top_eng >= 0.28):
            speaker_ids.add(top.get("track_id"))

        # Add a second speaker only when truly comparable.
        if len(ranked) > 1 and speaker_ids:
            second = ranked[1]
            second_prop = (
                0.50 * second.get("dominance_score", 0.0)
                + 0.30 * second.get("activity_score", 0.0)
                + 0.20 * second.get("engagement_score", 0.0)
            )
            top_prop = (
                0.50 * top_dom
                + 0.30 * top_act
                + 0.20 * top_eng
            )
            if second_prop >= max(0.26, top_prop - 0.05):
                speaker_ids.add(second.get("track_id"))

    for person in people_with_scores:
        if person.get("track_id") in speaker_ids:  # Check if in speaker_ids set
            person["social_role"] = "Speaker"
            continue

        engagement = person.get("engagement_score", 0.0)
        dominance = person.get("dominance_score", 0.0)
        activity = person.get("activity_score", 0.0)
        features = person.get("behavior_features", {})
        proximity = features.get("proximity_density", 0.0)
        centrality = features.get("group_centrality", 0.5)

        if proximity < 0.05 or centrality < 0.08:
            person["social_role"] = "Isolated"
        elif engagement >= 0.18 and activity < 0.20:
            person["social_role"] = "Listener"
        elif engagement >= 0.20 or activity >= 0.22 or dominance >= 0.18:
            person["social_role"] = "Engaged"
        else:
            person["social_role"] = "Peripheral"

    return people_with_scores