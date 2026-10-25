import json
import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

OUT_DIR = "output/long"
FINAL = f"{OUT_DIR}/final_long.mp4"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
PRIVACY = os.getenv("UPLOAD_PRIVACY", "private")  # private, unlisted or public


def get_credentials():
    refresh = os.getenv("YT_REFRESH_TOKEN")
    if not refresh and os.path.exists("token.json"):
        with open("token.json") as f:
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
        raise SystemExit("Login expired or invalid. Run auth.py again.\n" + str(e)[:200])
    return creds


def main():
    with open(f"{OUT_DIR}/meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    with open(f"{OUT_DIR}/job.json", encoding="utf-8") as f:
        job = json.load(f)

    youtube = build("youtube", "v3", credentials=get_credentials())
    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"][:4900],
            "tags": meta.get("tags", [])[:10],
            "categoryId": "26",  # Howto & Style
        },
        "status": {
            "privacyStatus": PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(
        FINAL, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True
    )
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"Uploading '{meta['title']}' as {PRIVACY}...")
    response, retries = None, 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retries < 5:
                retries += 1
                print(f"Server error {e.resp.status}, retry {retries}/5")
                time.sleep(2 ** retries)
                continue
            raise

    video_id = response["id"]
    if not os.getenv("SKIP_STATUS"):
        qpath = job["queue_file"]
        with open(qpath, encoding="utf-8") as f:
            queue = json.load(f)
        queue["status"] = "uploaded"
        queue["youtube_id"] = video_id
        with open(qpath, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)

    print("\nUploaded!")
    print("Watch:  https://www.youtube.com/watch?v=" + video_id)
    print("Studio: https://studio.youtube.com/video/" + video_id + "/edit")


main()