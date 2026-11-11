import json
import os
import tempfile
import unittest
from unittest.mock import patch

from series_engine import SERIES, next_episode


class SeriesEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        os.makedirs("output", exist_ok=True)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def write_uploads(self, rows):
        with open("output/uploaded_videos.json", "w", encoding="utf-8") as f:
            json.dump(rows, f)

    def test_first_run_starts_first_planned_series(self):
        name, number, topic = next_episode()
        self.assertEqual(name, list(SERIES)[0])
        self.assertEqual(number, 1)
        self.assertEqual(topic, SERIES[name][0])

    def test_successful_upload_advances_episode(self):
        name = list(SERIES)[0]
        self.write_uploads([{"series": name, "episode_number": 1}])
        selected, number, topic = next_episode()
        self.assertEqual(selected, name)
        self.assertEqual(number, 2)
        self.assertEqual(topic, SERIES[name][1])

    def test_preview_does_not_advance_without_upload_record(self):
        first = next_episode()
        second = next_episode()
        self.assertEqual(first, second)

    def test_finished_series_rotates_to_next(self):
        name = list(SERIES)[0]
        rows = [{"series": name, "episode_number": i + 1} for i in range(len(SERIES[name]))]
        self.write_uploads(rows)
        selected, number, topic = next_episode()
        self.assertNotEqual(selected, name)
        self.assertEqual(number, 1)
        self.assertEqual(topic, SERIES[selected][0])

    def test_catalog_contains_safe_controversial_topics(self):
        topics = " ".join(topic.lower() for episodes in SERIES.values() for topic in episodes)
        self.assertIn("steroids", topics)
        self.assertIn("testosterone", topics)
        self.assertIn("trt", topics)


if __name__ == "__main__":
    unittest.main()
