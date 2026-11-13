"""Free-tier AI provider adapters for FitFuel script generation.

Provider order is controlled by the caller: Gemini, Groq, then OpenRouter.
OpenRouter is hard-restricted to its free router or explicit :free model IDs.
"""
from dataclasses import dataclass
import os
import time

import requests


DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_OPENROUTER_MODEL = "openrouter/free"
REQUEST_TIMEOUT_SECONDS = 45
MAX_TRANSIENT_RETRIES = 1


@dataclass
class ProviderResponse:
    text: str
    provider: str
    model: str


class ProviderError(RuntimeError):
    pass


class OpenAICompatibleProvider:
    def __init__(self, name, api_key, endpoint, model, timeout=REQUEST_TIMEOUT_SECONDS):
        self.name = name
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout

    def generate(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.name == "OpenRouter":
            headers["HTTP-Referer"] = "https://youtube.com/@fitfuel-0"
            headers["X-Title"] = "FitFuel Script Generator"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You write evidence-aware fitness education scripts. "
                        "Follow the user's prompt exactly and return valid JSON only. "
                        "Do not include markdown fences or commentary."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(MAX_TRANSIENT_RETRIES + 1):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt >= MAX_TRANSIENT_RETRIES:
                    raise ProviderError(f"{self.name} network failure: {exc}") from exc
                time.sleep(2)
                continue

            if response.status_code in (500, 502, 503, 504) and attempt < MAX_TRANSIENT_RETRIES:
                time.sleep(2)
                continue

            if response.status_code >= 400:
                # Do not retry 401/403/429: move to the next provider immediately.
                detail = (response.text or "")[:350]
                raise ProviderError(
                    f"{self.name} HTTP {response.status_code}: {detail}"
                )

            try:
                body = response.json()
                text = body["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise ProviderError(
                    f"{self.name} returned an unexpected chat-completion response"
                ) from exc

            if isinstance(text, list):
                text = "".join(
                    part.get("text", "") for part in text if isinstance(part, dict)
                )
            if not isinstance(text, str) or not text.strip():
                raise ProviderError(f"{self.name} returned empty content")

            return ProviderResponse(text=text.strip(), provider=self.name, model=self.model)

        raise ProviderError(f"{self.name} failed after bounded retries")


def build_external_providers(env=None):
    """Return configured external providers in strict Groq -> OpenRouter order."""
    env = os.environ if env is None else env
    providers = []

    groq_key = env.get("GROQ_API_KEY", "").strip()
    if groq_key:
        model = env.get("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()
        providers.append(
            OpenAICompatibleProvider(
                "Groq",
                groq_key,
                "https://api.groq.com/openai/v1/chat/completions",
                model,
            )
        )

    openrouter_key = env.get("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        model = env.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip()
        if model != "openrouter/free" and not model.endswith(":free"):
            raise ValueError(
                "OPENROUTER_MODEL must be 'openrouter/free' or an explicit ':free' model. "
                "Paid OpenRouter models are blocked to preserve the $0 budget."
            )
        providers.append(
            OpenAICompatibleProvider(
                "OpenRouter",
                openrouter_key,
                "https://openrouter.ai/api/v1/chat/completions",
                model,
            )
        )

    return providers
