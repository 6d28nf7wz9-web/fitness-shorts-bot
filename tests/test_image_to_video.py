import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import image_to_video as i2v


class ImageToVideoSafetyTests(unittest.TestCase):
    def test_generation_is_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(i2v.is_enabled())
            with patch.object(i2v.requests, "post") as post:
                with self.assertRaises(i2v.I2VDisabled):
                    i2v.generate_video("missing.png", "test prompt", "out.mp4")
                post.assert_not_called()

    def test_production_workflow_hard_locks_generation_off(self):
        with open(".github/workflows/daily.yml", encoding="utf-8") as f:
            workflow = f.read()
        self.assertIn('I2V_ENABLED: "0"', workflow)
        self.assertNotIn("vars.I2V_ENABLED", workflow)

    def test_scene_limit_is_hard_capped_at_two(self):
        with patch.dict(os.environ, {"I2V_MAX_SCENES": "99"}):
            self.assertEqual(i2v.max_scenes(), 2)

    def test_scene_needs_explicit_enablement_and_local_still(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_dir = Path(tmp)
            image = image_dir / "scene_1.png"
            image.write_bytes(b"png-placeholder")
            with patch.object(i2v, "INPUT_DIR", image_dir):
                with patch.dict(os.environ, {"I2V_ENABLED": "0", "I2V_MAX_SCENES": "2"}):
                    self.assertFalse(i2v.scene_is_eligible(1))
                with patch.dict(os.environ, {"I2V_ENABLED": "1", "I2V_MAX_SCENES": "2"}):
                    self.assertTrue(i2v.scene_is_eligible(1))
                    self.assertFalse(i2v.scene_is_eligible(3))

    def test_provider_dispatch_is_mocked_and_download_is_not_networked(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "scene_1.png"
            image.write_bytes(b"x" * 64)
            with patch.dict(os.environ, {
                "I2V_ENABLED": "1",
                "KLING_API_KEY": "test-token-not-real",
                "I2V_PROVIDER": "kling",
            }):
                with patch.object(i2v, "_generate_kling", return_value="https://example.invalid/video.mp4") as gen:
                    with patch.object(i2v, "_download", return_value="mock-output.mp4") as download:
                        result = i2v.generate_video(image, "muscle anatomy", "out.mp4")
            self.assertEqual(result, "mock-output.mp4")
            gen.assert_called_once()
            download.assert_called_once_with("https://example.invalid/video.mp4", "out.mp4")

    def test_unknown_provider_fails_before_any_request(self):
        with patch.dict(os.environ, {"I2V_PROVIDER": "unknown"}):
            with self.assertRaises(i2v.I2VError):
                i2v.configured_provider()


if __name__ == "__main__":
    unittest.main()
