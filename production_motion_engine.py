"""Purpose-driven motion primitives for FitFuel's short-form renderer.

All timing is deterministic and derived from the scene narration duration.  The
module deliberately avoids decorative motion when no meaningful emphasis exists.
"""
import html
import re

_WORD = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_IMPORTANT = {
    "muscle": {"protein", "muscle", "tension", "repair", "growth", "protein", "strength", "hypertrophy", "recovery"},
    "nutrition": {"protein", "carbohydrate", "fiber", "absorption", "nutrient", "meal", "fuel"},
    "heart": {"heart", "blood", "oxygen", "pulse", "cardio", "circulation"},
    "fat_loss": {"calorie", "deficit", "energy", "fat", "intake", "expenditure"},
    "hydration": {"water", "hydration", "fluid", "electrolyte", "sodium", "potassium"},
    "exercise": {"load", "joint", "range", "motion", "squat", "repetition", "exercise"},
    "hormones": {"hormone", "insulin", "cortisol", "leptin", "ghrelin", "receptor", "signal"},
    "supplements": {"caffeine", "dose", "supplement", "evidence"},
    "creatine": {"creatine", "atp", "phosphocreatine", "energy", "recharge", "performance"},
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
            f'--word-duration:{max(.12, end-start):.3f}s;--word-delay:{start:.3f}s">{word}</span>'
        )
    if not spans:
        return ""
    return '<div class="kinetic-line" aria-label="Spoken key terms">' + " ".join(spans) + "</div>"


def presenter_gesture(narration, category):
    """Select a readable gesture from the actual teaching intent."""
    text = str(narration or "").lower()
    if re.search(r"\\b(point|show|look|notice|this|here|target|watch)\\b", text):
        return "point"
    if re.search(r"\\b(compare|versus|instead|difference|whereas|while)\\b", text):
        return "compare"
    if re.search(r"\\b(demonstrate|perform|bend|extend|lower|raise|rotate|squat|press|pull|hinge)\\b", text):
        return "demonstrate"
    if re.search(r"\\b(why|because|remember|important|means|therefore|explain)\\b", text):
        return "explain"
    if category in ("muscle", "exercise", "heart"):
        return "demonstrate"
    if category in ("hormones", "creatine", "nutrition"):
        return "explain"
    return "talk"


def presenter_expression(narration, category):
    """Choose a subtle facial expression from the emotional/teaching cue."""
    text = str(narration or "").lower()
    if re.search(r"\\b(surprising|surprisingly|wow|shocking|unexpected|myth|mistake)\\b", text):
        return "surprise"
    if re.search(r"\\b(warning|avoid|danger|risk|wrong|stop|careful|injury)\\b", text):
        return "concern"
    if re.search(r"\\b(great|excellent|success|stronger|progress|result|improve|benefit)\\b", text):
        return "smile"
    if re.search(r"\\b(focus|technique|precision|control|form|mechanics)\\b", text) or category == "exercise":
        return "focused"
    return "neutral"


def presenter_html(gesture="talk", expression="neutral"):
    """Small vector presenter with separate arm, torso, brow and mouth states."""
    gesture = gesture if gesture in {"talk", "point", "explain", "compare", "demonstrate"} else "talk"
    expression = expression if expression in {"neutral", "smile", "surprise", "concern", "focused"} else "neutral"
    return f"""<div class="presenter" data-gesture="{gesture}" data-expression="{expression}" aria-label="FitFuel presenter">
      <svg viewBox="0 0 100 120" role="img">
        <circle class="presenter-head" cx="50" cy="27" r="18"/>
        <path class="presenter-body" d="M20 112 Q20 62 50 62 Q80 62 80 112Z"/>
        <path class="presenter-arm arm-left" d="M23 78 Q8 65 13 53"/>
        <path class="presenter-arm arm-right" d="M77 78 Q91 67 88 54"/>
        <path class="presenter-brow brow-left" d="M38 19 Q44 16 48 19"/>
        <path class="presenter-brow brow-right" d="M52 19 Q58 16 63 19"/>
        <circle class="presenter-eye" cx="44" cy="27" r="2"/><circle class="presenter-eye" cx="57" cy="27" r="2"/>
        <path class="presenter-mouth mouth-neutral" d="M43 38 Q50 40 57 38"/>
        <path class="presenter-mouth mouth-smile" d="M41 36 Q50 47 59 36"/>
        <ellipse class="presenter-mouth mouth-surprise" cx="50" cy="39" rx="4" ry="6"/>
        <path class="presenter-mouth mouth-concern" d="M42 42 Q50 34 58 42"/>
        <path class="presenter-mouth mouth-focused" d="M43 39 H57"/>
      </svg></div>"""


