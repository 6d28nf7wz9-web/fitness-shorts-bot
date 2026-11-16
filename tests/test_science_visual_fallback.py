import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from clips_fast import _render_science_fallback, _validate_rendered_video


class ScienceFallbackTests(unittest.TestCase):
    def test_small_but_valid_mp4_is_accepted_by_ffprobe(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "scene.mp4")

            def fake_run(command, **kwargs):
                if command[0] == "ffmpeg":
                    with open(command[-1], "wb") as f:
                        f.write(b"x" * 1024)  # Validity is not determined by size.
                    return subprocess.CompletedProcess(command, 0)
                return subprocess.CompletedProcess(
                    command, 0,
                    stdout=json.dumps({
                        "format": {"duration": "3.5"},
                        "streams": [{
                            "codec_type": "video", "width": 1080, "height": 1920
                        }],
                    }),
                    stderr="",
                )

            with patch("clips_fast.subprocess.run", side_effect=fake_run) as run:
                _render_science_fallback(output, 3.5)

            self.assertTrue(os.path.isfile(output))
            self.assertEqual(os.path.getsize(output), 1024)
            ffmpeg_command = run.call_args_list[0].args[0]
            self.assertIn("1080x1920", " ".join(ffmpeg_command))
            self.assertIn("3.5", ffmpeg_command)
            self.assertEqual(run.call_args_list[1].args[0][0], "ffprobe")

    def test_rejects_missing_video_stream(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.mp4")
            with open(path, "wb") as f:
                f.write(b"x")
            result = subprocess.CompletedProcess(
                ["ffprobe"], 0,
                stdout=json.dumps({
                    "format": {"duration": "3.5"},
                    "streams": [{"codec_type": "audio"}],
                }),
                stderr="",
            )
            with patch("clips_fast.subprocess.run", return_value=result):
                with self.assertRaisesRegex(RuntimeError, "no valid video stream"):
                    _validate_rendered_video(path, 3.5)

    def test_rejects_invalid_or_empty_file_before_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.mp4")
            with open(path, "wb"):
                pass
            with patch("clips_fast.subprocess.run") as run:
                with self.assertRaisesRegex(RuntimeError, "non-empty"):
                    _validate_rendered_video(path, 3.5)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
