import json
import os
import subprocess

from clips import (
    CLIPS_DIR,
    RAW_DIR,
    choose_clip,
    download,
    process,
)

PART_SECONDS = float(os.getenv("PART_SECONDS", "2.6"))
MAX_PARTS = 4


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    used_ids = set()
    info = []

    for scene_index, scene in enumerate(scenes, 1):
        seconds = float(audio[scene_index - 1].get("seconds", 0))
        if seconds <= 0:
            raise RuntimeError(f"Scene {scene_index} has invalid audio duration: {seconds}")

        narration = str(scene.get("narration", "")).strip()
        keywords = _ordered_keywords(scene)
        parts = max(MIN_PARTS, min(MAX_PARTS, round(seconds / PART_SECONDS)))
        each = seconds / parts

        print(f"\nScene {scene_index} ({seconds:.2f}s, {parts} cuts)")
        print(f"  narration: {narration}")
        print(f"  search priority: {', '.join(keywords)}")

        part_files = []
        scene_clips = []

        for part_index in range(parts):
            # Rotate across the best narration-related terms to vary the visuals.
            keyword = keywords[part_index % len(keywords)]
            query, hit, url, portrait = choose_clip(
                kw,
                each,
                used_ids,
                context=narration,
            )

            used_ids.add(hit.get("id"))

            raw_file = os.path.join(RAW_DIR, f"s{scene_index}_{part_index}.mp4")
            part_file = os.path.join(CLIPS_DIR, f"s{scene_index}_{part_index}.mp4")

            try:
                download(url, raw_file)
                process(raw_file, part_file, each, portrait)
            finally:
                if os.path.exists(raw_file):
                    os.remove(raw_file)

            part_files.append(part_file)
            scene_clips.append({
                "query": query,
                "keyword": keyword,
                "pixabay_id": hit.get("id"),
                "page": hit.get("pageURL"),
                "author": hit.get("user"),
                "tags": hit.get("tags"),
                "orientation": "vertical" if portrait else "wide_blur_fit",
                "seconds": round(each, 2),
            })

            kind = "vertical" if portrait else "wide (blur-fit)"
            print(f"  cut {part_index + 1}: '{query}' -> {kind}, id {hit.get('id')}")
            print(f"    tags: {str(hit.get('tags', ''))[:120]}")

        output_file = os.path.join(CLIPS_DIR, f"scene_{scene_index}.mp4")
        _concat_parts(part_files, output_file, scene_index)

        info.append({
            "scene": scene_index,
            "narration": narration,
            "keywords": keywords,
            "file": output_file,
            "seconds": seconds,
            "clips": scene_clips,
            # Keep the previous field for compatibility with any downstream script.
            "pixabay_ids": [clip["pixabay_id"] for clip in scene_clips],
        })

    with open("output/clips_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print("\nSaved to output/clips_info.json")


if __name__ == "__main__":
    main()