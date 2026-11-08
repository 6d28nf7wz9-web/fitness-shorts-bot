import json
import os
import random
import subprocess

from clips import download, keyword_variants, pick_file, search
from relevance import popularity, relevance

OUT_DIR = "output/long"
RAW_DIR = f"{OUT_DIR}/raw"
CHUNK_DIR = f"{OUT_DIR}/chunks"
W, H, FPS = 1920, 1080, 30
TARGET_CHUNK = 7.0  # seconds per clip


def choose(keyword, seconds, used_ids, context=""):
    variants = keyword_variants(keyword, context)
    if not variants:
        raise RuntimeError(f"No usable keywords for long section: {keyword}")

    for query in variants:
        hits = search(query)
        cands = []
        for hit in hits:
            hit_id = hit.get("id")
            if hit_id is None or hit_id in used_ids:
                continue
            f = pick_file(hit)
            if not f:
                continue
            url, w, h = f
            landscape = w >= h
            rel = relevance(hit, query, context)
            if rel == 0 or (rel < 2 and os.getenv("ALLOW_CATEGORY_ONLY_CLIPS", "0") != "1"):
                continue
            long_enough = (hit.get("duration") or 0) >= seconds
            cands.append(((rel, long_enough, landscape), hit, url, landscape))
        if cands:
            cands.sort(key=lambda c: (c[0], popularity(c[1])), reverse=True)
            top = cands[:6]
            weights = [4 if c[0][0] == 2 else 1 for c in top]     # clips matching the keyword are 4x more likely
            _, hit, url, landscape = random.choices(top, weights=weights)[0]
            return query, hit, url, landscape
        print(f"    no on-topic results for '{query}', trying the next search")
    raise RuntimeError(
        f"No specific clip found for long section: {keyword}. Category-only fallback is disabled. "
        f"Searches tried: {', '.join(variants)}"
    )


def process(raw, out, seconds, landscape, start):
    temp_out = out + ".tmp.mp4"
    base = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", raw,
        "-t", f"{seconds:.2f}", "-an",
    ]
    encode = [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-r", str(FPS), "-pix_fmt", "yuv420p", temp_out,
    ]

    try:
        if landscape:
            vf = (
                f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},fps={FPS},setsar=1"
            )
            cmd = base + ["-vf", vf] + encode
        else:
            fc = (
                f"[0:v]split[a][b];"
                f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},boxblur=30:5,eq=brightness=-0.15[bg];"
                f"[b]scale=-2:{H}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
                f"fps={FPS},setsar=1[v]"
            )
            cmd = base + ["-filter_complex", fc, "-map", "[v]"] + encode

        subprocess.run(cmd, check=True)

        if not os.path.exists(temp_out) or os.path.getsize(temp_out) <= 10_000:
            raise RuntimeError(f"FFmpeg produced an invalid chunk: {temp_out}")

        os.replace(temp_out, out)

    finally:
        if os.path.exists(temp_out):
            os.remove(temp_out)


def main():
    with open(f"{OUT_DIR}/timeline.json", encoding="utf-8") as f:
        tl = json.load(f)

    sections = tl.get("sections") or []
    if not sections:
        raise RuntimeError("Timeline has no sections.")

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CHUNK_DIR, exist_ok=True)

    used_ids, chunks, n = set(), [], 0
    for si, sec in enumerate(sections, 1):
        try:
            section_start = float(sec["start"])
            section_end = float(sec["end"])
        except (KeyError, TypeError, ValueError):
            raise RuntimeError(f"Section {si} has invalid start/end values.")

        dur = section_end - section_start
        if dur <= 0:
            raise RuntimeError(f"Section {si} has non-positive duration: {dur}")

        keywords = sec.get("keywords") or []
        if not keywords:
            raise RuntimeError(f"Section {si} has no search keywords.")

        parts = max(1, round(dur / TARGET_CHUNK))
        each = dur / parts
        print(f"\nSection {si}: {sec['heading']} ({dur:.0f}s, {parts} clips)")
        t = section_start
        for p in range(parts):
            n += 1
            kw = keywords[p % len(keywords)]
            query, hit, url, landscape = choose(
                kw, each, used_ids, sec.get("heading", "")
            )

            raw = f"{RAW_DIR}/c{n:03d}.mp4"
            out = f"{CHUNK_DIR}/c{n:03d}.mp4"

            try:
                download(url, raw)
                clip_len = hit.get("duration") or 0
                start = random.uniform(0, max(0.0, clip_len - each - 0.3))
                process(raw, out, each, landscape, start)
            finally:
                if os.path.exists(raw):
                    os.remove(raw)

            used_ids.add(hit["id"])
            chunks.append({
                "file": out, "start": round(t, 2), "end": round(t + each, 2),
                "section": si, "query": query, "pixabay_id": hit.get("id"),
                "page": hit.get("pageURL"), "author": hit.get("user"), "tags": hit.get("tags"),
            })
            t += each
            kind = "wide" if landscape else "vertical (blur-fit)"
            print(f"  {n:02d} '{query}' -> {kind}, id {hit.get('id')}  tags: {str(hit.get('tags', ''))[:60]}")

    with open(f"{OUT_DIR}/chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"\nSaved {len(chunks)} clips to {CHUNK_DIR}")


if __name__ == "__main__":
    main()
