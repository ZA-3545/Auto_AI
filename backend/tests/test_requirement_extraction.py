"""Requirement-extraction tests (PLANNING.md Section K).

Unit tests inject a fake AIProvider so they stay deterministic and offline.
Optional live provider checks run only when an API key is set.
"""

from __future__ import annotations

from typing import Callable

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai.base import AIProvider, AIProviderError
from app.main import app
from app.schemas.extraction import (
    ExtractedRequirements,
    TransmissionPreference,
)
from app.services.requirement_extraction import extract_requirements


class FakeAIProvider(AIProvider):
    """Deterministic stand-in that mimics structured-output extraction."""

    name = "fake"

    def __init__(self, handler: Callable[[str], ExtractedRequirements]) -> None:
        self._handler = handler

    @property
    def model_name(self) -> str:
        return "fake-model"

    def extract_requirements(self, message: str) -> ExtractedRequirements:
        return self._handler(message)


def _section_k_handler(message: str) -> ExtractedRequirements:
    """Maps Section K example inputs to expected structured outputs."""
    normalized = " ".join(message.lower().split())

    if "35 lakh" in normalized and "lahore" in normalized and "automatic" in normalized:
        return ExtractedRequirements(
            budget_min=None,
            budget_max=3_500_000,
            city="Lahore",
            condition=None,
            transmission=TransmissionPreference.automatic,
            body_type=None,
            purpose="family",
            fuel_priority=None,
            resale_priority=None,
            needs_clarification=False,
            clarification_question=None,
        )

    if normalized in {"my budget is 30", "budget is 30", "budget 30"} or (
        "budget" in normalized and "30" in normalized and "lakh" not in normalized and "pkr" not in normalized
    ):
        return ExtractedRequirements(
            budget_min=None,
            budget_max=None,
            city=None,
            condition=None,
            transmission=None,
            body_type=None,
            purpose=None,
            fuel_priority=None,
            resale_priority=None,
            needs_clarification=True,
            clarification_question="Do you mean PKR 30 lakh?",
        )

    raise AIProviderError(f"Fake provider has no fixture for: {message!r}")


@pytest.fixture()
def db_session():
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.pool import StaticPool
    from sqlmodel import SQLModel, create_engine

    from app.models.conversation import Conversation, Message  # noqa: F401
    from app.models.vehicle import Vehicle  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        SQLModel.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session) -> TestClient:
    from app.core.database import get_db

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_schema_rejects_clarification_without_question() -> None:
    with pytest.raises(ValidationError):
        ExtractedRequirements(
            needs_clarification=True,
            clarification_question=None,
        )


def test_roman_urdu_family_car_extraction() -> None:
    """Section K: mixed Roman Urdu + English → structured filters."""
    message = "35 lakh mein Lahore ke liye automatic family car"
    result = extract_requirements(message, provider=FakeAIProvider(_section_k_handler))

    req = result.requirements
    assert req.budget_max == 3_500_000
    assert req.city == "Lahore"
    assert req.transmission == TransmissionPreference.automatic
    assert req.purpose == "family"
    assert req.needs_clarification is False
    assert req.clarification_question is None
    # Extraction must not invent cars/listings
    assert not hasattr(req, "vehicles")
    assert "Corolla" not in req.model_dump_json()


def test_ambiguous_budget_needs_clarification() -> None:
    """Section K: bare number budget must not be guessed."""
    message = "My budget is 30"
    result = extract_requirements(message, provider=FakeAIProvider(_section_k_handler))

    req = result.requirements
    assert req.needs_clarification is True
    assert req.budget_max is None
    assert req.budget_min is None
    assert req.clarification_question is not None
    assert "lakh" in req.clarification_question.lower()


def test_extract_endpoint_roman_urdu(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routers import chat as chat_router
    from app.services.conversation_service import extract_with_memory

    def _fake_extract(db, message, *, conversation_id=None, reset=False, provider=None):
        return extract_with_memory(
            db,
            message,
            conversation_id=conversation_id,
            reset=reset,
            provider=FakeAIProvider(_section_k_handler),
        )

    monkeypatch.setattr(chat_router, "extract_with_memory", _fake_extract)

    response = client.post(
        "/api/chat/extract",
        json={"message": "35 lakh mein Lahore ke liye automatic family car"},
    )
    assert response.status_code == 200
    payload = response.json()
    req = payload["requirements"]
    assert req["budget_max"] == 3_500_000
    assert req["city"] == "Lahore"
    assert req["transmission"] == "automatic"
    assert req["purpose"] == "family"
    assert req["needs_clarification"] is False
    assert payload["conversation_id"]


def test_extract_endpoint_ambiguous_budget(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routers import chat as chat_router
    from app.services.conversation_service import extract_with_memory

    def _fake_extract(db, message, *, conversation_id=None, reset=False, provider=None):
        return extract_with_memory(
            db,
            message,
            conversation_id=conversation_id,
            reset=reset,
            provider=FakeAIProvider(_section_k_handler),
        )

    monkeypatch.setattr(chat_router, "extract_with_memory", _fake_extract)

    response = client.post("/api/chat/extract", json={"message": "My budget is 30"})
    assert response.status_code == 200
    req = response.json()["requirements"]
    assert req["needs_clarification"] is True
    assert req["budget_max"] is None
    assert "lakh" in (req["clarification_question"] or "").lower()


def test_provider_error_surfaces_as_502(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routers import chat as chat_router
    from app.ai.base import AIProviderError as Err
    from app.core.errors import FRIENDLY_LLM_UNAVAILABLE

    def _boom(db, message, *, conversation_id=None, reset=False, provider=None):
        raise Err("simulated provider failure")

    monkeypatch.setattr(chat_router, "extract_with_memory", _boom)

    response = client.post("/api/chat/extract", json={"message": "hello"})
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail == FRIENDLY_LLM_UNAVAILABLE
    assert "traceback" not in detail.lower()


@pytest.mark.integration
def test_live_openai_roman_urdu_family_car() -> None:
    """Live structured-output check — skipped when no provider key is set."""
    from app.ai.factory import get_ai_provider, reset_ai_provider_cache
    from app.core.config import get_settings

    get_settings.cache_clear()
    reset_ai_provider_cache()
    current = get_settings()
    if not (current.OPENROUTER_API_KEY or current.OPENAI_API_KEY):
        pytest.skip("No AI provider API key configured")

    result = extract_requirements(
        "35 lakh mein Lahore ke liye automatic family car",
        provider=get_ai_provider(),
    )
    req = result.requirements
    assert req.budget_max == 3_500_000
    assert req.city and req.city.lower() == "lahore"
    assert req.transmission == TransmissionPreference.automatic
    assert req.purpose and "family" in req.purpose.lower()
    assert req.needs_clarification is False


@pytest.mark.integration
def test_live_openai_ambiguous_budget() -> None:
    from app.ai.factory import get_ai_provider, reset_ai_provider_cache
    from app.core.config import get_settings

    get_settings.cache_clear()
    reset_ai_provider_cache()
    current = get_settings()
    if not (current.OPENROUTER_API_KEY or current.OPENAI_API_KEY):
        pytest.skip("No AI provider API key configured")

    result = extract_requirements("My budget is 30", provider=get_ai_provider())
    req = result.requirements
    assert req.needs_clarification is True
    assert req.budget_max is None
    assert req.clarification_question
