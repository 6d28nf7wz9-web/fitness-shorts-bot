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

            except (OSError, json.JSONDecodeError):
                pass

        return out

    def too_similar(topic, used):
        words = set(re.findall(r"[a-z0-9]+", topic.lower()))

        for old in used:
            old_words = set(
                re.findall(r"[a-z0-9]+", str(old).lower())
            )

            if topic.strip().lower() == str(old).strip().lower():
                return True

            if (
                len(words) >= 3
                and len(words & old_words) / len(words) >= 0.8
            ):
                return True

        return False


try:
    from relevance import keyword_is_relevant, fallbacks_for

except ImportError:
    def keyword_is_relevant(text):
        return True

    def fallbacks_for(text):
        return [
            "gym workout",
            "weight training",
            "healthy food",
            "cooking healthy meal",
            "meal prep",
        ]


def get_model_candidates():
    """Build a de-duplicated primary + fallback model list.

    Override the fallback order with GEMINI_FALLBACK_MODELS,
    a comma-separated list of model IDs available to your API key.
    """
    primary = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    ).strip()

    configured = os.getenv(
        "GEMINI_FALLBACK_MODELS",
        ""
    ).strip()

    if configured:
        fallbacks = [
            item.strip()
            for item in configured.split(",")
            if item.strip()
        ]
    else:
        fallbacks = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
        ]

    candidates = []

    for model in [primary, *fallbacks]:
        if model and model not in candidates:
            candidates.append(model)

    return candidates


MEMORY_FILE = "performance_memory.json"

from series_engine import next_episode, SERIES as SERIES_PLAN

SERIES = list(SERIES_PLAN)

BANNED = [
    "fat burner",
    "fat-burner",
    "detox",
    "guaranteed",
    "spot reduc",
    "miracle",
    "overnight",
    "in 7 days",
    "in a week",
]

DISCLAIMER = (
    "General fitness information, not medical advice. "
    "Consult a qualified professional if you have a health concern."
)