def presenter_css():
    return """
.presenter{position:absolute;z-index:9;top:235px;right:72px;width:76px;height:92px;opacity:.96;
 filter:drop-shadow(0 5px 12px rgba(0,0,0,.5));pointer-events:none}
.presenter svg{width:100%;height:100%;overflow:visible}
.presenter-head{fill:#d6a17e;stroke:#f4d1b7;stroke-width:2}
.presenter-body{fill:#72e6c2;stroke:#d7fff4;stroke-width:2;transform-origin:50px 85px;animation:ff-presenter-breathe 3.6s ease-in-out infinite}
.presenter-arm{fill:none;stroke:#d6a17e;stroke-width:9;stroke-linecap:round;transform-box:fill-box;transform-origin:50% 10%;animation:ff-presenter-talk 2.4s ease-in-out infinite}
.presenter-brow{fill:none;stroke:#172638;stroke-width:2.5;stroke-linecap:round}
.presenter-eye{fill:#172638}
.presenter-mouth{fill:none;stroke:#172638;stroke-width:2.2;stroke-linecap:round;display:none}
.presenter .mouth-neutral{display:block}
.presenter[data-expression="smile"] .mouth-neutral,.presenter[data-expression="smile"] .mouth-smile{display:none}
.presenter[data-expression="smile"] .mouth-smile{display:block}
.presenter[data-expression="surprise"] .mouth-neutral{display:none}
.presenter[data-expression="surprise"] .mouth-surprise{display:block;fill:#172638}
.presenter[data-expression="concern"] .mouth-neutral{display:none}
.presenter[data-expression="concern"] .mouth-concern{display:block}
.presenter[data-expression="focused"] .mouth-neutral{display:none}
.presenter[data-expression="focused"] .mouth-focused{display:block}
.presenter[data-expression="surprise"] .presenter-brow{stroke-width:3}
.presenter[data-expression="concern"] .brow-left{transform:rotate(-13deg);transform-origin:44px 18px}
.presenter[data-expression="concern"] .brow-right{transform:rotate(13deg);transform-origin:56px 18px}
.presenter[data-expression="smile"] .presenter-eye{transform:scaleY(.78);transform-origin:center}
.presenter[data-gesture="point"] .arm-right{animation:ff-presenter-point 2.8s ease-in-out infinite}
.presenter[data-gesture="point"] .arm-left{animation:ff-presenter-rest 2.8s ease-in-out infinite}
.presenter[data-gesture="explain"] .arm-left{animation:ff-presenter-explain 2.5s ease-in-out infinite}
.presenter[data-gesture="explain"] .arm-right{animation:ff-presenter-explain 2.5s ease-in-out infinite reverse}
.presenter[data-gesture="compare"] .arm-left{animation:ff-presenter-compare-left 3s ease-in-out infinite}
.presenter[data-gesture="compare"] .arm-right{animation:ff-presenter-compare-right 3s ease-in-out infinite}
.presenter[data-gesture="demonstrate"] .arm-left{animation:ff-presenter-demo 2.2s ease-in-out infinite}
.presenter[data-gesture="demonstrate"] .arm-right{animation:ff-presenter-demo 2.2s ease-in-out infinite reverse}
.presenter[data-gesture="point"] .presenter-body{animation:ff-presenter-lean 2.8s ease-in-out infinite}
@keyframes ff-presenter-breathe{0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.025)}}
@keyframes ff-presenter-talk{0%,100%{transform:rotate(0)}45%{transform:rotate(-7deg)}70%{transform:rotate(4deg)}}
@keyframes ff-presenter-point{0%,100%{transform:rotate(-8deg) translateY(0)}50%{transform:rotate(62deg) translateY(-7px)}}
@keyframes ff-presenter-rest{0%,100%{transform:rotate(0)}50%{transform:rotate(-8deg)}}
@keyframes ff-presenter-explain{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(24deg) translateY(-5px)}}
@keyframes ff-presenter-compare-left{0%,100%{transform:rotate(-28deg)}50%{transform:rotate(12deg) translateY(-5px)}}
@keyframes ff-presenter-compare-right{0%,100%{transform:rotate(28deg)}50%{transform:rotate(-12deg) translateY(-5px)}}
@keyframes ff-presenter-demo{0%,100%{transform:rotate(-22deg)}50%{transform:rotate(26deg) translateY(-8px)}}
@keyframes ff-presenter-lean{50%{transform:translateX(-5px) rotate(-5deg)}}
"""


