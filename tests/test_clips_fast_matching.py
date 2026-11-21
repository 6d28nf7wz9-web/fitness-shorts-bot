import unittest

from clips_fast import sentence_contexts, _require_exact_footage_match


class SentenceContextTests(unittest.TestCase):
    def test_one_sentence_is_split_into_distinct_visual_beats(self):
        contexts = sentence_contexts(
            "Protein supports repair, muscle growth, and recovery after training",
            3,
        )
        self.assertEqual(len(contexts), 3)
        self.assertTrue(all(contexts))
        self.assertEqual(len(set(contexts)), 3)

    def test_more_cuts_than_sentences_do_not_repeat_last_sentence(self):
        contexts = sentence_contexts(
            "The heart pumps blood. Oxygen reaches working muscles.",
            4,
        )
        self.assertEqual(len(contexts), 4)
        self.assertTrue(all(contexts))

    def test_exact_training_clip_passes_cut_level_gate(self):
        hit = {"tags": "barbell weight plates gym strength training", "pageURL": ""}
        score = _require_exact_footage_match(
            hit,
            "barbell loading plates | athlete adding weight | gym close-up",
            "The lifter adds plates to the barbell.",
        )
        self.assertEqual(score, 2)

    def test_food_clip_cannot_pass_training_cut_gate(self):
        hit = {"tags": "scrambled eggs plate breakfast nutrition", "pageURL": ""}
        with self.assertRaisesRegex(RuntimeError, "failed exact semantic match"):
            _require_exact_footage_match(
                hit,
                "barbell loading plates | athlete adding weight | gym close-up",
                "The lifter adds plates to the barbell.",
            )

    def test_empty_narration_is_safe(self):
        self.assertEqual(sentence_contexts("", 2), ["", ""])


if __name__ == "__main__":
    unittest.main()
