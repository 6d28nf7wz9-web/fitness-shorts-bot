"""Create a cautious YouTube Partner Program progress snapshot.

Shorts video totals are a channel-owned upload-log proxy, not a certification of
eligible public Shorts Feed views. Public watch-hour eligibility must be verified
in YouTube Studio's Earn tab.
"""
import json
import os
from datetime import date, datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

UPLOAD_LOG = "output/uploaded_videos.json"
OUTPUT = "output/monetization_progress.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def credentials():
    refresh = os.getenv("YT_REFRESH_TOKEN")
    if not refresh and os.path.exists("token.json"):
        with open("token.json", encoding="utf-8") as handle:
            refresh = json.load(handle).get("refresh_token")
    if not refresh:
        raise SystemExit("YT_REFRESH_TOKEN is missing.")
    auth = Credentials(
        None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    auth.refresh(Request())
    return auth


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def query_report(api, start, end, metrics, dimensions=None):
    kwargs = {
        "ids": "channel==MINE",
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "metrics": metrics,
    }
    if dimensions:
        kwargs["dimensions"] = dimensions
    return api.reports().query(**kwargs).execute()


def main():
    auth = credentials()
    youtube = build("youtube", "v3", credentials=auth)
    analytics = build("youtubeAnalytics", "v2", credentials=auth)
    today = datetime.now(timezone.utc).date()
    end = today - timedelta(days=2)  # Allow for reporting delay.
    start_90 = end - timedelta(days=89)
    start_365 = end - timedelta(days=364)

    try:
        channel_response = youtube.channels().list(part="statistics", mine=True).execute()
        channels = channel_response.get("items", [])
        if not channels:
            raise SystemExit("No YouTube channel was returned for the authorized account.")
        stats = channels[0].get("statistics", {})
        subscriber_count = int(stats["subscriberCount"]) if stats.get("subscriberCount") else None
        total_channel_views = int(stats.get("viewCount", 0) or 0)

        uploads = load_json(UPLOAD_LOG, [])
        short_ids = {
            str(item.get("video_id"))
            for item in uploads
            if isinstance(item, dict) and item.get("video_id")
            and item.get("status", "uploaded") == "uploaded"
        }

        short_views = 0
        short_engaged_views = 0
        short_rows = 0
        if short_ids:
            report = query_report(
                analytics, start_90, end,
                "views,engagedViews", dimensions="video"
            )
            headers = [column["name"] for column in report.get("columnHeaders", [])]
            for row in report.get("rows", []):
                values = dict(zip(headers, row))
                if str(values.get("video", "")) in short_ids:
                    short_views += int(values.get("views", 0) or 0)
                    short_engaged_views += int(values.get("engagedViews", 0) or 0)
                    short_rows += 1

        watch_report = query_report(
            analytics, start_365, end, "estimatedMinutesWatched"
        )
        watch_headers = [column["name"] for column in watch_report.get("columnHeaders", [])]
        watch_values = dict(zip(watch_headers, watch_report.get("rows", [[]])[0])) if watch_report.get("rows") else {}
        estimated_minutes = int(watch_values.get("estimatedMinutesWatched", 0) or 0)

    except HttpError as error:
        if error.resp.status in (401, 403):
            raise SystemExit(
                "YouTube read access denied. Re-run auth.py and update YT_REFRESH_TOKEN "
                "with youtube.readonly and yt-analytics.readonly scopes."
            )
        raise

    public_uploads_90d = sum(
        1 for item in uploads if isinstance(item, dict)
        and item.get("status", "uploaded") == "uploaded"
        and item.get("privacy") == "public"
        and item.get("uploaded_at", "")[:10] >= start_90.isoformat()
    ) if isinstance(uploads, list) else 0

    def progress(value, target):
        if value is None:
            return None
        return round(min(value / target * 100, 100), 2)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_through": end.isoformat(),
        "channel": {
            "subscribers": subscriber_count,
            "total_channel_views_lifetime": total_channel_views,
        },
        "last_90_days": {
            "uploaded_public_shorts_in_log": public_uploads_90d,
            "shorts_video_views_proxy": short_views,
            "shorts_engaged_views": short_engaged_views,
            "shorts_videos_with_analytics_rows": short_rows,
            "shorts_upload_log_video_count": len(short_ids),
        },
        "last_365_days": {
            "channel_estimated_watch_minutes_all_content": estimated_minutes,
            "channel_estimated_watch_hours_all_content": round(estimated_minutes / 60, 2),
        },
        "standard_ads_revenue_milestones": {
            "subscribers_target": 1000,
            "subscribers_progress_percent": progress(subscriber_count, 1000),
            "shorts_valid_public_views_target_90d": 10000000,
            "shorts_video_views_proxy_progress_percent": progress(short_views, 10000000),
            "public_watch_hours_target_12m": 4000,
            "public_watch_hours_progress_percent": None,
            "public_watch_hours_note": (
                "Not calculated from estimatedMinutesWatched: this API metric includes content "
                "that may not qualify. Verify eligible public watch hours in YouTube Studio > Earn."
            ),
        },
        "expanded_ypp_reference": {
            "subscribers_target": 500,
            "shorts_valid_public_views_target_90d": 3000000,
            "public_watch_hours_target_12m": 3000,
            "public_uploads_target_90d": 3,
            "note": "Country availability and all other YPP requirements apply; verify in Studio > Earn.",
        },
        "limitations": [
            "Shorts video views are a proxy from videos in output/uploaded_videos.json, not verified eligible public Shorts Feed views.",
            "The Shorts proxy may include views outside the Shorts Feed and can be incomplete if upload history is incomplete.",
            "Estimated channel watch hours are not the same as eligible public watch hours.",
            "YouTube Studio > Earn is the authoritative source for monetization eligibility.",
        ],
    }
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print("Monetization progress snapshot saved:", OUTPUT)
    print("Subscribers:", subscriber_count if subscriber_count is not None else "hidden/unavailable")
    print(f"Shorts views proxy (90d): {short_views:,} / 10,000,000")
    print(f"Shorts engaged views (90d): {short_engaged_views:,}")
    print(f"Public uploads in upload log (90d): {public_uploads_90d}")
    print(f"Channel estimated watch hours (365d, not eligibility hours): {estimated_minutes / 60:.2f}")
    print("Check YouTube Studio > Earn for the official eligible public Shorts views and watch hours.")


if __name__ == "__main__":
    main()
