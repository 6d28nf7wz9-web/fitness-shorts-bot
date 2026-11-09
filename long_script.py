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


FALLBACK_TOPIC_ANGLES = [
    "Why your strength stalls when every workout feels equally hard",
    "How to make your first working set more productive",
    "The simple reason your protein meals leave you hungry",
    "Why adding more exercises can slow your gym progress",
    "How to choose a weight that actually challenges your muscles",
    "What happens when you rest too little between hard sets",
    "How daily walking supports a sustainable fat-loss routine",
    "Why repeating the same workout forever stops being useful",
    "How to build a balanced high-protein breakfast with ordinary foods",
    "The difference between training hard and training with good form",
    "Why a consistent sleep schedule supports better workouts",
    "How to make a calorie deficit easier without extreme dieting",
    "What beginners should track besides the number on the scale",
    "How to progress a squat without changing the exercise",
    "Why meal portions matter more than a single food choice",
]


def build_prompt(used, trends, suggested_angle):
    recent = ", ".join(used[-60:]) if used else "none yet"
    trend_block = ""
    if trends:
        lines = "\n".join(
            f"- {t.get('topic')} (safe angle: {t.get('safe_angle', '')})"
            for t in trends[:8]
        )
        trend_block = f"""
Trending right now. You MAY use one only if it fits the channel and is distinct:
{lines}
Never follow a fad, supplement, extreme diet, detox or medical claim. Never copy anyone's title.
"""
    return f"""You write scripts for a YouTube channel (widescreen videos, 3 to 5 minutes) that gives practical, evidence-based advice on building muscle and losing fat.

A real person will read this script aloud as a voiceover, so write exactly how people talk: short sentences, contractions, simple words, nothing hard to pronounce.
{trend_block}
PREFERRED FRESH ANGLE FOR THIS GENERATION: {suggested_angle}
Treat this as a starting direction, not wording to copy. Make a distinct, useful topic.
Topics already used (do NOT repeat or closely overlap): {recent}
Do not reuse any topic rejected in the latest generation attempts. Choose a genuinely different angle.

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
- Section 1 is a hook of 25-45 words. Start with the most surprising or useful result, promise what the viewer will learn, and open one loop that you close near the end.
- Each middle section is 70-120 words: one clear point, one concrete example, one short accurate reason, and one simple thing to do today. End each section with a one-sentence bridge.
- Vary the rhythm: a short question, a surprising fact, or a quick "here is the mistake" moment in every section.
- Speak directly to "you", use contractions and everyday words, keep sentences under 16 words, and sound like a friend explaining.
- The last section is a short recap that closes the loop, asks one simple question for comments, and ends with "Subscribe for more tips like this."
- Each section has 4 or 5 different keywords for stock footage. EVERY search must show training or food. Include concrete words such as dumbbell, barbell, squat, treadmill, chicken, eggs, salad, rice, meal prep. Never use abstract or unrelated scenes. No brand names or people's names.
- Only well-established, evidence-based advice (progressive overload, adequate protein, calorie balance, sleep, consistency). Acknowledge results vary.
- Never mention or promote steroids, SARMs, supplements, fat burners, detoxes, miracle products, medical conditions, spot reduction, extreme diets, or medical treatment.
- Never use these exact phrases or words in the viewer-facing topic, title, description, headings, or narration: steroid, SARM, fat burner, detox, guaranteed, spot reduction, miracle, overnight, in 7 days, in a week.
- Never promise results or timeframes.
- No emojis.
"""

