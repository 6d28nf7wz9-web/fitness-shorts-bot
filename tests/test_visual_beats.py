import unittest

from visual_beats import split_visual_beats, build_visual_beat_overlays


class VisualBeatTests(unittest.TestCase):
    def test_long_narration_is_split_into_readable_phrase_beats(self):
        narration = "Protein supports muscle repair. Progressive overload drives growth because training creates a stimulus."
        beats = split_visual_beats(narration, max_words=7)
        self.assertGreaterEqual(len(beats), 3)
        self.assertTrue(all(1 <= len(x.split()) <= 7 for x in beats))
        self.assertEqual(" ".join(beats).replace(".", ""), narration.replace(".", ""))

    def test_visual_beats_cover_full_scene_duration(self):
        scene = {"narration": "Protein supports muscle repair. Sleep improves recovery and performance."}
        overlays = build_visual_beat_overlays(scene, 8.0, 1, 12.0)
        self.assertEqual(len(overlays), 2)
        self.assertIn('data-start="12.000"', overlays[0])
        self.assertIn('data-duration="', overlays[0])
        self.assertIn("visual-beat-label", overlays[0])
        durations = [float(x.split('data-duration="', 1)[1].split('"', 1)[0]) for x in overlays]
        self.assertAlmostEqual(sum(durations), 8.0, places=5)

    def test_empty_narration_still_gets_safe_visual_fallback(self):
        overlays = build_visual_beat_overlays({"visual_title": "Fitness science"}, 3.0, 2, 0.0)
        self.assertEqual(len(overlays), 1)
        self.assertIn("Fitness science", overlays[0])


if __name__ == "__main__":
    unittest.main()
