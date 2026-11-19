"""Tests for scene-aware Blender anatomy selection and HyperFrames routing."""
import unittest

from blender.render_scene_visuals import anatomy_view


class Scene3DAssetTests(unittest.TestCase):
    def test_explicit_anatomy_visual_type_selects_front_view(self):
        self.assertEqual(anatomy_view({
            "visual_type": "muscle_anatomy",
            "visual_title": "Major muscle groups",
        }), "anterior")

    def test_named_back_muscle_groups_select_posterior_view(self):
        self.assertEqual(anatomy_view({
            "visual_title": "Latissimus and trapezius",
            "narration": "The lats and traps stabilize the back.",
        }), "posterior")

    def test_front_muscle_groups_select_anterior_view(self):
        self.assertEqual(anatomy_view({
            "visual_title": "Biceps and pectorals",
            "narration": "The deltoids assist the movement.",
        }), "anterior")

    def test_general_muscle_growth_is_not_misclassified_as_anatomy(self):
        self.assertIsNone(anatomy_view({
            "visual_title": "Build muscle faster",
            "narration": "Progressive overload supports long-term muscle growth.",
        }))

    def test_protein_synthesis_keeps_its_own_science_visual(self):
        self.assertIsNone(anatomy_view({
            "visual_title": "Protein synthesis",
            "narration": "Amino acids support muscle protein synthesis.",
        }))


if __name__ == "__main__":
    unittest.main()
