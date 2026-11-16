import unittest

from relevance import relevance


class StrictFootageRelevanceTests(unittest.TestCase):
    def test_generic_training_tags_are_not_an_exact_match(self):
        hit = {"tags": "fitness gym workout training athlete outdoors", "pageURL": ""}
        self.assertEqual(
            relevance(hit, "muscle fiber activation graphic",
                      "Muscle fibers adapt to mechanical tension"),
            1,
        )

    def test_specific_topic_terms_are_an_exact_match(self):
        hit = {"tags": "muscle fiber activation anatomy", "pageURL": ""}
        self.assertEqual(
            relevance(hit, "muscle fiber activation graphic",
                      "Muscle fibers adapt to mechanical tension"),
            2,
        )

    def test_unrelated_beach_footage_is_rejected(self):
        hit = {"tags": "beach ocean sea waves coastline", "pageURL": ""}
        self.assertEqual(
            relevance(hit, "muscle fiber activation graphic",
                      "Muscle fibers adapt to mechanical tension"),
            0,
        )


if __name__ == "__main__":
    unittest.main()
