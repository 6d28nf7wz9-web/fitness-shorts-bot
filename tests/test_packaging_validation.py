"""Tests for FitFuel upload title and description packaging checks."""
import unittest
from gen_script import validate_packaging


class PackagingValidationTests(unittest.TestCase):
    def test_accepts_relevant_concise_metadata(self):
        self.assertIsNone(validate_packaging(
            "Why Daily Steps Matter for Fat Loss",
            "Daily steps and fat loss",
            "Learn why everyday movement matters beyond your gym session. Follow FitFuel for practical fitness science."
        ))

    def test_rejects_title_unrelated_to_topic(self):
        self.assertIn("main topic keyword", validate_packaging(
            "The Secret Nobody Tells You", "Protein and hunger",
            "Learn how protein can help you feel full for longer."
        ))

    def test_rejects_hashtags_in_title_and_thin_description(self):
        self.assertIn("hashtags", validate_packaging(
            "Protein Tips #Shorts", "Protein tips",
            "A useful description for viewers."
        ))
        self.assertIn("too short", validate_packaging(
            "Protein Tips for Better Meals", "Protein tips",
            "Protein tips."
        ))


if __name__ == "__main__":
    unittest.main()
