import unittest

from production_motion_engine import (
    emphasize_words,
    kinetic_html,
    motion_engine_css,
    presenter_html,
    sound_cue_events,
    word_timeline,
)


class ProductionMotionEngineTests(unittest.TestCase):
    def test_uses_real_word_boundaries_when_complete(self):
        narration = "Protein supports muscle growth"
        timings = [
            {"text": "Protein", "start": 0.0, "end": 0.35},
            {"text": "supports", "start": 0.36, "end": 0.72},
            {"text": "muscle", "start": 0.73, "end": 1.0},
            {"text": "growth", "start": 1.01, "end": 1.4},
        ]
        timeline = word_timeline(narration, 2.0, timings)
        self.assertEqual(timeline[2]["start"], 0.73)
        self.assertEqual(timeline[3]["end"], 1.4)

    def test_falls_back_to_duration_weighting_for_missing_alignment(self):
        timeline = word_timeline("Build stronger muscle", 3.0)
        self.assertEqual(timeline[0]["start"], 0.0)
        self.assertAlmostEqual(timeline[-1]["end"], 3.0)
        self.assertEqual(len(timeline), 3)

    def test_emphasis_is_topic_specific_and_bounded(self):
        items = emphasize_words(
            "Protein supports muscle growth and recovery", "muscle", 4.0
        )
        self.assertTrue({"Protein", "muscle", "growth", "recovery"}.issubset(
            {item["word"] for item in items}
        ))
        self.assertLessEqual(len(items), 7)

    def test_kinetic_markup_escapes_untrusted_text(self):
        markup = kinetic_html("Muscle <growth>", "muscle", 2.0)
        self.assertIn("kinetic-word", markup)
        self.assertNotIn("<growth>", markup)

    def test_presenter_has_reserved_character_and_gesture(self):
        markup = presenter_html()
        self.assertIn('class="presenter"', markup)
        self.assertIn("presenter-arm", markup)
        self.assertIn("viewBox", markup)

    def test_motion_css_has_separate_word_and_presenter_animation(self):
        css = motion_engine_css()
        self.assertIn("@keyframes ff-word-hit", css)
        self.assertIn("@keyframes ff-presenter-gesture", css)

    def test_sound_cues_are_sparse_and_scene_relative(self):
        cues = sound_cue_events("Protein supports muscle growth", "muscle", 3.0, scene_start=5.0)
        self.assertTrue(any(cue["kind"] == "scene_whoosh" and cue["time"] == 5.0 for cue in cues))
        self.assertTrue(all(5.0 <= cue["time"] < 8.0 for cue in cues))


if __name__ == "__main__":
    unittest.main()
