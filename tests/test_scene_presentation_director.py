import unittest

from scene_presentation_director import direct_scenes
from visual_engine import build_visual_panel


class ScenePresentationDirectorTests(unittest.TestCase):
    def test_hook_and_payoff_have_dedicated_roles(self):
        scenes = direct_scenes([
            {"narration": "Stop making this recovery mistake"},
            {"narration": "Muscles adapt during rest"},
            {"narration": "So what should you change? Follow FitFuel"},
        ])
        self.assertEqual(scenes[0]["presentation_style"], "hook")
        self.assertEqual(scenes[0]["scene_role"], "hook")
        self.assertEqual(scenes[-1]["presentation_style"], "payoff")
        self.assertEqual(scenes[-1]["motion_cue"], "resolve_hold")

    def test_middle_scenes_avoid_adjacent_repetition(self):
        scenes = direct_scenes([
            {"narration": "Hook"},
            {"visual_category": "muscle", "narration": "Muscle growth needs recovery"},
            {"visual_category": "muscle", "narration": "Muscle strength improves over time"},
            {"visual_category": "muscle", "narration": "Muscle adaptation needs protein"},
            {"narration": "Question? Follow FitFuel"},
        ])
        styles = [x["presentation_style"] for x in scenes]
        self.assertTrue(all(a != b for a, b in zip(styles[1:-2], styles[2:-1])))

    def test_intent_overrides_default_category(self):
        scenes = direct_scenes([
            {"narration": "Hook"},
            {"visual_category": "muscle", "narration": "But recovery matters more than volume"},
            {"narration": "Payoff? Follow FitFuel"},
        ])
        self.assertEqual(scenes[1]["presentation_style"], "comparison")
        self.assertEqual(scenes[1]["motion_cue"], "split_reveal")

    def test_visual_panel_exposes_safe_presentation_metadata(self):
        scene = direct_scenes([
            {"narration": "Hook"},
            {"visual_category": "hydration", "narration": "Water and electrolytes"},
            {"narration": "Payoff? Follow FitFuel"},
        ])[1]
        _, panel = build_visual_panel(scene, 2)
        self.assertIn('data-motion="count_up"', panel)
        self.assertIn("presentation-stat_card", panel)

    def test_explicit_general_hook_and_payoff_keep_general_visuals(self):
        scenes = direct_scenes([
            {"visual_category": "general", "narration": "Muscle recovery mistake"},
            {"visual_category": "general", "narration": "Muscle recovery solution"},
        ])
        self.assertEqual(build_visual_panel(scenes[0])[0], "general")
        self.assertEqual(build_visual_panel(scenes[1])[0], "general")

    def test_every_motion_cue_has_a_rendered_css_treatment(self):
        from visual_engine import visual_css
        css = visual_css()
        for cue in ("snap_reveal", "draw_on", "count_up", "split_reveal",
                    "step_build", "gesture_emphasis", "match_cut", "resolve_hold"):
            self.assertIn('[data-motion="' + cue + '"]', css)

    def test_empty_scene_list_is_safe(self):
        self.assertEqual(direct_scenes([]), [])


if __name__ == "__main__":
    unittest.main()