def validate(data, used):
    if not isinstance(data, dict):
        return "response is not a JSON object"
    for key in ("topic", "title", "description", "hashtags", "sections"):
        if key not in data:
            return f"missing key: {key}"
    for key in ("topic", "title", "description"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            return f"{key} must be non-empty text"
    if not isinstance(data.get("hashtags"), list) or not 4 <= len(data["hashtags"]) <= 6:
        return "needs 4 to 6 hashtags"
    secs = data["sections"]
    if not isinstance(secs, list) or not 5 <= len(secs) <= 8:
        return "needs 5 to 8 sections"
    total = 0
    for index, section in enumerate(secs, 1):
        if not isinstance(section, dict):
            return f"section {index} is not an object"
        if not str(section.get("heading", "")).strip():
            return f"section {index} has an empty heading"
        narration = str(section.get("narration", "")).strip()
        n = len(narration.split())
        if n < 25 or n > 170:
            return f"section {index} has {n} words"
        kws = section.get("keywords")
        if not isinstance(kws, list) or len(kws) < 3 or not all(str(k).strip() for k in kws):
            return f"section {index} needs at least 3 keywords"
        total += n
    if not 400 <= total <= 850:
        return f"total is {total} words (target 450-700)"
    if len(data["title"]) > 100:
        return "title too long"

    # Apply safety/content filters to viewer-facing text, not stock-footage search terms.
    public_text = " ".join([
        data["topic"], data["title"], data["description"],
        *[str(s.get("heading", "")) + " " + str(s.get("narration", "")) for s in secs],
    ]).lower()
    for bad in BANNED:
        if bad in public_text:
            return f"contains banned phrase in viewer-facing text: {bad}"
    if too_similar(data["topic"], used):
        return "topic already used or too similar to a previous topic"
    return None

def _is_temporary_gemini_error(exc):
    message = str(exc).lower()
    status = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
    return status in (429, 500, 502, 503, 504) or any(
        marker in message for marker in (
            '503', 'unavailable', 'high demand', '429', 'resource_exhausted',
            'rate limit', '500', '502', '504', 'internal error',
            'deadline exceeded', 'temporarily',
        )
    )


def generate_with_retry(client, model, prompt, retries=1):
    for retry in range(retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    response_mime_type='application/json',
                ),
            )
        except Exception as exc:
            if not _is_temporary_gemini_error(exc) or retry >= retries:
                raise
            delay = min(4 * (2 ** retry), 12)
            print(f'Temporary Gemini error for {model}: {str(exc)[:180]}')
            print(f'Retrying {model} in {delay}s before falling back...')
            time.sleep(delay)


def generate(used, trends):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=api_key)
    print(f"Trending topics available: {len(trends)}")

    # Include both Shorts and long-form history; don't let a previous long topic
    # accidentally pass validation just because it was omitted from this list.
    history = list(dict.fromkeys([str(x) for x in all_used() if str(x).strip()]))
    for item in used:
        if str(item).strip() and str(item) not in history:
            history.append(str(item))

    model_candidates = get_model_candidates()
    if not model_candidates:
        raise RuntimeError("No Gemini models configured")
    print("Gemini model fallback order:", " -> ".join(model_candidates))

    rejected_topics = []
    last_problem = "No valid response received"
    max_rounds = 4

    for round_no in range(1, max_rounds + 1):
        available_angles = [
            angle for angle in FALLBACK_TOPIC_ANGLES
            if not too_similar(angle, history + rejected_topics)
        ]
        if not available_angles:
            # If the small starter bank is exhausted, use a fresh angle based on
            # the round number; validation still blocks actual duplicate topics.
            available_angles = [
                "A practical way to improve workout consistency",
                "How to make everyday meals more filling",
                "A simple training mistake and how to correct it",
                "How to measure progress beyond body weight",
            ]
        suggested_angle = available_angles[(round_no - 1) % len(available_angles)]
        prompt = build_prompt(
            history + rejected_topics,
            trends,
            suggested_angle,
        )
        if rejected_topics:
            prompt += (
                "\n\nIMPORTANT: These topics were rejected as repeats; do not use them "
                "or close variations: " + ", ".join(rejected_topics[-12:])
            )
        if last_problem and round_no > 1:
            prompt += (
                "\n\nCorrection from the previous round: " + last_problem
                + ". Generate a completely different valid script. Do not explain the correction."
            )

        print(f"\nLong script generation round {round_no}/{max_rounds}")
        had_api_response = False

        for model in model_candidates:
            try:
                response = generate_with_retry(
                    client, model, prompt, retries=1
                )
                if not getattr(response, "text", None):
                    last_problem = "Gemini returned an empty response"
                    print(f"{model}: {last_problem}")
                    continue
                had_api_response = True
                data = parse_json(response.text)
                problem = validate(data, history + rejected_topics)
                if problem:
                    last_problem = problem
                    if problem.startswith("topic already used"):
                        topic = str(data.get("topic", "")).strip()
                        if topic and topic not in rejected_topics:
                            rejected_topics.append(topic)
                    print(f"{model}: rejected script: {problem}")
                    # Try the next model with the same fresh-angle instruction;
                    # the next round also receives the exact validation feedback.
                    continue

                print(f"Used model: {model}")
                return data

            except Exception as exc:
                last_problem = str(exc)
                print(f"{model} failed: {last_problem[:220]}")
                continue

        if round_no < max_rounds:
            delay = min(8 * round_no, 24)
            print(
                f"No valid script in round {round_no}. "
                f"Trying a new angle after {delay}s. Last issue: {last_problem[:180]}"
            )
            time.sleep(delay)

    raise RuntimeError(
        f"Could not get a valid long script after {max_rounds} rounds "
        f"and {len(model_candidates)} model candidates per round. "
        f"Last issue: {last_problem}"
    )

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



if __name__ == "__main__":
    main()
