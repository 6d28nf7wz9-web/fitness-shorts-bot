import py_compile
import re

SHORTS_RULES = """Rules:
- 4 to 6 scenes. Total narration between 70 and 100 words (about 30 seconds spoken).
- Scene 1 is the hook: at most 12 words, no greeting, no "hey guys". Open with a specific mistake, a surprising fact, a myth, or a bold claim the viewer wants to check. Style examples: "You are doing cardio at the wrong time." or "This one habit quietly stalls your muscle growth."
- Scene 2 promises the payoff in one short sentence, so the viewer knows why to keep watching.
- Middle scenes: one clear point, one concrete example, and one simple action to do today. Speak directly to "you". Sentences under 14 words. Use contractions and everyday words, like a friend explaining.
- Use a number or a specific detail whenever it is well established and accurate.
- The last scene is a loop ending: its final sentence should flow naturally back into the hook, so the video feels continuous when it replays. Add a very short follow line only if there is room, like "Follow for tomorrow's tip."
- Each keyword field names 2 or 3 different filmable searches separated by a vertical bar, for example "man lifting dumbbells | gym close up | person resting". Describe things you can see. No brand names, no people's names.
- Only well-established, evidence-based advice (progressive overload, adequate protein, calorie balance, sleep, consistency).
- Never mention steroids, supplements, fat burners, detoxes, medical conditions, or spot reduction.
- Never promise results or timeframes (no "lose 10 kg in a week").
- Simple words, energetic tone, no emojis.
"""

LONG_RULES = """Rules:
- 5 to 8 sections. Total narration between 450 and 700 words.
- Section 1 is a hook of 25-45 words. Start with the most surprising or useful result, promise what the viewer will learn, and open one loop that you close near the end, for example "and the last tip is the one most people skip".
- Each middle section is 70-120 words: one clear point, one concrete example, one short accurate reason, and one simple thing to do today. End each section with a one-sentence bridge that makes the viewer want the next section.
- Vary the rhythm: a short question, a surprising fact, or a quick "here is the mistake" moment in every section, so the energy never stays flat.
- Speak directly to "you", use contractions and everyday words, keep sentences under 16 words, and sound like a friend explaining.
- The last section is a short recap that closes the loop from the hook, asks one simple question for the comments, and ends with "Subscribe for more tips like this."
- Each section has 4 or 5 different keywords for stock footage, each describing something you can film, like "man lifting dumbbells", "woman running outdoors", "healthy meal prep", "person sleeping". No brand names, no people's names.
- Only well-established, evidence-based advice (progressive overload, adequate protein, calorie balance, sleep, consistency). Acknowledge that results vary between people.
- Never mention steroids, supplements, fat burners, detoxes, medical conditions, or spot reduction.
- Never promise results or timeframes.
- No emojis.
"""

RULES_PATTERN = r"(?m)^Rules:\n(?:- [^\n]*\n)+"
TITLE_PATTERN = r'"title": "max 60 characters[^"]*"'
TITLE_NEW = '"title": "max 60 characters, starts with a strong word or a number, includes the main keyword, creates curiosity, truthful and not misleading"'
KEYWORD_PATTERN = r'"keyword": "2-3 plain English words for a stock video search"'
KEYWORD_NEW = '"keyword": "2 or 3 filmable stock searches separated by a vertical bar"'


def patch_file(path, edits):
    try:
        with open(path, encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        print(f"[skip] {path} not found")
        return
    text = original
    for pattern, repl in edits:
        text, n = re.subn(pattern, lambda m, r=repl: r, text)
        print(f"  {'ok  ' if n else 'MISS'} {pattern[:55]}")
    if text == original:
        print(f"[same] {path}: nothing to change")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if path.endswith(".py"):
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
            print(f"[undo] {path} did not compile, restored: {str(e)[:200]}")
            return
    print(f"[done] {path}")


patch_file("gen_script.py", [
    (RULES_PATTERN, SHORTS_RULES),
    (TITLE_PATTERN, TITLE_NEW),
    (KEYWORD_PATTERN, KEYWORD_NEW),
])
patch_file("long_script.py", [(RULES_PATTERN, LONG_RULES)])
patch_file(".github/workflows/daily.yml", [(r"python clips\.py", "python clips_fast.py")])
print("\nDone. Test with: python gen_script.py")