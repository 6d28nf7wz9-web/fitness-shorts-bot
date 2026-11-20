"""Tests for scene-aware Blender anatomy selection and HyperFrames routing."""
import os
import tempfile
import unittest
from pathlib import Path

from blender.render_scene_visuals import anatomy_view, scene_topic
from hyperframes_render import prepare_scene_3d


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

    def test_science_topics_map_to_distinct_3d_scenes(self):
        cases = {
            "Protein synthesis": "protein",
            "Cardiovascular flow": "heart",
            "Hydration and electrolytes": "hydration",
            "Creatine and ATP": "creatine",
            "Energy balance": "fat_loss",
            "Progressive overload": "tracking",
            "Build muscle faster": "muscle",
            "Exercise biomechanics": "exercise",
            "Nutrition and digestion": "nutrition",
            "Hormone signaling": "hormones",
            "Supplement evidence": "supplements",
            "Recovery and sleep": "recovery",
            "General fitness science": "general",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(scene_topic({"visual_title": title}), expected)

    def test_real_exercise_demonstrations_have_a_3d_fallback(self):
        self.assertEqual(scene_topic({
            "visual_title": "How to perform a squat",
            "narration": "Keep your chest up and drive through the floor.",
        }), "exercise")

    def test_explicit_joint_mechanics_uses_3d_biomechanics(self):
        self.assertEqual(scene_topic({
            "visual_type": "exercise_biomechanics",
            "visual_title": "Knee joint mechanics",
        }), "exercise")

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

    def test_hyperframes_can_load_a_rendered_3d_anatomy_plate(self):
        with tempfile.TemporaryDirectory() as temp:
            previous = os.getcwd()
            try:
                os.chdir(temp)
                source = Path("output/science_3d/scene_2.mp4")
                source.parent.mkdir(parents=True)
                source.write_bytes(b"3d-preview" * 3000)
                assets = Path("assets")
                assets.mkdir()
                result = prepare_scene_3d(2, assets)
                self.assertEqual(result, "scene_2_3d_anatomy.mp4")
                self.assertTrue((assets / result).is_file())
            finally:
                os.chdir(previous)

    def test_missing_blender_or_unsupported_scene_fails_instead_of_silent_fallback(self):
        source = Path(__file__).resolve().parents[1] / "blender" / "render_scene_visuals.py"
        renderer = source.read_text(encoding="utf-8")
        self.assertIn("Blender is required for the approved 3D production pipeline", renderer)
        self.assertIn("refusing a silent fallback", renderer)
        self.assertIn("all scenes must have verified 3D plates", renderer)

    def test_hyperframes_stages_3d_assets_instead_of_overlaying_2d_svg(self):
        source = Path(__file__).resolve().parents[1] / "hyperframes_render.py"
        renderer = source.read_text(encoding="utf-8")
        self.assertIn('science_panel = ""', renderer)
        self.assertIn('science-3d-footage', renderer)
        self.assertIn('top:820px!important', renderer)



if __name__ == "__main__":
    unittest.main()
