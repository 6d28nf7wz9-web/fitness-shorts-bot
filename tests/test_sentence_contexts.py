import unittest

from clips_fast import sentence_contexts


class SentenceContextTests(unittest.TestCase):
    def test_each_cut_receives_a_sentence_level_context(self):
        contexts = sentence_contexts(
            "Protein supports repair. Sleep improves recovery! Hydration helps performance.",
            3,
        )
        self.assertEqual(contexts, [
            "Protein supports repair.",
            "Sleep improves recovery!",
            "Hydration helps performance.",
        ])

    def test_more_cuts_than_sentences_reuse_last_sentence(self):
        contexts = sentence_contexts("Train consistently. Recover well.", 4)
        self.assertEqual(len(contexts), 4)
        self.assertTrue(all(context for context in contexts))
        self.assertEqual(contexts[-1], "Recover well.")

    def test_empty_narration_is_safe(self):
        self.assertEqual(sentence_contexts("", 2), ["", ""])


if __name__ == "__main__":
    unittest.main()
