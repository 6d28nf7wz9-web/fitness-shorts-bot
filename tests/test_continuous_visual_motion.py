import unittest

from production_motion_engine import presenter_css
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
        with open("hyperframes_render.py", encoding="utf-8") as f:
            renderer = f.read()
        self.assertIn("presenter_gesture(", renderer)
        self.assertIn("presenter_expression(", renderer)
        self.assertIn("css += presenter_css()", renderer)
        self.assertIn("ff-diagram-label-reveal", renderer)
        self.assertIn("prefers-reduced-motion: reduce", renderer)
        css = presenter_css()
        for gesture in ("point", "explain", "compare", "demonstrate"):
            self.assertIn('data-gesture="' + gesture + '"', css)
        for expression in ("smile", "surprise", "concern", "focused"):
            self.assertIn('data-expression="' + expression + '"', css)


if __name__ == "__main__":
    unittest.main()
