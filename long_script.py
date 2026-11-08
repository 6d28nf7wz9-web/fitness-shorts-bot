import json
import os
import re
import time

from google import genai
from google.genai import types

from gen_script import BANNED, DISCLAIMER, get_model_candidates, parse_json
from topics import all_used, too_similar

USED_FILE = "used_long_topics.json"
QUEUE_DIR = "queue"


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_trends():
    data = load_json("output/trends.json", [])
    return [t for t in data if isinstance(t, dict) and t.get("topic")]


def build_prompt(used, trends):
    recent = ", ".join(used[-40:]) if used else "none yet"
    trend_block = ""
    if trends:
        lines = "\n".join(
            f"- {t.get('topic')} (safe angle: {t.get('safe_angle', '')})"
            for t in trends[:8]
        )
        trend_block = f"""
Trending right now. Use ONE of these as the topic if it fits, following its safe angle:
{lines}
Never follow a fad, supplement, extreme diet, detox or medical claim. Never copy anyone's title.
"""
    return f"""You write scripts for a YouTube channel (widescreen videos, 3 to 5 minutes) that gives practical, evidence-based advice on building muscle and losing fat.

A real person will read this script aloud as a voiceover, so write exactly how people talk: short sentences, contractions, simple words, nothing hard to pronounce.
{trend_block}
Topics already used (do NOT repeat or closely overlap): {recent}

Return ONLY valid JSON, no markdown, with exactly these keys:
{{
  "topic": "short unique label, 3-6 words",
  "title": "max 70 characters, includes the main searchable keyword, curious but truthful",
  "description": "two or three sentences summarizing the video",
  "hashtags": ["4 to 6 relevant hashtags without the # symbol"],
  "sections": [
    {{
      "heading": "2-5 word on-screen title",
      "narration": "what the speaker says in this section",
      "keywords": ["3 to 5 different searches, each showing training or food"]
    }}
  ]
}}

Rules:
- 5 to 8 sections. Total narration between 450 and 700 words.
- Section 1 is a hook of 25-45 words. Start with the most surprising or useful result, promise what the viewer will learn, and open one loop that you close near the end, for example "and the last tip is the one most people skip".
- Each middle section is 70-120 words: one clear point, one concrete example, one short accurate reason, and one simple thing to do today. End each section with a one-sentence bridge that makes the viewer want the next section.
- Vary the rhythm: a short question, a surprising fact, or a quick "here is the mistake" moment in every section, so the energy never stays flat.
- Speak directly to "you", use contractions and everyday words, keep sentences under 16 words, and sound like a friend explaining.
- The last section is a short recap that closes the loop from the hook, asks one simple question for the comments, and ends with "Subscribe for more tips like this."
- Each section has 4 or 5 different keywords for stock footage. EVERY search must show training or food: a person exercising, gym equipment, an athlete, running or stretching, cooking, a healthy meal, fresh ingredients, or someone eating healthy food. Always include a concrete training or food word such as dumbbell, barbell, squat, treadmill, chicken, eggs, salad, rice, meal prep. Never use abstract or unrelated scenes such as people thinking, hungry faces, offices, cities, nature, money, crowds or friends hanging out. Examples: "man lifting dumbbells", "barbell close up", "cooking chicken breast", "healthy meal prep". No brand names, no people's names.
- Only well-established, evidence-based advice (progressive overload, adequate protein, calorie balance, sleep, consistency). Acknowledge that results vary between people.
- Never mention steroids, supplements, fat burners, detoxes, medical conditions, or spot reduction.
- Never promise results or timeframes.
- No emojis.
"""