def motion_engine_css():
    return """
/* Kinetic emphasis is tied to each word's narration window. */
.kinetic-line{position:absolute;z-index:8;left:100px;right:100px;top:925px;min-height:72px;
 display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;pointer-events:none}
.kinetic-word{display:inline-block;opacity:0;transform:translateY(18px) scale(.92);
 animation:ff-word-hit var(--word-duration) cubic-bezier(.16,1,.3,1) both;
 animation-delay:var(--word-delay);font-size:38px;font-weight:900;padding:5px 12px;border-radius:12px;background:rgba(7,22,36,.84);border:1px solid rgba(114,230,194,.28);letter-spacing:1px;
 color:#72e6c2;text-shadow:0 4px 22px #000,0 0 20px rgba(114,230,194,.35)}
@keyframes ff-word-hit{0%{opacity:0;transform:translateY(18px) scale(.92)}
 18%{opacity:1;transform:translateY(0) scale(1.08)}35%,82%{opacity:1;transform:scale(1)}
 100%{opacity:0;transform:translateY(-8px) scale(.98)}}
"""


def motion_engine_css():
    return """
/* Kinetic emphasis is tied to each word's narration window. */
.kinetic-line{position:absolute;z-index:8;left:100px;right:100px;top:925px;min-height:72px;
 display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;pointer-events:none}
.kinetic-word{display:inline-block;opacity:0;transform:translateY(18px) scale(.92);
 animation:ff-word-hit var(--word-duration) cubic-bezier(.16,1,.3,1) both;
 animation-delay:var(--word-delay);font-size:38px;font-weight:900;padding:5px 12px;border-radius:12px;background:rgba(7,22,36,.84);border:1px solid rgba(114,230,194,.28);letter-spacing:1px;
 color:#72e6c2;text-shadow:0 4px 22px #000,0 0 20px rgba(114,230,194,.35)}
@keyframes ff-word-hit{0%{opacity:0;transform:translateY(18px) scale(.92)}
 18%{opacity:1;transform:translateY(0) scale(1.08)}35%,82%{opacity:1;transform:scale(1)}
 100%{opacity:0;transform:translateY(-8px) scale(.98)}}
/* Scene entrance varies by shot intent; transitions remain short and legible. */
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
.presenter.gesture-point .presenter-arm{animation:ff-presenter-point 2.8s ease-in-out infinite}
.presenter.gesture-explain .presenter-arm{animation:ff-presenter-explain 2.5s ease-in-out infinite}
.presenter.gesture-compare .presenter-arm{animation:ff-presenter-compare 3s ease-in-out infinite}
.presenter.gesture-demonstrate .presenter-arm{animation:ff-presenter-demo 2.2s ease-in-out infinite}
.presenter.gesture-point .presenter-body{animation:ff-presenter-lean 2.8s ease-in-out infinite}
@keyframes ff-presenter-point{0%,100%{transform:rotate(-4deg) translateY(-2px)}50%{transform:rotate(32deg) translateY(-5px)}}
@keyframes ff-presenter-explain{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(10deg) translateY(-7px)}}
@keyframes ff-presenter-compare{0%,100%{transform:rotate(-12deg)}50%{transform:rotate(16deg) translateY(-4px)}}
@keyframes ff-presenter-demo{0%,100%{transform:rotate(-18deg)}50%{transform:rotate(22deg) translateY(-8px)}}
@keyframes ff-presenter-lean{50%{transform:translateX(-5px) rotate(-5deg)}}
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


__all__ = ["word_timeline", "emphasize_words", "kinetic_html", "presenter_html", "presenter_gesture", "presenter_expression", "presenter_css",
           "motion_engine_css", "sound_cue_events"]
