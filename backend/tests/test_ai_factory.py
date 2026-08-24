"""AI provider factory tests — no live network calls."""

from types import SimpleNamespace

import pytest

from app.ai.base import AIProviderError
from app.ai.factory import get_ai_provider, reset_ai_provider_cache
from app.ai.openrouter_provider import normalize_openrouter_model


def _settings(**overrides: object) -> SimpleNamespace:
    values = {
        "AI_PROVIDER": "openai",
        "OPENAI_API_KEY": "sk-test-openai",
        "OPENAI_MODEL": "gpt-4o-mini",
        "OPENROUTER_API_KEY": "",
        "OPENROUTER_MODEL": "openai/gpt-4o-mini",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> None:
    reset_ai_provider_cache()
    yield
    reset_ai_provider_cache()


def test_normalize_openrouter_model_adds_openai_prefix() -> None:
    assert normalize_openrouter_model("gpt-4o-mini") == "openai/gpt-4o-mini"
    assert normalize_openrouter_model("openai/gpt-4o-mini") == "openai/gpt-4o-mini"
    assert normalize_openrouter_model("") == "openai/gpt-4o-mini"


def test_factory_uses_openrouter_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.factory.get_settings",
        lambda: _settings(
            AI_PROVIDER="openrouter",
            OPENAI_API_KEY="",
            OPENROUTER_API_KEY="sk-or-v1-test",
        ),
    )
    provider = get_ai_provider()
    assert provider.name == "openrouter"
    assert provider.model_name == "openai/gpt-4o-mini"
    assert "openrouter.ai" in str(provider._client.base_url)


def test_factory_openroute_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.factory.get_settings",
        lambda: _settings(
            AI_PROVIDER="openroute",
            OPENAI_API_KEY="",
            OPENROUTER_API_KEY="sk-or-v1-test",
        ),
    )
    assert get_ai_provider().name == "openrouter"


def test_factory_auto_detects_openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.factory.get_settings",
        lambda: _settings(
            AI_PROVIDER="openai",
            OPENAI_API_KEY="sk-or-v1-test",
            OPENROUTER_API_KEY="",
        ),
    )
    provider = get_ai_provider()
    assert provider.name == "openrouter"
    assert "openrouter.ai" in str(provider._client.base_url)


def test_factory_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.factory.get_settings",
        lambda: _settings(AI_PROVIDER="openai", OPENAI_API_KEY="sk-test-openai"),
    )
    provider = get_ai_provider()
    assert provider.name == "openai"
    assert "openai.com" in str(provider._client.base_url)


def test_factory_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.factory.get_settings",
        lambda: _settings(AI_PROVIDER="not-a-provider"),
    )
    with pytest.raises(AIProviderError, match="Unsupported AI_PROVIDER"):
        get_ai_provider()
