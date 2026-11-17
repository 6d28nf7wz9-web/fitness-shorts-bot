import unittest

from visual_engine import visual_css


class ContinuousVisualMotionContractTests(unittest.TestCase):
    def test_each_science_category_has_continuous_motion_tracks(self):
        css = visual_css()
        expected = (
            "fiber-pulse", "flow", "heartbeat", "float", "node-pulse",
        )
        for keyframe in expected:
            self.assertIn("@keyframes " + keyframe, css)
        self.assertIn("animation:fiber-pulse", css)
        self.assertIn("animation:heartbeat", css)
        self.assertIn("animation:flow", css)

    def test_category_specific_secondary_motion_is_present_in_renderer(self):
        with open("hyperframes_render.py", encoding="utf-8") as f:
            renderer = f.read()
        for category, marker in (
            ("muscle", "ff-fiber-travel"),
            ("nutrition", "ff-fuel-arrive"),
            ("heart", "ff-heart-contract"),
            ("fat_loss", "ff-energy-balance"),
            ("hydration", "ff-ion-orbit"),
            ("exercise", "ff-joint-rotate"),
            ("hormones", "ff-signal-pass"),
            ("creatine", "ff-atp-charge"),
            ("supplements", "ff-dose-rock"),
            ("general", "ff-process-sequence"),
        ):
            self.assertIn(".science-" + category, renderer)
            self.assertIn(marker, renderer)

    def test_presenter_is_scene_driven_and_has_reduced_motion_fallback(self):
        with open("avatar.py", encoding="utf-8") as f:
            avatar = f.read()
        with open("avatar_motion.py", encoding="utf-8") as f:
            cues = f.read()
        with open("hyperframes_render.py", encoding="utf-8") as f:
            renderer = f.read()
        self.assertIn("scene_motion_cues(layout)", avatar)
        self.assertIn("ffmpeg_motion_expression(cues", avatar)
        self.assertIn("presenter_gesture(", cues)
        self.assertIn("presenter_expression(", cues)
        self.assertIn("apply_expression_mouth_states", avatar)
        self.assertIn("ff-diagram-label-reveal", renderer)
        self.assertIn("prefers-reduced-motion: reduce", renderer)



if __name__ == "__main__":
    unittest.main()
