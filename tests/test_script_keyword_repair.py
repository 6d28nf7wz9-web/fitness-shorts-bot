"""Regression tests: never replace unfilmable scene keywords with generic stock searches."""

import unittest

from gen_script import repair_keywords


class ScriptKeywordRepairTests(unittest.TestCase):
    def test_keeps_specific_authored_keywords(self):
        data = {"scenes": [{"narration": "Protein supports muscle repair.", "keyword": "protein shake preparation | chicken breast meal"}]}
        repaired = repair_keywords(data)
        self.assertEqual(
            repaired["scenes"][0]["keyword"],
            "protein shake preparation | chicken breast meal",
        )

    def test_does_not_inject_generic_training_or_food_keywords(self):
        data = {"scenes": [{"narration": "Hormone signals regulate testosterone.", "keyword": ""}]}
        repaired = repair_keywords(data)
        self.assertEqual(repaired["scenes"][0]["keyword"], "")

    def test_filters_unrelated_keywords_without_generic_replacement(self):
        data = {"scenes": [{"narration": "Insulin is a hormone signal.", "keyword": "ancient castle | night sky"}]}
        repaired = repair_keywords(data)
        self.assertEqual(repaired["scenes"][0]["keyword"], "")


if __name__ == "__main__":
    unittest.main()
