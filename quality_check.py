"""Pre-upload quality gate for generated Shorts scripts and clip relevance."""
import json
import os
import re
import sys

from relevance import relevance


def words(s):
    return set(re.findall(r"[a-z]{3,}", str(s).lower()))


def main():
    script_path = "output/script.json"
    clip_path = "output/clips_info.json"
    if not os.path.exists(script_path):
        raise SystemExit("Missing output/script.json")
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    scenes = script.get("scenes", [])
    errors = []
    warnings = []
    if not 4 <= len(scenes) <= 5:
        errors.append(f"Short must have 4-5 scenes, found {len(scenes)}")
    total = sum(len(str(s.get("narration", "")).split()) for s in scenes)
    if not 45 <= total <= 65:
        errors.append(f"Narration word count {total} outside 45-65")
    if scenes:
        hook = len(str(scenes[0].get("narration", "")).split())
        if not 4 <= hook <= 9:
            errors.append(f"Hook has {hook} words; expected 4-9")
    if len(str(script.get("title", ""))) > 60:
        errors.append("Title exceeds 60 characters")

    if not os.path.exists(clip_path):
        warnings.append("Clip metadata not found yet; run clips_fast.py before this gate.")
    else:
        with open(clip_path, encoding="utf-8") as f:
            clips = json.load(f)
        if len(clips) != len(scenes):
            errors.append(f"Clip scenes {len(clips)} != script scenes {len(scenes)}")
        for i, (scene, info) in enumerate(zip(scenes, clips), 1):
            if info.get("source") == "i2v":
                if not os.path.isfile(info.get("file", "")):
                    errors.append(f"Scene {i}: AI video file is missing")
                else:
                    print(f"Scene {i}: AI-generated visual; stock relevance check not applicable")
                continue
            narration = str(scene.get("narration", ""))
            parts = info.get("clips", [])
            if not parts:
                errors.append(f"Scene {i}: no clip metadata")
                continue
            weak = []
            for part in parts:
                hit = {"tags": part.get("tags", ""), "pageURL": part.get("page", "")}
                score = relevance(hit, part.get("keyword", ""), narration)
                if score < 2:
                    weak.append(str(part.get("pixabay_id")))
            if weak and len(weak) == len(parts):
                errors.append(
                    f"Scene {i}: all {len(parts)} footage cuts lack a specific scene match "
                    f"(IDs {', '.join(weak[:4])}); blocking upload"
                )
            elif weak:
                warnings.append(
                    f"Scene {i}: {len(weak)}/{len(parts)} footage cuts lack a specific scene match "
                    f"(IDs {', '.join(weak[:4])})"
                )

    print(f"Quality gate: {len(scenes)} scenes, {total} spoken words")
    for warning in warnings:
        print("WARN:", warning)
    for error in errors:
        print("FAIL:", error)
    if errors:
        sys.exit(1)
    print("PASS: structural quality checks clear")


if __name__ == "__main__":
    main()
