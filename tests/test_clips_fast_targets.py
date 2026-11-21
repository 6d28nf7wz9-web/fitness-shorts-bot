import unittest

from clips_fast import _cut_keywords, _exercise_variants, _ordered_keywords


class SpokenMovementBrollTests(unittest.TestCase):
    def test_romanian_deadlift_is_more_specific_than_generic_gym(self):
        scene = {
            "keyword": "gym workout|weight training",
            "visual_title": "Romanian Deadlift",
            "narration": "Keep the bar close as you hinge at the hips.",
        }
        keywords = _ordered_keywords(scene)
        self.assertEqual(keywords[0], "romanian deadlift")
        self.assertIn("gym workout", keywords)

    def test_each_sentence_can_drive_a_different_exercise_query(self):
        scene = {"keyword": "strength training", "narration": "Squats and bench press"}
        base = _ordered_keywords(scene)
        squat = _cut_keywords(scene, "Lower into the squat with control.", base)
        bench = _cut_keywords(scene, "Press the bar away from your chest.", base)
        self.assertEqual(squat[0], "barbell squat")
        self.assertEqual(bench[0], "barbell bench press")
        self.assertNotEqual(squat[0], bench[0])

    def test_named_exercise_is_detected_without_generic_workout_word(self):
        self.assertEqual(_exercise_variants("During the Romanian deadlift, hinge at the hips")[0],
                         "romanian deadlift")

    def test_unrelated_sentence_does_not_invent_an_exercise(self):
        self.assertEqual(_exercise_variants("Protein supports recovery"), [])

    def test_scene_target_is_retained_when_sentence_is_general(self):
        scene = {"visual_title": "Hip Thrust", "keyword": "glute training"}
        result = _cut_keywords(scene, "This builds strength over time.", ["glute training"])
        self.assertEqual(result[0], "barbell hip thrust")


if __name__ == "__main__":
    unittest.main()
