import unittest
from long_science_visuals import classify_section, chunk_windows

class LongScienceVisualTests(unittest.TestCase):
    def test_topic_specific_scene_selection(self):
        self.assertEqual(classify_section({"heading":"How muscle protein synthesis works"}),"protein_synthesis")
        self.assertEqual(classify_section({"heading":"Hydration and water balance"}),"hydration")
        self.assertEqual(classify_section({"heading":"Why sleep improves recovery"}),"recovery_sleep")
        self.assertEqual(classify_section({"heading":"A useful general principle"}),"process")
    def test_sections_split_into_contiguous_short_beats(self):
        windows=chunk_windows(0,16,7)
        self.assertEqual(windows,[(0.0,7.0),(7.0,14.0),(14.0,16.0)])
        self.assertTrue(all(b-a<=7 for a,b in windows))
        self.assertEqual(windows[0][0],0); self.assertEqual(windows[-1][1],16)
    def test_invalid_timing_is_rejected(self):
        with self.assertRaises(ValueError): chunk_windows(5,5,7)

if __name__=="__main__": unittest.main()
