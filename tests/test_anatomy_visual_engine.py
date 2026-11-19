import unittest

from visual_engine import build_visual_panel, classify_scene, visual_css


class AnatomyVisualEngineTests(unittest.TestCase):
    def test_explicit_muscle_anatomy_uses_anatomy_category(self):
        scene = {
            "visual_type": "muscle_anatomy",
            "visual_title": "How your muscles work",
            "narration": "The chest and shoulders contract during this movement.",
        }
        self.assertEqual(classify_scene(scene), "anatomy")

    def test_anatomy_panel_contains_distinct_muscle_groups_and_labels(self):
        category, panel = build_visual_panel(
            {"visual_type": "muscle_anatomy", "visual_title": "Muscle anatomy"},
            index=2,
        )
        self.assertEqual(category, "anatomy")
        for term in ("anatomy-pec", "anatomy-delt", "anatomy-bicep",
                     "anatomy-abs", "anatomy-oblique", "anatomy-quad",
                     "PECTORAL", "DELTOID", "BICEPS", "QUADRICEPS"):
            self.assertIn(term, panel)

    def test_category_specific_css_is_connected_to_svg_class(self):
        category, panel = build_visual_panel(
            {"visual_type": "muscle_anatomy", "visual_title": "Muscle anatomy"}
        )
        self.assertIn('class="science-svg science-anatomy"', panel)
        self.assertIn(".science-anatomy .anatomy-pec", visual_css())


if __name__ == "__main__":
    unittest.main()
