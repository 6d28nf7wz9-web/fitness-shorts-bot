import json
import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from gen_script import mark_used

FINAL = "output/final.mp4"
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
        raise SystemExit(
            "Login expired or invalid. Run auth.py again.\n" + str(e)[:200]
        )
    return creds


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    youtube = build("youtube", "v3", credentials=get_credentials())

    tags = [str(t).lstrip("#") for t in script.get("hashtags", [])][:10]
    body = {
        "snippet": {
            "title": script["title"],
            "description": script["description"],
            "tags": tags,
            "categoryId": "17",  # Sports
        },
        "status": {
            "privacyStatus": PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(FINAL, mimetype="video/mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

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
    mark_used(script["topic"])
    print("\nUploaded!")
    print("Watch:  https://www.youtube.com/watch?v=" + video_id)
    print("Studio: https://studio.youtube.com/video/" + video_id + "/edit")


main()