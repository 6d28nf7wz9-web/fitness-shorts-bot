"""Keeps the background clips on topic: every clip must be about training or food."""
import re

TRAINING = {
    "gym", "workout", "exercise", "fitness", "training", "weight", "weights", "weightlifting",
    "lifting", "dumbbell", "barbell", "kettlebell", "squat", "deadlift", "pushup", "pullup",
    "plank", "cardio", "treadmill", "running", "runner", "jogging", "jogger", "sprint",
    "cycling", "swimming", "yoga", "stretching", "muscle", "bodybuilding", "bodybuilder",
    "athlete", "athletic", "sport", "crossfit", "boxing", "abs", "biceps", "trainer",
    "calisthenics", "powerlifting", "strength", "warmup", "pilates", "aerobic", "treadmill",
}
FOOD = {
    "food", "meal", "healthy", "nutrition", "diet", "protein", "chicken", "egg", "salad",
    "vegetable", "fruit", "rice", "oats", "oatmeal", "breakfast", "lunch", "dinner", "cooking",
    "cook", "kitchen", "fish", "salmon", "meat", "beef", "steak", "nuts", "avocado", "smoothie",
    "yogurt", "grilled", "recipe", "eating", "ingredients", "organic", "vegan", "tuna", "beans",
    "lentils", "potato", "banana", "apple", "berries", "broccoli", "tomato", "juice", "snack",
    "cuisine", "dish", "vegetables", "fruits", "spinach", "carrot", "cheese", "milk",
}
# only accepted when the clip also has a health / fitness context tag
WEAK = {
    "walking", "walk", "hiking", "sleep", "sleeping", "bed", "resting", "recovery", "water",
    "bottle", "scale", "measuring", "steps", "stairs",
}
HEALTH_CONTEXT = {
    "fitness", "health", "healthy", "sport", "exercise", "workout", "training", "wellness",
    "lifestyle", "active", "athlete", "gym", "diet", "nutrition", "food", "meal",
}
FILLER = {
    "person", "people", "man", "woman", "men", "women", "looking", "close", "slow", "motion",
    "view", "outdoors", "outdoor", "with", "and", "the", "front", "back", "side", "top", "young",
    "happy", "friends", "group", "someone", "his", "her", "for", "from", "into", "over", "one",
}

TRAINING_FALLBACKS = ["gym workout", "weight training", "man lifting weights",
                      "woman running outdoors", "fitness training"]
FOOD_FALLBACKS = ["healthy food", "cooking healthy meal", "salad vegetables",
                  "cooking chicken", "meal prep"]


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


def hit_words(hit):
    slug = str(hit.get("pageURL", "")).rstrip("/").split("/")[-1]
    return words_of(f"{hit.get('tags', '')} {slug}")


def keyword_words(keyword):
    return words_of(keyword) - _FILLER


def keyword_is_relevant(text):
    w = words_of(text)
    return bool(w & (_STRONG | _WEAK))


def relevance(hit, keyword):
    """0 = off topic, 1 = a training or food clip, 2 = also matches the scene keyword."""
    hw = hit_words(hit)
    kw = keyword_words(keyword)
    strong = hw & _STRONG
    weak_ok = bool(hw & _WEAK & kw) and bool(hw & _CONTEXT)
    if not strong and not weak_ok:
        return 0
    return 2 if (hw & kw) else 1


def category(text):
    w = words_of(text)
    return "food" if len(w & _FOOD) > len(w & _TRAIN) else "training"


def fallbacks_for(text):
    return FOOD_FALLBACKS + TRAINING_FALLBACKS if category(text) == "food" \
        else TRAINING_FALLBACKS + FOOD_FALLBACKS


def popularity(hit):
    try:
        return int(hit.get("downloads") or 0) + 3 * int(hit.get("likes") or 0)
    except (TypeError, ValueError):
        return 0
