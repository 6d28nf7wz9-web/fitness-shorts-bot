import difflib
import json
import re

THRESHOLD = 0.5

STOP = {
    "the", "and", "for", "your", "you", "with", "that", "this", "from", "how",
    "why", "what", "does", "are", "not", "can", "get", "use", "best", "tip",
    "tips", "daily", "myth", "fact", "facts", "vs", "about", "into", "more",
    "less", "than", "real", "simple", "key", "way", "ways", "need", "every",
    "truth",
}


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    return [str(x) for x in data] if isinstance(data, list) else []


def all_used():
    """Every topic used so far, Shorts and long videos together."""
    return _load("used_topics.json") + _load("used_long_topics.json")


def _words(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP or len(w) < 3:
            continue
        if len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        out.add(w)
    return out


def similarity(a, b):
    ratio = difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
    wa, wb = _words(a), _words(b)
    overlap = len(wa & wb) / len(wa | wb) if wa and wb else 0.0
    return max(ratio, overlap)


def too_similar(topic, used, threshold=THRESHOLD):
    return any(similarity(topic, u) >= threshold for u in used)