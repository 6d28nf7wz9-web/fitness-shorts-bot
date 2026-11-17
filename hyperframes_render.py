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
from motion_director import motion_css, plan_scene_motion
from production_motion_engine import kinetic_html, motion_engine_css, sound_cue_events, presenter_html, presenter_gesture, presenter_expression, presenter_css

ROOT = Path("output/hyperframes")
W, H, FPS = 1080, 1920, 30
SAFE_TITLE_WIDTH = 880
SAFE_SUB_WIDTH = 820

def prepare_scene_footage(scene_index, assets_dir):
    """Copy only footage that passed the semantic stock matcher into the render."""
    info_path = Path("output/clips_info.json")
    if not info_path.exists():
        return None
    try:
        records = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    record = next((item for item in records if int(item.get("scene", 0)) == scene_index), None)
    if not record or record.get("source") != "stock":
        return None
    clips = record.get("clips") or []
    if not clips or any(item.get("source") not in ("stock", "stock+wan") for item in clips):
        return None
    source = Path(record.get("file", f"output/clips/scene_{scene_index}.mp4"))
    if not source.is_file() or source.stat().st_size < 10_000:
        return None
    destination = assets_dir / f"scene_{scene_index}_broll.mp4"
    shutil.copy2(source, destination)
    return destination.name

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
.titlebox{position:absolute;left:90px;right:90px;top:420px;height:300px;overflow:hidden;display:flex;align-items:center;justify-content:center;text-align:center}
.title{font-weight:900;letter-spacing:-2px;line-height:1.06;color:#fff;text-shadow:0 5px 28px #000;max-width:900px;overflow-wrap:anywhere}
.subbox{position:absolute;left:130px;right:130px;top:790px;height:150px;overflow:hidden;display:flex;align-items:center;justify-content:center;text-align:center}
.sub{font-weight:700;line-height:1.22;color:#72e6c2;text-shadow:0 3px 18px #000;max-width:820px;overflow-wrap:anywhere}

"""
    css += visual_css()
    css += motion_css()
    css += motion_engine_css()
    css += presenter_css()
    css += """
/* Progressive disclosure: reveal the diagram's claim, then its evidence. */
.science-svg .diagram-label{opacity:0;animation:ff-diagram-label-reveal .55s .28s cubic-bezier(.16,1,.3,1) both}
.science-svg .diagram-note{opacity:0;animation:ff-diagram-label-reveal .55s 1.05s cubic-bezier(.16,1,.3,1) both,ff-diagram-note-hold 3.4s 1.7s ease-in-out infinite alternate}
.science-muscle .fiber-two{animation-delay:.25s,.25s}
.science-muscle .fiber-three{animation-delay:.5s,.5s}
.science-muscle .fiber-four{animation-delay:.75s,.75s}
.science-nutrition .fuel-dots circle:nth-child(2){animation-delay:.25s}
.science-nutrition .fuel-dots circle:nth-child(3){animation-delay:.5s}
.science-heart .oxygen-two{animation-delay:.2s}
.science-heart .oxygen-three{animation-delay:.4s}
.science-heart .oxygen-four{animation-delay:.6s}
.science-hydration .electrolytes circle:nth-child(2){animation-delay:.25s}
.science-hydration .electrolytes circle:nth-child(3){animation-delay:.5s}
.science-hormones .signal-dots circle:nth-child(2){animation-delay:.2s}
.science-hormones .signal-dots circle:nth-child(3){animation-delay:.4s}
.science-creatine .creatine-dot:nth-of-type(2){animation-delay:.25s}
.science-creatine .creatine-dot:nth-of-type(3){animation-delay:.5s}
@keyframes ff-diagram-label-reveal{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes ff-diagram-note-hold{from{opacity:1}to{opacity:.78}}
"""
    css += """
@media (prefers-reduced-motion: reduce) {
  .motion-scene *, .science-panel:before {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
"""
    # Give each scientific metaphor its own movement grammar inside the scene.
    css += """
.science-muscle .fiber{animation:ff-fiber-travel 2.1s linear infinite,ff-fiber-breathe 1.8s ease-in-out infinite alternate}
.science-muscle .satellite circle{animation:ff-satellite-orbit 3.4s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.science-nutrition .plate{transform-origin:185px 210px;animation:ff-plate-turn 7s ease-in-out infinite alternate}
.science-nutrition .fuel-dots circle{animation:ff-fuel-arrive 2.4s ease-in-out infinite alternate}
.science-heart .heart-shape{animation:ff-heart-contract .86s ease-in-out infinite}
.science-heart .oxygen{animation:ff-oxygen-flow 2.8s linear infinite}
.science-fat_loss .balance-beam{transform-origin:380px 165px;animation:ff-energy-balance 4s ease-in-out infinite alternate}
.science-fat_loss .energy-in circle{animation:ff-energy-in 2.2s ease-in-out infinite}
.science-fat_loss .energy-out path{animation:ff-energy-out 2.2s ease-in-out infinite .6s}
.science-hydration .drop{animation:ff-drop-pulse 2.6s ease-in-out infinite alternate}
.science-hydration .electrolytes circle{animation:ff-ion-orbit 3s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.science-exercise .joint{transform-origin:380px 210px;animation:ff-joint-rotate 2.8s ease-in-out infinite alternate}
.science-exercise .lever{animation:ff-lever-flex 2.8s ease-in-out infinite alternate;transform-origin:380px 330px}
.science-hormones .signal-dots circle{animation:ff-signal-pass 2.4s ease-in-out infinite}
.science-hormones .receptor{animation:ff-receptor-open 2.4s ease-in-out infinite alternate;transform-origin:475px 210px}
.science-creatine .atp-core{animation:ff-atp-charge 2s ease-in-out infinite alternate}
.science-creatine .creatine-dot{animation:ff-phosphate-transfer 2s ease-in-out infinite}
.science-supplements .supplement-bottle{transform-origin:220px 240px;animation:ff-dose-rock 3s ease-in-out infinite alternate}
.science-general .process-pulse{animation:ff-process-sequence 2.7s ease-in-out infinite}
@keyframes ff-fiber-travel{to{stroke-dashoffset:-96}}@keyframes ff-fiber-breathe{to{opacity:.55;stroke-width:22}}
@keyframes ff-satellite-orbit{to{transform:translateY(-18px) scale(1.15)}}
@keyframes ff-plate-turn{to{transform:rotate(7deg)}}@keyframes ff-fuel-arrive{to{transform:translate(12px,-8px) scale(1.18);opacity:.65}}
@keyframes ff-heart-contract{0%,100%{transform:scale(1)}50%{transform:scale(1.09)}}
@keyframes ff-oxygen-flow{to{transform:translateX(42px);opacity:.35}}
@keyframes ff-energy-balance{to{transform:rotate(5deg)}}@keyframes ff-energy-in{50%{transform:translateY(-16px)}}
@keyframes ff-energy-out{50%{transform:translateY(-18px) scale(1.12)}}
@keyframes ff-drop-pulse{to{transform:translateY(-10px) scale(1.04);filter:drop-shadow(0 0 20px #65aaff)}}
@keyframes ff-ion-orbit{to{transform:translateY(-12px) scale(1.14)}}
@keyframes ff-joint-rotate{to{transform:rotate(12deg)}}@keyframes ff-lever-flex{to{transform:rotate(-7deg)}}
@keyframes ff-signal-pass{0%,100%{transform:translateX(-12px);opacity:.45}50%{transform:translateX(35px);opacity:1}}
@keyframes ff-receptor-open{to{transform:scaleY(1.12)}}
@keyframes ff-atp-charge{to{filter:brightness(1.7) drop-shadow(0 0 18px #72e6c2)}}
@keyframes ff-phosphate-transfer{50%{transform:translate(-90px,50px)}}
@keyframes ff-dose-rock{to{transform:rotate(4deg)}}@keyframes ff-process-sequence{0%,100%{opacity:.45}50%{opacity:1;transform:scale(1.3)}}
"""
    sound_cues = []
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
        # Only use scene footage that clips_fast.py selected with an exact
        # semantic match. Science fallback scenes keep the designed motion canvas.
        footage_name = prepare_scene_footage(i, assets)
        if footage_name:
            blocks.append(
                f'<video id="broll{i}" class="scene-footage" muted playsinline '
                f'data-start="{start}" data-duration="{enddur}" data-track-index="0" '
                f'src="assets/{html.escape(footage_name, quote=True)}"></video>'
            )
        else:
            blocks.append(
                f'<div id="bg{i}" class="scene-bg clip" data-start="{start}" '
                f'data-duration="{enddur}" data-track-index="0"></div>'
            )
        category, science_panel = build_visual_panel(scene, i)
        kinetic = kinetic_html(scene.get('narration', ''), category, dur, meta.get('word_timings'))
        sound_cues.extend(sound_cue_events(scene.get('narration', ''), category, dur, meta.get('word_timings'), cursor))
        motion = plan_scene_motion(scene, i, dur, category, is_last=(i == len(scenes)))
        blocks.append(f"""
<div id="overlay{i}" class="clip motion-scene science-{category} motion-scene-{i} {motion['class_name']}" data-motion-style="{motion['style']}" data-start="{start}" data-duration="{enddur}" data-track-index="2">
 <div class="shade"></div><div class="grid"></div>{presenter_html(presenter_gesture(scene.get('narration', ''), category), presenter_expression(scene.get('narration', ''), category))}
 <div class="brand">FITFUEL / SCIENCE EXPLAINED</div>
 <div class="titlebox"><div class="title" style="font-size:{title_size}px">{title_html}</div></div>
 <div class="subbox"><div class="sub" style="font-size:{sub_size}px">{sub_html}</div></div>
 {kinetic}
 {science_panel}
</div>""")
        cursor += dur
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FitFuel HyperFrames render</title><style>{css}
video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.scene-bg{{position:absolute;z-index:0;inset:0;width:100%;height:100%;background:radial-gradient(ellipse at 50% 42%,rgba(35,105,135,.32),transparent 58%),linear-gradient(155deg,#07111d 0%,#10263a 48%,#07111d 100%);}}
.scene-footage{{position:absolute;z-index:0;inset:0;width:100%;height:100%;object-fit:cover;filter:brightness(.72) saturate(1.08) contrast(1.04);transform:scale(1.045);animation:ff-camera-drift 7s ease-in-out both;}}
.scene-bg:after{{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent 0 71px,rgba(114,230,194,.055) 72px),repeating-linear-gradient(90deg,transparent 0 71px,rgba(114,230,194,.055) 72px);}}
.motion-scene{{z-index:2}}
.shade{{background:linear-gradient(180deg,rgba(4,10,18,.76) 0%,rgba(5,13,23,.12) 34%,rgba(5,13,23,.26) 58%,rgba(4,10,18,.84) 100%);}}
</style></head><body><div id="root" data-composition-id="fitfuel-short" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{FPS}" data-no-timeline>
{''.join(blocks)}
</div></body></html>"""
    (ROOT / "index.html").write_text(html_doc, encoding="utf-8")
    (ROOT / "sound_cues.json").write_text(json.dumps(sound_cues, ensure_ascii=False, indent=2), encoding="utf-8")
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
