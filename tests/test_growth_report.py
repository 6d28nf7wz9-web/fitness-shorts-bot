"""Offline tests for FitFuel growth report generation."""
import unittest

from growth_report import build_report


class GrowthReportTests(unittest.TestCase):
    def test_report_ranks_video_by_retention_and_includes_hook(self):
        memory = {
            "baseline": {"subscribers": 42, "viewed_vs_swiped_percent": 38.2},
            "analytics": {"period_end": "2026-11-12", "videos": {
                "low": {"views": 100, "engaged_views": 50, "average_view_percentage": 20, "subscribers_gained": 0},
                "high": {"views": 80, "engaged_views": 60, "average_view_percentage": 75, "subscribers_gained": 3},
            }},
            "video_performance": [
                {"video_id": "low", "topic": "Low retention", "hook": "A weak start"},
                {"video_id": "high", "topic": "Strong retention", "hook": "Stop doing this"},
            ],
            "topic_insights": [{"topic": "Strength", "videos": 2, "avg_view_percentage": 70, "avg_engaged_views_per_video": 55}],
            "series_insights": [{"series": "Myth check", "videos": 3, "avg_view_percentage": 65, "subscribers_gained": 4}],
        }
        report = build_report(memory)
        self.assertLess(report.index("Strong retention"), report.index("Low retention"))
        self.assertIn("Stop doing this", report)
        self.assertIn("38.2%", report)
        self.assertIn("Strength", report)
        self.assertIn("Myth check", report)

    def test_empty_memory_is_safe_and_explains_missing_data(self):
        report = build_report({})
        self.assertIn("No synced video data yet", report)
        self.assertIn("No topic-level analytics yet", report)
        self.assertIn("YouTube Studio > Earn", report)


if __name__ == "__main__":
    unittest.main()
