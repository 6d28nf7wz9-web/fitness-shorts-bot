"""Deterministic scene-source routing for FitFuel Shorts.

Scientific mechanisms go to Blender; observable real-world actions go to stock.
ArtCraft is a bounded last-resort only for real-world B-roll that stock cannot
cover. This router makes no network calls and never spends generation credits.
"""
import re

from visual_engine import classify_scene

BLENDER_CATEGORIES = {
    "anatomy", "muscle", "protein", "heart", "fat_loss", "hydration",
    "hormones", "creatine", "supplements", "tracking", "recovery",
    "nutrition",
}
STOCK_CUES = re.compile(
    r"\b(show|watch|perform|doing|demonstrat\w*|technique|form|"
    r"squat|deadlift|curl|press|lunge|push[- ]?up|pull[- ]?up|"
    r"cooking|chopping|meal prep|eating|walking|running|cycling)\b",
    re.I,
)


def route_scene(scene):
    """Return blender, stock, or stock_then_artcraft with an auditable reason."""
    category = classify_scene(scene)
    text = " ".join(str(scene.get(key, "")) for key in (
        "visual_title", "visual_subtitle", "visual_instruction",
        "keyword", "narration",
    ))
    declared = str(scene.get("visual_type", "")).lower()
    if declared in {"muscle_anatomy", "protein_synthesis", "energy_metabolism",
                    "hydration", "recovery_sleep", "digestion_fiber"}:
        return {"source": "blender", "category": category,
                "reason": "explicit scientific visual type"}
    if category in BLENDER_CATEGORIES and not STOCK_CUES.search(text):
        return {"source": "blender", "category": category,
                "reason": "spoken beat explains a biological or scientific mechanism"}
    if STOCK_CUES.search(text) or category == "exercise":
        return {"source": "stock_then_artcraft", "category": category,
                "reason": "spoken beat is best shown as an observable real-world action"}
    if category in BLENDER_CATEGORIES:
        return {"source": "blender", "category": category,
                "reason": "scientific concept requires a controlled explanatory visual"}
    return {"source": "stock_then_artcraft", "category": category,
            "reason": "real-world footage is preferred for this general scene"}