STARTER_MEMORY = {
    "version": 1,
    "source": "Initial channel analytics shared by owner; topic-level summary",
    "baseline": {
        "total_views": 7248,
        "watch_hours": 13.86,
        "subscribers": 60,
        "impressions": 7454,
        "ctr_percent": 2.07,
        "viewed_vs_swiped_percent": 38.2,
        "average_percentage_viewed": 31,
    },
    "topic_signals": [
        {
            "topic": "NEAT and daily movement",
            "category": "fat_loss_habits",
            "signal": "strong_views_and_subscribers",
            "confidence": "medium",
        },
        {
            "topic": "hunger, hormones and satiety",
            "category": "nutrition_and_hunger",
            "signal": "strong_views",
            "confidence": "medium",
        },
        {
            "topic": "muscle building methods and muscle growth",
            "category": "muscle_building",
            "signal": "strong_views_and_subscribers",
            "confidence": "medium",
        },
        {
            "topic": "eating late at night and fat gain",
            "category": "fat_loss_myths",
            "signal": "strong_views_and_subscribers",
            "confidence": "medium",
        },
        {
            "topic": "water and hydration for training",
            "category": "training_recovery",
            "signal": "strong_views_and_good_ctr",
            "confidence": "medium",
        },
        {
            "topic": "loaded stretch and exercise technique",
            "category": "exercise_technique",
            "signal": "good_ctr_and_subscribers",
            "confidence": "low",
        },
    ],
    "avoid_overusing": [
        "generic gym motivation",
        "generic workout footage",
        "repeated muscle growth myths",
    ],
    "learning_note": (
        "Update this file with per-video analytics "
        "as more reliable data becomes available."
    ),
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

    if not isinstance(data, list):
        return []

    return [
        trend
        for trend in data
        if isinstance(trend, dict) and trend.get("topic")
    ]


def load_performance_memory():
    memory = load_json(MEMORY_FILE, None)

    if not isinstance(memory, dict):
        memory = json.loads(json.dumps(STARTER_MEMORY))
        save_json(MEMORY_FILE, memory)

    for key, value in STARTER_MEMORY.items():
        if key not in memory:
            memory[key] = value

    return memory


def choose_content_type(used, memory):
    """Rotate formats while gently prioritizing proven topic categories."""

    counts = defaultdict(int)

    used_text = " ".join(
        str(topic).lower() for topic in used[-30:]
    )

    for item in memory.get("topic_signals", []):
        category = item.get("category")

        if category:
            counts[category] += 1

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


def choose_series(used):
    """Select the next planned episode based only on successful uploads."""
    return next_episode()


def performance_context(memory):
    baseline = memory.get("baseline", {})
    signals = memory.get("topic_signals", [])
    lines = []

    for item in signals[:10]:
        lines.append(
            f"- Topic: {item.get('topic', 'unknown')}; "
            f"category: {item.get('category', 'general')}; "
            f"observed signal: {item.get('signal', 'unrated')}; "
            f"confidence: {item.get('confidence', 'low')}"
        )

    baseline_text = (
        f"Channel baseline: "
        f"{baseline.get('viewed_vs_swiped_percent', 'unknown')}% "
        f"viewed vs swiped; "
        f"{baseline.get('average_percentage_viewed', 'unknown')}% "
        f"average percentage viewed. "
        "Treat these as channel-level baselines, not targets guaranteed for every Short."
    )

    series_insights = memory.get("series_insights", [])
    reliable_series = [
        item for item in series_insights
        if isinstance(item, dict) and int(item.get("videos", 0) or 0) >= 2
    ]
    if reliable_series:
        lines.append("Recurring-series performance (minimum 2 measured videos; descriptive, not causal):")
        for item in reliable_series[:4]:
            lines.append(
                f"- {item.get('series')}: {item.get('videos')} videos; "
                f"{item.get('avg_view_percentage')}% average viewed; "
                f"{item.get('avg_engaged_views_per_video')} average engaged views; "
                f"{item.get('subscribers_gained')} subscribers gained."
            )

    topic_insights = memory.get("topic_insights", [])
    reliable_topics = [
        item for item in topic_insights
        if isinstance(item, dict) and int(item.get("videos", 0) or 0) >= 2
    ]
    if reliable_topics:
        ranked_topics = sorted(
            reliable_topics,
            key=lambda item: (
                item.get("avg_view_percentage", 0),
                item.get("avg_engaged_views_per_video", 0),
            ),
            reverse=True,
        )
        lines.append(
            "Topic-level patterns (only topics with at least 2 measured videos; "
            "descriptive, small-sample evidence—not causal):"
        )
        for item in ranked_topics[:5]:
            lines.append(
                f"- {item.get('topic')}: {item.get('videos')} videos; "
                f"{item.get('avg_view_percentage')}% average viewed; "
                f"{item.get('avg_engaged_views_per_video')} average engaged views per video."
            )

    # First-week metrics make new Shorts comparable at the same age.
    first_week = memory.get("first_week_analytics", {}).get("videos", {})
    if isinstance(first_week, dict) and first_week:
        uploads = memory.get("video_performance", [])
        metadata = {
            item.get("video_id"): item
            for item in uploads
            if isinstance(item, dict) and item.get("video_id")
        }
        completed = [
            (video_id, stats) for video_id, stats in first_week.items()
            if stats.get("first_7_days_complete")
        ]
        completed.sort(
            key=lambda pair: (
                pair[1].get("average_view_percentage_first_7_days", 0),
                pair[1].get("engaged_views_first_7_days", 0),
            ),
            reverse=True,
        )
        if completed:
            lines.append(
                "Comparable first-seven-day results (only complete windows; "
                "compare hook/topic patterns, not causation):"
            )
            for video_id, stats in completed[:5]:
                item = metadata.get(video_id, {})
                lines.append(
                    f"- {item.get('topic') or item.get('title') or video_id}: "
                    f"{stats.get('views_first_7_days', 0)} views and "
                    f"{stats.get('engaged_views_first_7_days', 0)} engaged views "
                    f"in the first 7 days; "
                    f"{stats.get('average_view_percentage_first_7_days', 0)}% average viewed. "
                    f"Hook: {item.get('hook', 'not recorded')}"
                )

    first_week_topics = memory.get("first_week_topic_insights", [])
    comparable_topics = [
        item for item in first_week_topics
        if isinstance(item, dict) and int(item.get("videos", 0) or 0) >= 2
    ]
    if comparable_topics:
        comparable_topics.sort(
            key=lambda item: (
                item.get("avg_view_percentage_first_7_days", 0),
                item.get("avg_engaged_views_first_7_days", 0),
            ),
            reverse=True,
        )
        lines.append("Topic patterns from complete first-seven-day windows (minimum 2 videos):")
        for item in comparable_topics[:5]:
            lines.append(
                f"- {item.get('topic')}: {item.get('videos')} videos; "
                f"{item.get('avg_view_percentage_first_7_days')}% average viewed; "
                f"{item.get('avg_engaged_views_first_7_days')} average engaged views."
            )

    # Individual examples are useful for studying hooks, but compare similar-age videos.
    videos = memory.get("analytics", {}).get("videos", {})
    if isinstance(videos, dict) and videos:
        uploads = memory.get("video_performance", [])
        metadata = {
            item.get("video_id"): item
            for item in uploads
            if isinstance(item, dict) and item.get("video_id")
        }
        ranked = sorted(
            videos.items(),
            key=lambda pair: (
                pair[1].get("average_view_percentage", 0),
                pair[1].get("engaged_views", 0),
                pair[1].get("views", 0),
            ),
            reverse=True,
        )
        lines.append(
            "Recent video-level evidence (28-day reporting window; "
            "compare videos at similar age; NOT causal):"
        )
        for video_id, stats in ranked[:5]:
            item = metadata.get(video_id, {})
            lines.append(
                f"- {item.get('topic') or item.get('title') or video_id}: "
                f"{stats.get('views', 0)} views, "
                f"{stats.get('engaged_views', 0)} engaged views, "
                f"{stats.get('average_view_percentage', 0)}% average viewed, "
                f"{stats.get('average_view_duration_seconds', 0)}s average duration, "
                f"{stats.get('subscribers_gained', 0)} subscribers gained. "
                f"Opening hook: {item.get('hook', 'not recorded')}"
            )
        lines.append(
            "Use these hooks as examples to study specificity and curiosity; "
            "do not copy wording or infer causation from a single video."
        )

    if lines:
        return baseline_text + chr(10) + "Performance evidence (soft guidance only):" + chr(10) + chr(10).join(lines)
    return baseline_text

def build_prompt(content_type, used, trends, memory, research, series=None):
    series = series or SERIES[len(used) % len(SERIES)]
    recent = (
        ", ".join(str(topic) for topic in used[-80:])
        if used
        else "none yet"
    )

    trend_block = ""

    if trends:
        lines = "\n".join(
            f"- {trend.get('topic')} "
            f"(safe angle: {trend.get('safe_angle', '')})"
            for trend in trends[:8]
        )

        trend_block = (
            "\nPotential timely topics "
            "(use only if relevant and evidence-based):\n"
            f"{lines}\n"
        )

    research_block = chr(10).join(
        f"- PMID {p['pmid']} | {p.get('title', '')} | {p.get('journal', '')} ({p.get('year', '')}) | DOI: {p.get('doi') or 'none'} | Abstract: {p.get('abstract', '')}"
        for p in research
    ) or "No PubMed records retrieved. Use conservative established guidance only and return sources=[]; never fabricate citations."

    return f'''
You are the short-form video scriptwriter for FitFuel,
a practical fitness channel about building muscle and losing fat.

Your job is to make viewers STOP scrolling,
understand one useful idea instantly,
and stay until the payoff.

TODAY'S SERIES: {series}
Approved series names: {', '.join(SERIES)}. Use the assigned series exactly.
TODAY'S ANGLE: {content_type}

CHANNEL PERFORMANCE LEARNING:

{performance_context(memory)}

Use performance clues to choose a promising angle,
but do not repeat a successful topic word-for-word.
Balance proven themes with fresh useful ideas.
Optimize for viewer satisfaction and clarity, not clickbait.

{trend_block}

Recently used topics (avoid repeating or closely copying):
{recent}

SCIENTIFIC SOURCES FROM PUBMED (verified records):
{research_block}
Use only these papers as evidence. Claims must not exceed their abstracts. Never invent statistics, PMIDs, DOIs, authors, or journals. Include 1-4 supplied PMIDs supporting the main claims in sources; if none, use [].

Return ONLY valid JSON with exactly these keys:

{{
  "series": "one exact FitFuel series name from the approved list",
  "topic": "unique 3-6 word label",
  "title": "clear, curiosity-driven title, maximum 60 characters",
  "description": "one or two concise sentences",
  "hashtags": ["4 to 6 relevant hashtags without #"],\n  "sources": ["PubMed PMID from supplied list"],
  "scenes": [
    {{"narration": "one complete spoken sentence", "visual_title": "short slide headline", "visual_subtitle": "3-6 word takeaway", "visual_type": "one supported science visual type", "visual_instruction": "specific anatomical or physiological scene with objects, movement, and labels", "keyword": "filmable search 1 | filmable search 2 | filmable search 3"}}
  ]
}}

RETENTION STRUCTURE - follow this order:

1) HOOK (first 1-2 seconds):
4-9 spoken words.
Choose ONE hook mechanism and rotate it across uploads: a specific problem,
a surprising contrast, a direct challenge, or a concrete result.
Do not reuse the same opening structure in consecutive Shorts.
Use the strongest measured hooks as inspiration for specificity, never copy wording.
No greeting, channel name, setup, or generic openings.

2) PAYOFF PROMISE:
Tell viewers exactly what they will learn or fix.
Do not say "watch until the end".

3) VALUE:
Explain one main idea with a concrete example
and a simple action.
Keep each scene focused on one thought.

4) PAYOFF / LOOP:
Deliver the promised answer.
End with a short phrase that naturally echoes the opening idea.

STRICT SCRIPT RULES:

- Create 4 to 5 scenes. Every scene is exactly ONE spoken sentence and its own visual slide.\n- Each sentence must trigger a distinct slide/visual state; never leave one static diagram for multiple sentences.\n- Add visual_title (2-5 words), visual_subtitle (3-6 words), visual_type, and visual_instruction to every scene.
- visual_type must be one of: digestion_fiber, muscle_anatomy, exercise_biomechanics, protein_synthesis, energy_metabolism, hydration, recovery_sleep, food_nutrition, process.
- visual_instruction must describe the actual subject anatomy/process, what moves, where it moves, and the key visual labels; do not describe a generic title card.
- Match the illustration to the exact spoken sentence. If explaining dietary fiber, show food fiber travelling through the digestive tract and its relevant effect; if explaining an exercise, show the body position, joints, and muscles involved; if explaining a muscle, show that muscle anatomically; if explaining metabolism, show the actual energy pathway.
- Total narration: aim for 52-58 spoken words (hard limit 45-65),
  designed for roughly 18-27 seconds at a natural speaking pace.
- Count spoken words before returning JSON; stay comfortably inside the limit.
- Hook scene: 4-9 words.
- Each later scene: usually 8-17 words.
- One video = one idea. Do not cram multiple tips into one Short.
- Use "you" and everyday language.
- Be specific, energetic, and conversational.
- Deliver a real answer.
- No exaggerated claims, fake urgency, unsupported statistics,
  or empty motivational lines.
- Use numbers only when reliable and useful.
- Never invent studies or statistics.
- No long intro, greeting, recap, generic like-and-subscribe,
  or spoken disclaimer. The final scene MUST include a natural topic-specific
  question mark and the exact word "follow" with a brief FitFuel invitation.
- Before returning, verify: 4-5 scenes, 52-58 total narration words,
  first scene 4-9 words, final scene has "?" and "follow", and sources
  are selected only from the supplied PMID list.
- Title must accurately match the video
  and include the main topic naturally.
- Description: concise, relevant, no keyword stuffing.
- Hashtags: 4-6 relevant tags.
- Cover evidence-based fitness advice and controversial topics (including anabolic steroids, TRT, hormones, and PEDs) in a balanced, educational, non-promotional way.
- Explain risks and uncertainty clearly; never provide steroid/SARM cycles, doses, sourcing, stacking, or instructions to evade medical supervision.
- Distinguish prescribed TRT for diagnosed conditions from nonmedical anabolic-steroid use; do not equate them.
- Never promote fat burners, detoxes, miracle products, extreme diets, or spot reduction.
- Never promise a result or timeframe.

VISUAL SEARCH RULES:

- Every scene needs 2-3 DIFFERENT, realistic,
  filmable stock-footage searches separated by |.
- Every search must visibly show the exact action,
  food, or equipment being discussed.
- Include concrete terms such as dumbbell, squat, barbell,
  chicken breast, eggs, rice, salad, or meal prep when relevant.
- No abstract concepts, text graphics, offices, cities,
  nature, money, crowds, or named people/brands.
- Match the footage to that scene's spoken point,
  not generic gym footage in every scene.

Return JSON only. No markdown and no extra keys.
'''


def parse_json(response_text):
    text = response_text.strip()

    text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text,
        flags=re.MULTILINE,
    ).strip()

    data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Gemini response must be a JSON object")

    return data


