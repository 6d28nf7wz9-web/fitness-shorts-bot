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

from visual_engine import build_visual_panel, visual_css
from scene_presentation_director import direct_scenes
from visual_beats import build_visual_beat_overlays, visual_beat_css

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
    """Fit overlay copy to a hard line limit so it cannot collide with captions."""
    hard_lines = min(4, max(1, max_lines + 1))
    lines = wrap_words(text, max_chars)
    size = base

    if len(lines) > hard_lines:
        size = max(minimum, int(base * hard_lines / len(lines)))
        effective_chars = max(max_chars, int(max_chars * base / size))
        lines = wrap_words(text, effective_chars)
    else:
        effective_chars = max_chars

    if len(lines) > hard_lines:
        # Visual labels are summaries; keep narration intact but bound on-screen
        # copy to its safe box rather than allowing text to spill into captions.
        lines = lines[:hard_lines]
        last = lines[-1].rstrip()
        if len(last) >= effective_chars:
            last = last[:effective_chars - 1].rstrip()
        lines[-1] = last.rstrip(" .") + "…"

    return lines, size


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)
    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)
    scenes = direct_scenes(script.get("scenes", []))
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
.titlebox{position:absolute;left:90px;right:90px;top:420px;height:300px;overflow:hidden;display:flex;align-items:center;justify-content:center;text-align:center}
.title{font-weight:900;letter-spacing:-2px;line-height:1.06;color:#fff;text-shadow:0 5px 28px #000;max-width:900px;overflow-wrap:anywhere}
.subbox{position:absolute;left:130px;right:130px;top:790px;height:150px;overflow:hidden;display:flex;align-items:center;justify-content:center;text-align:center}
.sub{font-weight:700;line-height:1.22;color:#72e6c2;text-shadow:0 3px 18px #000;max-width:820px;overflow-wrap:anywhere}

/* Real scene composition changes: each presentation style relocates and resizes
   the title, supporting copy and science panel instead of only changing its SVG. */
.scene-layout-hook .titlebox{top:330px;height:260px;justify-content:flex-start;text-align:left}
.scene-layout-hook .subbox{top:650px;left:90px;right:280px;justify-content:flex-start;text-align:left}
.scene-layout-hook .science-panel{top:990px;height:570px}
.scene-layout-payoff .titlebox{top:350px;height:240px}
.scene-layout-payoff .subbox{top:650px}
.scene-layout-payoff .science-panel{top:930px;height:590px;left:110px;right:110px}
.scene-layout-stat_card .titlebox{top:300px;height:210px}
.scene-layout-stat_card .subbox{top:560px}
.scene-layout-stat_card .science-panel{top:850px;height:470px;left:130px;right:130px}
.scene-layout-comparison .titlebox{top:330px;height:240px;left:100px;right:100px}
.scene-layout-comparison .subbox{top:610px}
.scene-layout-comparison .science-panel{top:900px;left:95px;right:95px;height:570px;border:2px solid rgba(255,255,255,.3)}
.scene-layout-comparison .science-panel:after{content:"";position:absolute;top:105px;bottom:30px;left:50%;border-left:2px dashed rgba(255,255,255,.42)}
.scene-layout-timeline .titlebox{top:300px;height:220px;left:140px;right:140px}
.scene-layout-timeline .subbox{top:555px}
.scene-layout-timeline .science-panel{top:830px;height:640px;left:105px;right:105px}
.scene-layout-presenter_focus .titlebox{top:430px;left:95px;right:550px;height:420px;justify-content:flex-start;text-align:left}
.scene-layout-presenter_focus .subbox{top:900px;left:95px;right:550px;justify-content:flex-start;text-align:left}
.scene-layout-presenter_focus .science-panel{top:690px;left:555px;right:42px;height:620px}
.scene-layout-presenter_focus .science-svg{left:2%;width:96%;height:430px}
.scene-layout-broll_focus .titlebox{top:390px;height:240px}
.scene-layout-broll_focus .subbox{top:670px}
.scene-layout-broll_focus .science-panel{top:1290px;left:135px;right:135px;height:300px;opacity:.9}
.scene-layout-broll_focus .science-svg{top:70px;height:210px}
.scene-layout-broll_focus .science-heading{top:28px}
.scene-layout-diagram .science-panel{top:990px;height:550px}
.scene-layout-hook .title,.scene-layout-payoff .title{letter-spacing:-1px}
.scene-layout-comparison .science-panel{background:linear-gradient(90deg,rgba(8,25,42,.96) 0 49.7%,rgba(20,30,48,.96) 50.3% 100%)}
.scene-layout-broll_focus .shade{background:linear-gradient(180deg,rgba(4,10,18,.65),rgba(4,10,18,.08) 42%,rgba(4,10,18,.76))}
"""
    css += visual_css() + visual_beat_css()
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
        source = Path("output/clips") / f"scene_{i}.mp4"
        if not source.exists() or source.stat().st_size < 10_000:
            raise SystemExit(f"Missing visual scene {i}: {source}")
        shutil.copy2(source, assets / f"scene_{i}.mp4")
        blocks.append(f'<video id="bg{i}" data-start="{start}" data-duration="{enddur}" data-track-index="0" data-volume="0" muted src="assets/scene_{i}.mp4"></video>')
        beat_overlays = ''.join(build_visual_beat_overlays(scene, dur, i, cursor))
        blocks.append(f"""
<div id="overlay{i}" class="clip scene-layout-{html.escape(str(scene.get("presentation_style") or "diagram"))}" data-start="{start}" data-duration="{enddur}" data-track-index="2">
 <div class="shade"></div><div class="grid"></div>
 <div class="brand">FITFUEL / SCIENCE EXPLAINED</div>
 <div class="titlebox"><div class="title" style="font-size:{title_size}px">{title_html}</div></div>
 <div class="subbox"><div class="sub" style="font-size:{sub_size}px">{sub_html}</div></div>
</div>
{beat_overlays}""")
        cursor += dur
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FitFuel HyperFrames render</title><style>{css}
video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
</style></head><body><div id="root" data-composition-id="fitfuel-short" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-no-timeline>
{''.join(blocks)}
</div></body></html>"""
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")
    # Guard against accidental overlay/caption collision: caption ASS is bottom
    # anchored in assemble.py, visual text is confined to the middle safe zone.
    print(f"HyperFrames composition: {len(scenes)} scenes, {total:.2f}s; safe title/subtitle zones")
    subprocess.run(
        ["hyperframes", "lint", "."],
        cwd=str(ROOT), check=True
    )
    subprocess.run(
        ["hyperframes", "render", "--output", "base.mp4", "--fps", str(FPS), "--quality", "standard"],
        cwd=str(ROOT), check=True
    )
    output = ROOT / "base.mp4"
    if not output.exists() or output.stat().st_size < 100_000:
        raise SystemExit("HyperFrames render did not produce a valid base.mp4")
    print(f"HyperFrames visual render complete: {output} ({output.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
