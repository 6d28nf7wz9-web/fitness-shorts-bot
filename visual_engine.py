"""Scene-specific, dependency-free science diagrams for FitFuel Shorts."""
import html
import re

CATEGORIES = {
    "muscle": ("MUSCLE FIBER ADAPTATION", ["MECHANICAL TENSION", "REPAIR", "GROWTH"]),
    "nutrition": ("NUTRIENT PATHWAY", ["FOOD", "ABSORPTION", "FUEL"]),
    "heart": ("CARDIOVASCULAR FLOW", ["OXYGEN IN", "PUMP", "DELIVERY"]),
    "fat_loss": ("ENERGY BALANCE", ["ENERGY IN", "STORAGE", "ENERGY OUT"]),
    "hydration": ("HYDRATION & ELECTROLYTES", ["FLUID", "BALANCE", "PERFORMANCE"]),
    "exercise": ("MOVEMENT MECHANICS", ["LOAD", "JOINT", "MOTION"]),
    "hormones": ("HORMONE SIGNALING", ["SIGNAL", "RECEPTOR", "RESPONSE"]),
    "supplements": ("SUPPLEMENT EVIDENCE", ["DOSE", "EVIDENCE", "EXPECTATION"]),
    "general": ("THE SCIENCE", ["INPUT", "PROCESS", "RESULT"]),
}

RULES = [
    ("supplements", r"\b(?:supplement\w*|creatine|caffeine|pre[- ]?workout|protein powder|ergogenic aid)\b"),
    ("hydration", r"\b(?:hydration|dehydrat\w*|electrolyte\w*|sodium|potassium|fluid balance)\b"),
    ("heart", r"\b(?:heart|blood|circulation|cardiovascular|oxygen delivery|pulse|blood pressure)\b"),
    ("hormones", r"\b(?:hormone\w*|insulin|cortisol|testosterone|estrogen|ghrelin|leptin|receptor|thyroid)\b"),
    ("fat_loss", r"\b(?:fat loss|fat gain|calorie\w*|energy balance|burn fat|weight loss|calorie deficit)\b"),
    ("muscle", r"\b(?:muscle\w*|muscle fiber\w*|hypertrophy|strength|progressive overload|protein synthesis|muscle recovery)\b"),
    ("nutrition", r"\b(?:food|meal|nutrition|digest\w*|absorption|dietary fiber|carbohydrate\w*|protein intake|nutrient\w*)\b"),
    ("exercise", r"\b(?:exercise|squat|deadlift|curl|press|repetition|workout|training|joint|movement mechanics)\b"),
]


def classify_scene(scene):
    """Classify from authored scene intent first; broad stock-search keywords are fallback only."""
    fields = (
        ("visual_title", "visual_subtitle"),
        ("narration",),
        ("keyword",),
    )
    for group in fields:
        source = " ".join(str(scene.get(k, "")) for k in group).lower()
        for category, pattern in RULES:
            if re.search(pattern, source):
                return category
    return "general"

