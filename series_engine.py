"""Structured recurring Shorts series and upload-aware episode sequencing."""
import json
import os

SERIES = {
    "Steroid Reality Check": [
        "Do steroids build muscle faster—and at what cost?",
        "What happens to natural testosterone during a steroid cycle?",
        "Why can steroid use affect fertility and testicular function?",
        "Can testosterone production recover after stopping steroids?",
        "TRT and bodybuilding steroids are not the same thing",
        "Why steroid-related muscle gains can be difficult to keep",
    ],
    "Hormone Lab": [
        "What testosterone actually does for muscle",
        "Can low testosterone explain every gym plateau?",
        "How estrogen matters in the male body",
        "Cortisol: stress hormone or misunderstood villain?",
        "What sleep loss can do to hormone regulation",
        "Why hormone symptoms need medical testing—not guesses",
    ],
    "Gym Myth Court": [
        "Does training to failure build more muscle every time?",
        "Is soreness proof that a workout worked?",
        "Can fasted cardio burn more body fat overall?",
        "Does eating late automatically cause fat gain?",
        "Are high reps and low reps both useful for growth?",
        "Is sweating more a sign of a better workout?",
    ],
    "Natural vs Enhanced": [
        "What does natural muscle growth really depend on?",
        "Why do enhanced physiques change the comparison?",
        "Can supplements replace progressive overload?",
        "What realistic progress looks like without shortcuts",
        "Why genetics change the pace of muscle growth",
        "How to judge fitness claims without comparing physiques",
    ],
}


def _uploads():
    try:
        with open("output/uploaded_videos.json", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def next_episode():
    """Continue a series until its planned episodes are uploaded; previews don't advance it."""
    uploads = _uploads()
    last_series = next(
        (str(item.get("series", "")) for item in reversed(uploads)
         if item.get("series") in SERIES),
        None,
    )
    if last_series:
        count = sum(1 for item in uploads if item.get("series") == last_series)
        if count < len(SERIES[last_series]):
            return last_series, count + 1, SERIES[last_series][count]

    completed = {name: sum(1 for item in uploads if item.get("series") == name)
                 for name in SERIES}
    available = [name for name in SERIES if completed[name] < len(SERIES[name])]
    if not available:
        available = list(SERIES)
    # Rotate to the next series after the most recently completed/used one.
    prior = last_series or ""
    start = (list(SERIES).index(prior) + 1) % len(SERIES if prior in SERIES else list(SERIES))
    name = available[start % len(available)]
    return name, completed[name] + 1, SERIES[name][completed[name] % len(SERIES[name])]
