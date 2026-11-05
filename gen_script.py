"""Generate retention-focused FitFuel Shorts using channel performance memory."""
import json
import os
import re
import time
from collections import defaultdict

from google import genai
from google.genai import types

try:
    from topics import all_used, too_similar
except ImportError:
    def all_used():
        out = []
        for name in ("used_topics.json", "used_long_topics.json"):
            try:
                with open(name, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    out.extend(str(x) for x in data)
            except Exception:
                pass
        return out

    def too_similar(topic, used):
        words = set(re.findall(r"[a-z0-9]+", topic.lower()))
        for old in used:
            old_words = set(re.findall(r"[a-z0-9]+", str(old).lower()))
            if topic.strip().lower() == str(old).strip().lower():
                return True
            if len(words) >= 3 and len(words & old_words) / len(words) >= 0.8:
                return True
        return False

try:
    from relevance import keyword_is_relevant, fallbacks_for
except ImportError:
    def keyword_is_relevant(text):
        return True

    def fallbacks_for(text):
        return ["gym workout", "weight training", "healthy food", "cooking healthy meal", "meal prep"]

CONTENT_TYPES = [
    "a common gym mistake and the exact correction",
    "a fitness myth versus what actually works",
    "a simple food swap that supports a calorie deficit",
    "one practical exercise form cue",
    "a high-protein meal idea using familiar foods",
    "a simple muscle-building or fat-loss rule people can use today",
    "a comparison between two common exercises, foods, or habits",
]

MODEL_CANDIDATES = [m for m in [
    os.getenv("GEMINI_MODEL"), "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-3-flash-preview"
] if m]

MEMORY_FILE = "performance_memory.json"
BANNED = [
    "steroid", "sarm", "fat burner", "fat-burner", "detox", "guaranteed",
    "spot reduc", "miracle", "overnight", "in 7 days", "in a week",
]
DISCLAIMER = "General fitness information, not medical advice. Consult a qualified professional if you have a health concern."

# Initial learning signals based on the channel analytics shared by the owner.
# These are topic-level clues, not proof that every video on these topics will succeed.
STARTER_MEMORY = {
    "version": 1,
    "source": "Initial channel analytics shared by owner; topic-level summary",
    "baseline": {"total_views": 7248, "watch_hours": 13.86, "subscribers": 60,
                 "impressions": 7454, "ctr_percent": 2.07,
                 "viewed_vs_swiped_percent": 38.2, "average_percentage_viewed": 31},
    "topic_signals": [
        {"topic": "NEAT and daily movement", "category": "fat_loss_habits", "signal": "strong_views_and_subscribers", "confidence": "medium"},
        {"topic": "hunger, hormones and satiety", "category": "nutrition_and_hunger", "signal": "strong_views", "confidence": "medium"},
        {"topic": "muscle building methods and muscle growth", "category": "muscle_building", "signal": "strong_views_and_subscribers", "confidence": "medium"},
        {"topic": "eating late at night and fat gain", "category": "fat_loss_myths", "signal": "strong_views_and_subscribers", "confidence": "medium"},
        {"topic": "water and hydration for training", "category": "training_recovery", "signal": "strong_views_and_good_ctr", "confidence": "medium"},
        {"topic": "loaded stretch and exercise technique", "category": "exercise_technique", "signal": "good_ctr_and_subscribers", "confidence": "low"},
    ],
    "avoid_overusing": ["generic gym motivation", "generic workout footage", "repeated muscle growth myths"],
    "learning_note": "Update this file with per-video analytics as more reliable data becomes available."
}


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_used():
    data = load_json("used_topics.json", [])
    return data if isinstance(data, list) else []


def mark_used(topic):
    """Called by upload.py after a successful upload."""
    used = load_used()
    if topic and topic not in used:
        used.append(topic)
    save_json("used_topics.json", used)


def load_trends():
    data = load_json("output/trends.json", [])
    return [t for t in data if isinstance(t, dict) and t.get("topic")] if isinstance(data, list) else []


def load_performance_memory():
    memory = load_json(MEMORY_FILE, None)
    if not isinstance(memory, dict):
        memory = STARTER_MEMORY.copy()
        save_json(MEMORY_FILE, memory)
    # Fill missing sections without overwriting later user edits.
    for key, value in STARTER_MEMORY.items():
        memory.setdefault(key, value)
    return memory


def choose_content_type(used, memory):
    """Rotate formats while gently prioritizing evidence-backed topic categories."""
    counts = defaultdict(int)
    used_text = " ".join(str(x).lower() for x in used[-30:])
    for item in memory.get("topic_signals", []):
        category = item.get("category")
        if category:
            counts[category] += 1

    # Do not lock the channel into one niche; use a balanced rotation.
    preferred = [
        "a practical muscle-building technique with one clear action",
        "a fat-loss habit or myth explained with a concrete example",
        "a nutrition idea that helps control hunger or improve protein intake",
        "an exercise technique correction viewers can try immediately",
        "a recovery or training-performance habit with a clear payoff",
        "a realistic food comparison or high-protein meal idea",
    ]
    index = len(used) % len(preferred)
    selected = preferred[index]
    if "muscle" in used_text and "fat loss" not in used_text:
        selected = preferred[(index + 1) % len(preferred)]
    return selected


def performance_context(memory):
    baseline = memory.get("baseline", {})
    signals = memory.get("topic_signals", [])
    lines = []
    for item in signals[:10]:
        lines.append(
            f"- Topic: {item.get('topic', 'unknown')}; category: {item.get('category', 'general')}; "
            f"observed signal: {item.get('signal', 'unrated')}; confidence: {item.get('confidence', 'low')}"
        )
    baseline_text = (
        f"Channel baseline: {baseline.get('viewed_vs_swiped_percent', 'unknown')}% viewed vs swiped; "
        f"{baseline.get('average_percentage_viewed', 'unknown')}% average percentage viewed. "
        "Treat these as channel-level baselines, not targets guaranteed for every Short."
    )
    return baseline_text + ("\nTopic performance clues (use as soft guidance, not guarantees):\n" + "\n".join(lines) if lines else "")


def build_prompt(content_type, used, trends, memory):
    recent = ", ".join(str(x) for x in used[-80:]) if used else "none yet"
    trend_block = ""
    if trends:
        lines = "\n".join(
            f"- {t.get('topic')} (safe angle: {t.get('safe_angle', '')})" for t in trends[:8]
        )
        trend_block = f"\nPotential timely topics (use only if relevant and evidence-based):\n{lines}\n"

    return f'''You are the short-form video scriptwriter for FitFuel, a practical fitness channel about building muscle and losing fat.
Your job is to make viewers STOP scrolling, understand one useful idea instantly, and stay until the payoff.

TODAY'S ANGLE: {content_type}

CHANNEL PERFORMANCE LEARNING:
{performance_context(memory)}
Use performance clues to choose a promising angle, but do not repeat a successful topic word-for-word. Balance proven themes with fresh useful ideas. Optimize for viewer satisfaction and clarity, not clickbait.
{trend_block}
Recently used topics (avoid repeating or closely copying): {recent}

Return ONLY valid JSON with exactly these keys:
{{
  "topic": "unique 3-6 word label",
  "title": "clear, curiosity-driven title, maximum 60 characters",
  "description": "one or two concise sentences",
  "hashtags": ["4 to 6 relevant hashtags without #"],
  "scenes": [
    {{"narration": "spoken words for this scene", "keyword": "filmable search 1 | filmable search 2 | filmable search 3"}}
  ]
}}

RETENTION STRUCTURE â€” follow this order:
1) HOOK (first 1-2 seconds): 4-9 spoken words. Start with a specific problem, surprising contrast, direct challenge, or useful result. No greeting, channel name, setup, or generic openings.
2) PAYOFF PROMISE: tell viewers exactly what they will learn or fix. Do not say â€œwatch until the endâ€.
3) VALUE: explain one main idea with a concrete example and a simple action. Keep each scene focused on one thought.
4) PAYOFF / LOOP: deliver the promised answer. End with a short phrase that naturally echoes the opening idea.

STRICT SCRIPT RULES:
- Create 4 or 5 scenes only.
- Total narration: 45-65 spoken words, designed for roughly 18-27 seconds at a natural speaking pace.
- Hook scene: 4-9 words. Each later scene: usually 8-17 words.
- One video = one idea. Do not cram multiple tips into one Short.
- Use â€œyouâ€ and everyday language. Be specific, energetic, and conversational.
- Deliver a real answer. No exaggerated claims, fake urgency, unsupported statistics, or empty motivational lines.
- Use numbers only when reliable and useful. Never invent studies or statistics.
- No long intro, greeting, recap, like-and-subscribe, or spoken disclaimer.
- Title must accurately match the video and include the main topic naturally.
- Description: concise, relevant, no keyword stuffing. Hashtags: 4-6 relevant tags.
- Only established, evidence-based fitness advice: progressive overload, calorie balance, adequate protein, exercise technique, sleep, recovery, and consistency.
- Never promote steroids, SARMs, fat burners, detoxes, miracle products, extreme diets, medical treatment, or spot reduction. Never promise a result or timeframe.

VISUAL SEARCH RULES:
- Every scene needs 2-3 DIFFERENT, realistic, filmable stock-footage searches separated by |.
- Every search must visibly show the exact action, food, or equipment being discussed.
- Include concrete terms such as dumbbell, squat, barbell, chicken breast, eggs, rice, salad, or meal prep when relevant.
- No abstract concepts, text graphics, offices, cities, nature, money, crowds, or named people/brands.
- Match the footage to that scene's spoken point, not generic gym footage in every scene.

Return JSON only. No markdown and no extra keys.'''


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def repair_keywords(data):
    for scene in data.get("scenes", []):
        original = str(scene.get("keyword", ""))
        valid = []
        for keyword in (k.strip() for k in original.split("|")):
            if keyword and keyword_is_relevant(keyword) and keyword.lower() not in [v.lower() for v in valid]:
                valid.append(keyword)
        for fallback in fallbacks_for(scene.get("narration", "")):
            if len(valid) >= 3:
                break
            if keyword_is_relevant(fallback) and fallback.lower() not in [v.lower() for v in valid]:
                valid.append(fallback)
        if not valid:
            valid = ["gym workout", "healthy food"]
        scene["keyword"] = " | ".join(valid[:3])
    return data


def validate(data):
    required = ("topic", "title", "description", "hashtags", "scenes")
    for key in required:
        if key not in data:
            return f"missing key: {key}"
    if not isinstance(data["scenes"], list) or not 4 <= len(data["scenes"]) <= 5:
        return "needs 4 or 5 scenes"
    if not isinstance(data["hashtags"], list) or not 4 <= len(data["hashtags"]) <= 6:
        return "needs 4 to 6 hashtags"
    word_counts = []
    for scene in data["scenes"]:
        if not isinstance(scene, dict):
            return "invalid scene format"
        narration = str(scene.get("narration", "")).strip()
        if not narration:
            return "empty narration"
        word_counts.append(len(narration.split()))
        keywords = [k.strip() for k in str(scene.get("keyword", "")).split("|") if k.strip()]
        if not keywords:
            return "empty keyword"
        if not any(keyword_is_relevant(k) for k in keywords):
            return f"keyword not about training or food: {scene.get('keyword')}"
    total_words = sum(word_counts)
    if not 45 <= total_words <= 65:
        return f"narration is {total_words} words (target 45-65)"
    if not 4 <= word_counts[0] <= 9:
        return f"hook is {word_counts[0]} words (target 4-9)"
    if len(str(data["title"]).strip()) > 60:
        return "title exceeds 60 characters"
    if len(str(data["topic"]).split()) < 2:
        return "topic label is too vague"
    everything = json.dumps(data, ensure_ascii=False).lower()
    for bad in BANNED:
        if bad in everything:
            return f"contains banned phrase: {bad}"
    if too_similar(str(data["topic"]), all_used()):
        return "topic too close to one already used"
    return None


def generate_script():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=api_key)
    used = load_used()
    trends = load_trends()
    memory = load_performance_memory()
    content_type = choose_content_type(used, memory)
    print(f"Video angle: {content_type}")
    print("Using channel performance memory:", MEMORY_FILE)
    prompt = build_prompt(content_type, all_used(), trends, memory)
    max_attempts = 4
    last_problem = "Unknown error"

    for attempt in range(1, max_attempts + 1):
        print(f"\nGeneration attempt {attempt}/{max_attempts}")
        for model in MODEL_CANDIDATES:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.85, response_mime_type="application/json"),
                )
                if not response.text:
                    last_problem = "Empty Gemini response"
                    print(f"{model}: {last_problem}")
                    continue
                data = repair_keywords(parse_json(response.text))
                problem = validate(data)
                if problem:
                    last_problem = problem
                    print(f"{model}: Invalid script: {problem}")
                    prompt += f"\n\nThe previous output failed: {problem}. Generate a completely NEW script and obey every constraint. Return JSON only."
                    continue
                print(f"Successfully generated script using: {model}")
                print(f"Validated narration length: {sum(len(s['narration'].split()) for s in data['scenes'])} words")
                return data
            except Exception as exc:
                last_problem = str(exc)
                print(f"{model} failed: {last_problem[:250]}")
        if attempt < max_attempts:
            delay = min(5 * (2 ** (attempt - 1)), 30)
            print(f"Waiting {delay} seconds before retry...")
            time.sleep(delay)
    raise RuntimeError(f"Could not generate a valid script after {max_attempts} attempts. Last error: {last_problem}")


def finalize(data):
    tags = []
    for hashtag in data["hashtags"]:
        tag = "#" + str(hashtag).strip().lstrip("#").replace(" ", "")
        if tag not in tags:
            tags.append(tag)
    if "#Shorts" not in tags:
        tags.append("#Shorts")
    data["description"] = f"{data['description'].strip()}\n\n{' '.join(tags)}\n\n{DISCLAIMER}\n\nVideo clips and music: Pixabay."
    data["title"] = data["title"].strip()[:60]
    return data


if __name__ == "__main__":
    script = finalize(generate_script())
    os.makedirs("output", exist_ok=True)
    with open("output/script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print("\nTITLE:", script["title"])
    print("TOPIC:", script["topic"])
    for i, scene in enumerate(script["scenes"], 1):
        print(f"\nScene {i} [{scene['keyword']}]\n{scene['narration']}")
    print("\nSaved to output/script.json")    print("\nSaved to output/script.json")