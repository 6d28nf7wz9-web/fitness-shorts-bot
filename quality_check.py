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

    used_clip_ids = {}
    if not os.path.exists(clip_path):
        warnings.append("Clip metadata not found yet; run clips_fast.py before this gate.")
    else:
        with open(clip_path, encoding="utf-8") as f:
            clips = json.load(f)
        if len(clips) != len(scenes):
            errors.append(f"Clip scenes {len(clips)} != script scenes {len(scenes)}")
        for i, (scene, info) in enumerate(zip(scenes, clips), 1):
            if info.get("source") in ("i2v", "science_visual"):
                if not os.path.isfile(info.get("file", "")):
                    errors.append(f"Scene {i}: generated visual file is missing")
                else:
                    label = "AI-generated visual" if info.get("source") == "i2v" else "safe science-visual fallback"
                    print(f"Scene {i}: {label}; stock relevance check not applicable")
                continue
            narration = str(scene.get("narration", ""))
            parts = info.get("clips", [])
            if not parts:
                errors.append(f"Scene {i}: no clip metadata")
                continue
            weak = []
            for part in parts:
                if part.get("source") == "artcraft":
                    if not os.path.isfile(info.get("file", "")):
                        errors.append(f"Scene {i}: ArtCraft-generated visual file is missing")
                    elif part.get("match_status") != "prompted_generation":
                        errors.append(f"Scene {i}: ArtCraft visual lacks generation provenance")
                    elif os.getenv("SKIP_UPLOAD", "0") not in ("1", "true", "yes") and os.getenv("ALLOW_ARTCRAFT_UPLOAD", "0") != "1":
                        errors.append(
                            f"Scene {i}: ArtCraft-generated footage requires manual visual review "
                            "before public upload (set ALLOW_ARTCRAFT_UPLOAD=1 only after review)"
                        )
                    else:
                        warnings.append(
                            f"Scene {i}: ArtCraft-generated cut passed provenance checks; "
                            "manual review is still recommended."
                        )
                    continue
                clip_id = part.get("pixabay_id")
                if clip_id is not None:
                    previous_scene = used_clip_ids.get(str(clip_id))
                    if previous_scene is not None and previous_scene != i:
                        errors.append(f"Scene {i}: footage clip {clip_id} is reused from scene {previous_scene}")
                    else:
                        used_clip_ids[str(clip_id)] = i
                hit = {"tags": part.get("tags", ""), "pageURL": part.get("page", "")}
                score = relevance(hit, part.get("keyword", ""), narration)
                if score < 2:
                    weak.append(str(part.get("pixabay_id")))
            if weak:
                errors.append(
                    f"Scene {i}: {len(weak)}/{len(parts)} footage cuts lack a specific scene match "
                    f"(IDs {', '.join(weak[:4])}); blocking upload"
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
