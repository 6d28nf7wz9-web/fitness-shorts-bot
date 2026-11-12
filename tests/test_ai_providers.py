import unittest
from unittest.mock import Mock, patch

import requests

from ai_providers import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_OPENROUTER_MODEL,
    OpenAICompatibleProvider,
    ProviderError,
    build_external_providers,
)


class MultiProviderTests(unittest.TestCase):
    def test_provider_order_and_free_defaults(self):
        providers = build_external_providers({
            "GROQ_API_KEY": "groq-test",
            "OPENROUTER_API_KEY": "router-test",
        })
        self.assertEqual([p.name for p in providers], ["Groq", "OpenRouter"])
        self.assertEqual(providers[0].model, DEFAULT_GROQ_MODEL)
        self.assertEqual(providers[1].model, DEFAULT_OPENROUTER_MODEL)

    def test_missing_keys_skip_external_providers(self):
        self.assertEqual(build_external_providers({}), [])

    def test_openrouter_rejects_paid_model(self):
        with self.assertRaisesRegex(ValueError, "Paid OpenRouter models are blocked"):
            build_external_providers({
                "OPENROUTER_API_KEY": "router-test",
                "OPENROUTER_MODEL": "some-vendor/some-paid-model",
            })

    @patch("ai_providers.requests.post")
    def test_groq_uses_chat_completions_and_returns_text(self, post):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [{"message": {"content": '{"topic":"test"}'}}]
        }
        post.return_value = response
        provider = build_external_providers({"GROQ_API_KEY": "secret"})[0]

        result = provider.generate("write JSON")

        self.assertEqual(result.provider, "Groq")
        self.assertEqual(result.text, '{"topic":"test"}')
        self.assertEqual(post.call_args.kwargs["json"]["model"], DEFAULT_GROQ_MODEL)
        self.assertEqual(post.call_args.kwargs["timeout"], 45)

    @patch("ai_providers.time.sleep")
    @patch("ai_providers.requests.post")
    def test_transient_server_error_retries_once(self, post, sleep):
        failed = Mock(status_code=503, text="busy")
        success = Mock(status_code=200)
        success.json.return_value = {
            "choices": [{"message": {"content": '{"ok":true}'}}]
        }
        post.side_effect = [failed, success]
        provider = build_external_providers({"GROQ_API_KEY": "secret"})[0]

        self.assertEqual(provider.generate("prompt").text, '{"ok":true}')
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(2)

    @patch("ai_providers.time.sleep")
    @patch("ai_providers.requests.post")
    def test_quota_error_does_not_retry(self, post, sleep):
        post.return_value = Mock(status_code=429, text="rate limit")
        provider = build_external_providers({"GROQ_API_KEY": "secret"})[0]

        with self.assertRaisesRegex(ProviderError, "HTTP 429"):
            provider.generate("prompt")

        post.assert_called_once()
        sleep.assert_not_called()

    @patch("ai_providers.requests.post")
    def test_openrouter_sends_free_router_model(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": '{"ok":true}'}}]
        }
        post.return_value = response
        provider = build_external_providers({"OPENROUTER_API_KEY": "secret"})[0]

        provider.generate("prompt")

        self.assertEqual(post.call_args.kwargs["json"]["model"], "openrouter/free")
        self.assertIn("HTTP-Referer", post.call_args.kwargs["headers"])


if __name__ == "__main__":
    unittest.main()
