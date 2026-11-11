import unittest
from hyperframes_render import fit_text, wrap_words, scene_clip_path, USE_3D_PREVIEW


class HyperFramesTextLayoutTests(unittest.TestCase):
    def test_title_wraps_inside_safe_line_width(self):
        lines = wrap_words("PROGRESSIVE OVERLOAD BUILDS STRONGER MUSCLES", 20)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(len(line) <= 20 for line in lines))

    def test_fit_text_keeps_all_words_and_returns_bounded_font(self):
        source = "TRAIN SMARTER RECOVER BETTER AND BUILD MUSCLE"
        lines, size = fit_text(source, 2, 30, 43, 30)
        self.assertEqual(" ".join(lines), source)
        self.assertGreaterEqual(size, 30)
        self.assertLessEqual(size, 43)

    def test_long_title_is_bounded_to_safe_box(self):
        lines, size = fit_text(" ".join(["ANATOMY"] * 40), 3, 20, 78, 48)
        self.assertLessEqual(len(lines), 4)
        self.assertTrue(all(len(line) <= 32 for line in lines))
        self.assertGreaterEqual(size, 48)
        self.assertLessEqual(size, 78)
        self.assertTrue(lines[-1].endswith("…"))

    def test_long_subtitle_is_bounded_to_safe_box(self):
        lines, size = fit_text(" ".join(["TRAINING"] * 30), 2, 30, 43, 30)
        self.assertLessEqual(len(lines), 3)
        self.assertTrue(all(len(line) <= 43 for line in lines))
        self.assertGreaterEqual(size, 30)
        self.assertLessEqual(size, 43)
        self.assertTrue(lines[-1].endswith("…"))

    def test_empty_subtitle_has_safe_fallback(self):
        self.assertEqual(wrap_words("", 30), [""])

    def test_normal_production_uses_pixabay_clip_path_by_default(self):
        self.assertFalse(USE_3D_PREVIEW)
        self.assertEqual(str(scene_clip_path(2)), "output/clips/scene_2.mp4")

    def test_daily_workflow_does_not_enable_experimental_blender_preview(self):
        with open(".github/workflows/daily.yml", encoding="utf-8") as f:
            workflow = f.read()
        self.assertNotIn("FITFUEL_3D_PREVIEW", workflow)

    def test_daily_workflow_installs_renderer_and_sets_public_mode(self):
        with open(".github/workflows/daily.yml", encoding="utf-8") as f:
            workflow = f.read()
        self.assertIn('node-version: "22"', workflow)
        self.assertIn("hyperframes@0.9.31", workflow)
        self.assertIn("UPLOAD_PRIVACY: public", workflow)
        self.assertIn('HYPERFRAMES_RENDER: "1"', workflow)
        self.assertNotIn(r"public\n", workflow)


if __name__ == "__main__":
    unittest.main()
