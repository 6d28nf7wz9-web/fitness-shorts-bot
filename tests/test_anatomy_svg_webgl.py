from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class AnatomySvgWebglPrototypeTests(unittest.TestCase):
 def test_prototype_is_self_contained_svg_and_webgl(self):
  html=(ROOT/"prototypes/anatomy_svg_webgl/index.html").read_text()
  self.assertIn("<svg",html); self.assertIn("<canvas",html); self.assertIn("getContext('webgl'",html)
  self.assertNotIn("https://",html); self.assertIn("aria-label=",html)
if __name__=="__main__": unittest.main()
