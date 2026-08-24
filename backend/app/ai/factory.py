"""Factory for AI providers — swap via AI_PROVIDER env var."""

from functools import lru_cache

from app.ai.base import AIProvider, AIProviderError
from app.ai.openai_provider import OpenAIProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.core.config import get_settings

_OPENROUTER_ALIASES = {"openrouter", "openroute"}


def _is_openrouter_key(key: str) -> bool:
    return key.startswith("sk-or-")


@lru_cache
def get_ai_provider() -> AIProvider:
    current = get_settings()
    provider = current.AI_PROVIDER.strip().lower()
    openai_key = current.OPENAI_API_KEY
    openrouter_key = current.OPENROUTER_API_KEY or (
        openai_key if _is_openrouter_key(openai_key) else ""
    )

    # Use direct OpenAI only when a real OpenAI key is configured (sk-…, not sk-or-…).
    wants_direct_openai = bool(
        openai_key and not _is_openrouter_key(openai_key) and provider == "openai"
    )

    if openrouter_key and not wants_direct_openai:
        return OpenRouterProvider(
            api_key=openrouter_key,
            model=current.OPENROUTER_MODEL or current.OPENAI_MODEL,
            base_url=current.OPENROUTER_BASE_URL,
        )

    if provider == "openai" or wants_direct_openai:
        return OpenAIProvider(
            api_key=openai_key,
            model=current.OPENAI_MODEL,
        )

    if openrouter_key:
        return OpenRouterProvider(
            api_key=openrouter_key,
            model=current.OPENROUTER_MODEL or current.OPENAI_MODEL,
            base_url=current.OPENROUTER_BASE_URL,
        )

    raise AIProviderError(
        f"Unsupported AI_PROVIDER={current.AI_PROVIDER!r}. Supported: openai, openrouter"
    )


def reset_ai_provider_cache() -> None:
    """Clear cached provider (used in tests)."""
    get_ai_provider.cache_clear()
