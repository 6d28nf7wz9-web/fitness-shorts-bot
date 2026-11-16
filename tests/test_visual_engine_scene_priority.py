import unittest

from visual_engine import classify_scene, build_visual_panel


class VisualEngineScenePriorityTests(unittest.TestCase):
    def test_weight_loading_scene_is_not_overridden_by_creatine_narration(self):
        scene = {
            "visual_title": "Weight Loading",
            "visual_subtitle": "Add Weight Each Rep",
            "narration": "Creatine can support performance, but progressive overload matters.",
        }
        self.assertEqual(classify_scene(scene), "exercise")

    def test_creatine_scene_uses_supplement_diagram(self):
        scene = {
            "visual_title": "Creatine Effect",
            "visual_subtitle": "Supports Training Output",
            "narration": "Creatine supports repeated high intensity efforts.",
        }
        category, panel = build_visual_panel(scene, 2)
        self.assertEqual(category, "supplements")
        self.assertIn("SUPPLEMENT EVIDENCE", panel)

    def test_muscle_gain_scene_uses_muscle_diagram(self):
        scene = {
            "visual_title": "Measured Gain",
            "visual_subtitle": "Tiny Muscle Gain",
            "narration": "Creatine is not a shortcut to muscle growth.",
        }
        self.assertEqual(classify_scene(scene), "muscle")


if __name__ == "__main__":
    unittest.main()
