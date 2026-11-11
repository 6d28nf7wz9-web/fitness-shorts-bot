import unittest

from gen_script import _is_quota_exhausted


class GeminiQuotaClassificationTests(unittest.TestCase):
    def test_detects_hard_account_quota_exhaustion(self):
        error = "429 RESOURCE_EXHAUSTED: You exceeded your current quota, please check your plan and billing details."
        self.assertTrue(_is_quota_exhausted(error))

    def test_detects_per_model_quota_exhaustion(self):
        error = "Quota exceeded for metric generate_requests_per_model"
        self.assertTrue(_is_quota_exhausted(error))

    def test_does_not_classify_short_rate_limit_as_hard_quota(self):
        error = "429 RESOURCE_EXHAUSTED: Requests per minute limit reached; retry later."
        self.assertFalse(_is_quota_exhausted(error))


if __name__ == "__main__":
    unittest.main()
