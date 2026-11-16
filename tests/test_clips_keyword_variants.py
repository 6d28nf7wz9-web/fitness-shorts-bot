import unittest
from unittest.mock import patch

from clips import keyword_variants


class SceneKeywordVariantTests(unittest.TestCase):
    def test_specific_scene_targets_do_not_get_generic_fallbacks(self):
        variants = keyword_variants(
            "person loading barbell plates|gym weight loading close-up",
            "Can a supplement replace progressive overload?",
        )
        lowered = {item.lower() for item in variants}
        self.assertIn("person loading barbell plates", lowered)
        self.assertIn("gym weight loading close-up", lowered)
        self.assertNotIn("healthy food", lowered)
        self.assertNotIn("cooking healthy meal", lowered)
        self.assertNotIn("gym workout", lowered)
        self.assertNotIn("weight training", lowered)

    def test_category_fallbacks_remain_when_no_specific_target_exists(self):
        with patch("clips.keyword_is_relevant", return_value=False):
            variants = keyword_variants(
                "unsearchable phrase", "another unsearchable phrase"
            )
        self.assertTrue(variants)
        self.assertIn("gym workout", {item.lower() for item in variants})


if __name__ == "__main__":
    unittest.main()
