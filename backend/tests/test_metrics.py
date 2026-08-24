"""Evaluation metrics dashboard tests (PLANNING.md K.1)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.core.metrics_collector import (
    FEATURE_PATHS,
    record_extraction,
    record_llm_usage,
    record_request,
    record_search_outcome,
    reset_metrics,
)
from app.models.conversation import Conversation, Message
from app.services.metrics_service import build_admin_metrics


@pytest.fixture(autouse=True)
def _clean_metrics() -> None:
    reset_metrics()
    yield
    reset_metrics()


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
    session.add(
        Conversation(
            id="test-conv-1",
            requirements={"budget_max": 3_000_000},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    session.add(
        Message(
            conversation_id="test-conv-1",
            role="user",
            content="Family car Lahore",
            extracted_delta={"needs_clarification": False, "budget_max": 3_000_000},
            created_at=datetime.now(timezone.utc),
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        SQLModel.metadata.drop_all(engine)
        engine.dispose()


def test_computed_metrics_from_collector(db_session: Session) -> None:
    record_extraction(needs_clarification=False)
    record_extraction(needs_clarification=True)
    record_request(
        path=FEATURE_PATHS["search"],
        status_code=200,
        duration_ms=120,
        started_at_monotonic=1.0,
    )
    record_search_outcome(path=FEATURE_PATHS["search"], total=5)
    record_search_outcome(path=FEATURE_PATHS["search"], total=0)
    record_llm_usage(
        operation="extract_requirements",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        approx_cost_usd=0.0001,
        conversation_id="test-conv-1",
    )

    payload = build_admin_metrics(db_session)
    by_id = {m.id: m for m in payload.metrics}

    assert by_id["extraction_accuracy"].status == "computed"
    assert by_id["extraction_accuracy"].value == 50.0
    assert by_id["search_relevance"].status == "computed"
    assert by_id["search_relevance"].value == 50.0
    assert by_id["api_cost_total"].status == "computed"
    assert by_id["response_latency"].status == "computed"
    assert by_id["user_satisfaction"].status == "not_available"
    assert by_id["click_through_rate"].status == "not_available"
    assert by_id["recommendation_relevance"].status == "not_available"
    assert "not faked" in (by_id["recommendation_relevance"].note or "").lower()
    assert by_id["hallucination_rate"].status == "manual"
    assert payload.conversations_with_llm_cost == 1


def test_not_available_without_activity(db_session: Session) -> None:
    payload = build_admin_metrics(db_session)
    by_id = {m.id: m for m in payload.metrics}
    assert by_id["search_relevance"].status == "not_available"
    assert by_id["api_cost_total"].status == "not_available"
    assert by_id["db_conversations"].status == "computed"
    assert by_id["db_conversations"].value == 1
