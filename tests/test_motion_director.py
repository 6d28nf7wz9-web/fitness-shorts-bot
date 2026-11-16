import unittest

from motion_director import motion_css, plan_scene_motion


class MotionDirectorTests(unittest.TestCase):
    def test_first_scene_is_immediate_hook(self):
        plan = plan_scene_motion({}, 1, 2.0, "muscle")
        self.assertEqual(plan["role"], "hook")
        self.assertIn("motion-hook", plan["class_name"])

    def test_last_scene_is_payoff(self):
        plan = plan_scene_motion({}, 5, 3.0, "heart", is_last=True)
        self.assertEqual(plan["role"], "payoff")
        self.assertEqual(plan["focus"], "diagram")

    def test_long_scenes_receive_extra_attention_reset(self):
        short = plan_scene_motion({}, 2, 3.0, "exercise")
        long = plan_scene_motion({}, 2, 5.0, "exercise")
        self.assertEqual(short["pace"], "standard")
        self.assertEqual(long["pace"], "long")
        self.assertIn("motion-long", long["class_name"])

    def test_generic_scene_focuses_headline(self):
        plan = plan_scene_motion({}, 2, 2.0, "general")
        self.assertEqual(plan["focus"], "headline")

    def test_motion_css_uses_eased_frame_visual_language(self):
        css = motion_css()
        self.assertIn("cubic-bezier(.16,1,.3,1)", css)
        self.assertIn("@keyframes ff-panel-enter", css)
        self.assertIn("@keyframes ff-note-pulse", css)


if __name__ == "__main__":
    unittest.main()