def repair_keywords(data):
    for scene in data.get("scenes", []):
        original = str(scene.get("keyword", ""))

        valid = []

        for keyword in (
            item.strip()
            for item in original.split("|")
        ):
            if (
                keyword
                and keyword_is_relevant(keyword)
                and keyword.lower() not in [
                    value.lower() for value in valid
                ]
            ):
                valid.append(keyword)

        for fallback in fallbacks_for(
            scene.get("narration", "")
        ):
            if len(valid) >= 3:
                break

            if (
                keyword_is_relevant(fallback)
                and fallback.lower() not in [
                    value.lower() for value in valid
                ]
            ):
                valid.append(fallback)

        if not valid:
            valid = ["gym workout", "healthy food"]

        scene["keyword"] = " | ".join(valid[:3])

    return data


def validate(data):
    required = (
        "series",
        "sources",
        "topic",
        "title",
        "description",
        "hashtags",
        "scenes",
    )

    for key in required:
        if key not in data:
            return f"missing key: {key}"

    if data.get("series") not in SERIES:
        return "series must be one of the four approved FitFuel series"

    if (
        not isinstance(data["scenes"], list)
        or not 4 <= len(data["scenes"]) <= 5
    ):
        return "needs 4 or 5 scenes"

    if (
        not isinstance(data["hashtags"], list)
        or not 4 <= len(data["hashtags"]) <= 6
    ):
        return "needs 4 to 6 hashtags"

    word_counts = []

    for scene in data["scenes"]:
        if not isinstance(scene, dict):
            return "invalid scene format"

        narration = str(
            scene.get("narration", "")
        ).strip()

        if not narration:
            return "empty narration"

        word_counts.append(len(narration.split()))

        keywords = [
            keyword.strip()
            for keyword in str(
                scene.get("keyword", "")
            ).split("|")
            if keyword.strip()
        ]

        if not keywords:
            return "empty keyword"

        if not any(
            keyword_is_relevant(keyword)
            for keyword in keywords
        ):
            return (
                "keyword not about training or food: "
                f"{scene.get('keyword')}"
            )

    if not isinstance(data.get("sources"), list):
        return "sources must be a list of PubMed PMIDs"
    known_pmids = {str(p.get("pmid")) for p in load_json("output/research_sources.json", []) if isinstance(p, dict)}
    cited = [str(p).strip() for p in data.get("sources", [])]
    if any(p not in known_pmids for p in cited):
        return "sources contains PMID not retrieved from PubMed"
    if len(cited) > 5:
        return "maximum 5 references"

    total_words = sum(word_counts)

    final_line = str(data["scenes"][-1].get("narration", "")).lower()
    if "?" not in final_line or not any(word in final_line for word in ("follow", "next episode", "next part")):
        return "final scene needs a comment question and a short follow invitation"

    if not 45 <= total_words <= 65:
        return (
            f"narration is {total_words} words "
            "(target 45-65)"
        )

    if not 4 <= word_counts[0] <= 9:
        return (
            f"hook is {word_counts[0]} words "
            "(target 4-9)"
        )

    hook = str(data["scenes"][0].get("narration", "")).strip().lower()
    weak_openers = (
        "hey guys", "hello everyone", "welcome back",
        "in this video", "today we are", "today i'm going",
        "did you know", "let's talk about",
    )
    if any(hook.startswith(opening) for opening in weak_openers):
        return "hook starts with a generic greeting/setup; lead with the viewer problem or payoff"
    if hook.endswith("?") and len(hook.split()) < 5:
        return "hook question is too short to establish a specific curiosity"

    if len(str(data["title"]).strip()) > 60:
        return "title exceeds 60 characters"

    if len(str(data["topic"]).split()) < 2:
        return "topic label is too vague"

    everything = json.dumps(
        data,
        ensure_ascii=False
    ).lower()

    for bad in BANNED:
        if bad in everything:
            return f"contains banned phrase: {bad}"

    if too_similar(
        str(data["topic"]),
        all_used()
    ):
        return "topic too close to one already used"

    return None


