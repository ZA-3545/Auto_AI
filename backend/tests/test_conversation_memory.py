"""Conversation memory tests (PLANNING.md Section G)."""

from __future__ import annotations

from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.ai.base import AIProvider
from app.core.database import get_db
from app.main import app
from app.models.conversation import Conversation
from app.models.vehicle import Vehicle  # noqa: F401 — register metadata
from app.schemas.extraction import ExtractedRequirements, TransmissionPreference
from app.services.conversation_memory import (
    empty_requirements,
    is_reset_message,
    merge_requirements,
)
from app.services.conversation_service import extract_with_memory


class FakeAIProvider(AIProvider):
    name = "fake"

    def __init__(self, handler: Callable[[str], ExtractedRequirements]) -> None:
        self._handler = handler

    @property
    def model_name(self) -> str:
        return "fake-model"

    def extract_requirements(self, message: str) -> ExtractedRequirements:
        return self._handler(message)


def _memory_handler(message: str) -> ExtractedRequirements:
    """Deterministic extractor for multi-turn memory scenarios."""
    normalized = " ".join(message.lower().split())

    if is_reset_message(message) and normalized in {
        "start a new search",
        "start new search",
        "new search",
        "start over",
        "reset",
        "reset search",
        "clear search",
    }:
        return empty_requirements()

    if "under 30 lakh" in normalized or "30 lakh" in normalized:
        return ExtractedRequirements(
            budget_max=3_000_000,
            needs_clarification=False,
            clarification_question=None,
        )

    if normalized in {"automatic", "auto"} or normalized == "automatic please":
        return ExtractedRequirements(
            transmission=TransmissionPreference.automatic,
            needs_clarification=False,
            clarification_question=None,
        )

    if "lahore" in normalized:
        return ExtractedRequirements(
            city="Lahore",
            needs_clarification=False,
            clarification_question=None,
        )

    return empty_requirements()


@pytest.fixture()
def db_session() -> Session:
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
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_merge_keeps_previous_budget_when_new_turn_only_has_transmission() -> None:
    previous = ExtractedRequirements(
        budget_max=3_000_000,
        needs_clarification=False,
        clarification_question=None,
    )
    new = ExtractedRequirements(
        transmission=TransmissionPreference.automatic,
        needs_clarification=False,
        clarification_question=None,
    )
    merged = merge_requirements(previous, new)
    assert merged.budget_max == 3_000_000
    assert merged.transmission == TransmissionPreference.automatic


def test_two_turn_section_g_scenario(db_session: Session) -> None:
    """
    Turn 1: 'Show me cars under 30 lakh'
    Turn 2: 'Automatic'
    Final requirements must have both budget_max and transmission.
    """
    provider = FakeAIProvider(_memory_handler)

    turn1 = extract_with_memory(
        db_session,
        "Show me cars under 30 lakh",
        provider=provider,
    )
    assert turn1.conversation_id is not None
    assert turn1.requirements.budget_max == 3_000_000
    assert turn1.requirements.transmission is None

    turn2 = extract_with_memory(
        db_session,
        "Automatic",
        conversation_id=turn1.conversation_id,
        provider=provider,
    )
    assert turn2.conversation_id == turn1.conversation_id
    assert turn2.requirements.budget_max == 3_000_000
    assert turn2.requirements.transmission == TransmissionPreference.automatic
    # Turn delta should only show transmission
    assert turn2.turn_requirements is not None
    assert turn2.turn_requirements.transmission == TransmissionPreference.automatic
    assert turn2.turn_requirements.budget_max is None


def test_reset_clears_requirements(db_session: Session) -> None:
    provider = FakeAIProvider(_memory_handler)
    turn1 = extract_with_memory(
        db_session, "Show me cars under 30 lakh", provider=provider
    )
    reset = extract_with_memory(
        db_session,
        "start a new search",
        conversation_id=turn1.conversation_id,
        provider=provider,
    )
    assert reset.reset is True
    assert reset.requirements.budget_max is None
    assert reset.requirements.transmission is None


def test_extract_endpoint_two_turn_memory(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.routers import chat as chat_router

    def _extract(db, message, *, conversation_id=None, reset=False, provider=None):
        return extract_with_memory(
            db,
            message,
            conversation_id=conversation_id,
            reset=reset,
            provider=FakeAIProvider(_memory_handler),
        )

    monkeypatch.setattr(chat_router, "extract_with_memory", _extract)

    r1 = client.post(
        "/api/chat/extract",
        json={"message": "Show me cars under 30 lakh"},
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["requirements"]["budget_max"] == 3_000_000
    conversation_id = body1["conversation_id"]
    assert conversation_id

    r2 = client.post(
        "/api/chat/extract",
        json={"message": "Automatic", "conversation_id": conversation_id},
    )
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["requirements"]["budget_max"] == 3_000_000
    assert body2["requirements"]["transmission"] == "automatic"
    assert body2["conversation_id"] == conversation_id


def test_reset_endpoint(client: TestClient, db_session: Session) -> None:
    provider = FakeAIProvider(_memory_handler)
    turn1 = extract_with_memory(
        db_session, "Show me cars under 30 lakh", provider=provider
    )
    response = client.post(
        "/api/chat/reset",
        json={"conversation_id": turn1.conversation_id},
    )
    assert response.status_code == 200
    assert response.json()["requirements"]["budget_max"] is None

    stored = db_session.get(Conversation, turn1.conversation_id)
    assert stored is not None
    assert stored.requirements.get("budget_max") is None
