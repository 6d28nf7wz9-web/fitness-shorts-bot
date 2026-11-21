"""Render scene-matched 3D science plates for the production video timeline.

Supported scientific categories are rendered as topic-specific 3D scenes. The
resulting MP4s are consumed by HyperFrames as visual layers; SVG remains only a
fallback for unsupported or general-purpose topics. This script never uploads or publishes a video.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from visual_engine import classify_scene


SUPPORTED_3D_TOPICS = {
    "anatomy", "muscle", "protein", "heart", "fat_loss", "hydration",
    "exercise", "nutrition", "hormones", "creatine", "supplements",
    "tracking", "recovery", "general",
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
        raise RuntimeError(f"3D science render missing or too small: {mp4}")
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "json", str(mp4),
    ], text=True)
    stream = json.loads(probe)["streams"][0]
    if (stream.get("width"), stream.get("height")) != (720, 1280):
        raise RuntimeError(f"Unexpected 3D plate dimensions: {stream}")
    if stream.get("r_frame_rate") != "30/1":
        raise RuntimeError(f"Unexpected 3D plate frame rate: {stream}")
    print(f"3D science scene {index}: {topic}, {frames} source frames -> {mp4}")


def main():
    script_path = ROOT / "output" / "script.json"
    audio_path = ROOT / "output" / "audio_info.json"
    if not script_path.exists() or not audio_path.exists():
        raise SystemExit("3D science renderer: script.json and audio_info.json are required; refusing silent 2D fallback.")
    scenes = json.loads(script_path.read_text(encoding="utf-8")).get("scenes", [])
    audio = json.loads(audio_path.read_text(encoding="utf-8"))
    if not scenes or len(scenes) != len(audio):
        raise SystemExit("3D science renderer: non-empty scene/audio lists with matching counts are required.")
    blender = shutil.which("blender")
    if not blender:
        raise SystemExit("3D science renderer: Blender is required for the approved 3D production pipeline.")
    generated_dir = ROOT / "output" / "science_3d"
    if generated_dir.exists():
        shutil.rmtree(generated_dir)
    rendered = 0
    for index, (scene, timing) in enumerate(zip(scenes, audio), 1):
        topic = scene_topic(scene)
        if not topic:
            raise SystemExit(f"3D science renderer: scene {index} has no supported 3D topic; refusing a silent fallback.")
        render_scene(index, scene, float(timing.get("seconds", 0)), topic, blender)
        rendered += 1
    if rendered != len(scenes):
        raise SystemExit(f"3D science renderer: rendered {rendered}/{len(scenes)} scenes; all scenes must have verified 3D plates.")
    print(f"3D science production plates rendered and validated: {rendered}/{len(scenes)} scenes")


if __name__ == "__main__":
    main()
