"""Tests for analytics-driven topic and hook recommendations."""
import unittest
from topic_intelligence import recommend_topics, hook_learning, _mature_video_rows


class TopicIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.memory = {
            "analytics": {
                "period_end": "2026-11-20",
                "videos": {
                    "food1": {"views": 500, "engaged_views": 180, "average_view_percentage": 70, "subscribers_gained": 3},
                    "food2": {"views": 300, "engaged_views": 110, "average_view_percentage": 65, "subscribers_gained": 2},
                    "weak": {"views": 3, "engaged_views": 1, "average_view_percentage": 150, "subscribers_gained": 0},
                },
            },
            "video_performance": [
                {"video_id": "food1", "topic": "Lean ground beef swap", "hook": "Stop choosing the fattier option.", "uploaded_at": "2026-11-01T10:00:00Z"},
                {"video_id": "food2", "topic": "Protein first for hunger", "hook": "Still hungry after your meal?", "uploaded_at": "2026-11-02T10:00:00Z"},
                {"video_id": "weak", "topic": "Amazing muscle growth", "hook": "Did you know?", "uploaded_at": "2026-11-01T10:00:00Z"},
            ],
        }

    def test_tiny_samples_and_replay_retention_do_not_dominate(self):
        rows = _mature_video_rows(self.memory)
        self.assertEqual({row["video_id"] for row in rows}, {"food1", "food2"})
        self.assertTrue(all(row["retention"] <= 100 for row in rows))

    def test_recommendations_exclude_recent_duplicates(self):
        rows = recommend_topics(self.memory, used=["Which high-protein breakfast keeps you full longer?"])
        self.assertTrue(rows)
        self.assertNotEqual(rows[0]["topic"], "Which high-protein breakfast keeps you full longer?")

    def test_hook_learning_returns_measured_openings_only(self):
        rows = hook_learning(self.memory)
        self.assertEqual(len(rows), 2)
        self.assertIn(rows[0]["pattern"], ("specific curiosity question", "direct challenge or mistake correction"))
        self.assertGreaterEqual(rows[0]["views"], 25)

    def test_empty_memory_returns_exploration_candidates(self):
        rows = recommend_topics({})
        self.assertTrue(rows)
        self.assertTrue(all(row["evidence_videos"] == 0 for row in rows))


if __name__ == "__main__":
    unittest.main()
