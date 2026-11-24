"""Deterministic 2D scene presentation direction for FitFuel Shorts.

Chooses a visual treatment per scene from narration intent and category.
No 3D, external services, or runtime dependencies.
"""
import re

from visual_engine import classify_scene

STYLES = ("diagram", "stat_card", "comparison", "timeline", "presenter_focus", "broll_focus")

INTENTS = (
    ("comparison", r"\b(but|versus|vs\.?|compared|difference|instead|more than|less than)\b"),
    ("stat_card", r"\b(percent|\d+\s?(?:%|percent)|number|study|research|times|grams?|calories?)\b"),
    ("timeline", r"\b(first|then|next|finally|before|after|process|step|phase)\b"),
    ("diagram", r"\b(why|because|signal|pathway|causes?|leads? to|mechanism|how)\b"),
)

CATEGORY_STYLE = {
    "muscle": "diagram", "nutrition": "stat_card", "heart": "diagram",
    "fat_loss": "comparison", "hydration": "stat_card",
    "exercise": "presenter_focus", "hormones": "diagram", "general": "broll_focus",
}


def _intent(scene):
    text = " ".join(str(scene.get(k, "")) for k in ("narration", "visual_title", "visual_subtitle")).lower()
    for style, pattern in INTENTS:
        if re.search(pattern, text):
            return style
    return None


def direct_scenes(scenes):
    """Return copied scenes with stable style and motion direction metadata."""
    result = []
    previous = None
    count = len(scenes)
    for index, original in enumerate(scenes):
        scene = dict(original)
        category = classify_scene(scene)
        narration = str(scene.get("narration", "")).lower()
        if index == 0:
            style, motion = "hook", "snap_reveal"
        elif index == count - 1:
            style, motion = "payoff", "resolve_hold"
        else:
            style = _intent(scene) or CATEGORY_STYLE.get(category, "broll_focus")
            if style == previous:
                style = next((candidate for candidate in STYLES if candidate != previous and candidate != style), "diagram")
            motion = {
                "diagram": "draw_on", "stat_card": "count_up",
                "comparison": "split_reveal", "timeline": "step_build",
                "presenter_focus": "gesture_emphasis", "broll_focus": "match_cut",
            }[style]
        if index == 0 and not narration:
            motion = "snap_reveal"
        scene["presentation_style"] = style
        scene["motion_cue"] = motion
        scene["scene_role"] = "hook" if index == 0 else ("payoff" if index == count - 1 else "explain")
        result.append(scene)
        previous = style
    return result
