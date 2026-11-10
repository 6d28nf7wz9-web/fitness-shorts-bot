import unittest
from hyperframes_render import fit_text, wrap_words


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

    def test_empty_subtitle_has_safe_fallback(self):
        self.assertEqual(wrap_words("", 30), [""])


if __name__ == "__main__":
    unittest.main()
