import os
import unittest
from unittest.mock import Mock, patch

import long_script


def make_script(title, first_heading):
    narration = (
        "A practical training example shows how to apply this idea "
        "with careful form and steady progress. " * 9
    )
    sections = []
    for index in range(5):
        sections.append({
            "heading": first_heading if index == 0 else f"Practical Step {index + 1}",
            "narration": narration,
            "keywords": ["barbell squat", "dumbbell press", "chicken rice"],
        })
    return {
        "topic": "A fresh training approach",
        "title": title,
        "description": "Evidence-based fitness advice for your next workout.",
        "hashtags": ["fitness", "strength", "training", "nutrition"],
        "sections": sections,
    }


class LongScriptTests(unittest.TestCase):
    def test_rejects_reworded_title_from_previous_long_video(self):
        candidate = make_script(
            "Why Every Workout Feeling Hard Stalls Your Muscle Growth",
            "A Different Opening",
        )
        previous = [{
            "id": "L016",
            "topic": "Breaking Lift Stalls With Microplates",
            "title": "Why Your Lifts Stall Even When Workouts Feel Hard",
            "sections": [{"heading": "The Constant Effort Trap"}],
        }]

        problem = long_script.validate(candidate, [], previous)

        self.assertIn("script overlaps previous long video", problem)

    def test_rejects_repeated_section_heading_even_with_a_new_title(self):
        candidate = make_script(
            "Build a Balanced High Protein Breakfast",
            "The Constant Effort Trap",
        )
        previous = [{
            "id": "L015",
            "topic": "Fixing Static Weight Strength Stalls",
            "title": "A Different Strength Training Subject",
            "sections": [{"heading": "The Constant Effort Trap"}],
        }]

        problem = long_script.validate(candidate, [], previous)

        self.assertIn("script repeats a previous long-video section", problem)

    def test_allows_a_genuinely_distinct_long_video(self):
        candidate = make_script(
            "Build a Balanced High Protein Breakfast",
            "Protein Before Training",
        )
        previous = [{
            "id": "L016",
            "topic": "Breaking Lift Stalls With Microplates",
            "title": "Why Your Lifts Stall Even When Workouts Feel Hard",
            "sections": [{"heading": "The Constant Effort Trap"}],
        }]

        self.assertIsNone(long_script.validate(candidate, [], previous))

    def test_transient_503_gets_one_bounded_retry(self):
        client = Mock()
        client.models.generate_content.side_effect = [
            RuntimeError("503 UNAVAILABLE: high demand"),
            Mock(text='{"ok": true}'),
        ]

        with patch("long_script.time.sleep") as sleep:
            response = long_script.generate_with_retry(
                client, "test-model", "test prompt", retries=1
            )

        self.assertEqual(response.text, '{"ok": true}')
        self.assertEqual(client.models.generate_content.call_count, 2)
        sleep.assert_called_once_with(4)

    def test_hard_quota_error_is_not_retried(self):
        client = Mock()
        client.models.generate_content.side_effect = RuntimeError(
            "429 RESOURCE_EXHAUSTED: You exceeded your current quota; check billing details"
        )

        with patch("long_script.time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "exceeded your current quota"):
                long_script.generate_with_retry(
                    client, "test-model", "test prompt", retries=1
                )

        client.models.generate_content.assert_called_once()
        sleep.assert_not_called()

    def test_hard_quota_stops_model_fallback(self):
        client = Mock()
        client.models.generate_content.side_effect = RuntimeError(
            "429 RESOURCE_EXHAUSTED: You exceeded your current quota"
        )

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), patch(
            "long_script.genai.Client", return_value=client
        ), patch(
            "long_script.get_model_candidates", return_value=["model-a", "model-b"]
        ), patch("long_script.all_used", return_value=[]), patch(
            "long_script.load_previous_scripts", return_value=[]
        ), patch("long_script.time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "Gemini quota exhausted"):
                long_script.generate([], [])

        client.models.generate_content.assert_called_once()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
