import unittest

from relevance import relevance


class WorkplaceFalsePositiveTests(unittest.TestCase):
    def test_office_footage_is_rejected_for_creatine_training(self):
        hit = {"tags": "man office desk laptop computer health fitness training creatine"}
        self.assertEqual(relevance(hit, "creatine muscle performance", "supports repeated high intensity efforts"), 0)

    def test_office_footage_is_rejected_for_generic_gym_search(self):
        hit = {"tags": "businessman sitting at desk gym workout training"}
        self.assertEqual(relevance(hit, "gym workout", "person training with weights"), 0)

    def test_office_footage_is_allowed_when_office_is_the_actual_subject(self):
        hit = {"tags": "office desk laptop computer"}
        self.assertGreater(relevance(hit, "office desk", "working at a desk"), 0)

    def test_relevant_gym_footage_is_not_blocked_by_workplace_filter(self):
        hit = {"tags": "athlete gym dumbbell strength training"}
        self.assertEqual(relevance(hit, "dumbbell strength training", "lifting weights in gym"), 2)


if __name__ == "__main__":
    unittest.main()
