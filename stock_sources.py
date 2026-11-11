"""Free stock video adapters normalized for clips.py.

Pexels requires a user-provided API key. NASA's public media API is keyless.
Mixkit/Videvo do not provide a stable public search API; their licensed downloads
can be imported into stock_library/ with a .json sidecar (documented below).
"""
import json
import os
import re
import time
from pathlib import Path

import requests

CACHE_FILE = "output/search_cache.json"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "FitFuel-video-pipeline/1.0"})


def _cache_load():
    try:
        return json.loads(Path(CACHE_FILE).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _cache_save(cache):
    Path("output").mkdir(parents=True, exist_ok=True)
    Path(CACHE_FILE).write_text(json.dumps(cache), encoding="utf-8")


def _cached(key, fetch):
    cache = _cache_load()
    item = cache.get(key)
    if item and time.time() - item.get("time", 0) < 86400:
        return item.get("hits", [])
    try:
        hits = fetch()
        if hits:
            cache[key] = {"time": time.time(), "hits": hits}
            _cache_save(cache)
        return hits
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        print(f"  source search warning ({key.split(':', 1)[0]}): {str(exc)[:140]}")
        return []


def _pexels(query):
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        return []
    def fetch():
        response = SESSION.get(
            "https://api.pexels.com/v1/videos/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 30, "orientation": "portrait"},
            timeout=25,
        )
        response.raise_for_status()
        out = []
        for video in response.json().get("videos", []):
            files = sorted(video.get("video_files", []),
                           key=lambda f: (f.get("width", 0) <= 1920, f.get("width", 0)),
                           reverse=True)
            chosen = next((f for f in files if f.get("link") and f.get("file_type", "").startswith("video/")), None)
            if not chosen:
                continue
            page_url = video.get("url", "https://www.pexels.com")
            tags = re.sub(r"[-_/]", " ", page_url.rsplit("/", 2)[-2])
            out.append({
                "id": f"pexels:{video.get('id')}",
                "tags": tags,
                "duration": int(video.get("duration", 0)),
                "user": (video.get("user") or {}).get("name", "Pexels contributor"),
                "pageURL": page_url,
                "videos": {"large": {"url": chosen["link"], "width": chosen.get("width", 0),
                                    "height": chosen.get("height", 0), "size": 0}},
            })
        return out
    return _cached("pexels:" + query.lower(), fetch)



def _coverr(query):
    """Search Coverr's official API. Demo keys are limited to 50 requests/hour."""
    key = os.getenv("COVERR_API_KEY", "").strip()
    if not key:
        return []

    def fetch():
        response = SESSION.get(
            "https://api.coverr.co/videos",
            headers={"x-api-key": key},
            params={
                "query": query,
                "page_size": 20,
                "sort": "popular",
                "urls": "true",
            },
            timeout=25,
        )
        response.raise_for_status()
        out = []
        for video in response.json().get("hits", []):
            if not video.get("id"):
                continue
            # Prefer the download URL; signed URLs are tied to this API key.
            urls = video.get("urls") or {}
            mp4 = urls.get("mp4_download") or urls.get("mp4")
            if not mp4:
                continue
            # Never use sponsored partner footage or watermarked premium previews.
            if (video.get("is_sponsored") or video.get("sponsored") or video.get("is_partner_content")
                    or video.get("is_premium") or video.get("is_premium_preview") or video.get("is_watermarked")):
                continue
            creator = video.get("creator") or video.get("contributor") or video.get("user") or {}
            if isinstance(creator, str):
                author = creator
                creator_url = ""
            else:
                author = (creator.get("name") or creator.get("full_name")
                          or video.get("creator_name") or video.get("author") or "")
                creator_url = (creator.get("url") or creator.get("profile_url")
                               or video.get("creator_url") or "")
            title = video.get("title") or video.get("description") or "Coverr stock video"
            tags_value = video.get("tags") or []
            tags = " ".join(map(str, tags_value)) if isinstance(tags_value, list) else str(tags_value)
            width = int(video.get("max_width") or video.get("width") or 0)
            height = int(video.get("max_height") or video.get("height") or 0)
            out.append({
                "id": f"coverr:{video.get('id')}",
                "tags": f"{title} {tags} {video.get('description', '')}",
                "duration": int(float(video.get("duration") or 0)),
                "user": author,
                "pageURL": creator_url or video.get("url") or video.get("page_url") or "https://coverr.co/",
                "videos": {"large": {
                    "url": mp4,
                    "width": width,
                    "height": height,
                    "size": 0,
                }},
            })
        return out

    return _cached("coverr:" + query.lower(), fetch)


def track_coverr_download(video_id):
    """Notify Coverr after a selected clip is actually downloaded, as required by API terms."""
    key = os.getenv("COVERR_API_KEY", "").strip()
    if not key or not video_id:
        return
    try:
        response = SESSION.patch(
            f"https://api.coverr.co/videos/{video_id}/stats/downloads",
            headers={"x-api-key": key},
            timeout=12,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        # Tracking failures should not discard a successfully downloaded render asset.
        print(f"  Coverr download tracking warning: {str(exc)[:140]}")


def _nasa(query):
    # NASA is a niche source; only videos with downloadable MP4 assets are returned.
    def fetch():
        response = SESSION.get(
            "https://images-api.nasa.gov/search",
            params={"q": query, "media_type": "video", "page_size": 8},
            timeout=25,
        )
        response.raise_for_status()
        out = []
        for item in response.json().get("collection", {}).get("items", [])[:5]:
            data = (item.get("data") or [{}])[0]
            nasa_id = data.get("nasa_id")
            if not nasa_id:
                continue
            manifest = SESSION.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=25)
            manifest.raise_for_status()
            assets = manifest.json()
            urls = assets.get("collection", {}).get("items", [])
            mp4 = next((a.get("href") for a in urls if str(a.get("href", "")).lower().endswith(".mp4")), None)
            if not mp4:
                continue
            title = data.get("title", "")
            desc = data.get("description", "")
            out.append({
                "id": f"nasa:{nasa_id}", "tags": f"{title} {desc[:350]}",
                "duration": 0, "user": data.get("secondary_creator", "NASA"),
                "pageURL": item.get("href", f"https://images.nasa.gov/details/{nasa_id}"),
                "videos": {"large": {"url": mp4, "width": 1920, "height": 1080, "size": 0}},
            })
        return out
    return _cached("nasa:" + query.lower(), fetch)


def _local_mixkit_videvo(query):
    """Use locally downloaded licensed clips; never scrape restricted websites."""
    folder = Path("stock_library")
    if not folder.exists():
        return []
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    out = []
    for sidecar in folder.glob("*.json"):
        try:
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
            video = folder / meta.get("file", (sidecar.stem + ".mp4"))
            if not video.is_file() or meta.get("source", "").lower() not in {"mixkit", "videvo"}:
                continue
            tags = " ".join([str(meta.get("title", "")), *map(str, meta.get("tags", []))])
            tag_words = set(re.findall(r"[a-z0-9]+", tags.lower()))
            if not words.intersection(tag_words):
                continue
            out.append({
                "id": f"{meta.get('source')}:{sidecar.stem}", "tags": tags,
                "duration": int(meta.get("duration", 0)), "user": meta.get("author", meta.get("source")),
                "pageURL": meta.get("url", ""), "videos": {"large": {
                    "url": str(video.resolve()), "width": int(meta.get("width", 1080)),
                    "height": int(meta.get("height", 1920)), "size": video.stat().st_size}},
            })
        except (OSError, ValueError, TypeError):
            continue
    return out


def search_stock_sources(query):
    results = []
    if os.getenv("COVERR_API_KEY"):
        print(f"  Coverr search: {query}")
        results.extend(_coverr(query))
    if os.getenv("PEXELS_API_KEY"):
        print(f"  Pexels search: {query}")
        results.extend(_pexels(query))
    if os.getenv("NASA_VIDEO_SEARCH", "0") == "1":
        print(f"  NASA video search: {query}")
        results.extend(_nasa(query))
    results.extend(_local_mixkit_videvo(query))
    return results
