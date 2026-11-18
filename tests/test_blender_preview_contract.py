"""Regression guards for the standalone Blender preview generator.

These tests intentionally avoid importing bpy, so they run in normal Python CI.
The headless Blender workflow performs the real render and MP4 validation.
"""
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "blender" / "fitfuel_science_preview.py"


class BlenderPreviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_portrait_composition_is_enforced(self):
        self.assertIn('camera.data.ortho_scale = 10.8', self.source)
        self.assertIn('args.width / args.height > 0.75', self.source)

    def test_phone_readable_hierarchy_is_present(self):
        for required in ('Brand label', 'Main title', 'Subtitle', 'Callout label left',
                         'Callout label right', 'Footer', 'Scientific note'):
            self.assertIn(required, self.source)

    def test_scientific_visual_has_moving_activation_signal(self):
        self.assertIn('Traveling activation signal', self.source)
        self.assertIn('pulse.keyframe_insert(data_path="location"', self.source)

    def test_output_path_is_defined_in_main_scope(self):
        self.assertIn('output_dir = Path(args.output_dir).resolve()', self.source)
        self.assertIn('first_frame = output_dir / "frame_0001.png"', self.source)
        self.assertIn('last_frame = output_dir / f"frame_{scene.frame_end:04d}.png"', self.source)

    def test_detached_floor_horizon_is_not_reintroduced(self):
        self.assertNotIn('Midnight studio floor', self.source)
        self.assertNotIn('primitive_plane_add(size=200', self.source)


if __name__ == "__main__":
    unittest.main()
