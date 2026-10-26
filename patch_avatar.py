import py_compile
import re

CAPTION_SHORT = (r",120,120,560,1(?=\n)", ",120,120,700,1", ",120,120,700,1")


def patch_file(path, edits):
    try:
        with open(path, encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        print(f"[skip] {path} not found")
        return
    text = original
    for pattern, repl, done in edits:
        if done in text:
            print(f"  already  {pattern[:50]}")
            continue
        text, n = re.subn(pattern, repl, text)
        print(f"  {'ok     ' if n else 'MISSING'}  {pattern[:50]}")
    if text == original:
        print(f"[no change] {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if path.endswith(".py"):
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
            print(f"[undone] {path} did not compile: {str(e)[:200]}")
            return
    print(f"[done] {path}")


patch_file("assemble.py", [CAPTION_SHORT])
patch_file("long_assemble.py", [
    (r",160,160,70,1(?=\n)", ",100,520,70,1", ",100,520,70,1"),
    (r"int\(1500 /", "int(1250 /", "int(1250 /"),
])
patch_file("long_shorts.py", [
    CAPTION_SHORT,
    (r"(?m)^from yt import upload_video$",
     "from yt import upload_video\nfrom avatar import add_avatar", "add_avatar"),
    (r"(?m)^(\s+)out, dur = render\(tl, chunks, si, n, random\.choice\(music_files\)\)$",
     r'\g<0>\n\1add_avatar(out, tl["recording"], tl["audio_start"] + sec["start"], dur, "short")',
     'add_avatar(out,'),
])
patch_file(".github/workflows/daily.yml", [
    (r"(?m)^([ ]+)run: python assemble\.py[ ]*$",
     r"\1run: |\n\1  python assemble.py\n\1  python avatar.py short", "avatar.py short"),
])
patch_file(".github/workflows/long_ai.yml", [
    (r"(?m)^([ ]+)run: python long_assemble\.py[ ]*$",
     r"\1run: |\n\1  python long_assemble.py\n\1  python avatar.py long", "avatar.py long"),
])

with open("requirements.txt", encoding="utf-8") as f:
    reqs = f.read().lower()
extra = [p for p in ("pillow", "numpy") if p not in reqs]
if extra:
    with open("requirements.txt", "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(extra) + "\n")
    print("[done] requirements.txt: added " + ", ".join(extra))

print("\nFinished. Next: python make_avatar.py")