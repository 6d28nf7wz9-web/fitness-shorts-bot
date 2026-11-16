"""Analytics-driven topic and hook intelligence for FitFuel Shorts.

This module deliberately treats the channel's measured results as directional
signals, not causal evidence or a prediction of YouTube distribution.
"""
import math
import re
from datetime import date

MIN_VIEWS = 25
MIN_ENGAGED_VIEWS = 8
MIN_AGE_DAYS = 7

TOPIC_CATALOG = [
    ("nutrition", "Which high-protein breakfast keeps you full longer?", ["protein", "hunger", "breakfast", "satiety"]),
    ("nutrition", "A simple lean-protein swap for everyday meals", ["food", "beef", "chicken", "protein", "swap"]),
    ("nutrition", "What to eat before training when energy dips", ["food", "pre-workout", "carb", "energy"]),
    ("fat_loss", "Why daily steps matter beyond your gym session", ["neat", "steps", "fat loss", "movement"]),
    ("fat_loss", "Does meal timing matter more than total intake?", ["eating late", "meal timing", "fat gain"]),
    ("training", "How to make Romanian deadlifts target your hamstrings", ["romanian deadlift", "hinge", "hamstring", "technique"]),
    ("training", "How close to failure should your working sets be?", ["training", "failure", "rir", "sets"]),
    ("training", "Can lighter weights build muscle when reps are hard?", ["light weights", "reps", "muscle"]),
    ("recovery", "How hydration affects strength during a workout", ["hydration", "water", "workout", "strength"]),
    ("recovery", "What a deload week should actually change", ["deload", "recovery", "training"]),
    ("science", "Why soreness is a poor scorecard for muscle growth", ["soreness", "muscle growth", "workout"]),
    ("science", "What progressive overload looks like in real training", ["progressive overload", "muscle", "training"]),
]


def _words(value):
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _similarity(left, right):
    a, b = _words(left), _words(right)
    return len(a & b) / max(1, len(a | b))


def _category(text):
    value = str(text or "").lower()
    rules = {
        "nutrition": ("protein", "food", "meal", "beef", "chicken", "hunger", "fiber", "breakfast"),
        "fat_loss": ("fat loss", "neat", "steps", "calorie", "eating late", "fasting"),
        "training": ("deadlift", "squat", "rep", "failure", "technique", "weight", "muscle growth", "rir"),
        "recovery": ("hydration", "water", "sleep", "recovery", "deload", "caffeine", "sodium"),
        "science": ("soreness", "hormone", "testosterone", "trt", "steroid", "progressive overload"),
    }
    matches = [(sum(token in value for token in tokens), name) for name, tokens in rules.items()]
    score, name = max(matches, default=(0, ""))
    return name if score else "general"


def _mature_video_rows(memory):
    analytics = memory.get("analytics", {})
    videos = analytics.get("videos", {})
    uploads = memory.get("video_performance", [])
    if not isinstance(videos, dict) or not isinstance(uploads, list):
        return []
    metadata = {
        str(row.get("video_id")): row for row in uploads
        if isinstance(row, dict) and row.get("video_id")
    }
    try:
        report_day = date.fromisoformat(str(analytics.get("period_end", "")))
    except ValueError:
        report_day = None

    rows = []
    for video_id, stats in videos.items():
        if not isinstance(stats, dict):
            continue
        item = metadata.get(str(video_id), {})
        try:
            uploaded = date.fromisoformat(str(item.get("uploaded_at", ""))[:10])
        except ValueError:
            continue
        if report_day is None or (report_day - uploaded).days < MIN_AGE_DAYS:
            continue
        views = max(0, int(stats.get("views", 0) or 0))
        engaged = max(0, int(stats.get("engaged_views", 0) or 0))
        if views < MIN_VIEWS or engaged < MIN_ENGAGED_VIEWS:
            continue
        retention = min(100.0, max(0.0, float(stats.get("average_view_percentage", 0) or 0)))
        engagement_rate = min(1.0, engaged / max(views, 1))
        subs = max(0, int(stats.get("subscribers_gained", 0) or 0))
        subscriber_rate = min(1.0, subs / max(views, 1) * 100)
        score = (
            0.40 * retention / 100
            + 0.30 * engagement_rate
            + 0.20 * math.log1p(views) / math.log1p(max(views, 1))
            + 0.10 * subscriber_rate
        )
        label = item.get("topic") or item.get("title") or ""
        hook = item.get("hook") or ""
        rows.append({
            "video_id": str(video_id), "label": str(label), "hook": str(hook),
            "category": _category(" ".join((label, hook))),
            "views": views, "engaged": engaged, "retention": retention,
            "score": score,
        })
    return rows


def recommend_topics(memory, used=None, trends=None, limit=5):
    """Return a transparent shortlist ranked from mature channel evidence."""
    used = [str(value) for value in (used or [])]
    trends = trends if isinstance(trends, list) else []
    rows = _mature_video_rows(memory if isinstance(memory, dict) else {})
    category_scores = {}
    for row in rows:
        category_scores.setdefault(row["category"], []).append(row["score"])
    category_scores = {
        key: sum(values) / len(values) for key, values in category_scores.items()
    }

    recent = used[-50:]
    trend_text = [str(item.get("topic", "")) for item in trends if isinstance(item, dict)]
    ranked = []
    for topic, category, keywords in TOPIC_CATALOG:
        if any(_similarity(topic, old) >= 0.48 for old in recent):
            continue
        if any(_similarity(topic, old) >= 0.60 for old in trend_text):
            continue
        evidence = category_scores.get(category, 0.0)
        # A neutral prior prevents categories with no measured videos being treated as failures.
        score = 0.50 + (evidence - 0.50) * 0.65 if category in category_scores else 0.50
        ranked.append({
            "topic": topic,
            "category": category,
            "score": round(score, 4),
            "evidence_videos": sum(1 for row in rows if row["category"] == category),
            "evidence": "measured channel signal" if category in category_scores else "exploration; no mature category sample",
        })
    ranked.sort(key=lambda item: (item["score"], item["evidence_videos"]), reverse=True)
    return ranked[:max(1, int(limit))]


def hook_learning(memory, limit=4):
    """Summarize stronger measured openings without copying their wording."""
    rows = _mature_video_rows(memory if isinstance(memory, dict) else {})
    rows = [row for row in rows if row["hook"]]
    rows.sort(key=lambda row: row["score"], reverse=True)
    return [{
        "hook": row["hook"],
        "topic": row["label"],
        "views": row["views"],
        "retention": row["retention"],
        "pattern": _hook_pattern(row["hook"]),
    } for row in rows[:max(1, int(limit))]]


def _hook_pattern(hook):
    value = str(hook).strip().lower()
    if "?" in value:
        return "specific curiosity question"
    if value.startswith(("stop ", "don't ", "do not ")):
        return "direct challenge or mistake correction"
    if any(word in value for word in ("instead", "but", "versus", "vs")):
        return "contrast"
    return "direct problem, claim, or payoff"
