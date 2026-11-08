import json
import os
import random
import subprocess
import time

import requests

from relevance import keyword_is_relevant, popularity, relevance, fallbacks_for

API_URL = "https://pixabay.com/api/videos/"
RAW_DIR = "output/raw"
CLIPS_DIR = "output/clips"
CACHE_FILE = "output/search_cache.json"

W, H, FPS = 1080, 1920, 30


def load_cache():
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    os.makedirs("output", exist_ok=True)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def search(query):
    key = os.getenv("PIXABAY_API_KEY")

    if not key:
        raise RuntimeError("PIXABAY_API_KEY is not set")

    cache = load_cache()
    entry = cache.get(query)

    if entry and time.time() - entry.get("time", 0) < 86400:
        return entry.get("hits", [])

    params = {
        "key": key,
        "q": query,
        "per_page": 50,
        "video_type": "film",
        "safesearch": "true",
        "min_width": 720,
    }

    for attempt in range(1, 4):
        try:
            r = requests.get(API_URL, params=params, timeout=30)

            if r.status_code == 429:
                print("Pixabay rate limit, waiting 10s...")
                time.sleep(10)
                continue

            r.raise_for_status()

            hits = r.json().get("hits", [])

            # Do not cache empty results; they may be transient.
            if hits:
                cache[query] = {
                    "time": time.time(),
                    "hits": hits
                }
                save_cache(cache)

            return hits

        except requests.RequestException as e:
            print(f"[attempt {attempt}] search failed: {str(e)[:150]}")
            time.sleep(3)

    return []


def pick_file(hit):
    videos = hit.get("videos", {})

    for name in ("large", "medium", "small"):
        v = videos.get(name) or {}

        if not v.get("url"):
            continue

        if name == "large" and (v.get("size") or 0) > 45_000_000:
            continue

        return (
            v["url"],
            int(v.get("width") or 0),
            int(v.get("height") or 0)
        )

    return None


def keyword_variants(keyword, context=""):
    variants=[]
    for value in (keyword, context):
        for term in str(value or "").split("|"):
            term=term.strip()
            if term and keyword_is_relevant(term): variants.append(term)
    for value in (keyword, context):
        variants.extend(fallbacks_for(value))
    seen=set(); result=[]
    for term in variants:
        key=term.lower().strip()
        if key and key not in seen: seen.add(key); result.append(term)
    return result


def choose_clip(keyword, seconds, used_ids, context=""):
    variants = keyword_variants(keyword, context)

    if not variants:
        raise RuntimeError(f"No usable scene keywords: {keyword}")

    candidates = {}
    reusable = {}

    for query in variants:
        print(f"  Pixabay search: {query}")
        hits = search(query)

        for hit in hits:
            hit_id = hit.get("id")

            # Pixabay results without an ID cannot be tracked safely.
            if hit_id is None:
                continue

            is_reused = hit_id in used_ids

            file_info = pick_file(hit)
            if not file_info:
                continue

            # Score against the actual search query, not narration words.
            score = relevance(hit, query, context)

            if score == 0:
                continue

            url, w, h = file_info
            portrait = h > w
            duration = int(hit.get("duration") or 0)
            long_enough = duration >= seconds

            rank = (
                score,
                long_enough,
                portrait,
                popularity(hit)
            )

            target = reusable if is_reused else candidates
            previous = target.get(hit_id)
            if previous is None or rank > previous[0]:
                target[hit_id] = (
                    rank, query, hit, url, portrait
                )

    if not candidates and reusable:
        candidates = reusable
        print("  WARNING: Reusing relevant clips because no unused matches were found.")

    exact = [
        item for item in candidates.values()
        if item[0][0] == 2
    ]

    category_matches = [
        item for item in candidates.values()
        if item[0][0] == 1
    ]

    if exact:
        pool = exact
        print(f"  Using {len(pool)} specific matching clips.")
    elif category_matches:
        pool = category_matches
        print(
            f"  No specific match; using "
            f"{len(pool)} same-category clips."
        )
    else:
        raise RuntimeError(
            f"No relevant clip found for: {keyword}. "
            f"Searches tried: {', '.join(variants)}"
        )

    pool.sort(key=lambda item: item[0], reverse=True)
    top = pool[:6]

    weights = [
        4 if item[0][0] == 2 else 1
        for item in top
    ]

    _, query, hit, url, portrait = random.choices(
        top,
        weights=weights
    )[0]

    return query, hit, url, portrait


def download(url, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    for attempt in range(1, 4):
        try:
            if os.path.exists(path):
                os.remove(path)

            with requests.get(
                url,
                stream=True,
                timeout=60
            ) as r:
                r.raise_for_status()

                with open(path, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        if chunk:
                            f.write(chunk)

            if os.path.isfile(path) and os.path.getsize(path) > 10000:
                return

            raise RuntimeError("Downloaded file is empty or too small")

        except (requests.RequestException, OSError, RuntimeError) as e:
            if os.path.exists(path):
                os.remove(path)

            print(f"[attempt {attempt}] download failed: {str(e)[:150]}")

            if attempt < 3:
                time.sleep(3)

    raise RuntimeError(f"Could not download {url}")


def process(raw, out, seconds, portrait):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    temp_out = f"{out}.tmp.mp4"

    try:
        if os.path.exists(temp_out):
            os.remove(temp_out)

        base = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-stream_loop", "-1", "-i", raw,
            "-t", str(seconds), "-an"
        ]

        encode = [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            temp_out
        ]

        if portrait:
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
                f"[b]crop='min(iw,ih)':'min(iw,ih)',scale={W}:{W}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
                f"fps={FPS},setsar=1[v]"
            )
            cmd = base + [
                "-filter_complex", fc,
                "-map", "[v]"
            ] + encode

        subprocess.run(cmd, check=True)

        if not os.path.isfile(temp_out) or os.path.getsize(temp_out) <= 10000:
            raise RuntimeError(f"FFmpeg produced an invalid output: {temp_out}")

        os.replace(temp_out, out)

    except Exception:
        if os.path.exists(temp_out):
            os.remove(temp_out)
        raise


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    used_ids = set()
    info = []

    for i, scene in enumerate(script["scenes"], 1):
        seconds = audio[i - 1]["seconds"]

        keyword = str(scene.get("keyword", "")).strip()
        narration = str(scene.get("narration", ""))

        print(f"\nScene {i} ({seconds}s): {keyword}")

        query, hit, url, portrait = choose_clip(
            keyword,
            seconds,
            used_ids,
            narration
        )

        raw = f"{RAW_DIR}/scene_{i}.mp4"
        out = f"{CLIPS_DIR}/scene_{i}.mp4"

        try:
            download(url, raw)
            process(raw, out, seconds, portrait)
            if hit.get("id") is not None:
                used_ids.add(hit["id"])
        finally:
            if os.path.exists(raw):
                os.remove(raw)

        print(
            f"  selected '{query}' | "
            f"id={hit.get('id')} | tags={str(hit.get('tags', ''))[:120]}"
        )

        info.append({
            "scene": i,
            "file": out,
            "seconds": seconds,
            "query": query,
            "keyword": keyword,
            "narration": narration,
            "pixabay_id": hit.get("id"),
            "page": hit.get("pageURL"),
            "author": hit.get("user"),
            "tags": hit.get("tags"),
        })

    with open("output/clips_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print("\nSaved to output/clips_info.json")


if __name__ == "__main__":
    main()