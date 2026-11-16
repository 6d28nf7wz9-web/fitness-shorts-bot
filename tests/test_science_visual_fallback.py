import os
import tempfile
import unittest
from unittest.mock import patch

from clips_fast import _render_science_fallback


class ScienceFallbackTests(unittest.TestCase):
    def test_fallback_renders_a_neutral_vertical_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "scene.mp4")

            def fake_ffmpeg(command, check):
                with open(command[-1], "wb") as f:
                    f.write(b"x" * 12000)

            with patch("clips_fast.subprocess.run", side_effect=fake_ffmpeg) as run:
                _render_science_fallback(output, 3.5)

            self.assertTrue(os.path.isfile(output))
            self.assertGreater(os.path.getsize(output), 10000)
            command = run.call_args.args[0]
            self.assertIn("1080x1920", " ".join(command))
            self.assertIn("3.5", command)


if __name__ == "__main__":
    unittest.main()
