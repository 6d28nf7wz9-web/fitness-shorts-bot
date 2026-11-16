"""Purpose-driven motion primitives for FitFuel's short-form renderer.

All timing is deterministic and derived from the scene narration duration.  The
module deliberately avoids decorative motion when no meaningful emphasis exists.
"""
import html
import re

_WORD = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_IMPORTANT = {
    "muscle": {"tension", "repair", "growth", "protein", "strength", "hypertrophy", "recovery"},
    "nutrition": {"protein", "carbohydrate", "fiber", "absorption", "nutrient", "meal", "fuel"},
    "heart": {"heart", "blood", "oxygen", "pulse", "cardio", "circulation"},
    "fat_loss": {"calorie", "deficit", "energy", "fat", "intake", "expenditure"},
    "hydration": {"water", "hydration", "fluid", "electrolyte", "sodium", "potassium"},
    "exercise": {"load", "joint", "range", "motion", "squat", "repetition", "exercise"},
    "hormones": {"hormone", "insulin", "cortisol", "leptin", "ghrelin", "receptor", "signal"},
    "supplements": {"creatine", "caffeine", "dose", "supplement", "evidence"},
}
_FALLBACK = {"key", "important", "because", "actually", "your", "this", "that", "with", "from", "when", "they", "will", "have", "more", "than"}


def word_timeline(narration, duration, word_timings=None):
    """Return safe word-level timing; prefer actual supplied timestamps."""
    words = _WORD.findall(str(narration or ""))
    duration = max(0.05, float(duration))
    if not words:
        return []
    if isinstance(word_timings, list) and len(word_timings) == len(words):
        result = []
        for word, item in zip(words, word_timings):
            try:
                start, end = float(item["start"]), float(item["end"])
            except (KeyError, TypeError, ValueError):
                break
            if start < 0 or end <= start or end > duration + 0.25:
                break
            result.append({"word": word, "start": start, "end": min(end, duration)})
        if len(result) == len(words):
            return result
    # Duration-weighted fallback is stable and better than one static title.
    weights = [max(1, len(w)) for w in words]
    total = sum(weights)
    cursor, result = 0.0, []
    for word, weight in zip(words, weights):
        end = cursor + duration * weight / total
        result.append({"word": word, "start": round(cursor, 3), "end": round(end, 3)})
        cursor = end
    result[-1]["end"] = round(duration, 3)
    return result


def emphasize_words(narration, category, duration, word_timings=None, limit=7):
    """Pick a few topic-relevant words and attach their spoken-time windows."""
    terms = _IMPORTANT.get(category, set())
    timeline = word_timeline(narration, duration, word_timings)
    selected = []
    for item in timeline:
        token = re.sub(r"[^\w'-]", "", item["word"]).lower()
        if token in terms or (not terms and token not in _FALLBACK and len(token) >= 6):
            selected.append(item)
    if not selected:
        selected = [x for x in timeline if len(x["word"]) >= 6][:2]
    # Bound visual density; keep words spread across the scene.
    if len(selected) > limit:
        stride = (len(selected) - 1) / (limit - 1)
        selected = [selected[round(i * stride)] for i in range(limit)]
    return selected


def kinetic_html(narration, category, duration, word_timings=None):
    spans = []
    for item in emphasize_words(narration, category, duration, word_timings):
        word = html.escape(item["word"])
        start, end = item["start"], item["end"]
        spans.append(
            f'<span class="kinetic-word" style="--word-start:{start:.3f}s;'
            f'--word-duration:{max(.12, end-start):.3f}s">{word}</span>'
        )
    if not spans:
        return ""
    return '<div class="kinetic-line" aria-label="Spoken key terms">' + " ".join(spans) + "</div>"


def presenter_html():
    """Compact, self-contained presenter mark in a reserved top-right safe zone."""
    return """<div class="presenter" aria-label="FitFuel presenter">
      <svg viewBox="0 0 100 120" role="img">
        <circle class="presenter-head" cx="50" cy="27" r="18"/>
        <path class="presenter-body" d="M20 112 Q20 62 50 62 Q80 62 80 112Z"/>
        <path class="presenter-arm" d="M23 78 Q8 65 13 53 M77 78 Q91 67 88 54"/>
        <circle class="presenter-eye" cx="44" cy="25" r="2"/><circle class="presenter-eye" cx="57" cy="25" r="2"/>
        <path class="presenter-mouth" d="M43 37 Q50 42 57 37"/>
      </svg></div>"""


def motion_engine_css():
    return """
/* Kinetic emphasis is tied to each word's narration window. */
.kinetic-line{position:absolute;z-index:8;left:100px;right:100px;top:1010px;min-height:92px;
 display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:12px;pointer-events:none}
.kinetic-word{display:inline-block;opacity:0;transform:translateY(18px) scale(.92);
 animation:ff-word-hit var(--word-duration) cubic-bezier(.16,1,.3,1) both;
 animation-delay:var(--word-start);font-size:46px;font-weight:900;letter-spacing:1px;
 color:#72e6c2;text-shadow:0 4px 22px #000,0 0 20px rgba(114,230,194,.35)}
@keyframes ff-word-hit{0%{opacity:0;transform:translateY(18px) scale(.92)}
 18%{opacity:1;transform:translateY(0) scale(1.08)}35%,82%{opacity:1;transform:scale(1)}
 100%{opacity:0;transform:translateY(-8px) scale(.98)}}
/* Scene entrance varies by shot intent; transitions remain short and legible. */
.motion-scene{animation:ff-scene-enter 520ms cubic-bezier(.16,1,.3,1) both}
.motion-hook{--transition-origin:50% 50%}
.motion-support{--transition-origin:50% 60%}
.motion-payoff{--transition-origin:50% 45%}
@keyframes ff-scene-enter{from{opacity:.45;transform:scale(1.025);filter:blur(5px)}
 to{opacity:1;transform:scale(1);filter:blur(0)}}
/* Small presenter is kept in a reserved corner, never over the title or diagram. */
.presenter{position:absolute;z-index:9;top:235px;right:72px;width:76px;height:92px;opacity:.94;
 filter:drop-shadow(0 5px 12px rgba(0,0,0,.5));pointer-events:none}
.presenter svg{width:100%;height:100%;overflow:visible}
.presenter-head{fill:#d6a17e;stroke:#f4d1b7;stroke-width:2}
.presenter-body{fill:#72e6c2;stroke:#d7fff4;stroke-width:2}
.presenter-arm{fill:none;stroke:#d6a17e;stroke-width:9;stroke-linecap:round;transform-origin:50px 65px;animation:ff-presenter-gesture 2.4s ease-in-out infinite}
.presenter-eye{fill:#172638}.presenter-mouth{fill:none;stroke:#172638;stroke-width:2;stroke-linecap:round}
@keyframes ff-presenter-gesture{0%,100%{transform:rotate(0)}45%{transform:rotate(-7deg)}70%{transform:rotate(4deg)}}
"""


def sound_cue_events(narration, category, duration, word_timings=None, scene_start=0.0):
    """Describe sparse SFX cue points for the final audio muxer."""
    cues = []
    for item in emphasize_words(narration, category, duration, word_timings):
        cues.append({"time": round(float(scene_start) + item["start"], 3), "kind": "soft_tick", "word": item["word"]})
    cues.append({"time": round(float(scene_start), 3), "kind": "scene_whoosh", "word": ""})
    return cues


__all__ = ["word_timeline", "emphasize_words", "kinetic_html", "presenter_html",
           "motion_engine_css", "sound_cue_events"]
