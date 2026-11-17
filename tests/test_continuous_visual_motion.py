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
        self.assertIn("SHORT_AVATAR_FRAME = 220", avatar)
        self.assertIn("pad={SHORT_AVATAR_FRAME}:{SHORT_AVATAR_FRAME}", avatar)
        self.assertIn("overlay=x={SHORT_AVATAR_X}", avatar)
        self.assertIn("overlay=x={SHORT_AVATAR_X}", avatar)
        self.assertIn("ff-diagram-label-reveal", renderer)
        self.assertIn("prefers-reduced-motion: reduce", renderer)

    def test_recovery_topic_has_its_own_visual_metaphor(self):
        from visual_engine import build_visual_panel, classify_scene
        recovery = {"visual_title": "Why Recovery Days Matter", "narration": "Rest helps muscle recovery."}
        growth = {"visual_title": "Build Muscle Faster", "narration": "Mechanical tension supports muscle growth."}
        self.assertEqual(classify_scene(recovery), "recovery")
        self.assertEqual(classify_scene(growth), "muscle")
        category, panel = build_visual_panel(recovery, 1)
        self.assertEqual(category, "recovery")
        self.assertIn("recovery-clock", panel)
        self.assertNotIn("fiber-group", panel)



if __name__ == "__main__":
    unittest.main()
