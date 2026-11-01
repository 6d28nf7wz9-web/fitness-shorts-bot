import json
import os
import re
import time

from google import genai
from google.genai import types

try:
    from topics import all_used, too_similar
except ImportError:                      # topics.py is optional
    def all_used():
        out = []
        for name in ("used_topics.json", "used_long_topics.json"):
            try:
                with open(name, encoding="utf-8") as f:
                    out += [str(x) for x in json.load(f)]
            except Exception:
                pass
        return out

    def too_similar(topic, used):
        return topic.strip().lower() in [u.strip().lower() for u in used]

try:
    from relevance import keyword_is_relevant
except ImportError:                      # relevance.py is optional
    def keyword_is_relevant(text):
        return True

# Shorts are built for the Shorts feed: one sharp idea, a strong hook, nothing cut from long videos.
CONTENT_TYPES = [
    "a myth that sounds true but is wrong, and what actually works",
    "a common mistake people make in the gym or with food, and the simple fix",
    "a this-versus-that comparison (two foods, two exercises or two habits) with a clear winner and why",
    "a quick food swap or an easy high-protein meal idea, using only well known and rounded numbers",
    "one form cue that makes a popular exercise work better and feel safer",
    "a surprising but well established fact about muscle, fat loss, sleep or recovery",
    "a simple rule of thumb the viewer can use today, like how much protein, how many steps or how long to rest",
]

# Tried in order. Set GEMINI_MODEL as a secret to force a specific one.
MODEL_CANDIDATES = [
    m for m in [
        os.getenv("GEMINI_MODEL"),
        "gemini-flash-latest",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
    ] if m
]

BANNED = [
    "steroid", "sarm", "fat burner", "fat-burner", "detox", "guaranteed",
    "spot reduc", "miracle", "overnight", "in 7 days", "in a week",
]

DISCLAIMER = (
    "General fitness information, not medical advice. "
    "Consult a doctor before starting a new program."
)


