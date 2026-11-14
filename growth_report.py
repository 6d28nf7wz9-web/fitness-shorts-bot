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

    ranked = sorted(
        ((video_id, stats) for video_id, stats in videos.items() if isinstance(stats, dict)),
        key=lambda pair: (
            float(pair[1].get("average_view_percentage", 0) or 0),
            int(pair[1].get("engaged_views", 0) or 0),
            int(pair[1].get("views", 0) or 0),
        ),
        reverse=True,
    )
    for video_id, stats in ranked[:10]:
        item = metadata.get(video_id, {})
        label = item.get("topic") or item.get("title") or video_id
        hook = str(item.get("hook") or "not recorded").replace("|", "\\|").replace("\\n", " ")
        lines.append(
            f"| {label} | {_number(stats.get('views'), 0)} | "
            f"{_number(stats.get('engaged_views'), 0)} | "
            f"{_number(stats.get('average_view_percentage'))}% | "
            f"{_number(stats.get('subscribers_gained'), 0)} | {hook} |"
        )
    if not ranked:
        lines.append("| No synced video data yet | — | — | — | — | — |")

    lines += ["", "## Topic signals", ""]
    topics = [
        row for row in memory.get("topic_insights", [])
        if isinstance(row, dict)
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
        lines.append("- No topic-level analytics yet.")

    lines += ["", "## Series signals", ""]
    series = [row for row in memory.get("series_insights", []) if isinstance(row, dict)]
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
        lines.append("- No series-level analytics yet.")

    lines += [
        "",
        "## Actionable guidance",
        "",
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
