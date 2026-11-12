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
from image_to_video import (
    generate_video,
    scene_image_path,
    scene_is_eligible,
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


def _try_i2v(scene_index, scene, seconds, output_file):
    """Try one explicitly enabled AI scene; return metadata or None for stock fallback."""
    if not scene_is_eligible(scene_index):
        return None

    image_path = scene_image_path(scene_index)
    raw_file = os.path.join(RAW_DIR, f"i2v_scene_{scene_index}.mp4")
    prompt = "Scene narration: " + str(scene.get("narration", ""))
    prompt += ". Visual direction: " + str(scene.get("visual_title") or scene.get("keyword") or "")

    try:
        print(
            f"  AI visual enabled: provider={os.getenv('I2V_PROVIDER', 'kling')} "
            f"image={image_path}"
        )
        generate_video(image_path, prompt, raw_file)
        process(raw_file, output_file, seconds, True)
        return {
            "scene": scene_index,
            "source": "i2v",
            "provider": os.getenv("I2V_PROVIDER", "kling"),
            "input_image": str(image_path),
            "file": output_file,
            "seconds": seconds,
            "narration": str(scene.get("narration", "")),
            "clips": [{
                "source": "i2v",
                "keyword": str(scene.get("keyword", "")),
                "tags": "AI-generated image-to-video scene",
                "seconds": min(5, seconds),
            }],
            "pixabay_ids": [],
        }
    except Exception as exc:
        # Never chain to another paid provider. The regular stock path is the
        # only fallback, preventing accidental multi-provider credit spend.
        print(f"  AI visual unavailable; falling back to stock: {str(exc)[:220]}")
        return None
    finally:
        if os.path.exists(raw_file):
            os.remove(raw_file)


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
        output_file = os.path.join(
            CLIPS_DIR,
            f"scene_{scene_index}.mp4"
        )

        print(
            f"\nScene {scene_index} "
            f"({seconds:.2f}s)"
        )
        print(f"  narration: {narration}")

        # AI is strictly opt-in, limited to the first configured scenes, and
        # requires a pre-generated still. Missing images never trigger billing.
        ai_info = _try_i2v(
            scene_index,
            scene,
            seconds,
            output_file,
        )
        if ai_info:
            info.append(ai_info)
            print(f"  source: image-to-video ({ai_info['provider']})")
            continue

        parts = max(
            MIN_PARTS,
            min(
                MAX_PARTS,
                round(seconds / PART_SECONDS)
            )
        )

        each = seconds / parts
        print(f"  stock fallback: {parts} cuts")
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

                if str(clip_id or "").startswith("coverr:"):
                    from stock_sources import track_coverr_download
                    track_coverr_download(str(clip_id).split(":", 1)[1])

                # Wan may enhance one selected stock segment, using a frame
                # from that exact Coverr/Pixabay result as its visual reference.
                # If disabled or unsuccessful, the original stock segment is used.
                wan_file = try_animate_stock(raw_file, scene, each, part_file)
                if wan_file:
                    try:
                        process(wan_file, part_file, each, True)
                    finally:
                        if os.path.exists(wan_file):
                            os.remove(wan_file)
                    clip_source = "stock+wan"
                else:
                    process(raw_file, part_file, each, portrait)
                    clip_source = "stock"

                if clip_id is not None:
                    used_ids.add(clip_id)

            finally:
                if os.path.exists(raw_file):
                    os.remove(raw_file)

            part_files.append(part_file)

            scene_clips.append({
                "source": clip_source,
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

        _concat_parts(
            part_files,
            output_file,
            scene_index,
        )

        info.append({
            "scene": scene_index,
            "source": "stock",
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
