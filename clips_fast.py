
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
MIN_PARTS = 1


def _ordered_keywords(scene):
    """Return scene search keywords in their original priority order."""
    raw = str(scene.get("keyword", "")).strip()

    keywords = [
        item.strip()
        for item in raw.split("|")
        if item.strip()
    ]

    if not keywords:
        keywords = ["gym workout", "healthy food"]

    return keywords


def _concat_parts(part_files, output_file, scene_index):
    """Concatenate video segments into one scene video."""
    if not part_files:
        raise RuntimeError(
            f"Scene {scene_index} has no video parts to concatenate."
        )

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    list_file = os.path.join(
        CLIPS_DIR,
        f"concat_scene_{scene_index}.txt"
    )

    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for path in part_files:
                absolute_path = os.path.abspath(path)
                escaped_path = absolute_path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                output_file,
            ],
            check=True,
        )

    finally:
        if os.path.exists(list_file):
            os.remove(list_file)


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)

    scenes = script.get("scenes", [])

    if not scenes:
        raise RuntimeError(
            "No scenes found in output/script.json"
        )

    if not isinstance(audio, list):
        raise RuntimeError(
            "output/audio_info.json must contain a list"
        )

    if len(audio) != len(scenes):
        raise RuntimeError(
            f"Audio entries ({len(audio)}) do not match "
            f"script scenes ({len(scenes)}). "
            "Run voice.py again."
        )

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs("output", exist_ok=True)

    used_ids = set()
    info = []

    for scene_index, scene in enumerate(scenes, 1):
        seconds = float(
            audio[scene_index - 1].get("seconds", 0)
        )

        if seconds <= 0:
            raise RuntimeError(
                f"Scene {scene_index} has invalid audio duration: "
                f"{seconds}"
            )

        narration = str(
            scene.get("narration", "")
        ).strip()

        keywords = _ordered_keywords(scene)

        parts = max(
            MIN_PARTS,
            min(
                MAX_PARTS,
                round(seconds / PART_SECONDS)
            )
        )

        each = seconds / parts

        print(
            f"\nScene {scene_index} "
            f"({seconds:.2f}s, {parts} cuts)"
        )
        print(f"  narration: {narration}")
        print(
            f"  search priority: {', '.join(keywords)}"
        )

        part_files = []
        scene_clips = []

        for part_index in range(parts):
            keyword = "|".join(keywords)

            query, hit, url, portrait = choose_clip(
                keyword,
                each,
                used_ids,
                context=narration,
            )

            clip_id = hit.get("id")

            raw_file = os.path.join(
                RAW_DIR,
                f"s{scene_index}_{part_index}.mp4"
            )

            part_file = os.path.join(
                CLIPS_DIR,
                f"s{scene_index}_{part_index}.mp4"
            )

            try:
                download(url, raw_file)

                process(
                    raw_file,
                    part_file,
                    each,
                    portrait,
                )

                if clip_id is not None:
                    used_ids.add(clip_id)

            finally:
                if os.path.exists(raw_file):
                    os.remove(raw_file)

            part_files.append(part_file)

            scene_clips.append({
                "query": query,
                "keyword": keyword,
                "pixabay_id": clip_id,
                "page": hit.get("pageURL"),
                "author": hit.get("user"),
                "tags": hit.get("tags"),
                "orientation": (
                    "vertical"
                    if portrait
                    else "wide_blur_fit"
                ),
                "seconds": round(each, 2),
            })

            kind = (
                "vertical"
                if portrait
                else "wide (blur-fit)"
            )

            print(
                f"  cut {part_index + 1}: "
                f"'{query}' -> {kind}, id {clip_id}"
            )

            print(
                f"    tags: "
                f"{str(hit.get('tags', ''))[:120]}"
            )

        output_file = os.path.join(
            CLIPS_DIR,
            f"scene_{scene_index}.mp4"
        )

        _concat_parts(
            part_files,
            output_file,
            scene_index,
        )

        info.append({
            "scene": scene_index,
            "narration": narration,
            "keywords": keywords,
            "file": output_file,
            "seconds": seconds,
            "clips": scene_clips,
            "pixabay_ids": [
                clip["pixabay_id"]
                for clip in scene_clips
            ],
        })

    with open(
        "output/clips_info.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            info,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\nSaved to output/clips_info.json")


if __name__ == "__main__":
    main()
