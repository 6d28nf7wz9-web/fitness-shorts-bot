import os
import unittest
from unittest.mock import patch

from artcraft_scene_provider import _prompt, is_enabled


class ArtCraftProviderTests(unittest.TestCase):
    def test_provider_is_disabled_without_explicit_opt_in(self):
        with patch.dict(os.environ, {
            "ARTCRAFT_ENABLED": "0",
            "ARTCRAFT_API_KEY": "test-key",
            "ARTCRAFT_MAX_GENERATIONS": "2",
        }, clear=False):
            self.assertFalse(is_enabled())

    def test_provider_is_disabled_without_api_key_or_budget(self):
        with patch.dict(os.environ, {
            "ARTCRAFT_ENABLED": "1",
            "ARTCRAFT_API_KEY": "",
            "ARTCRAFT_MAX_GENERATIONS": "2",
        }, clear=False):
            self.assertFalse(is_enabled())
        with patch.dict(os.environ, {
            "ARTCRAFT_ENABLED": "1",
            "ARTCRAFT_API_KEY": "test-key",
            "ARTCRAFT_MAX_GENERATIONS": "0",
        }, clear=False):
            self.assertFalse(is_enabled())

    def test_provider_requires_all_opt_in_conditions(self):
        with patch.dict(os.environ, {
            "ARTCRAFT_ENABLED": "true",
            "ARTCRAFT_API_KEY": "test-key",
            "ARTCRAFT_MAX_GENERATIONS": "1",
        }, clear=False):
            self.assertTrue(is_enabled())

    def test_prompt_is_scene_specific_and_forbids_overlay_text(self):
        prompt = _prompt({
            "visual_title": "Romanian Deadlift",
            "visual_subtitle": "Hip hinge mechanics",
        }, "Keep a neutral spine while hinging at the hips.")
        self.assertIn("Romanian Deadlift", prompt)
        self.assertIn("neutral spine", prompt)
        self.assertIn("No text, captions", prompt)
        self.assertIn("Vertical 9:16", prompt)


if __name__ == "__main__":
    unittest.main()
