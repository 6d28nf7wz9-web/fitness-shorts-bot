import unittest

from visual_engine import build_visual_panel, visual_css, scene_archetype
from assemble import build_captions


class VisualPolishTests(unittest.TestCase):
    def test_science_cards_are_rectangular_and_scene_varied(self):
        _, first = build_visual_panel({"narration": "Muscle growth"}, 1)
        _, second = build_visual_panel({"narration": "Muscle recovery"}, 2)
        _, third = build_visual_panel({"narration": "Muscle strength"}, 3)
        self.assertIn('data-variant="0"', first)
        self.assertIn('data-variant="1"', second)
        self.assertIn('data-variant="2"', third)
        css = visual_css()
        self.assertIn("border-radius:24px!important", css)
        self.assertIn("overflow:hidden;contain:strict", css)

    def test_every_science_category_uses_the_same_rectangular_safe_frame(self):
        for category in ("muscle", "nutrition", "heart", "fat_loss", "hydration", "exercise", "hormones", "general"):
            _, panel = build_visual_panel({"visual_type": category}, 1)
            self.assertIn('class="science-panel', panel)
            self.assertIn('preserveAspectRatio="xMidYMid meet"', panel)
        css = visual_css()
        self.assertIn("border-radius:24px!important;overflow:hidden!important", css)
        self.assertIn("clip-path:inset(0 round 24px)", css)
        self.assertIn("max-width:90%;max-height:400px", css)

    def test_long_science_labels_are_scaled_not_truncated(self):
        category, panel = build_visual_panel({
            "visual_type": "muscle",
            "visual_title": "A scientific label that is deliberately much longer than the safe frame"
        }, 1)
        self.assertEqual(category, "muscle")
        self.assertIn("PROTEIN", panel)
        # SVG label text is preserved and constrained to its viewBox width.
        self.assertIn('textLength="', panel)
        self.assertIn('lengthAdjust="spacingAndGlyphs"', panel)

    def test_scene_specific_visual_models_change_with_the_claim(self):
        a = {"narration": "Protein synthesis creates new muscle proteins"}
        b = {"narration": "Progressive overload means lifting heavier loads"}
        c = {"narration": "Sleep and rest support muscle recovery"}
        self.assertEqual(scene_archetype(a, "muscle"), "synthesis")
        self.assertEqual(scene_archetype(b, "muscle"), "overload")
        self.assertEqual(scene_archetype(c, "muscle"), "recovery")
        _, pa = build_visual_panel(a, 1)
        _, pb = build_visual_panel(b, 2)
        self.assertIn('data-archetype="synthesis"', pa)
        self.assertNotEqual(pa, pb)

    def test_nutrition_visual_models_match_the_claim(self):
        self.assertEqual(scene_archetype({"narration": "Protein absorption"}, "nutrition"), "protein_path")
        self.assertEqual(scene_archetype({"narration": "Meal timing before training"}, "nutrition"), "timing")

    def test_word_karaoke_tags_are_valid_ass_commands(self):
        script = {"scenes": [{"narration": "Build muscle with enough protein"}]}
        captions = build_captions(script, [{"seconds": 3.0}])
        self.assertIn("{\\k", captions)
        self.assertNotIn("{\\\\k", captions)

    def test_all_diagram_text_is_clipped_inside_card(self):
        css = visual_css()
        self.assertIn(".science-panel .science-svg text", css)
        self.assertIn("paint-order:stroke", css)


if __name__ == "__main__":
    unittest.main()
