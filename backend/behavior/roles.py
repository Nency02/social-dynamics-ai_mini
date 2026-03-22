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

    # Single-person scenes have no social proximity signal; classify from
    # self-expressiveness so solo speaking can still be detected.
    if len(people_with_scores) == 1:
        p = people_with_scores[0]
        engagement = p.get("engagement_score", 0.0)
        dominance = p.get("dominance_score", 0.0)
        activity = p.get("activity_score", 0.0)

        if activity >= 0.18 or dominance >= 0.18:
            p["social_role"] = "Speaker"
        elif activity >= 0.10 or dominance >= 0.10 or engagement >= 0.08:
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

    def _speaking_evidence(person):
        features = person.get("behavior_features", {})
        dom = person.get("dominance_score", 0.0)
        act = person.get("activity_score", 0.0)
        eng = person.get("engagement_score", 0.0)
        gesture = features.get("gesture_activity", 0.0)
        arm_spread = features.get("arm_spread", 0.0)
        body_lean = features.get("body_lean", 0.0)

        # Require live visible speaking cues to avoid stale "Speaker" labels.
        visibly_speaking = (
            act >= 0.24
            and (
                gesture >= 0.20
                or arm_spread >= 0.25
                or (gesture >= 0.14 and body_lean >= 0.35)
            )
        )

        propensity = (
            0.45 * dom
            + 0.25 * act
            + 0.15 * gesture
            + 0.10 * arm_spread
            + 0.05 * eng
        )
        return visibly_speaking, propensity

    speaker_ids = set()
    if ranked:
        evidence = []
        for p in ranked:
            visible, propensity = _speaking_evidence(p)
            evidence.append((p, visible, propensity))

        top_prop = evidence[0][2]

        # Primary rule: choose up to two people with live speaking cues and
        # propensity close to the top speaker in this frame.
        visible_candidates = [
            item
            for item in evidence
            if item[1] and item[2] >= 0.18 and (top_prop - item[2]) <= 0.08
        ]
        for p, _, _ in visible_candidates[:2]:
            speaker_ids.add(p.get("track_id"))

        # Backup rule: if no strong visible cues, avoid forcing a speaker too
        # early; only mark one when confidence is clearly high.
        if not speaker_ids:
            top_person, top_visible, top_prop = evidence[0]
            next_prop = evidence[1][2] if len(evidence) > 1 else 0.0
            top_gap = top_prop - next_prop

            if top_prop >= 0.28 and (top_visible or top_gap >= 0.07):
                speaker_ids.add(top_person.get("track_id"))

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