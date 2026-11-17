import unittest

from clips_fast import sentence_contexts


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

    def test_empty_narration_is_safe(self):
        self.assertEqual(sentence_contexts("", 2), ["", ""])


if __name__ == "__main__":
    unittest.main()
