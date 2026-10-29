import py_compile
import re

TOPIC = ('EVERY search must show training or food: a person exercising, gym equipment, an athlete, '
         'running or stretching, cooking, a healthy meal, fresh ingredients, or someone eating healthy food. '
         'Always include a concrete training or food word such as dumbbell, barbell, squat, treadmill, '
         'chicken, eggs, salad, rice, meal prep. Never use abstract or unrelated scenes such as people '
         'thinking, hungry faces, offices, cities, nature, money, crowds or friends hanging out. ')

SHORTS_RULE = ('- Each keyword field names 2 or 3 different filmable searches separated by a vertical bar. '
               + TOPIC +
               'Examples: "man lifting dumbbells | barbell close up | gym workout" and '
               '"cooking chicken breast | healthy meal prep | fresh vegetables". '
               'No brand names, no people\'s names.\n')
LONG_RULE = ('- Each section has 4 or 5 different keywords for stock footage. '
             + TOPIC +
             'Examples: "man lifting dumbbells", "barbell close up", "cooking chicken breast", '
             '"healthy meal prep". No brand names, no people\'s names.\n')

RULE_PATTERN = r"(?m)^- Each (?:keyword|section has)[^\n]*\n"
SCHEMA_EDITS = [
    ('"keyword": "2 or 3 filmable stock searches separated by a vertical bar"',
     '"keyword": "2 or 3 searches separated by a vertical bar, each showing training or food"'),
    ('"keyword": "2-3 plain English words for a stock video search"',
     '"keyword": "2 or 3 searches separated by a vertical bar, each showing training or food"'),
    ('"keywords": ["3 to 5 different plain English searches for stock footage"]',
     '"keywords": ["3 to 5 different searches, each showing training or food"]'),
]


def patch(path, rule):
    try:
        with open(path, encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        print(f"[skip] {path} not found")
        return
    text, n = re.subn(RULE_PATTERN, lambda m: rule, original)
    changed_schema = 0
    for old, new in SCHEMA_EDITS:
        if old in text:
            text = text.replace(old, new)
            changed_schema += 1
    print(f"  {path}: keyword rule replaced {n}x, schema line changed {changed_schema}x")
    if text == original:
        print(f"[no change] {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        with open(path, "w", encoding="utf-8") as f:
            f.write(original)
        print(f"[undone] {path} did not compile, restored the old version: {str(e)[:200]}")
        return
    print(f"[done] {path}")


patch("gen_script.py", SHORTS_RULE)
patch("long_script.py", LONG_RULE)
print("\nFinished. New scripts will ask for keywords about training and food only.")