def _is_quota_exhausted(exc):
    """Detect hard account/project quota exhaustion (not a brief RPM throttle)."""
    message = str(exc).lower()
    markers = (
        "exceeded your current quota",
        "quota exceeded",
        "billing details",
        "generate_requests_per_model",
        "free_tier_requests",
    )
    return any(marker in message for marker in markers)


def _is_temporary_gemini_error(exc):
    """Return True for rate limits and temporary Gemini service failures."""
    message = str(exc).lower()
    status = (
        getattr(exc, "code", None)
        or getattr(exc, "status_code", None)
    )

    temporary_markers = (
        "503",
        "unavailable",
        "high demand",
        "429",
        "resource_exhausted",
        "rate limit",
        "500",
        "502",
        "504",
        "internal error",
        "deadline exceeded",
        "temporarily",
    )

    return (
        status in (429, 500, 502, 503, 504)
        or any(marker in message for marker in temporary_markers)
    )


def _generate_with_retry(client, model, prompt, retries=1):
    """Try a model briefly; let the caller move to a fallback quickly."""

    for retry in range(retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    response_mime_type="application/json",
                ),
            )

        except Exception as exc:
            if (
                not _is_temporary_gemini_error(exc)
                or retry >= retries
            ):
                raise

            delay = min(3 * (2 ** retry), 6)

            print(
                f"Temporary Gemini error for {model} "
                f"(retry {retry + 1}/{retries}): "
                f"{str(exc)[:160]}"
            )

            print(
                f"Retrying this model once in {delay} seconds..."
            )

            time.sleep(delay)


