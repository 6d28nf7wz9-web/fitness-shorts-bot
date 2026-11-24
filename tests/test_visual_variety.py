"""Regression tests for category-specific FitFuel science visuals."""
import unittest
from visual_engine import CATEGORIES, build_visual_panel, classify_scene, visual_css


class VisualVarietyTests(unittest.TestCase):
    def test_each_category_has_a_distinct_visual_composition(self):
        scenes = {
            "muscle": {"narration": "Muscle hypertrophy and recovery after strength training"},
            "nutrition": {"narration": "Food digestion and dietary fiber in a meal"},
            "heart": {"narration": "Heart rate and blood circulation deliver oxygen"},
            "fat_loss": {"narration": "A calorie deficit changes fat loss and energy balance"},
            "hydration": {"narration": "Water and electrolytes improve hydration"},
            "exercise": {"narration": "A squat exercise changes joint range and movement"},
            "hormones": {"narration": "Insulin and cortisol are hormone signals"},
        }
        panels = {}
        for expected, scene in scenes.items():
            category, panel = build_visual_panel(scene)
            self.assertEqual(category, expected)
            panels[category] = panel
        self.assertEqual(len(set(panels.values())), len(panels))
        for marker, category in [
            ("heart-shape", "heart"), ("plate-outer", "nutrition"),
            ("molecule-bonds", "hormones"), ("fiber-lines", "muscle"),
            ("water-drop", "hydration"), ("limb-line", "exercise"),
            ("balance-pan", "fat_loss"),
        ]:
            self.assertIn(marker, panels[category])

    def test_svg_labels_are_expanded_and_not_template_placeholders(self):
        _, panel = build_visual_panel({"narration": "Water and hydration improve performance"})
        self.assertNotIn("$", panel)
        self.assertIn("WATER", panel)
        self.assertIn("ELECTROLYTES", panel)
        self.assertIn("PERFORMANCE", panel)

    def test_explicit_visual_type_overrides_ambiguous_narration(self):
        self.assertEqual(classify_scene({
            "visual_type": "heart", "narration": "A workout improves performance"
        }), "heart")

    def test_unknown_topic_uses_general_timeline(self):
        category, panel = build_visual_panel({"narration": "A useful daily habit"})
        self.assertEqual(category, "general")
        self.assertIn("timeline-node", panel)

    def test_each_category_has_dedicated_css_direction(self):
        css = visual_css()
        for category in CATEGORIES:
            self.assertIn(f".panel-{category}", css)


if __name__ == "__main__":
    unittest.main()
