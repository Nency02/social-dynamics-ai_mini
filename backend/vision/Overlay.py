"""
visualization/overlay.py
Rich visual overlay for the Social Dynamics AI pipeline.

Renders:
  - Colour-coded bounding boxes per social role
  - Per-person label (Track-ID + Role) with opaque background
  - Three mini score-bars (Engagement / Dominance / Activity)
  - Engagement connection lines between attentive pairs
  - Semi-transparent HUD panel (top-left) with group metrics
  - Role legend (bottom-left)
"""

import cv2


ROLE_COLORS = {
    "Speaker": (50, 50, 230),
    "Listener": (50, 200, 50),
    "Engaged": (200, 200, 40),
    "Peripheral": (30, 165, 230),
    "Isolated": (120, 120, 120),
    "Unknown": (180, 180, 180),
}

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FONT_AA = cv2.LINE_AA


def _bar(img, x, y, w, h, value, color, bg=(40, 40, 40)):
    """Draw a filled progress bar."""
    cv2.rectangle(img, (x, y), (x + w, y + h), bg, -1)
    filled = int(w * max(0.0, min(1.0, float(value))))
    if filled > 0:
        cv2.rectangle(img, (x, y), (x + filled, y + h), color, -1)


def _text_bg(img, text, origin, font_scale, color, thickness, bg_color, pad=3):
    """Draw text with a filled rectangle background."""
    (tw, th), baseline = cv2.getTextSize(text, _FONT, font_scale, thickness)
    ox, oy = origin
    cv2.rectangle(
        img,
        (ox - pad, oy - th - pad),
        (ox + tw + pad, oy + baseline + pad),
        bg_color,
        -1,
    )
    cv2.putText(img, text, (ox, oy), _FONT, font_scale, color, thickness, _FONT_AA)


def draw_person(frame, person):
    bbox = person.get("bbox_xyxy")
    if bbox is None:
        return

    x1, y1 = int(bbox[0]), int(bbox[1])
    x2, y2 = int(bbox[2]), int(bbox[3])

    track_id = person.get("track_id", "?")
    role = person.get("social_role", "Unknown")
    confidence = person.get("confidence", None)
    engagement = person.get("engagement_score", 0.0)
    dominance = person.get("dominance_score", 0.0)
    activity = person.get("activity_score", 0.0)

    color = ROLE_COLORS.get(role, ROLE_COLORS["Unknown"])
    thickness = 3 if role == "Speaker" else 2

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    conf_txt = f" {confidence:.2f}" if isinstance(confidence, (float, int)) else ""
    label = f"#{track_id}  {role}{conf_txt}"
    lbl_y = max(y1 - 6, 20)
    _text_bg(frame, label, (x1, lbl_y), 0.52, (255, 255, 255), 2, color)

    bar_top = y1 + 8
    bar_w = 46
    bar_h = 7
    gap = 14

    bars = [
        ("Eng", engagement, (50, 200, 50)),
        ("Dom", dominance, (50, 50, 220)),
        ("Act", activity, (200, 160, 40)),
    ]
    for i, (lbl, val, bcol) in enumerate(bars):
        bx = x1 + 4 + i * (bar_w + gap)
        cv2.putText(frame, lbl, (bx, bar_top + bar_h - 1), _FONT, 0.32, bcol, 1, _FONT_AA)
        _bar(frame, bx + 10, bar_top, bar_w, bar_h, val, bcol)


def draw_connections(frame, people, threshold=0.42):
    """
    Draw a line between two people when both have engagement >= threshold.
    Line opacity encodes average engagement strength.
    """
    centers = []
    for p in people:
        bbox = p.get("bbox_xyxy")
        if bbox:
            cx = int((float(bbox[0]) + float(bbox[2])) / 2)
            cy = int((float(bbox[1]) + float(bbox[3])) / 2)
            centers.append((cx, cy, p.get("engagement_score", 0.0)))
        else:
            centers.append(None)

    overlay = frame.copy()
    for i in range(len(people)):
        for j in range(i + 1, len(people)):
            if centers[i] is None or centers[j] is None:
                continue
            ei, ej = centers[i][2], centers[j][2]
            if ei >= threshold and ej >= threshold:
                strength = (ei + ej) / 2.0
                alpha = int(80 + 120 * strength)
                color = (alpha, alpha, 40)
                cv2.line(overlay, centers[i][:2], centers[j][:2], color, 1, _FONT_AA)

    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)


def draw_hud(frame, group_metrics, fps=None):
    cohesion = group_metrics.get("group_cohesion", 0.0)
    spread = group_metrics.get("group_spread", 0.0)
    avg_eng = group_metrics.get("avg_engagement", 0.0)
    num_people = group_metrics.get("num_people", 0)

    px, py = 10, 10
    pw, ph = 230, 120

    overlay = frame.copy()
    cv2.rectangle(overlay, (px, py), (px + pw, py + ph), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    cv2.rectangle(frame, (px, py), (px + pw, py + ph), (80, 80, 80), 1)

    ty = py + 18
    cv2.putText(frame, "SOCIAL  DYNAMICS  AI", (px + 8, ty), _FONT, 0.44, (210, 210, 210), 1, _FONT_AA)

    ty += 18
    cv2.putText(frame, f"People: {num_people}", (px + 8, ty), _FONT, 0.42, (170, 170, 170), 1, _FONT_AA)
    if fps is not None:
        cv2.putText(frame, f"FPS: {fps:.1f}", (px + 135, ty), _FONT, 0.42, (170, 170, 170), 1, _FONT_AA)

    metrics = [
        ("Cohesion", cohesion, (50, 200, 50)),
        ("Spread", spread, (200, 120, 50)),
        ("Engagement", avg_eng, (50, 200, 200)),
    ]
    for label, val, color in metrics:
        ty += 20
        cv2.putText(frame, label, (px + 8, ty + 7), _FONT, 0.38, (150, 150, 150), 1, _FONT_AA)
        _bar(frame, px + 82, ty, 140, 10, val, color)
        cv2.putText(frame, f"{val:.2f}", (px + 226, ty + 9), _FONT, 0.35, color, 1, _FONT_AA)


def draw_legend(frame):
    h = frame.shape[0]
    x, y = 10, h - 10

    for role, color in reversed(list(ROLE_COLORS.items())):
        if role == "Unknown":
            continue
        (_, th), _ = cv2.getTextSize(role, _FONT, 0.38, 1)
        y -= th + 7
        cv2.rectangle(frame, (x, y - 1), (x + 12, y + th - 2), color, -1)
        cv2.putText(frame, role, (x + 16, y + th - 3), _FONT, 0.38, (210, 210, 210), 1, _FONT_AA)


def render_frame(frame, people, group_metrics, fps=None):
    """
    Full render pass. Mutates frame in place and returns it.

    Order: connections (background) -> per-person -> HUD -> legend.
    """
    if people:
        draw_connections(frame, people)
        for person in people:
            draw_person(frame, person)

    draw_hud(frame, group_metrics, fps=fps)
    draw_legend(frame)
    return frame
