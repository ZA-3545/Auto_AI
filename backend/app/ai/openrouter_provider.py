"""OpenRouter provider — OpenAI-compatible client pointed at OpenRouter."""

from __future__ import annotations

from app.ai.openai_provider import OpenAIProvider

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-4o-mini"


def normalize_openrouter_model(model: str) -> str:
    """OpenRouter model ids are `provider/model` (e.g. openai/gpt-4o-mini)."""
    trimmed = model.strip()
    if not trimmed:
        return OPENROUTER_DEFAULT_MODEL
    if "/" in trimmed:
        return trimmed
    return f"openai/{trimmed}"


class OpenRouterProvider(OpenAIProvider):
    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str | None = None,
    ) -> None:
        super().__init__(
            api_key,
            normalize_openrouter_model(model),
            base_url=base_url or OPENROUTER_DEFAULT_BASE_URL,
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AutoAI",
            },
            name="openrouter",
            missing_key_message=(
                "OPENROUTER_API_KEY is missing. Set it in backend/.env "
                "(OpenRouter keys start with sk-or-v1-) to use the OpenRouter provider."
            ),
        )
