"""Render a short local/CI preview of the scientific animation families."""
import os
import subprocess
from pathlib import Path

from science_visuals import render_scene

SCENES = [
    {
        "narration": "Dietary fiber travels through the digestive system and reaches the colon.",
        "visual_title": "Where dietary fiber goes",
        "visual_subtitle": "Follow fiber through the digestive tract",
        "visual_type": "digestion_fiber",
    },
    {
        "narration": "Resistance training challenges muscle fibers and they adapt over time.",
        "visual_title": "Muscle fibers under tension",
        "visual_subtitle": "A simplified view of muscle structure and adaptation",
        "visual_type": "muscle_anatomy",
    },
    {
        "narration": "During a shoulder press, the deltoids and triceps help move the weight overhead.",
        "visual_title": "Shoulder press biomechanics",
        "visual_subtitle": "Watch the pressing movement and working muscles",
        "visual_type": "exercise_biomechanics",
    },
    {
        "narration": "Cells convert stored energy into ATP that powers movement.",
        "visual_title": "How cells make usable energy",
        "visual_subtitle": "Stored energy is converted into cellular energy",
        "visual_type": "energy_metabolism",
    },
]

def main():
    out = Path("output")
    out.mkdir(exist_ok=True)
    clips = []
    for i, scene in enumerate(SCENES, 1):
        clip = out / f"science_preview_scene_{i}.mp4"
        print(f"Rendering preview scene {i}/{len(SCENES)}")
        render_scene(scene, i, 3.0, str(clip))
        clips.append(clip)

    concat_file = out / "science_preview_concat.txt"
    concat_file.write_text(
        "".join(f"file '{clip.resolve()}'\n" for clip in clips),
        encoding="utf-8",
    )
    final = out / "science_preview.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c", "copy", str(final)
    ], check=True)
    concat_file.unlink(missing_ok=True)
    for clip in clips:
        clip.unlink(missing_ok=True)
    print(f"Preview ready: {final}")

if __name__ == "__main__":
    main()
