"""Regression tests for scene-specific stock footage matching and upload gating."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from clips import choose_clip
from quality_check import main as quality_check_main
from relevance import relevance


def make_hit(hit_id, tags):
    return {
        "id": hit_id,
        "tags": tags,
        "pageURL": f"https://example.invalid/video/{hit_id}",
        "duration": 20,
        "videos": {
            "medium": {
                "url": f"https://example.invalid/video/{hit_id}.mp4",
                "width": 1080,
                "height": 1920,
                "size": 100_000,
            }
        },
    }


class ClipRelevanceRegressionTests(unittest.TestCase):
    def test_category_fallback_cannot_turn_food_footage_into_a_training_match(self):
        food_hit = make_hit(
            11638,
            "chop vegetables food cooking kitchen meal dinner healthy cuisine",
        )

        def search_only_food_fallback(query):
            return [food_hit] if query == "cooking healthy meal" else []

        scene_keywords = "gym workout|weight training|fitness training"
        narration = "Synthetic hormones flood your blood and confuse your brain signals."

        with patch("clips.search", side_effect=search_only_food_fallback):
            with patch.dict(os.environ, {"ALLOW_CATEGORY_ONLY_CLIPS": "0"}):
                with self.assertRaisesRegex(RuntimeError, "No specific footage match"):
                    choose_clip(scene_keywords, 2.5, set(), context=narration)

    def test_demographic_and_pose_words_do_not_make_a_bird_a_specific_fitness_match(self):
        bird = {"tags": "bullfinch male bird nature sitting perched"}
        score = relevance(
            bird,
            "male athlete sitting thoughtfully on gym bench",
            "Steroids quickly shut down your testes.",
        )
        self.assertEqual(score, 0)

    def test_generic_swimming_word_does_not_match_jellyfish_to_sperm_scene(self):
        jellyfish = {"tags": "jellyfish tank water marine aquarium sea swimming"}
        score = relevance(
            jellyfish,
            "microscopic sperm cells swimming in lab sample",
            "Natural sperm and testosterone production.",
        )
        self.assertEqual(score, 0)

    def test_real_scene_specific_terms_still_select_a_matching_clip(self):
        relevant_hit = make_hit(
            9001,
            "steroid injection gym fitness training",
        )
        with patch("clips.search", return_value=[relevant_hit]):
            with patch.dict(os.environ, {"ALLOW_CATEGORY_ONLY_CLIPS": "0"}):
                _, selected, _, _ = choose_clip(
                    "steroid injection in gym",
                    2.5,
                    set(),
                    context="Steroid injections can affect testosterone.",
                )
        self.assertEqual(selected["id"], 9001)

    def test_quality_gate_blocks_a_scene_when_every_cut_is_weak(self):
        scenes = [
            {"narration": "Steroids can shut down natural hormone signals."},
            {"narration": "Synthetic hormones may suppress the brain signals that normally regulate testosterone production."},
            {"narration": "Lower signaling can reduce sperm production and affect fertility over time in men."},
            {"narration": "Discuss hormone use with a qualified clinician before making any decisions about treatment."},
        ]
        clip_info = [
            {
                "scene": index,
                "source": "stock",
                "clips": [
                    {
                        "pixabay_id": 20000 + index,
                        "keyword": "gym workout",
                        "tags": "chop vegetables food cooking kitchen meal",
                        "page": f"https://example.invalid/video/{index}",
                    }
                ],
            }
            for index in range(1, 5)
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = os.path.join(tmp, "output")
            os.makedirs(output_dir)
            with open(os.path.join(output_dir, "script.json"), "w", encoding="utf-8") as f:
                json.dump({"title": "Hormone facts", "scenes": scenes}, f)
            with open(os.path.join(output_dir, "clips_info.json"), "w", encoding="utf-8") as f:
                json.dump(clip_info, f)

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                captured = io.StringIO()
                with redirect_stdout(captured):
                    with self.assertRaises(SystemExit) as raised:
                        quality_check_main()
                self.assertEqual(raised.exception.code, 1)
                self.assertIn("blocking upload", captured.getvalue())
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
