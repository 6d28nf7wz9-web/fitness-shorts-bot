import unittest

from production_motion_engine import (
    emphasize_words,
    kinetic_html,
    motion_engine_css,
    presenter_html,
    presenter_gesture,
    presenter_expression,
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

    def test_protein_and_tracking_emphasis_use_relevant_terms(self):
        protein_words = {item["word"].lower() for item in emphasize_words(
            "Protein breaks into amino acids and supports muscle growth", "protein", 4.0
        )}
        tracking_words = {item["word"].lower() for item in emphasize_words(
            "Increase load when reps are controlled and track progression", "tracking", 4.0
        )}
        self.assertTrue({"protein", "amino", "muscle"}.issubset(protein_words))
        self.assertTrue({"load", "reps", "progression"}.issubset(tracking_words))

    def test_kinetic_markup_escapes_untrusted_text(self):
        markup = kinetic_html("Muscle <growth>", "muscle", 2.0)
        self.assertIn("kinetic-word", markup)
        self.assertNotIn("<growth>", markup)

    def test_kinetic_words_use_absolute_composition_time(self):
        markup = kinetic_html(
            "Protein supports muscle growth", "muscle", 2.0,
            scene_start=6.25,
        )
        self.assertIn("--word-delay:6.250s", markup)
        self.assertIn("--word-start:6.250s", markup)

    def test_presenter_has_reserved_character_and_gesture(self):
        markup = presenter_html()
        self.assertIn('class="presenter"', markup)
        self.assertIn("data-gesture=", markup)
        self.assertIn("presenter-arm", markup)
        self.assertIn("viewBox", markup)

    def test_presenter_gesture_tracks_teaching_intent(self):
        self.assertEqual(presenter_gesture("Look at this target", "muscle"), "point")
        self.assertEqual(presenter_gesture("Compare these two methods", "general"), "compare")
        self.assertEqual(presenter_gesture("Lower the weight and extend the hip", "exercise"), "demonstrate")
        self.assertEqual(presenter_gesture("Remember why this matters", "general"), "explain")

    def test_presenter_expression_tracks_emotional_context(self):
        self.assertEqual(presenter_expression("This surprising myth is unexpected", "general"), "surprise")
        self.assertEqual(presenter_expression("Avoid this dangerous mistake", "general"), "concern")
        self.assertEqual(presenter_expression("Great progress and stronger results", "general"), "smile")
        self.assertEqual(presenter_expression("Control your form and technique", "exercise"), "focused")

    def test_presenter_html_uses_safe_expression_and_gesture_states(self):
        markup = presenter_html("compare", "surprise")
        self.assertIn('data-gesture="compare"', markup)
        self.assertIn('data-expression="surprise"', markup)
        self.assertIn('class="presenter-mouth mouth-surprise"', markup)
        self.assertIn("@keyframes ff-presenter-compare-left", motion_engine_css() + __import__("production_motion_engine").presenter_css())

    def test_motion_css_has_separate_word_and_presenter_animation(self):
        css = motion_engine_css()
        self.assertIn("@keyframes ff-word-hit", css)
        self.assertIn("@keyframes ff-presenter-talk", __import__("production_motion_engine").presenter_css())

    def test_sound_cues_are_sparse_and_scene_relative(self):
        cues = sound_cue_events("Protein supports muscle growth", "muscle", 3.0, scene_start=5.0)
        self.assertTrue(any(cue["kind"] == "scene_whoosh" and cue["time"] == 5.0 for cue in cues))
        self.assertTrue(any(cue["kind"] == "science_muscle" and cue["time"] == 5.18 for cue in cues))
        self.assertTrue(all(5.0 <= cue["time"] < 8.0 for cue in cues))
        self.assertLessEqual(sum(cue["kind"] == "soft_tick" for cue in cues), 4)

    def test_sound_reveal_is_specific_to_science_category(self):
        cues = sound_cue_events("Water restores fluid balance", "hydration", 2.0)
        self.assertIn("science_hydration", {cue["kind"] for cue in cues})
        self.assertEqual(cues[0]["kind"], "scene_whoosh")


    def test_presenter_gesture_matches_protein_and_progression_diagrams(self):
        self.assertEqual(presenter_gesture("Protein supports muscle repair", "protein"), "explain")
        self.assertEqual(presenter_gesture("Increase load when reps are controlled", "tracking"), "point")
        self.assertEqual(presenter_gesture("Supplements support but do not replace training", "supplements"), "explain")

if __name__ == "__main__":
    unittest.main()
