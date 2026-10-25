import datetime
import json
import os
import re
import time

from google import genai
from google.genai import types

from topics import all_used, too_similar

CONTENT_TYPES = [
    "a muscle-building tip (progressive overload, rep ranges, rest, form)",
    "a fat-loss tip (protein, calorie balance, daily steps, sleep, habits)",
    "a myth vs fact about fitness",
    "a common gym mistake and how to fix it",
    "a simple meal or daily habit tip for body composition",
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
    """Called later by main.py after a successful upload."""
    used = load_used()
    used.append(topic)
    with open("used_topics.json", "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def build_prompt(content_type, used):
    recent = ", ".join(used[-60:]) if used else "none yet"
    return f"""You write scripts for a YouTube Shorts channel that gives daily evidence-based tips for building muscle and losing fat.

Today's video type: {content_type}.

Topics already used (do NOT repeat or closely overlap): {recent}

Return ONLY valid JSON, no markdown, with exactly these keys:
{{
  "topic": "short unique label, 3-6 words",
  "title": "max 60 characters, catchy but truthful",
  "description": "two short sentences summarizing the tip",
  "hashtags": ["4 to 6 relevant hashtags without the # symbol"],
  "scenes": [
    {{"narration": "one or two short spoken sentences", "keyword": "2-3 plain English words for a stock video search"}}
  ]
}}

Rules:
- 4 to 6 scenes. Total narration between 75 and 105 words (about 35 seconds spoken).
- Scene 1 is a hook of at most 12 words that grabs attention in 3 seconds.
- The last scene is a call to action ending with "Follow for a daily tip."
- Middle scenes give the tip and one short, accurate reason.
- Each keyword must describe something filmable, like "man lifting dumbbells", "woman running outdoors", "healthy meal prep", "person sleeping". No brand names, no people's names.
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
        if not str(s.get("keyword", "")).strip():
            return "empty keyword"
        words += len(s["narration"].split())
    if not 60 <= words <= 125:
        return f"narration is {words} words (want 75-105)"
    if len(data["title"]) > 100:
        return "title too long"
    everything = json.dumps(data).lower()
    for bad in BANNED:
        if bad in everything:
            return f"contains banned phrase: {bad}"
    if too_similar(data["topic"], all_used()):
        return "topic already used"
    return None


def generate_script():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=api_key)
    used = load_used()
    content_type = CONTENT_TYPES[len(used) % len(CONTENT_TYPES)]
    prompt = build_prompt(content_type, all_used())

    for attempt in range(1, 4):
        for model in MODEL_CANDIDATES:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.9,
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
