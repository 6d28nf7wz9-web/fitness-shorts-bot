import json
import os
import re
import subprocess

from wan_stock_assist import try_animate_stock
from relevance import relevance as footage_relevance

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


def sentence_contexts(narration, count):
    """Distribute sentence-sized narration context across B-roll cuts."""
    sentences = [
        re.sub(r"\s+", " ", item).strip()
        for item in re.split(r"(?<=[.!?])\s+", str(narration or ""))
        if item.strip()
    ]
    count = max(1, int(count))
    if not sentences:
        words = str(narration or "").split()
        if not words:
            return [""] * count
        return [" ".join(words[round(i * len(words) / count):round((i + 1) * len(words) / count)]) for i in range(count)]

    # Group adjacent sentences by word count; never repeat the last sentence
    # simply because a scene needs more cuts than it has punctuation marks.
    groups = [[] for _ in range(count)]
    loads = [0] * count
    for sentence in sentences:
        target = min(range(count), key=lambda idx: (loads[idx], idx))
        groups[target].append(sentence)
        loads[target] += len(sentence.split())
    contexts = [" ".join(group).strip() for group in groups]
    # If the narration has fewer sentences than cuts, keep the final spoken
    # idea available for the remaining cuts instead of emitting empty queries.
    last_context = next((sentence for sentence in reversed(sentences) if sentence), "")
    contexts = [context if context else last_context for context in contexts]

    # A single long sentence still needs distinct visual beats. Split its clauses
    # or, as a final fallback, its words into contiguous slices.
    if len(sentences) == 1 and count > 1:
        clauses = [part.strip() for part in re.split(r",|;|\\b(?:and|but|while|because|then)\\b", sentences[0], flags=re.I) if part.strip()]
        if len(clauses) >= count:
            contexts = [" ".join(clauses[round(i * len(clauses) / count):round((i + 1) * len(clauses) / count)]) for i in range(count)]
        else:
            words = sentences[0].split()
            contexts = [" ".join(words[round(i * len(words) / count):round((i + 1) * len(words) / count)]) for i in range(count)]
    return contexts


EXERCISE_TARGETS = (
    (r"\bromanian deadlift\b|\brdl\b", ["romanian deadlift", "dumbbell romanian deadlift", "barbell hip hinge"]),
    (r"\bdeadlift\b", ["barbell deadlift", "deadlift exercise", "hip hinge lifting"]),
    (r"\bsquat\b", ["barbell squat", "person performing squat", "squat exercise"]),
    (r"\blunge\b|\bsplit squat\b", ["dumbbell lunge", "walking lunge exercise", "split squat"]),
    (r"\bbench press\b|\bpress the bar\b|\bchest press\b", ["barbell bench press", "bench press exercise", "chest pressing"]),
    (r"\bpush[- ]?up\b", ["push up exercise", "person doing pushups", "pushup form"]),
    (r"\bpull[- ]?up\b", ["pull up exercise", "person doing pullups", "hanging pullup"]),
    (r"\blat pulldown\b", ["lat pulldown machine", "cable lat pulldown", "back pulldown exercise"]),
    (r"\bbicep curl\b|\bcurl\b", ["dumbbell bicep curl", "barbell curl exercise", "biceps training"]),
    (r"\bshoulder press\b|\boverhead press\b|\bpress overhead\b", ["dumbbell shoulder press", "barbell overhead press", "shoulder press exercise"]),
    (r"\bplank\b", ["forearm plank exercise", "person holding plank", "plank form"]),
    (r"\bhip thrust\b", ["barbell hip thrust", "hip thrust exercise", "glute bridge movement"]),
    (r"\browing\b|\bseated row\b|\bbent[- ]over row\b", ["seated cable row", "bent over barbell row", "rowing exercise"]),
    (r"\bcalf raise\b", ["standing calf raise", "seated calf raise", "calf raise exercise"]),
)


def _exercise_variants(text):
    """Return only exercise-specific queries actually named in this narration slice."""
    text = str(text or "").lower()
    for pattern, variants in EXERCISE_TARGETS:
        if re.search(pattern, text):
            return list(variants)
    return []


def _dedupe(items):
    seen, result = set(), []
    for item in items:
        item = str(item or "").strip()
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _ordered_keywords(scene):
    """Prioritize exact movement named by the full scene before broad authored terms."""
    raw = str(scene.get("keyword", "")).strip()
    authored = [item.strip() for item in raw.split("|") if item.strip()]
    context = " ".join([raw] + [
        str(scene.get(key, "")) for key in
        ("visual_title", "visual_subtitle", "narration", "description")
    ])
    return _dedupe(_exercise_variants(context) + authored) or ["gym workout"]


def _cut_keywords(scene, sentence_context, base_keywords=None):
    """Re-rank B-roll searches per spoken sentence so each cut depicts its own action."""
    base = list(base_keywords or _ordered_keywords(scene))
    slice_targets = _exercise_variants(sentence_context)
    scene_targets = _exercise_variants(" ".join([
        str(scene.get("visual_title", "")),
        str(scene.get("visual_subtitle", "")),
        str(scene.get("keyword", "")),
    ]))
    return _dedupe(slice_targets + scene_targets + base) or ["gym workout"]


