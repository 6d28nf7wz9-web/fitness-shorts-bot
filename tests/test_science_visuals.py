"""Smoke tests for scientific scene classification and output helpers."""
import unittest
import tempfile
from pathlib import Path
from science_visuals import classify, classify_scene, wrap, visual_beat_durations, render_scene

class ScienceVisualTests(unittest.TestCase):
    def test_protein(self):
        self.assertEqual(classify("Amino acids support muscle protein synthesis"), "protein")
    def test_energy(self):
        self.assertEqual(classify("Calorie deficit and fat loss"), "energy")
    def test_hydration(self):
        self.assertEqual(classify("Water and hydration improve performance"), "hydration")
    def test_fallback(self):
        self.assertEqual(classify("A useful habit"), "generic")
    def test_dietary_fiber_gets_digestive_system(self):
        self.assertEqual(classify_scene({"narration":"Dietary fiber travels to the colon"}), "digestion_fiber")
    def test_exercise_gets_biomechanics(self):
        self.assertEqual(classify_scene({"narration":"During a squat your knees and hips bend"}), "exercise_biomechanics")
    def test_muscle_fibers_are_not_digestive_fiber(self):
        self.assertEqual(classify_scene({"narration":"Muscle fibers adapt after resistance training"}), "muscle_anatomy")
    def test_model_visual_type_is_respected(self):
        self.assertEqual(classify_scene({"narration":"A useful point","visual_type":"muscle_anatomy"}), "muscle_anatomy")
    def test_visual_beats_stay_at_or_below_six_seconds(self):
        beats = visual_beat_durations(13.2)
        self.assertEqual(len(beats), 3)
        self.assertTrue(all(4.0 <= beat <= 6.0 for beat in beats))
        self.assertAlmostEqual(sum(beats), 13.2, places=5)
    def test_short_scene_keeps_its_natural_duration(self):
        self.assertEqual(visual_beat_durations(2.5), [2.5])
    def test_renderer_builds_a_multi_beat_mp4(self):
        scene = {"narration": "Muscle protein synthesis uses amino acids.", "visual_type": "protein_synthesis"}
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "short.mp4")
            info = render_scene(scene, 1, 8.0, output)
            self.assertTrue(Path(output).is_file())
            self.assertEqual(info["visual_beats"], [4.0, 4.0])

if __name__ == "__main__": unittest.main()