def generate_script():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    used = load_used()
    trends = load_trends()
    memory = load_performance_memory()

    series, episode_number, episode_topic = choose_series(used)
    content_type = episode_topic
    print(f"Video series: {series} | Episode {episode_number}")
    print(f"Episode topic: {episode_topic}")
    print("Using channel performance memory:", MEMORY_FILE)

    from research_sources import research_for_topic
    research = research_for_topic(content_type)

    prompt = build_prompt(
        content_type,
        all_used(),
        trends,
        memory,
        research,
        series,
    )

    model_candidates = get_model_candidates()

    print(
        "Gemini model fallback order:",
        " -> ".join(model_candidates)
    )

    max_attempts = 3
    last_problem = "Unknown error"
    quota_failures = []

    for attempt in range(1, max_attempts + 1):
        print(
            f"\nGeneration attempt {attempt}/{max_attempts}"
        )

        api_failures = 0

        for model in model_candidates:
            try:
                response = _generate_with_retry(
                    client,
                    model,
                    prompt,
                    retries=1
                )

                if not response.text:
                    last_problem = "Empty Gemini response"
                    print(f"{model}: {last_problem}")
                    continue

                data = repair_keywords(
                    parse_json(response.text)
                )

                problem = validate(data)

                if problem:
                    last_problem = problem

                    print(
                        f"{model}: Invalid script: {problem}"
                    )

                    prompt += (
                        "\n\nThe previous output failed: "
                        f"{problem}. Generate a completely NEW script "
                        "and obey every constraint. Return JSON only."
                    )

                    continue

                print(
                    f"Successfully generated script using: {model}"
                )

                total_words = sum(
                    len(scene["narration"].split())
                    for scene in data["scenes"]
                )

                print(
                    f"Validated narration length: "
                    f"{total_words} words"
                )

                data["episode_number"] = episode_number
                data["episode_topic"] = episode_topic
                return data

            except Exception as exc:
                last_problem = str(exc)
                api_failures += 1
                if _is_quota_exhausted(exc):
                    quota_failures.append(model)

                print(
                    f"{model} failed; moving to next model: "
                    f"{last_problem[:220]}"
                )

        # Hard account quota exhaustion is not fixed by repeating the same prompt.
        if quota_failures:
            raise RuntimeError(
                "Gemini account/project quota is exhausted for this run. "
                "The configured fallback models returned quota errors: "
                f"{', '.join(quota_failures)}. Check Google AI Studio billing "
                "and per-model request/token quotas, or use an API key/project "
                "with available quota. "
                f"Last error: {last_problem[:300]}"
            )

        if api_failures == len(model_candidates):
            raise RuntimeError(
                "All configured Gemini models failed. "
                "Check model access/quota or set GEMINI_MODEL and "
                "GEMINI_FALLBACK_MODELS to model IDs enabled for your API key. "
                f"Last error: {last_problem}"
            )

        if attempt < max_attempts:
            delay = min(
                5 * (2 ** (attempt - 1)),
                30,
            )

            print(
                f"Waiting {delay} seconds before retry..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Could not generate a valid script after "
        f"{max_attempts} attempts. Last error: {last_problem}"
    )


