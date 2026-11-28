import unittest
from fitfuel_cleanroom import build_storyboard, score_clip
class CleanRoomTests(unittest.TestCase):
 def test_storyboard_uses_audio_timing_and_story_roles(self):
  board=build_storyboard({"scenes":[{"narration":"A clear opening hook","keyword":"opening hook"},{"narration":"Protein supports muscle repair","keyword":"protein muscle"}]},[{"seconds":2.5},{"seconds":3.0}])
  self.assertEqual(board["scene_count"],2); self.assertEqual(board["scenes"][1]["start"],2.5)
  self.assertEqual(board["scenes"][0]["role"],"opening"); self.assertEqual(board["scenes"][1]["role"],"closing")
 def test_rejects_scene_audio_mismatch(self):
  with self.assertRaisesRegex(ValueError,"script/audio"): build_storyboard({"scenes":[{"narration":"Hello","keyword":"hello"}]},[])
 def test_rejects_missing_narration(self):
  with self.assertRaisesRegex(ValueError,"narration"): build_storyboard({"scenes":[{"keyword":"protein"}]},[{"seconds":2}])
 def test_specific_metadata_scores_higher_than_unrelated(self):
  good,_=score_clip({"tags":"protein amino acids chicken meal prep"},"Protein supports muscle repair",["protein amino acids"])
  bad,_=score_clip({"tags":"mountain sunset landscape travel"},"Protein supports muscle repair",["protein amino acids"])
  self.assertGreater(good,bad); self.assertEqual(bad,0.0)
if __name__=="__main__": unittest.main()
