"""Render scene-matched 3D anatomy plates for the production video timeline.

Only explicit anatomy scenes are rendered. The resulting MP4s are consumed by
HyperFrames as visual layers; the ordinary SVG diagrams remain a fallback for
non-anatomy topics. This script never uploads or publishes a video.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

from visual_engine import classify_scene


ROOT = Path(__file__).resolve().parents[1]


def anatomy_view(scene):
    """Return anterior/posterior for an explicit anatomical scene, else None."""
    visual_type = str(scene.get("visual_type", "")).lower().replace("-", "_")
    text = " ".join(str(scene.get(key, "")) for key in
                    ("visual_title", "visual_subtitle", "narration")).lower()
    if visual_type in {"muscle_anatomy", "anatomy", "muscle_groups"} or classify_scene(scene) == "anatomy":
        explicit = True
    else:
        explicit = bool(re.search(
            r"\b(pectoralis|pectorals|deltoid|biceps|triceps|latissimus|lats|"
            r"trapezius|traps|quadriceps|hamstrings|glutes|gastrocnemius|"
            r"muscle anatomy|muscle groups|anterior muscles|posterior muscles)\b",
            text,
        ))
    if not explicit:
        return None
    if re.search(r"\b(back|posterior|lats|latissimus|traps|trapezius|triceps|"
                 r"glutes|hamstrings|calves|gastrocnemius)\b", text):
        return "posterior"
    return "anterior"


def render_scene(index, scene, duration, view, blender="blender"):
    out = ROOT / "output" / "science_3d"
    frame_dir = out / f"frames_{index}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames = max(48, min(600, int(round(max(2.0, duration) * 24))))
    blend_file = out / f"scene_{index}.blend"
    mp4 = out / f"scene_{index}.mp4"
    title = str(scene.get("visual_title") or "MUSCLE ANATOMY").strip()[:64]
    command = [
        blender, "-b", "--factory-startup", "--python-exit-code", "1",
        "--python", str(ROOT / "blender" / "fitfuel_science_preview.py"), "--",
        "--view", view, "--clean",
        "--output-dir", str(frame_dir),
        "--blend-file", str(blend_file),
        "--frames", str(frames), "--width", "720", "--height", "1280",
        "--title", title,
    ]
    subprocess.run(command, check=True)
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", "24", "-i", str(frame_dir / "frame_%04d.png"),
        "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4),
    ], check=True)
    if not mp4.is_file() or mp4.stat().st_size < 20_000:
        raise RuntimeError(f"3D anatomy render missing or too small: {mp4}")
    print(f"3D anatomy scene {index}: {view}, {frames} frames -> {mp4}")


def main():
    script_path = ROOT / "output" / "script.json"
    audio_path = ROOT / "output" / "audio_info.json"
    if not script_path.exists() or not audio_path.exists():
        print("3D anatomy: script/audio metadata unavailable; keeping existing visual fallback.")
        return
    scenes = json.loads(script_path.read_text(encoding="utf-8")).get("scenes", [])
    audio = json.loads(audio_path.read_text(encoding="utf-8"))
    if len(scenes) != len(audio):
        raise SystemExit("3D anatomy renderer: scene/audio count mismatch")
    blender = shutil.which("blender")
    if not blender:
        print("3D anatomy: Blender is not installed; keeping existing visual fallback.")
        return
    rendered = 0
    for index, (scene, timing) in enumerate(zip(scenes, audio), 1):
        view = anatomy_view(scene)
        if not view:
            continue
        render_scene(index, scene, float(timing.get("seconds", 0)), view, blender)
        rendered += 1
    print(f"3D anatomy production plates rendered: {rendered}/{len(scenes)} scenes")


if __name__ == "__main__":
    main()
