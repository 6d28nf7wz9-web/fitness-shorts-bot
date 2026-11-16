"""Build a human-readable, offline FitFuel growth report from saved analytics memory."""
import json
import os
from datetime import datetime, timezone

MEMORY_PATH = os.getenv("FITFUEL_MEMORY_PATH", "performance_memory.json")
OUTPUT_PATH = os.getenv("FITFUEL_GROWTH_REPORT", "output/growth_report.md")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def _number(value, digits=1):
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def build_report(memory):
    memory = memory if isinstance(memory, dict) else {}
    baseline = memory.get("baseline", {})
    analytics = memory.get("analytics", {})
    uploads = memory.get("video_performance", [])
    videos = analytics.get("videos", {})
    metadata = {
        str(item.get("video_id")): item
        for item in uploads
        if isinstance(item, dict) and item.get("video_id")
    }

    lines = [
        "# FitFuel — Growth & Content Performance",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Analytics data through: {analytics.get('period_end', 'not synced')}",
        "",
        "## Channel baseline (owner-provided snapshot)",
        "",
        f"- Views: {_number(baseline.get('total_views'), 0)}",
        f"- Watch hours: {_number(baseline.get('watch_hours'), 2)}",
        f"- Subscribers: {_number(baseline.get('subscribers'), 0)}",
        f"- Viewed vs swiped: {_number(baseline.get('viewed_vs_swiped_percent'))}%",
        f"- Average viewed: {_number(baseline.get('average_percentage_viewed'))}%",
        "",
        "## Best measured videos",
        "",
        "| Video / topic | Views (window) | Engaged views | Avg viewed | Subs gained | Opening hook |",
        "|---|---:|---:|---:|---:|---|",
    ]

    # Avoid misleading "winners" caused by tiny samples or replay-heavy retention.
    eligible = []
    for video_id, stats in videos.items():
        if not isinstance(stats, dict):
            continue
        views = int(stats.get("views", 0) or 0)
        engaged = int(stats.get("engaged_views", 0) or 0)
        if views < 50 or engaged < 15:
            continue
        retention = max(0.0, min(100.0, float(stats.get("average_view_percentage", 0) or 0)))
        engagement_rate = engaged / max(views, 1)
        subs = max(0, int(stats.get("subscribers_gained", 0) or 0))
        # Transparent directional score: retention 45%, engagement rate 35%, reach 15%, subs 5%.
        score = (retention * .45) + (min(engagement_rate, 1.0) * 100 * .35) + (min(views / 1000, 1.0) * 15) + (min(subs / 5, 1.0) * 5)
        eligible.append((video_id, stats, score))
    ranked = sorted(eligible, key=lambda row: row[2], reverse=True)
    for video_id, stats, score in ranked[:10]:
        item = metadata.get(video_id, {})
        label = item.get("topic") or item.get("title") or video_id
        hook = str(item.get("hook") or "not recorded").replace("|", "\\|").replace("\\n", " ")
        lines.append(
            f"| {label} (score {score:.1f}) | {_number(stats.get('views'), 0)} | "
            f"{_number(stats.get('engaged_views'), 0)} | "
            f"{_number(stats.get('average_view_percentage'))}% | "
            f"{_number(stats.get('subscribers_gained'), 0)} | {hook} |"
        )
    if not videos:
        lines.append("| No synced video data yet | — | — | — | — | — |")
    elif not ranked:
        lines.append("| No videos passed the minimum sample (50 views, 15 engaged views) | — | — | — | — | — |")

    # First-week comparison only uses fully completed seven-day windows.
    first_week = memory.get("first_week_analytics", {}).get("videos", {})
    complete = []
    for video_id, fw in first_week.items():
        if not isinstance(fw, dict) or not fw.get("first_7_days_complete"):
            continue
        views7 = int(fw.get("views_first_7_days", 0) or 0)
        engaged7 = int(fw.get("engaged_views_first_7_days", 0) or 0)
        retention7 = float(fw.get("average_view_percentage_first_7_days", 0) or 0)
        item = metadata.get(video_id, {})
        complete.append((video_id, item, fw, views7, engaged7, retention7))
    complete.sort(key=lambda row: (row[5], row[4], row[3]), reverse=True)
    lines += ["", "## First 7 days — completed windows only", ""]
    if complete:
        lines += ["| Video/topic | Views (7d) | Engaged (7d) | Avg viewed |", "|---|---:|---:|---:|"]
        for video_id, item, fw, views7, engaged7, retention7 in complete[:10]:
            label = item.get("topic") or item.get("title") or video_id
            lines.append(f"| {label} | {views7} | {engaged7} | {retention7:.1f}% |")
    else:
        lines.append("- No fully completed 7-day windows in this sync; newer uploads are intentionally excluded.")
    partial = sum(1 for fw in first_week.values() if isinstance(fw, dict) and not fw.get("first_7_days_complete"))
    if partial:
        lines.append(f"- {partial} additional uploads have incomplete windows and are not ranked.")

    lines += ["", "## Topic signals", ""]
    topics = [
        row for row in memory.get("topic_insights", [])
        if isinstance(row, dict) and int(row.get("videos", 0) or 0) >= 2
    ]
    topics.sort(
        key=lambda row: (
            float(row.get("avg_view_percentage", 0) or 0),
            float(row.get("avg_engaged_views_per_video", 0) or 0),
        ),
        reverse=True,
    )
    for row in topics[:8]:
        lines.append(
            f"- **{row.get('topic', 'Unknown')}** — {row.get('videos', 0)} videos; "
            f"{_number(row.get('avg_view_percentage'))}% average viewed; "
            f"{_number(row.get('avg_engaged_views_per_video'), 0)} engaged views/video."
        )
    if not topics:
        lines.append("- No topic has at least 2 measured videos yet; single-video topics are excluded to avoid false winners.")

    lines += ["", "## Series signals", ""]
    series = [
        row for row in memory.get("series_insights", [])
        if isinstance(row, dict) and int(row.get("videos", 0) or 0) >= 3
    ]
    series.sort(
        key=lambda row: (
            float(row.get("avg_view_percentage", 0) or 0),
            int(row.get("avg_engaged_views_per_video", 0) or 0),
        ),
        reverse=True,
    )
    for row in series[:8]:
        lines.append(
            f"- **{row.get('series', 'Unknown')}** — {row.get('videos', 0)} videos; "
            f"{_number(row.get('avg_view_percentage'))}% average viewed; "
            f"{_number(row.get('subscribers_gained'), 0)} subscribers gained."
        )
    if not series:
        lines.append("- No series has at least 3 measured videos yet; small series are excluded from ranking.")

    lines += [
        "",
        "## Actionable guidance",
        "",
        "- Winner shortlist excludes videos below 50 views or 15 engaged views; score is directional, not a YouTube ranking factor.",
        "- Prioritize topics/hooks that combine retention with engaged views and subscriber gains.",
        "- Compare Shorts at similar ages; use complete first-7-day metrics when available.",
        "- Treat small samples as directional only; do not infer causation from one video.",
        "- Keep scripts original and useful; avoid near-duplicate mass-produced episodes.",
        "- Shorts-feed watch time does not count toward the 4,000 public watch-hour route.",
        "",
        "## Data limitations",
        "",
        "- Views and engaged views are reporting-window metrics, not guaranteed eligible monetization views.",
        "- Viewed-vs-swiped is shown only if present in the owner-provided baseline; it is not currently fetched by this sync.",
        "- Verify official YPP eligibility in YouTube Studio > Earn.",
        "",
    ]
    return "\n".join(lines)


def main():
    report = build_report(load_json(MEMORY_PATH, {}))
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(report)
    print(f"Growth report saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
