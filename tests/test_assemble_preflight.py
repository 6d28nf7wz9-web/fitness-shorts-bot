import os
import tempfile
import unittest

from assemble import validate_preflight


class AssemblyPreflightTests(unittest.TestCase):
    def _audio_fixture(self, root):
        audio_dir = os.path.join(root, "output", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        voice = os.path.join(audio_dir, "voice_1.wav")
        with open(voice, "wb") as f:
            f.write(b"v" * 12000)
        return [{
            "scene": 1,
            "seconds": 2.5,
            "file": os.path.relpath(voice, root),
        }]

    def test_hyperframes_does_not_require_legacy_scene_clip(self):
        with tempfile.TemporaryDirectory() as root:
            audio = self._audio_fixture(root)
            scenes = [{"narration": "A short test scene."}]
            # No output/clips/scene_1.mp4 is created: HyperFrames draws the visuals.
            validate_preflight(scenes, audio, hyperframes_enabled=True, root=root)

    def test_legacy_renderer_still_requires_scene_clip(self):
        with tempfile.TemporaryDirectory() as root:
            audio = self._audio_fixture(root)
            scenes = [{"narration": "A short test scene."}]
            with self.assertRaisesRegex(SystemExit, "output/clips/scene_1.mp4"):
                validate_preflight(scenes, audio, hyperframes_enabled=False, root=root)

    def test_legacy_renderer_accepts_scene_clip_when_present(self):
        with tempfile.TemporaryDirectory() as root:
            audio = self._audio_fixture(root)
            clips_dir = os.path.join(root, "output", "clips")
            os.makedirs(clips_dir, exist_ok=True)
            with open(os.path.join(clips_dir, "scene_1.mp4"), "wb") as f:
                f.write(b"c" * 12000)
            scenes = [{"narration": "A short test scene."}]
            validate_preflight(scenes, audio, hyperframes_enabled=False, root=root)

    def test_missing_voiceover_is_always_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            scenes = [{"narration": "A short test scene."}]
            audio = [{"scene": 1, "seconds": 2.5, "file": "output/audio/missing.wav"}]
            with self.assertRaisesRegex(SystemExit, "missing or invalid audio"):
                validate_preflight(scenes, audio, hyperframes_enabled=True, root=root)


if __name__ == "__main__":
    unittest.main()
