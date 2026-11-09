import tempfile
import unittest
from pathlib import Path
from long_science_visuals import classify_section, chunk_windows, draw_scene, render_chunk

class LongScienceVisualTests(unittest.TestCase):
    def test_topic_specific_scene_selection(self):
        self.assertEqual(classify_section({"heading":"How muscle protein synthesis works"}),"protein_synthesis")
        self.assertEqual(classify_section({"heading":"Hydration and water balance"}),"hydration")
        self.assertEqual(classify_section({"heading":"Why sleep improves recovery"}),"recovery_sleep")
        self.assertEqual(classify_section({"heading":"A useful general principle"}),"process")
        self.assertEqual(classify_section({"heading":"A useful principle","narration":"Dietary fiber supports the gut microbiome"}),"digestion_fiber")
    def test_sections_split_into_contiguous_short_beats(self):
        windows=chunk_windows(0,16,5)
        self.assertEqual(windows,[(0.0,5.0),(5.0,10.0),(10.0,15.0),(15.0,16.0)])
        self.assertTrue(all(b-a<=6 for a,b in windows))
        self.assertEqual(windows[0][0],0); self.assertEqual(windows[-1][1],16)
    def test_landscape_motion_graphic_frame_renders(self):
        image = draw_scene({"heading": "Muscle protein synthesis", "keywords": ["protein", "muscle"]}, "protein_synthesis", 1, 2, 0.5, 8)
        self.assertEqual(image.size, (1280, 720))
        second_beat = draw_scene({"heading": "Muscle protein synthesis"}, "protein_synthesis", 1, 2, 0.5, 8, beat_index=1)
        self.assertNotEqual(image.tobytes(), second_beat.tobytes())

    def test_ffmpeg_renders_a_short_animated_scene(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "scene.mp4"
            render_chunk({"heading": "Hydration", "keywords": ["water"]}, 1, "hydration", 0, 1.0, 1.0, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 1000)

    def test_invalid_timing_is_rejected(self):
        with self.assertRaises(ValueError): chunk_windows(5,5,7)

if __name__=="__main__": unittest.main()
