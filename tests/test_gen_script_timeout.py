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
