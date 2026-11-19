"""Render scene-matched 3D science plates for the production video timeline.

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


SUPPORTED_3D_TOPICS = {
    "anatomy", "muscle", "protein", "heart", "fat_loss", "hydration",
    "exercise", "nutrition", "hormones", "creatine", "supplements",
    "tracking", "recovery",
}


def scene_topic(scene):
    """Map the shared visual classifier to a supported Blender 3D scene."""
    category = classify_scene(scene)
    return category if category in SUPPORTED_3D_TOPICS else None


def anatomy_view(scene):
    """Return anterior/posterior for anatomy scenes, else None."""
    if scene_topic(scene) != "anatomy":
        return None
    text = " ".join(str(scene.get(key, "")) for key in
                    ("visual_title", "visual_subtitle", "narration")).lower()
    if re.search(r"\b(back|posterior|lats|latissimus|traps|trapezius|triceps|glutes|hamstrings|calves|gastrocnemius)\b", text):
        return "posterior"
    return "anterior"

def render_scene(index, scene, duration, topic, blender="blender"):
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
        "--topic", topic, "--clean",
        "--output-dir", str(frame_dir),
        "--blend-file", str(blend_file),
        "--frames", str(frames), "--width", "720", "--height", "1280",
        "--title", title,
    ]
    if topic == "anatomy":
        command.extend(["--view", anatomy_view(scene) or "anterior"])
    subprocess.run(command, check=True)
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", "24", "-i", str(frame_dir / "frame_%04d.png"),
        "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4),
    ], check=True)
    if not mp4.is_file() or mp4.stat().st_size < 20_000:
        raise RuntimeError(f"3D anatomy render missing or too small: {mp4}")
    print(f"3D science scene {index}: {topic}, {frames} frames -> {mp4}")


def main():
    script_path = ROOT / "output" / "script.json"
    audio_path = ROOT / "output" / "audio_info.json"
    if not script_path.exists() or not audio_path.exists():
        print("3D science: script/audio metadata unavailable; keeping existing visual fallback.")
        return
    scenes = json.loads(script_path.read_text(encoding="utf-8")).get("scenes", [])
    audio = json.loads(audio_path.read_text(encoding="utf-8"))
    if len(scenes) != len(audio):
        raise SystemExit("3D science renderer: scene/audio count mismatch")
    blender = shutil.which("blender")
    if not blender:
        print("3D anatomy: Blender is not installed; keeping existing visual fallback.")
        return
    rendered = 0
    for index, (scene, timing) in enumerate(zip(scenes, audio), 1):
        topic = scene_topic(scene)
        if not topic:
            continue
        render_scene(index, scene, float(timing.get("seconds", 0)), topic, blender)
        rendered += 1
    print(f"3D science production plates rendered: {rendered}/{len(scenes)} scenes")


if __name__ == "__main__":
    main()
