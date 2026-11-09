"""Regression tests for FitFuel series-level performance learning."""

import unittest

from analytics_sync import build_series_insights


class SeriesAnalyticsTests(unittest.TestCase):
    def test_groups_metrics_by_series_and_ranks_by_retention(self):
        uploads = [
            {"series": "Fitness Myth Check", "analytics": {
                "views": 100, "engaged_views": 60,
                "average_view_percentage": 80, "subscribers_gained": 3,
            }},
            {"series": "Fitness Myth Check", "analytics": {
                "views": 200, "engaged_views": 120,
                "average_view_percentage": 70, "subscribers_gained": 2,
            }},
            {"series": "Smart Food Choices", "analytics": {
                "views": 500, "engaged_views": 100,
                "average_view_percentage": 35, "subscribers_gained": 1,
            }},
            {"series": "Unmeasured", "title": "No analytics yet"},
        ]

        result = build_series_insights(uploads)
        self.assertEqual(result[0]["series"], "Fitness Myth Check")
        self.assertEqual(result[0]["videos"], 2)
        self.assertEqual(result[0]["avg_views_per_video"], 150)
        self.assertEqual(result[0]["avg_engaged_views_per_video"], 90)
        self.assertEqual(result[0]["avg_view_percentage"], 75)
        self.assertEqual(result[0]["subscribers_gained"], 5)
        self.assertEqual(result[1]["series"], "Smart Food Choices")

    def test_ignores_missing_or_invalid_analytics(self):
        self.assertEqual(build_series_insights([
            {"series": "Fitness Myth Check"},
            None,
            {"topic": "missing series", "analytics": {"views": 10}},
        ]), [])


if __name__ == "__main__":
    unittest.main()
