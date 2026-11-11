"""Build an isolated Blender CGI preview from output/script.json.

This is deliberately preview-only: it writes output/3d_preview/ and never uploads.
Set FITFUEL_PREVIEW_FAST=1 for low-resolution CI previews.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from visual_scene_registry import resolve_scene_family

OUT = Path("output/3d_preview")
BLENDER_SCRIPT = Path(__file__).with_name("blender_3d_scenes.py")

FAMILY_TO_BLENDER = {
    "exercise_biomechanics": "exercise_biomechanics",
    "muscle_anatomy": "muscle_anatomy",
    "digestive_system": "digestion_fiber",
    "food_nutrition": "food_nutrition",
    "metabolism_hormones": "energy_metabolism",
    "hydration": "hydration",
    "sleep_recovery": "recovery_sleep",
    "general_science": "process",
}

FIXTURE = {
    "title": "FitFuel 3D Preview",
    "scenes": [
        {"narration": "A controlled squat activates the quadriceps and glutes.", "visual_title": "SQUAT BIOMECHANICS"},
        {"narration": "Muscle fibers contract and adapt to progressive overload.", "visual_title": "MUSCLE FIBERS"},
        {"narration": "Fiber travels through the stomach and intestines.", "visual_title": "DIGESTIVE SYSTEM"},
        {"narration": "Protein supplies amino acids for muscle repair.", "visual_title": "PROTEIN SYNTHESIS"},
    ],
}


def load_script(path, fixture=False):
    if fixture or not Path(path).exists():
        return FIXTURE
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    scenes = data.get("scenes", [])
    if not scenes:
        raise ValueError("Preview script has no scenes")
    return data


def scene_kind(scene):
    family = resolve_scene_family(
        str(scene.get("visual_title", "")) + " " + str(scene.get("narration", ""))
    )
    return FAMILY_TO_BLENDER.get(family, "process")


def render_preview(script, blender="blender", duration=2.5):
    executable = shutil.which(blender)
    if not executable:
        raise RuntimeError("Blender executable not found. Install Blender or set PATH.")
    OUT.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, scene in enumerate(script["scenes"], 1):
        target = OUT / f"scene_{i}.mp4"
        kind = scene_kind(scene)
        text = str(scene.get("visual_title") or scene.get("narration") or script.get("title", "FITFUEL"))
        cmd = [
            executable, "-b", "-P", str(BLENDER_SCRIPT), "--",
            "--kind", kind, "--duration", str(duration), "--output", str(target),
            "--orientation", "portrait", "--text", text[:52],
        ]
        if kind == "exercise_biomechanics":
            cmd += ["--exercise", text[:30]]
        print(f"[3D preview] scene {i}/{len(script['scenes'])}: {kind} — {text[:70]}", flush=True)
        subprocess.run(cmd, check=True)
        if not target.exists() or target.stat().st_size < 10_000:
            raise RuntimeError(f"Blender did not create a valid clip: {target}")
        clips.append(target)

    concat = OUT / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve()}'\\n" for p in clips), encoding="utf-8")
    final = OUT / "preview.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat), "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final),
    ], check=True)
    print(f"3D preview ready: {final} ({final.stat().st_size/1e6:.1f} MB)")
    return final


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--script", default="output/script.json")
    p.add_argument("--fixture", action="store_true", help="Render a safe built-in test script")
    p.add_argument("--duration", type=float, default=2.5)
    p.add_argument("--blender", default="blender")
    a = p.parse_args()
    if a.duration <= 0 or a.duration > 10:
        p.error("--duration must be >0 and <=10 seconds per scene")
    script = load_script(a.script, a.fixture)
    render_preview(script, a.blender, a.duration)


if __name__ == "__main__":
    main()