def validate(data, used):
    for key in ("topic", "title", "description", "hashtags", "sections"):
        if key not in data:
            return f"missing key: {key}"
    secs = data["sections"]
    if not isinstance(secs, list) or not 5 <= len(secs) <= 8:
        return "needs 5 to 8 sections"
    total = 0
    for s in secs:
        if not str(s.get("heading", "")).strip():
            return "empty heading"
        n = len(str(s.get("narration", "")).split())
        if n < 25 or n > 170:
            return f"a section has {n} words"
        kws = s.get("keywords")
        if not isinstance(kws, list) or len(kws) < 3 or not all(str(k).strip() for k in kws):
            return "each section needs at least 3 keywords"
        total += n
    if not 400 <= total <= 850:
        return f"total is {total} words (want 450-700)"
    if len(data["title"]) > 100:
        return "title too long"
    everything = json.dumps(data).lower()
    for bad in BANNED:
        if bad in everything:
            return f"contains banned phrase: {bad}"
    if too_similar(data["topic"], all_used()):
        return "topic already used"
    return None


def generate(used, trends):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=api_key)
    print(f"Trending topics available: {len(trends)}")
    prompt = build_prompt(all_used(), trends)
    for attempt in range(1, 4):
        for model in get_model_candidates():
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
            problem = validate(data, used)
            if problem:
                print(f"[attempt {attempt}] {model} gave a bad script: {problem}")
                break
            print(f"Used model: {model}")
            return data
        time.sleep(5)
    raise RuntimeError("Could not get a valid long script after 3 attempts")


def reading_text(video_id, data):
    words = sum(len(s["narration"].split()) for s in data["sections"])
    minutes = round(words / 150, 1)
    repo = os.getenv("GITHUB_REPOSITORY", "YOUR-USERNAME/fitness-shorts-bot")
    lines = [
        f"# Record this video: {video_id}",
        "",
        f"**Title:** {data['title']}",
        f"**Length:** about {minutes} minutes ({words} words)",
        "",
        "## How to record (about 10 minutes)",
        "1. Find a quiet room. Hold your phone about a hand's width from your mouth.",
        "2. Open Voice Memos and read the sections below in order, in ONE recording. Pause about one second between sections.",
        "3. Speak naturally. You can reword sentences in your own style, because captions follow what you actually say. If you stumble, keep going. For a big mistake, restart the recording.",
        f"4. Name the file exactly **{video_id}**, for example {video_id}.m4a.",
        f"5. Upload it here: https://github.com/{repo}/upload/main/recordings",
        "   Then tap Commit changes. The video builds automatically.",
        "",
        "---",
        "",
    ]
    for i, s in enumerate(data["sections"], 1):
        lines += [f"## Section {i}: {s['heading']}", "", s["narration"].strip(), ""]
    return "\n".join(lines)


def main():
    used = load_json(USED_FILE, [])
    trends = load_trends()
    data = generate(used, trends)

    video_id = "L%03d" % (len(used) + 1)
    data["id"] = video_id
    data["status"] = "waiting_for_recording"
    data["description"] = (
        f"{data['description'].strip()}\n\n"
        f"{' '.join('#' + str(h).strip().lstrip('#').replace(' ', '') for h in data['hashtags'])}\n\n"
        f"{DISCLAIMER}\n\nVideo clips and music: Pixabay."
    )
    data["title"] = data["title"].strip()[:100]

    os.makedirs(QUEUE_DIR, exist_ok=True)
    os.makedirs("output", exist_ok=True)
    with open(f"{QUEUE_DIR}/{video_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(f"{QUEUE_DIR}/{video_id}.txt", "w", encoding="utf-8") as f:
        f.write(reading_text(video_id, data))

    used.append(data["topic"])
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)

    with open("output/long_id.txt", "w") as f:
        f.write(video_id)
    with open("output/long_issue_title.txt", "w") as f:
        f.write(f"Record {video_id}: {data['title']}")

    words = sum(len(s["narration"].split()) for s in data["sections"])
    print(f"\n{video_id}: {data['title']}")
    print(f"Topic: {data['topic']}  |  {len(data['sections'])} sections, {words} words")
    print(f"Reading script: {QUEUE_DIR}/{video_id}.txt")


main()