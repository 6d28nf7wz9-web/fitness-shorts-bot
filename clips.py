import json
import os
import subprocess
import time

import requests

API_URL = "https://pixabay.com/api/videos/"
RAW_DIR = "output/raw"
CLIPS_DIR = "output/clips"
CACHE_FILE = "output/search_cache.json"
W, H, FPS = 1080, 1920, 30
FALLBACK_KEYWORDS = ["gym workout", "healthy food", "running outdoors", "fitness training"]


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
    if entry and time.time() - entry["time"] < 86400:
        return entry["hits"]
    params = {
        "key": key,
        "q": query,
        "per_page": 30,
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
            cache[query] = {"time": time.time(), "hits": hits}
            save_cache(cache)
            return hits
        except requests.RequestException as e:
            print(f"[attempt {attempt}] search failed: {str(e)[:150]}")
            time.sleep(3)
    return []


def pick_file(hit):
    """Return (url, width, height) for the best usable file of a hit."""
    videos = hit.get("videos", {})
    for name in ("large", "medium", "small"):
        v = videos.get(name) or {}
        if not v.get("url"):
            continue
        if name == "large" and (v.get("size") or 0) > 45_000_000:
            continue  # too big, try medium
        return v["url"], int(v.get("width") or 0), int(v.get("height") or 0)
    return None


def keyword_variants(keyword):
    words = keyword.split()
    variants = [keyword]
    if len(words) > 2:
        variants.append(" ".join(words[-2:]))
    if len(words) > 1:
        variants.append(words[-1])
    variants += FALLBACK_KEYWORDS
    seen, result = set(), []
    for v in variants:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def choose_clip(keyword, seconds, used_ids):
    for query in keyword_variants(keyword):
        hits = search(query)
        candidates = []
        for hit in hits:
            if hit.get("id") in used_ids:
                continue
            f = pick_file(hit)
            if not f:
                continue
            url, w, h = f
            portrait = h > w
            long_enough = (hit.get("duration") or 0) >= seconds
            candidates.append(((portrait, long_enough), hit, url, portrait))
        if candidates:
            candidates.sort(key=lambda c: c[0], reverse=True)
            _, hit, url, portrait = candidates[0]
            return query, hit, url, portrait
        print(f"  no usable results for '{query}', trying next keyword")
    raise RuntimeError(f"No clip found for keyword: {keyword}")


def download(url, path):
    for attempt in range(1, 4):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if os.path.getsize(path) > 10000:
                return
        except requests.RequestException as e:
            print(f"[attempt {attempt}] download failed: {str(e)[:150]}")
            time.sleep(3)
    raise RuntimeError(f"Could not download {url}")


def process(raw, out, seconds, portrait):
    base = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", raw, "-t", str(seconds), "-an"]
    encode = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS), "-pix_fmt", "yuv420p", out]
    if portrait:
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1"
        cmd = base + ["-vf", vf] + encode
    else:
        fc = (
            f"[0:v]split[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,eq=brightness=-0.15[bg];"
            f"[b]crop='min(iw,ih)':'min(iw,ih)',scale={W}:{W}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={FPS},setsar=1[v]"
        )
        cmd = base + ["-filter_complex", fc, "-map", "[v]"] + encode
    subprocess.run(cmd, check=True)


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)
    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)
    used_ids, info = set(), []

    for i, scene in enumerate(script["scenes"], 1):
        seconds = audio[i - 1]["seconds"]
        print(f"\nScene {i} ({seconds}s) keyword: {scene['keyword']}")
        query, hit, url, portrait = choose_clip(scene["keyword"], seconds, used_ids)
        used_ids.add(hit.get("id"))
        raw = f"{RAW_DIR}/scene_{i}.mp4"
        out = f"{CLIPS_DIR}/scene_{i}.mp4"
        download(url, raw)
        process(raw, out, seconds, portrait)
        kind = "vertical" if portrait else "wide (blur-fit)"
        print(f"  used '{query}' -> {kind} clip, id {hit.get('id')}")
        info.append({
            "scene": i,
            "file": out,
            "seconds": seconds,
            "query": query,
            "pixabay_id": hit.get("id"),
            "page": hit.get("pageURL"),
            "author": hit.get("user"),
        })

    with open("output/clips_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    print("\nSaved to output/clips_info.json")


main()