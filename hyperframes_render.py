"""Render Gemini scene visuals and matching Pixabay footage through HyperFrames.

The legacy FFmpeg caption/audio mixer remains responsible for word-level subtitles
and sound. HyperFrames owns the complete visual timeline and safe typography.
"""
import html
import json
import os
import re
import subprocess
import shutil
from pathlib import Path

ROOT = Path("output/hyperframes")
W, H, FPS = 1080, 1920, 30
SAFE_TITLE_WIDTH = 880
SAFE_SUB_WIDTH = 820


def wrap_words(text, limit):
    words = re.sub(r"\s+", " ", str(text or "")).strip().split()
    lines, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) > limit and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def fit_text(text, max_lines, max_chars, base, minimum):
    lines = wrap_words(text, max_chars)
    if len(lines) > max_lines:
        # Keep complete wording while reducing font and allowing a third line.
        max_lines = min(4, len(lines))
    size = max(minimum, min(base, int(base * max_lines / max(len(lines), max_lines)))))
    return lines, size


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)
    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)
    scenes = script.get("scenes", [])
    if not scenes or len(scenes) != len(audio):
        raise SystemExit("HyperFrames: scene/audio count mismatch")

    ROOT.mkdir(parents=True, exist_ok=True)
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    total = sum(float(x["seconds"]) for x in audio)
    css = """
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#07111d;color:#f5f8ff;font-family:Arial,'DejaVu Sans',sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07111d}
.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:brightness(.48) saturate(.78)}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,10,18,.82) 0%,rgba(5,13,23,.20) 34%,rgba(5,13,23,.30) 58%,rgba(4,10,18,.88) 100%)}
.grid{position:absolute;inset:0;opacity:.12;background-image:linear-gradient(#6ea4c8 1px,transparent 1px),linear-gradient(90deg,#6ea4c8 1px,transparent 1px);background-size:72px 72px}
.brand{position:absolute;left:84px;right:84px;top:120px;text-align:center;font-size:25px;letter-spacing:7px;color:#72e6c2;font-weight:800}
.titlebox{position:absolute;left:90px;right:90px;top:420px;height:300px;display:flex;align-items:center;justify-content:center;text-align:center}
.title{font-weight:900;letter-spacing:-2px;line-height:1.06;color:#fff;text-shadow:0 5px 28px #000;max-width:900px;overflow-wrap:anywhere}
.subbox{position:absolute;left:130px;right:130px;top:790px;min-height:150px;display:flex;align-items:center;justify-content:center;text-align:center}
.sub{font-weight:700;line-height:1.22;color:#72e6c2;text-shadow:0 3px 18px #000;max-width:820px;overflow-wrap:anywhere}

"""
    blocks = []
    cursor = 0.0
    for i, (scene, meta) in enumerate(zip(scenes, audio), 1):
        dur = max(.1, float(meta["seconds"]))
        title = str(scene.get("visual_title") or scene.get("narration") or script.get("title") or "FITNESS SCIENCE").strip()
        subtitle = str(scene.get("visual_subtitle") or "").strip()
        title_lines, title_size = fit_text(title, 3, 20, 78, 48)
        sub_lines, sub_size = fit_text(subtitle, 2, 30, 43, 30)
        title_html = "<br>".join(html.escape(x) for x in title_lines)
        sub_html = "<br>".join(html.escape(x) for x in sub_lines)
        start = f"{cursor:.3f}"
        enddur = f"{dur:.3f}"
        source = Path(f"output/clips/scene_{i}.mp4")
        shutil.copy2(source, assets / f"scene_{i}.mp4")
        blocks.append(f'<video id="bg{i}" data-start="{start}" data-duration="{enddur}" data-track-index="0" data-volume="0" src="assets/scene_{i}.mp4"></video>')
        blocks.append(f"""
<div id="overlay{i}" class="clip" data-start="{start}" data-duration="{enddur}" data-track-index="2">
 <div class="shade"></div><div class="grid"></div>
 <div class="brand">FITFUEL / SCIENCE EXPLAINED</div>
 <div class="titlebox"><div class="title" style="font-size:{title_size}px">{title_html}</div></div>
 <div class="subbox"><div class="sub" style="font-size:{sub_size}px">{sub_html}</div></div>
</div>""")
        cursor += dur
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FitFuel HyperFrames render</title><style>{css}
video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
</style></head><body><div id="root" data-composition-id="fitfuel-short" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{FPS}">
{''.join(blocks)}
</div></body></html>"""
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")
    # Guard against accidental overlay/caption collision: caption ASS is bottom
    # anchored in assemble.py, visual text is confined to the middle safe zone.
    print(f"HyperFrames composition: {len(scenes)} scenes, {total:.2f}s; safe title/subtitle zones")
    subprocess.run(
        ["npx", "--yes", "hyperframes", "lint", "."],
        cwd=str(ROOT), check=True
    )
    subprocess.run(
        ["npx", "--yes", "hyperframes", "render", "--output", "base.mp4", "--fps", str(FPS), "--quality", "standard"],
        cwd=str(ROOT), check=True
    )
    output = ROOT / "base.mp4"
    if not output.exists() or output.stat().st_size < 100_000:
        raise SystemExit("HyperFrames render did not produce a valid base.mp4")
    print(f"HyperFrames visual render complete: {output} ({output.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
