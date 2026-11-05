"""Build short-form scene clips using narration-aware Pixabay searches."""
import json
import os
import re
import subprocess

from clips import CLIPS_DIR, RAW_DIR, choose_clip, download, process

PART_SECONDS = float(os.getenv("PART_SECONDS", "2.6"))
MAX_PARTS = max(1, int(os.getenv("MAX_PARTS", "4")))
MIN_PARTS = max(1, int(os.getenv("MIN_PARTS", "1")))


def _words(text):
    """Simple normalized words for matching a scene's search terms to narration."""
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def _ordered_keywords(scene):
    """Prioritize the supplied keywords that best reflect what the scene says."""
    narration = _words(scene.get("narration", ""))
    raw = [part.strip() for part in str(scene.get("keyword", "")).split("|")]
    keywords = []
    seen = set()
    for keyword in raw:
        key = keyword.lower()
        if keyword and key not in seen:
            seen.add(key)
            keywords.append(keyword)

    if not keywords:
        keywords = ["gym workout"]

    # A keyword with more words in common with the narration is tried first.
    # Original order breaks ties, preserving the scriptwriter's intended priority.
    indexed = list(enumerate(keywords))
    indexed.sort(
        key=lambda item: (
            len(_words(item[1]) & narration),
            -item[0],
        ),
        reverse=True,
    )
    return [keyword for _, keyword in indexed]


def _safe_id(hit):
    clip_id = hit.get("id")
    return str(clip_id) if clip_id is not None else None


def _concat_parts(part_files, output_file, scene_number):
    if len(part_files) == 1:
        os.replace(part_files[0], output_file)
        return

    list_path = os.path.join(CLIPS_DIR, f"list_{scene_number}.txt")
    # ffmpeg concat demuxer requires safely quoted paths.
    with open(list_path, "w", encoding="utf-8") as f:
        for part_file in part_files:
            absolute = os.path.abspath(part_file).replace("'", "'\\''")
            f.write(f"file '{absolute}'\n")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                "-safe", "0", "-i", list_path, "-c", "copy", output_file,
            ],
            check=True,
        )
    finally:
        for part_file in part_files:
            if os.path.exists(part_file):
                os.remove(part_file)
        if os.path.exists(list_path):
            os.remove(list_path)


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)
    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)

    scenes = script.get("scenes", [])
    if not scenes:
        raise RuntimeError("output/script.json contains no scenes")
    if len(audio) < len(scenes):
        raise RuntimeError(
            f"audio_info.json has {len(audio)} entries for {len(scenes)} scenes"
        )

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs("output", exist_ok=True)

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
                keyword,
                each,
                used_ids,
                context=narration,
            )

            clip_id = _safe_id(hit)
            if clip_id:
                used_ids.add(clip_id)

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

    print(f"\nSaved {len(info)} scene entries to output/clips_info.json")


if __name__ == "__main__":
    main()main()