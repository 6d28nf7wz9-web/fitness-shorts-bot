"""Scene-aware relevance scoring for fitness and nutrition stock footage."""

import re

TRAINING = {
    "gym", "workout", "exercise", "fitness", "training", "weight",
    "weights", "weightlifting", "lifting", "dumbbell", "barbell",
    "kettlebell", "squat", "deadlift", "pushup", "pullup", "plank",
    "cardio", "treadmill", "running", "runner", "jogging", "cycling",
    "swimming", "yoga", "stretching", "muscle", "bodybuilding",
    "bodybuilder", "athlete", "sport", "crossfit", "boxing", "abs",
    "biceps", "trainer", "calisthenics", "powerlifting", "strength",
    "warmup", "pilates", "aerobic", "lat", "pulldown", "bench",
    "press", "rowing", "row", "lunge", "lunges", "glute", "shoulder",
    "chest", "triceps", "curl", "curls"
}

FOOD = {
    "food", "meal", "healthy", "nutrition", "diet", "protein",
    "chicken", "egg", "salad", "vegetable", "fruit", "rice",
    "oats", "oatmeal", "breakfast", "lunch", "dinner", "cooking",
    "cook", "kitchen", "fish", "salmon", "meat", "beef", "steak",
    "nuts", "avocado", "smoothie", "yogurt", "grilled", "recipe",
    "eating", "ingredients", "organic", "vegan", "tuna", "beans",
    "lentils", "potato", "banana", "apple", "berries", "broccoli",
    "tomato", "juice", "snack", "vegetables", "fruits", "spinach",
    "carrot", "cheese", "milk", "mealprep"
}

WEAK = {
    "walking", "walk", "hiking", "sleep", "sleeping", "bed",
    "resting", "recovery", "water", "bottle", "scale",
    "measuring", "steps", "stairs"
}

HEALTH_CONTEXT = {
    "fitness", "health", "healthy", "sport", "exercise", "workout",
    "training", "wellness", "lifestyle", "active", "athlete",
    "gym", "diet", "nutrition", "food", "meal"
}

FILLER = {
    "person", "people", "man", "woman", "men", "women",
    "looking", "close", "slow", "motion", "view", "outdoors",
    "outdoor", "with", "and", "the", "front", "back", "side",
    "top", "young", "happy", "friends", "group", "someone",
    "his", "her", "for", "from", "into", "over", "one",
    "doing", "using", "showing", "video", "footage", "clip",
    "professional", "indoors"
}

GENERIC = {
    "gym", "workout", "fitness", "training", "exercise",
    "healthy", "health", "food", "meal", "nutrition", "diet",
    "sport", "person", "people", "weight", "weights", "body"
}

TRAINING_FALLBACKS = [
    "gym workout", "weight training", "fitness training"
]

FOOD_FALLBACKS = [
    "healthy food", "cooking healthy meal", "meal prep"
]


def norm(word):
    word = word.lower()
    if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    return word


def words_of(text):
    return {norm(w) for w in re.findall(r"[a-z]+", str(text).lower())}


_TRAIN = {norm(w) for w in TRAINING}
_FOOD = {norm(w) for w in FOOD}
_STRONG = _TRAIN | _FOOD
_WEAK = {norm(w) for w in WEAK}
_CONTEXT = {norm(w) for w in HEALTH_CONTEXT}
_FILLER = {norm(w) for w in FILLER}
_GENERIC = {norm(w) for w in GENERIC}


def hit_words(hit):
    slug = str(hit.get("pageURL", "")).rstrip("/").split("/")[-1]
    return words_of(f"{hit.get('tags', '')} {slug}")


def keyword_words(keyword):
    return words_of(keyword) - _FILLER


def scene_terms(keyword, context=""):
    terms = (words_of(keyword) | words_of(context)) - _FILLER
    specific = terms - _GENERIC

    # If no distinctive term exists, retain the original terms
    # rather than making matching impossible.
    return specific if specific else terms


def keyword_is_relevant(text):
    w = keyword_words(text)

    if w & _STRONG:
        return True

    if w & _WEAK and w & _CONTEXT:
        return True

    phrases = [
        "muscle gain", "muscle growth", "fat loss", "weight loss",
        "calorie deficit", "strength training", "weight training",
        "resistance training", "meal prep", "high protein",
        "protein rich", "healthy eating", "body composition",
        "personal trainer"
    ]

    return any(p in str(text).lower() for p in phrases)


def relevance(hit, keyword, context=""):
    """0=off-topic, 1=category match, 2=specific keyword match."""

    hw = hit_words(hit)
    query_words = keyword_words(keyword)

    ambiguous = {
        "bench", "press", "row", "lat",
        "water", "bottle", "weight"
    }

    query_specific = query_words - _GENERIC - _WEAK - ambiguous
    matched = hw & query_specific

    # Require at least two specific matching words.
    if len(matched) >= 2:
        return 2

    # Category fallback: only accept footage from the same category.
    target_category = category(keyword)

    if target_category == "food" and hw & _FOOD:
        return 1

    if target_category == "training" and hw & _TRAIN:
        return 1

    return 0


def category(text):
    w = words_of(text)

    return (
        "food"
        if len(w & _FOOD) > len(w & _TRAIN)
        else "training"
    )


def fallbacks_for(text):
    if category(text) == "food":
        return FOOD_FALLBACKS + TRAINING_FALLBACKS

    return TRAINING_FALLBACKS + FOOD_FALLBACKS


def popularity(hit):
    try:
        return (
            int(hit.get("downloads") or 0)
            + 3 * int(hit.get("likes") or 0)
        )
    except (TypeError, ValueError):
        return 0
