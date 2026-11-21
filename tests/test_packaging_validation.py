"""Tests for FitFuel upload title and description packaging checks."""
import unittest
from gen_script import validate_packaging, ensure_final_cta, validate_scientific_claims


class PackagingValidationTests(unittest.TestCase):
    def test_repairs_missing_question_and_follow_cta(self):
        data = {"scenes": [{"narration": "A useful final point."}]}
        ensure_final_cta(data)
        final = data["scenes"][-1]["narration"]
        self.assertIn("?", final)
        self.assertIn("follow", final.lower())

    def test_does_not_duplicate_existing_cta(self):
        original = "What would you change? Follow FitFuel for more."
        data = {"scenes": [{"narration": original}]}
        ensure_final_cta(data)
        self.assertEqual(data["scenes"][-1]["narration"], original)

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


    def test_rejects_universal_fixed_weekly_weight_jump(self):
        data = {"scenes": [{"narration": "Increase the weight by 2 kg every week."}]}
        self.assertIn("universal progression", validate_scientific_claims(data))

    def test_rejects_weekly_strength_doubling_claim(self):
        data = {"scenes": [{"narration": "You can double your strength every week."}]}
        self.assertIn("strength-doubling", validate_scientific_claims(data))

    def test_accepts_performance_based_progression(self):
        data = {"scenes": [{"narration": "Add a small amount when all target reps feel controlled."}]}
        self.assertIsNone(validate_scientific_claims(data))
if __name__ == "__main__":
    unittest.main()