def load_used():
    try:
        with open("used_topics.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def mark_used(topic):
    """Called by upload.py after a successful upload."""
    used = load_used()
    used.append(topic)
    with open("used_topics.json", "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def load_trends():
    try:
        with open("output/trends.json", encoding="utf-8") as f:
            data = json.load(f)
        return [t for t in data if isinstance(t, dict) and t.get("topic")]
    except Exception:
        return []


def build_prompt(content_type, used, trends):
    recent = ", ".join(used[-80:]) if used else "none yet"
    trend_block = ""
    if trends:
        lines = "\n".join(
            f"- {t.get('topic')} (safe angle: {t.get('safe_angle', '')})" for t in trends[:8]
        )
        trend_block = f"""
Topics people are searching for right now. Use ONE if it fits today's video type, following its safe angle:
{lines}
Never follow a fad, supplement, extreme diet, detox or medical claim. Never copy anyone's title.
"""
    return f"""You write scripts for a YouTube Shorts channel about building muscle and losing fat. These Shorts stand alone: they are NOT clips of long videos, so the very first second must grab attention.

Today's video type: {content_type}.
{trend_block}
Topics already used on this channel, including the long videos (do NOT repeat or closely overlap any of them): {recent}

Return ONLY valid JSON, no markdown, with exactly these keys:
{{
  "topic": "short unique label, 3-6 words",
  "title": "max 60 characters, starts with a strong word or a number, includes the main keyword, creates curiosity, truthful and not misleading",
  "description": "two short sentences summarizing the tip",
  "hashtags": ["4 to 6 relevant hashtags without the # symbol"],
  "scenes": [
    {{"narration": "one or two short spoken sentences", "keyword": "2 or 3 searches separated by a vertical bar, each showing training or food"}}
  ]
}}

Rules:
- 4 to 6 scenes. Total narration between 70 and 100 words (about 30 seconds spoken).
- Scene 1 is the hook: at most 12 words, no greeting. Pick ONE pattern: "Stop doing X if you want Y.", "Nobody tells you this about X.", "You have been doing X wrong.", "This one swap changes X.", "Gym myth: X.", or "X versus Y: there is a clear winner." Be specific, never vague.
- Scene 2 promises the payoff in one short sentence so the viewer keeps watching.
- Middle scenes: one clear point, one concrete example, one simple action to do today. Speak directly to "you". Sentences under 14 words. Everyday words, contractions, like a friend explaining.
- Use a number or a specific detail only when it is well established and accurate. Round numbers and say "about". Never invent statistics or studies.
- The last scene is a loop ending: its final sentence flows back into the hook so the video feels continuous when it replays.
- Each keyword field names 2 or 3 different filmable searches separated by a vertical bar. EVERY search must show training or food: a person exercising, gym equipment, an athlete, running or stretching, cooking, a healthy meal, fresh ingredients, or someone eating healthy food. Always include a concrete training or food word such as dumbbell, barbell, squat, treadmill, chicken, eggs, salad, rice, meal prep. Never use abstract or unrelated scenes such as people thinking, hungry faces, offices, cities, nature, money, crowds or friends hanging out. Examples: "man lifting dumbbells | barbell close up | gym workout" and "cooking chicken breast | healthy meal prep | fresh vegetables". No brand names, no people's names.
- Only well-established, evidence-based advice (progressive overload, adequate protein, calorie balance, sleep, consistency).
- Never mention steroids, supplements, fat burners, detoxes, medical conditions, or spot reduction.
- Never promise results or timeframes (no "lose 10 kg in a week").
- Simple words, energetic tone, no emojis.
"""


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def validate(data):
    """Return a problem description, or None if the script is fine."""
    for key in ("topic", "title", "description", "hashtags", "scenes"):
        if key not in data:
            return f"missing key: {key}"
    scenes = data["scenes"]
    if not isinstance(scenes, list) or not 4 <= len(scenes) <= 6:
        return "needs 4 to 6 scenes"
    words = 0
    for s in scenes:
        if not str(s.get("narration", "")).strip():
            return "empty narration"
        kw = [k.strip() for k in str(s.get("keyword", "")).split("|") if k.strip()]
        if not kw:
            return "empty keyword"
        good = sum(1 for k in kw if keyword_is_relevant(k))
        if not keyword_is_relevant(kw[0]) or good * 2 < len(kw):
            return f"keyword not about training or food: {s.get('keyword')}"
        words += len(s["narration"].split())
    if not 60 <= words <= 125:
        return f"narration is {words} words (want 70-100)"
    if len(data["title"]) > 100:
        return "title too long"
    first = scenes[0]["narration"].split()
    if len(first) > 18:
        return "the hook is too long"
    everything = json.dumps(data).lower()
    for bad in BANNED:
        if bad in everything:
            return f"contains banned phrase: {bad}"
    if too_similar(data["topic"], all_used()):
        return "topic too close to one already used"
    return None


def generate_script():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=api_key)
    used = load_used()
    trends = load_trends()
    content_type = CONTENT_TYPES[len(used) % len(CONTENT_TYPES)]
    print(f"Video type: {content_type}")
    prompt = build_prompt(content_type, all_used(), trends)

    for attempt in range(1, 4):
        for model in MODEL_CANDIDATES:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.95,
                        response_mime_type="application/json",
                    ),
                )
                data = parse_json(response.text)
            except Exception as e:
                print(f"[attempt {attempt}] {model} failed: {str(e)[:200]}")
                continue
            problem = validate(data)
            if problem:
                print(f"[attempt {attempt}] {model} gave a bad script: {problem}")
                break
            print(f"Used model: {model}")
            return data
        time.sleep(5)
    raise RuntimeError("Could not get a valid script after 3 attempts")


def finalize(data):
    tags = []
    for h in data["hashtags"]:
        tag = "#" + str(h).strip().lstrip("#").replace(" ", "")
        if tag not in tags:
            tags.append(tag)
    if "#Shorts" not in tags:
        tags.append("#Shorts")
    data["description"] = (
        f"{data['description'].strip()}\n\n{' '.join(tags)}\n\n"
        f"{DISCLAIMER}\n\nVideo clips and music: Pixabay."
    )
    data["title"] = data["title"].strip()[:100]
    return data


if __name__ == "__main__":
    script = finalize(generate_script())
    os.makedirs("output", exist_ok=True)
    with open("output/script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print("\nTITLE:", script["title"])
    print("TOPIC:", script["topic"])
    for i, s in enumerate(script["scenes"], 1):
        print(f"\nScene {i} [{s['keyword']}]\n{s['narration']}")
    print("\nSaved to output/script.json")