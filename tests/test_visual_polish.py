import unittest

from visual_engine import build_visual_panel, visual_css
from assemble import build_captions


class VisualPolishTests(unittest.TestCase):
    def test_science_cards_are_rectangular_and_scene_varied(self):
        _, first = build_visual_panel({"narration": "Muscle growth"}, 1)
        _, second = build_visual_panel({"narration": "Muscle recovery"}, 2)
        _, third = build_visual_panel({"narration": "Muscle strength"}, 3)
        self.assertIn('data-variant="0"', first)
        self.assertIn('data-variant="1"', second)
        self.assertIn('data-variant="2"', third)
        css = visual_css()
        self.assertIn("border-radius:24px!important", css)
        self.assertIn("overflow:hidden;contain:strict", css)

    def test_word_karaoke_tags_are_valid_ass_commands(self):
        script = {"scenes": [{"narration": "Build muscle with enough protein"}]}
        captions = build_captions(script, [{"seconds": 3.0}])
        self.assertIn("{\\k", captions)
        self.assertNotIn("{\\\\k", captions)

    def test_all_diagram_text_is_clipped_inside_card(self):
        css = visual_css()
        self.assertIn(".science-panel .science-svg text", css)
        self.assertIn("paint-order:stroke", css)


if __name__ == "__main__":
    unittest.main()
