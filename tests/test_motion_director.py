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
        self.assertIn("@keyframes ff-camera-push", css)
        self.assertIn("@keyframes ff-camera-pull", css)

    def test_scenes_alternate_layout_and_camera_movement(self):
        plans = [plan_scene_motion({}, i, 3.0, "muscle") for i in range(1, 7)]
        self.assertEqual(plans[0]["camera"], "push")
        self.assertEqual(plans[1]["camera"], "drift")
        self.assertEqual(plans[2]["camera"], "pull")
        self.assertEqual(len({p["layout"] for p in plans}), 2)
        self.assertTrue(all("layout-" in p["class_name"] for p in plans))

    def test_scenes_cycle_through_five_distinct_motion_variants(self):
        plans = [plan_scene_motion({}, i, 3.0, "muscle") for i in range(1, 6)]
        self.assertEqual([p["variant"] for p in plans], ["rise", "scale", "slide", "focus", "snap"])
        css = motion_css()
        for name in ("rise", "scale", "slide", "focus", "snap"):
            self.assertIn("variant-" + name, css)

    def test_support_scenes_rotate_through_distinct_transitions(self):
        plans = [plan_scene_motion({}, i, 3.0, "muscle") for i in range(2, 6)]
        self.assertEqual([p["transition"] for p in plans], ["wipe", "slide-up", "zoom", "reveal"])
        self.assertTrue(all("transition-" in p["class_name"] for p in plans))
        css = motion_css()
        for name in ("slide-up", "wipe", "zoom", "reveal"):
            self.assertIn(f"ff-transition-{name}", css)


if __name__ == "__main__":
    unittest.main()
