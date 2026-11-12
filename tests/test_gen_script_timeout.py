import unittest
from unittest.mock import Mock, patch

import gen_script


class GeminiTimeoutTests(unittest.TestCase):
    @patch("gen_script.genai.Client")
    def test_client_has_request_timeout_and_no_sdk_retry_loop(self, client_factory):
        gen_script.create_gemini_client("test-key")

        options = client_factory.call_args.kwargs["http_options"]
        self.assertEqual(options.timeout, gen_script.GEMINI_REQUEST_TIMEOUT_MS)
        self.assertEqual(options.retry_options.attempts, 1)

    def test_disabled_custom_retry_makes_only_one_api_call(self):
        client = Mock()
        client.models.generate_content.side_effect = RuntimeError(
            "503 service unavailable"
        )

        with self.assertRaisesRegex(RuntimeError, "503"):
            gen_script._generate_with_retry(
                client, "test-model", "test prompt", retries=0
            )

        client.models.generate_content.assert_called_once()

    def test_transient_503_gets_one_bounded_retry(self):
        client = Mock()
        client.models.generate_content.side_effect = [
            RuntimeError("503 UNAVAILABLE: high demand"),
            Mock(text='{"ok": true}'),
        ]

        with patch("gen_script.time.sleep") as sleep:
            response = gen_script._generate_with_retry(
                client, "test-model", "test prompt", retries=1
            )

        self.assertEqual(response.text, '{"ok": true}')
        self.assertEqual(client.models.generate_content.call_count, 2)
        sleep.assert_called_once_with(3)

    def test_hard_quota_error_is_not_retried(self):
        client = Mock()
        client.models.generate_content.side_effect = RuntimeError(
            "429 RESOURCE_EXHAUSTED: You exceeded your current quota; check billing details"
        )

        with patch("gen_script.time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "exceeded your current quota"):
                gen_script._generate_with_retry(
                    client, "test-model", "test prompt", retries=1
                )

        client.models.generate_content.assert_called_once()
        sleep.assert_not_called()

    def test_negated_guarantee_language_is_not_banned(self):
        self.assertNotIn("guaranteed", gen_script.BANNED)
        self.assertIn("guaranteed recovery", gen_script.BANNED)

    def test_invalid_environment_values_fall_back_to_safe_defaults(self):
        with patch.dict("os.environ", {"FITFUEL_TEST_LIMIT": "0"}):
            self.assertEqual(
                gen_script._positive_int_env("FITFUEL_TEST_LIMIT", 45), 45
            )
        with patch.dict("os.environ", {"FITFUEL_TEST_LIMIT": "not-a-number"}):
            self.assertEqual(
                gen_script._positive_int_env("FITFUEL_TEST_LIMIT", 45), 45
            )


if __name__ == "__main__":
    unittest.main()
