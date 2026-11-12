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
    "sport", "person", "people", "weight", "weights", "body",
    # Demographic, posture, and motion descriptors are not proof that a
    # clip depicts the actual subject (e.g. a bird tagged "male" or "sitting").
    "athlete", "male", "female", "sitting", "standing",
    "thoughtfully", "stressed", "preparing", "holding",
    "locker", "room", "running", "swimming"
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
    ambiguous = {"bench", "press", "row", "lat", "water", "bottle", "weight"}
    query_specific = query_words - _GENERIC - _WEAK - ambiguous

    # Only distinctive terms count as direct keyword matches.
    direct_matches = hw & query_specific
    if len(direct_matches) >= 2:
        return 2

    # One distinctive query-word match is enough for a specific match.
    if query_specific and (hw & query_specific):
        return 2

    # Use narration as supporting evidence, not as a replacement for the search query.
    context_specific = scene_terms(keyword, context) - _GENERIC - _WEAK - ambiguous
    if len(hw & context_specific) >= 2:
        return 2

    target_category = category(keyword)
    if target_category not in ("food", "training"):
        target_category = category(context)

    if target_category == "food" and hw & _FOOD:
        return 1
    if target_category == "training" and hw & _TRAIN:
        return 1

    return 0

def category(text):
    w = words_of(text)
    food_score = len(w & _FOOD)
    training_score = len(w & _TRAIN)

    if food_score > training_score:
        return "food"
    if training_score > food_score:
        return "training"
    return None


def fallbacks_for(text):
    target = category(text)
    if target == "food":
        return FOOD_FALLBACKS
    if target == "training":
        return TRAINING_FALLBACKS
    return TRAINING_FALLBACKS + FOOD_FALLBACKS

def popularity(hit):
    try:
        return (
            int(hit.get("downloads") or 0)
            + 3 * int(hit.get("likes") or 0)
        )
    except (TypeError, ValueError):
        return 0
