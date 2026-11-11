import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import text_to_video as t2v


class TextToVideoPreflightTests(unittest.TestCase):
    def setUp(self):
        self.script = {"scenes": [
            {"narration": "Your muscles adapt when training stress is followed by recovery.",
             "visual_title": "Muscle recovery and adaptation", "keyword": "muscle recovery"},
            {"narration": "Protein provides amino acids for muscle repair.",
             "visual_title": "Protein synthesis", "keyword": "protein food"},
        ]}
        self.audio = [{"seconds": 5.4}, {"seconds": 4.2}]

    def test_builds_one_prompt_per_scene(self):
        plan = t2v.build_plan(self.script, self.audio)
        self.assertEqual(len(plan["scenes"]), 2)
        self.assertEqual(plan["scenes"][0]["target_generation_seconds"], 5)
        self.assertIn("3D anatomical fitness-explainer", plan["scenes"][0]["prompt"])
        self.assertIn(self.script["scenes"][1]["narration"], plan["scenes"][1]["prompt"])
        self.assertEqual(plan["scenes"][0]["aspect_ratio"], "9:16")

    def test_missing_narration_fails_closed(self):
        with self.assertRaises(ValueError):
            t2v.scene_prompt({"narration": "  "}, 1)

    def test_audio_scene_mismatch_fails(self):
        with self.assertRaises(ValueError):
            t2v.build_plan(self.script, self.audio[:1])

    def test_all_hosted_providers_are_marked_paid_api(self):
        for provider in ("kling", "runway", "wan"):
            self.assertEqual(t2v.PROVIDERS[provider]["status"], "paid_api")

    def test_preflight_does_not_make_network_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path.cwd()
            try:
                os.chdir(tmp)
                Path("output").mkdir()
                Path("output/script.json").write_text(json.dumps(self.script), encoding="utf-8")
                Path("output/audio_info.json").write_text(json.dumps(self.audio), encoding="utf-8")
                with patch("requests.post") as post, patch("requests.get") as get:
                    t2v.main()
                post.assert_not_called()
                get.assert_not_called()
                result = json.loads(Path("output/t2v_prompt_plan.json").read_text(encoding="utf-8"))
                self.assertEqual(len(result["scenes"]), 2)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