def finalize(data):
    tags = []
    for hashtag in data["hashtags"]:
        tag = "#" + str(hashtag).strip().lstrip("#").replace(" ", "")
        if tag not in tags:
            tags.append(tag)
    if "#Shorts" not in tags:
        tags.append("#Shorts")

    from research_sources import references_block
    all_papers = load_json("output/research_sources.json", [])
    cited_pmids = {str(x) for x in data.get("sources", [])}
    cited_papers = [p for p in all_papers if str(p.get("pmid")) in cited_pmids]
    data["references"] = cited_papers
    ref_text = references_block(cited_papers)
    data["description"] = (
        f"Series: {data.get('series', 'FitFuel')}\n"
        f"{data['description'].strip()}\n\n"
        f"{' '.join(tags)}\n\n"
        f"{DISCLAIMER}\n\n"
        f"{ref_text}\n\n"
        "Educational illustrations; not medical advice."
    )
    data["title"] = data["title"].strip()[:60]
    return data


if __name__ == "__main__":
    script = finalize(generate_script())

    os.makedirs("output", exist_ok=True)

    with open(
        "output/script.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            script,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\nTITLE:", script["title"])
    print("TOPIC:", script["topic"])

    for i, scene in enumerate(
        script["scenes"],
        1
    ):
        print(
            f"\nScene {i} [{scene['keyword']}]\n"
            f"{scene['narration']}"
        )

    print("\nSaved to output/script.json")