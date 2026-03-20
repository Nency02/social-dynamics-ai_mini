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

    ranked = sorted(
        people_with_scores,
        key=lambda p: p.get("dominance_score", 0.0),
        reverse=True,
    )

    # NEW APPROACH: Anyone above threshold is a Speaker (not just #1)
    # This allows multiple people to be "Speakers" if they're both actively speaking
    speaker_ids = set()
    for person in ranked:
        dominance = person.get("dominance_score", 0.0)
        if dominance >= 0.12:  # Absolute threshold for being a speaker
            speaker_ids.add(person.get("track_id"))

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

        # LOWERED THRESHOLDS for better classroom detection
        if proximity < 0.05 or centrality < 0.08:  # Was 0.12 and 0.18
            person["social_role"] = "Isolated"
        elif engagement >= 0.18 and activity < 0.10:  # Was 0.42 and 0.22
            person["social_role"] = "Listener"
        elif engagement >= 0.15 or dominance >= 0.12:  # Was 0.36 and 0.32
            person["social_role"] = "Engaged"
        else:
            person["social_role"] = "Peripheral"

    return people_with_scores