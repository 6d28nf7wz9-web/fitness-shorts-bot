"""Regression tests for fail-closed stock keyword selection."""

import unittest

from clips_fast import _ordered_keywords


class FastClipKeywordTests(unittest.TestCase):
    def test_preserves_authored_keyword_priority(self):
        scene = {"keyword": "protein meal prep|chicken rice bowl|healthy lunch"}
        self.assertEqual(
            _ordered_keywords(scene),
            ["protein meal prep", "chicken rice bowl", "healthy lunch"],
        )

    def test_rejects_missing_keywords_instead_of_using_generic_footage(self):
        for scene in ({}, {"keyword": ""}, {"keyword": " |  | "}):
            with self.subTest(scene=scene):
                with self.assertRaisesRegex(RuntimeError, "generic"):
                    _ordered_keywords(scene)


if __name__ == "__main__":
    unittest.main()
