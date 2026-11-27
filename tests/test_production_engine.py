import unittest

from production_engine import build_manifest, review_manifest


class ProductionDirectorTests(unittest.TestCase):
    def test_builds_timed_scene_manifest(self):
        script = {"title": "Test", "scenes": [
            {"narration": "Protein supports muscle repair.", "keyword": "protein|muscle"},
            {"narration": "Sleep supports recovery.", "keyword": "sleep|recovery"},
        ]}
        audio = [{"seconds": 2.5}, {"seconds": 3.0}]
        manifest = build_manifest(script, audio)
        self.assertEqual(manifest["scene_count"], 2)
        self.assertEqual(manifest["scenes"][1]["start"], 2.5)
        self.assertEqual(manifest["duration"], 5.5)
        self.assertEqual(manifest["scenes"][0]["visual_mode"], "science")
        self.assertTrue(review_manifest(manifest)["passed"])

    def test_rejects_missing_keywords(self):
        with self.assertRaisesRegex(ValueError, "visual search keywords"):
            build_manifest({"scenes": [{"narration": "A complete sentence."}]}, [{"seconds": 2}])

    def test_rejects_scene_audio_mismatch(self):
        with self.assertRaisesRegex(ValueError, "scene/audio mismatch"):
            build_manifest({"scenes": [{"narration": "Test", "keyword": "test"}]}, [])

    def test_review_blocks_timeline_overlap(self):
        manifest = {"scenes": [
            {"scene": 1, "start": 0, "end": 3, "duration": 3, "narration": "A", "search_keywords": ["a"]},
            {"scene": 2, "start": 2, "end": 4, "duration": 2, "narration": "B", "search_keywords": ["b"]},
        ]}
        report = review_manifest(manifest)
        self.assertFalse(report["passed"])
        self.assertTrue(any("overlaps" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
