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


    def test_food_clip_with_shared_plate_tag_is_rejected_for_barbell_scene(self):
        hit = {
            "tags": "scrambled eggs plate cucumbers food fork breakfast nutrition",
            "pageURL": "",
        }
        self.assertEqual(
            relevance(hit, "barbell loading plates | athlete adding weight | gym close-up",
                       "I’ll show why progressive overload still matters."),
            0,
        )

    def test_specific_training_clip_still_matches_lifting_scene(self):
        hit = {
            "tags": "barbell weight plates gym strength training",
            "pageURL": "",
        }
        self.assertEqual(
            relevance(hit, "barbell loading plates | athlete adding weight | gym close-up",
                       "I’ll show why progressive overload still matters."),
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
