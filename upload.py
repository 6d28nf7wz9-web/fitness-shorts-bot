
import json
import os
import time
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from gen_script import mark_used

FINAL = "output/final.mp4"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

PRIVACY = os.getenv("UPLOAD_PRIVACY", "private")
UPLOAD_LOG = "output/uploaded_videos.json"


def get_credentials():
    refresh = os.getenv("YT_REFRESH_TOKEN")

    if not refresh and os.path.exists("token.json"):
        with open("token.json", encoding="utf-8") as f:
            refresh = json.load(f)["refresh_token"]

    if not refresh:
        raise SystemExit("No refresh token found. Run auth.py first.")

    creds = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=SCOPES,
    )

    try:
        creds.refresh(Request())
    except Exception as e:
        raise SystemExit(
            "Login expired or invalid. Run auth.py again.\n" + str(e)[:200]
        )

    return creds


def save_upload(video_id, script):
    os.makedirs("output", exist_ok=True)

    try:
        with open(UPLOAD_LOG, encoding="utf-8") as f:
            records = json.load(f)
        if not isinstance(records, list):
            records = []
    except (FileNotFoundError, json.JSONDecodeError):
        records = []

    if any(item.get("video_id") == video_id for item in records):
        print("Video already exists in upload history.")
        return

    records.append({
        "video_id": video_id,
        "title": script.get("title", ""),
        "topic": script.get("topic", ""),
        "series": script.get("series", "Unclassified"),
        "episode_number": script.get("episode_number"),
        "episode_topic": script.get("episode_topic", ""),
        "hook": (script.get("scenes") or [{}])[0].get("narration", ""),
        "script_word_count": sum(len(str(scene.get("narration", "")).split()) for scene in script.get("scenes", [])),
        "scene_count": len(script.get("scenes", [])),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "privacy": PRIVACY,
        "status": "uploaded",
    })

    with open(UPLOAD_LOG, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved upload record: {video_id}")


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    # Credit the footage providers/contributors actually used in this render.
    try:
        with open("output/clips_info.json", encoding="utf-8") as f:
            clip_data = json.load(f)
        providers, creators = set(), set()
        for scene in clip_data if isinstance(clip_data, list) else []:
            for clip in scene.get("clips", []):
                asset_id = str(clip.get("pixabay_id", ""))
                page = str(clip.get("page", ""))
                author = str(clip.get("author", "")).strip()
                if asset_id.startswith("pexels:"):
                    providers.add("Pexels")
                    if author and page:
                        creators.add(f"{author} ({page})")
                elif asset_id.startswith("coverr:"):
                    providers.add("Coverr")
                    if author and page:
                        creators.add(f"{author} on Coverr ({page})")
                elif asset_id.startswith("nasa:"):
                    providers.add("NASA")
                elif asset_id.startswith("mixkit:"):
                    providers.add("Mixkit")
                    if author: creators.add(author)
                elif asset_id.startswith("videvo:"):
                    providers.add("Videvo")
                    if author: creators.add(author)
        if providers:
            attribution = "Stock footage sources: " + ", ".join(sorted(providers)) + "."
            if "Coverr" in providers:
                attribution += "\nCoverr stock footage: https://coverr.co/"
            if creators:
                attribution += "\nContributors/assets: " + "; ".join(sorted(creators)[:8])
            script["description"] = script.get("description", "").rstrip() + "\n\n" + attribution
    except (OSError, ValueError, TypeError):
        pass

    # Preview mode must never initialize YouTube credentials or upload anything.
    if os.getenv("SKIP_UPLOAD", "").strip().lower() in {"1", "true", "yes"}:
        if not os.path.isfile(FINAL) or os.path.getsize(FINAL) < 10000:
            raise SystemExit(f"Preview video is missing or invalid: {FINAL}")
        print(f"SKIP_UPLOAD is enabled: validated {FINAL}; no YouTube client created.")
        return

    youtube = build("youtube", "v3", credentials=get_credentials())

    tags = [
        str(t).lstrip("#")
        for t in script.get("hashtags", [])
    ][:10]

    body = {
        "snippet": {
            "title": script["title"],
            "description": script["description"],
            "tags": tags,
            "categoryId": "17",
        },
        "status": {
            "privacyStatus": PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        FINAL,
        mimetype="video/mp4",
        chunksize=-1,
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"Uploading '{script['title']}' as {PRIVACY}...")

    response, retries = None, 0

    while response is None:
        try:
            _, response = request.next_chunk()
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retries < 5:
                retries += 1
                print(f"Server error {e.resp.status}, retry {retries}/5")
                time.sleep(2 ** retries)
                continue
            raise

    video_id = response["id"]

    save_upload(video_id, script)
    mark_used(script["topic"])

    print("\nUploaded successfully!")
    print("Watch:  https://www.youtube.com/watch?v=" + video_id)
    print("Studio: https://studio.youtube.com/video/" + video_id + "/edit")
    print("History: " + UPLOAD_LOG)


if __name__ == "__main__":
    main()