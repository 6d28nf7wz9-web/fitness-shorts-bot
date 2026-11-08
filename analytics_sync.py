"""Sync YouTube Analytics into performance memory for evidence-based learning."""
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
MEMORY_PATH = "performance_memory.json"
UPLOAD_LOG = "output/uploaded_videos.json"
WINDOW_DAYS = int(os.getenv("ANALYTICS_WINDOW_DAYS", "28"))


def get_credentials():
    refresh = os.getenv("YT_REFRESH_TOKEN")
    if not refresh and os.path.exists("token.json"):
        with open("token.json", encoding="utf-8") as handle:
            refresh = json.load(handle).get("refresh_token")
    if not refresh:
        raise SystemExit("YT_REFRESH_TOKEN is missing.")
    credentials = Credentials(
        None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    credentials.refresh(Request())
    return credentials


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def build_topic_insights(uploads):
    grouped = defaultdict(list)
    for item in uploads:
        if not isinstance(item, dict) or not item.get("topic"):
            continue
        stats = item.get("analytics")
        if isinstance(stats, dict):
            grouped[str(item["topic"]).strip()].append(stats)

    insights = []
    for topic, rows in grouped.items():
        count = len(rows)
        insights.append({
            "topic": topic,
            "videos": count,
            "total_views": sum(int(row.get("views", 0) or 0) for row in rows),
            "total_engaged_views": sum(int(row.get("engaged_views", 0) or 0) for row in rows),
            "avg_views_per_video": round(sum(int(row.get("views", 0) or 0) for row in rows) / count),
            "avg_engaged_views_per_video": round(sum(int(row.get("engaged_views", 0) or 0) for row in rows) / count),
            "avg_view_percentage": round(sum(float(row.get("average_view_percentage", 0) or 0) for row in rows) / count, 2),
            "avg_view_duration_seconds": round(sum(float(row.get("average_view_duration_seconds", 0) or 0) for row in rows) / count, 2),
            "sample_note": "Small sample; descriptive only, not causal.",
        })
    return sorted(insights, key=lambda row: (
        row["avg_view_percentage"], row["avg_engaged_views_per_video"], row["avg_views_per_video"]
    ), reverse=True)



def build_first_week_metrics(api, uploads, report_end):
    """Compare Shorts over their first seven calendar days after publication."""
    published = {}
    for item in uploads:
        if not isinstance(item, dict) or not item.get("video_id") or not item.get("uploaded_at"):
            continue
        try:
            published[str(item["video_id"])] = date.fromisoformat(str(item["uploaded_at"])[:10])
        except ValueError:
            continue
    if not published:
        return {}

    start = max(min(published.values()), report_end - timedelta(days=89))
    query = {
        "ids": "channel==MINE",
        "startDate": start.isoformat(),
        "endDate": report_end.isoformat(),
        "dimensions": "video,day",
        "metrics": "views,engagedViews,averageViewDuration,averageViewPercentage",
        "maxResults": 200,
    }
    headers = None
    rows = []
    while True:
        page = api.reports().query(**query).execute()
        headers = page.get("columnHeaders", headers)
        rows.extend(page.get("rows", []))
        token = page.get("nextPageToken")
        if not token:
            break
        query["pageToken"] = token

    grouped = defaultdict(list)
    names = [column["name"] for column in (headers or [])]
    for row in rows:
        values = dict(zip(names, row))
        video_id = str(values.get("video", ""))
        if video_id not in published:
            continue
        try:
            day = date.fromisoformat(str(values.get("day", "")))
        except ValueError:
            continue
        age = (day - published[video_id]).days
        if 0 <= age < 7:
            grouped[video_id].append(values)

    result = {}
    for video_id, daily_rows in grouped.items():
        total_views = sum(int(row.get("views", 0) or 0) for row in daily_rows)
        total_engaged = sum(int(row.get("engagedViews", 0) or 0) for row in daily_rows)
        if total_views:
            avg_pct = sum(
                float(row.get("averageViewPercentage", 0) or 0) * int(row.get("views", 0) or 0)
                for row in daily_rows
            ) / total_views
            avg_duration = sum(
                float(row.get("averageViewDuration", 0) or 0) * int(row.get("views", 0) or 0)
                for row in daily_rows
            ) / total_views
        else:
            avg_pct = avg_duration = 0
        upload_day = published[video_id]
        complete = report_end >= upload_day + timedelta(days=6)
        result[video_id] = {
            "views_first_7_days": total_views,
            "engaged_views_first_7_days": total_engaged,
            "average_view_percentage_first_7_days": round(avg_pct, 2),
            "average_view_duration_seconds_first_7_days": round(avg_duration, 2),
            "days_since_upload_in_report": min(max((report_end - upload_day).days + 1, 0), 7),
            "first_7_days_complete": complete,
            "period_start": upload_day.isoformat(),
            "period_end": min(upload_day + timedelta(days=6), report_end).isoformat(),
        }
    return result


def build_first_week_topic_insights(uploads):
    grouped = defaultdict(list)
    for item in uploads:
        if not isinstance(item, dict) or not item.get("topic"):
            continue
        stats = item.get("first_week_analytics", {})
        if stats.get("first_7_days_complete"):
            grouped[str(item["topic"]).strip()].append(stats)

    insights = []
    for topic, rows in grouped.items():
        count = len(rows)
        views = sum(row.get("views_first_7_days", 0) for row in rows)
        engaged = sum(row.get("engaged_views_first_7_days", 0) for row in rows)
        insights.append({
            "topic": topic,
            "videos": count,
            "avg_views_first_7_days": round(views / count),
            "avg_engaged_views_first_7_days": round(engaged / count),
            "avg_view_percentage_first_7_days": round(sum(
                row.get("average_view_percentage_first_7_days", 0) for row in rows
            ) / count, 2),
            "sample_note": "Only complete first-seven-day windows; descriptive, not causal.",
        })
    return sorted(insights, key=lambda row: (
        row["avg_view_percentage_first_7_days"],
        row["avg_engaged_views_first_7_days"],
    ), reverse=True)


def main():
    memory = read_json(MEMORY_PATH, {})
    uploads = read_json(UPLOAD_LOG, [])
    if not isinstance(memory, dict):
        memory = {}
    if not isinstance(uploads, list) or not uploads:
        print("No upload history yet; nothing to sync.")
        return

    end = date.today() - timedelta(days=2)  # Analytics data can lag.
    start = end - timedelta(days=WINDOW_DAYS - 1)
    print(f"Analytics window: {start} -> {end}")
    api = build("youtubeAnalytics", "v2", credentials=get_credentials())

    try:
        query = {
            "ids": "channel==MINE",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": "video",
            "metrics": "views,engagedViews,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost",
            "sort": "-views",
            "maxResults": 200,
        }
        rows = []
        headers = None
        while True:
            page = api.reports().query(**query).execute()
            headers = page.get("columnHeaders", headers)
            rows.extend(page.get("rows", []))
            next_token = page.get("nextPageToken")
            if not next_token:
                break
            query["pageToken"] = next_token
        report = {"columnHeaders": headers or [], "rows": rows}
    except HttpError as error:
        if error.resp.status in (401, 403):
            raise SystemExit(
                "Analytics access denied. Re-run auth.py and update YT_REFRESH_TOKEN "
                "with the authorized token (yt-analytics.readonly)."
            )
        raise

    headers = [header["name"] for header in report.get("columnHeaders", [])]
    videos = {}
    for row in report.get("rows", []):
        values = dict(zip(headers, row))
        video_id = str(values.get("video", ""))
        if not video_id:
            continue
        videos[video_id] = {
            "views": int(values.get("views", 0) or 0),
            "engaged_views": int(values.get("engagedViews", 0) or 0),
            "average_view_duration_seconds": round(float(values.get("averageViewDuration", 0) or 0), 2),
            "average_view_percentage": round(float(values.get("averageViewPercentage", 0) or 0), 2),
            "likes": int(values.get("likes", 0) or 0),
            "comments": int(values.get("comments", 0) or 0),
            "shares": int(values.get("shares", 0) or 0),
            "subscribers_gained": int(values.get("subscribersGained", 0) or 0),
            "subscribers_lost": int(values.get("subscribersLost", 0) or 0),
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    enriched = []
    for item in uploads:
        if not isinstance(item, dict):
            continue
        copy = dict(item)
        video_id = copy.get("video_id")
        if video_id in videos:
            copy["analytics"] = videos[video_id]
        enriched.append(copy)

    synced_at = datetime.now(timezone.utc).isoformat()
    memory["analytics"] = {
        "source": "YouTube Analytics API",
        "window_days": WINDOW_DAYS,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "last_sync": synced_at,
        "videos": videos,
    }
    memory["video_performance"] = enriched
    memory["topic_insights"] = build_topic_insights(enriched)
    memory["learning_note"] = (
        "Per-video metrics synced from YouTube Analytics. Compare videos at similar age; "
        "use retention and engaged views, not raw views alone. Topic averages are descriptive "
        "and should be treated cautiously until each topic has multiple videos."
    )
    with open(MEMORY_PATH, "w", encoding="utf-8") as handle:
        json.dump(memory, handle, ensure_ascii=False, indent=2)

    print(f"Synced {len(videos)} videos and {len(memory['topic_insights'])} topic groups into {MEMORY_PATH}")
    if not videos:
        print("No report rows returned (API delay or no views in selected period).")


if __name__ == "__main__":
    main()