def _require_exact_footage_match(hit, keyword, context=""):
    """Fail closed unless the chosen stock clip matches this exact spoken beat."""
    score = footage_relevance(hit, keyword, context)
    if score != 2:
        raise RuntimeError(
            f"Selected B-roll failed exact semantic match (score={score}): {keyword}"
        )
    return score


def _validate_rendered_video(path, expected_seconds):
    """Validate the actual MP4 streams; file size alone is not a validity test."""
    if not os.path.isfile(path) or os.path.getsize(path) <= 0:
        raise RuntimeError("FFmpeg did not create a non-empty science fallback")

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,width,height",
            "-of", "json", path,
        ],
        check=True, capture_output=True, text=True,
    )
    try:
        metadata = json.loads(probe.stdout or "{}")
        streams = metadata.get("streams", [])
        video = next(
            (stream for stream in streams if stream.get("codec_type") == "video"),
            None,
        )
        duration = float(metadata.get("format", {}).get("duration", 0))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("FFprobe returned invalid science fallback metadata") from exc

    if not video or not video.get("width") or not video.get("height"):
        raise RuntimeError("Science fallback has no valid video stream")
    if duration <= 0 or abs(duration - float(expected_seconds)) > max(1.0, expected_seconds * 0.15):
        raise RuntimeError(
            f"Science fallback duration mismatch: expected {expected_seconds}s, got {duration}s"
        )


def _render_science_fallback(output_file, seconds):
    """Render a neutral vertical bridge; HyperFrames adds scene-specific graphics."""
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    temp_file = output_file + ".tmp.mp4"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i",
                "color=c=0x07111d:s=1080x1920:r=30",
                "-t", str(seconds),
                "-vf",
                "drawbox=x=70:y=90:w=940:h=1740:color=0x72e6c2@0.10:t=3,"
                "format=yuv420p",
                "-an", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "22", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", temp_file,
            ],
            check=True,
        )
        _validate_rendered_video(temp_file, seconds)
        os.replace(temp_file, output_file)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        raise RuntimeError(f"Science fallback FFmpeg/FFprobe failed: {str(detail)[:500]}") from exc
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


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
        output_file = os.path.join(
            CLIPS_DIR,
            f"scene_{scene_index}.mp4"
        )

        print(
            f"\nScene {scene_index} "
            f"({seconds:.2f}s)"
        )
        print(f"  narration: {narration}")

        parts = max(
            MIN_PARTS,
            min(
                MAX_PARTS,
                round(seconds / PART_SECONDS)
            )
        )

        each = seconds / parts
        cut_contexts = sentence_contexts(narration, parts)
        print(f"  stock fallback: {parts} cuts")
        print(
            f"  search priority: {', '.join(keywords)}"
        )

        part_files = []
        scene_clips = []

        try:
            for part_index in range(parts):
                sentence_context = cut_contexts[part_index]
                cut_keywords = _cut_keywords(scene, sentence_context, keywords)
                keyword = "|".join(cut_keywords)
                query, hit, url, portrait = choose_clip(
                    keyword, each, used_ids, context=sentence_context
                )
                match_score = _require_exact_footage_match(hit, keyword, sentence_context)
                clip_id = hit.get("id")
                raw_file = os.path.join(
                    RAW_DIR, f"s{scene_index}_{part_index}.mp4"
                )
                part_file = os.path.join(
                    CLIPS_DIR, f"s{scene_index}_{part_index}.mp4"
                )

                try:
                    download(url, raw_file)
                    if str(clip_id or "").startswith("coverr:"):
                        from stock_sources import track_coverr_download
                        track_coverr_download(str(clip_id).split(":", 1)[1])

                    wan_file = try_animate_stock(raw_file, scene, each, part_file)
                    if wan_file:
                        try:
                            process(wan_file, part_file, each, portrait)
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
                    "sentence_context": sentence_context,
                    "relevance_score": match_score,
                    "match_status": "exact",
                    "pixabay_id": clip_id,
                    "page": hit.get("pageURL"),
                    "author": hit.get("user"),
                    "tags": hit.get("tags"),
                    "orientation": "vertical" if portrait else "wide_blur_fit",
                    "seconds": round(each, 2),
                })

                kind = "vertical" if portrait else "wide (blur-fit)"
                print(
                    f"  cut {part_index + 1}: '{query}' -> {kind}, id {clip_id}"
                )
                print(f"    tags: {str(hit.get('tags', ''))[:120]}")

            _concat_parts(part_files, output_file, scene_index)
            info.append({
                "scene": scene_index,
                "source": "stock",
                "narration": narration,
                "keywords": keywords,
                "file": output_file,
                "seconds": seconds,
                "clips": scene_clips,
                "pixabay_ids": [clip["pixabay_id"] for clip in scene_clips],
            })
        except RuntimeError as exc:
            if not any(marker in str(exc) for marker in (
                "No specific footage match",
                "No unused scene-matched footage remains",
            )):
                raise
            print(
                f"  No verified stock match for scene {scene_index}; "
                "using a clean science-visual canvas instead."
            )
            for path in part_files:
                if os.path.exists(path):
                    os.remove(path)
            _render_science_fallback(output_file, seconds)
            info.append({
                "scene": scene_index,
                "source": "science_visual",
                "narration": narration,
                "keywords": keywords,
                "file": output_file,
                "seconds": seconds,
                "clips": [],
                "pixabay_ids": [],
                "fallback_reason": str(exc),
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
