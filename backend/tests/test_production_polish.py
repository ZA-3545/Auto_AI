"""Phase 8 — error handling & rate-limit smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.errors import FRIENDLY_LLM_UNAVAILABLE, FRIENDLY_RATE_LIMITED
from app.core.rate_limit import SlidingWindowRateLimiter
from app.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_validation_error_is_user_friendly() -> None:
    response = client.post("/api/chat/extract", json={})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "Invalid request" in body["detail"]
    assert "traceback" not in str(body).lower()


def test_listing_rejects_empty_after_strip_via_min_length() -> None:
    response = client.post(
        "/api/listings/analyze",
        json={"listing_text": ""},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_search_budget_min_gt_max() -> None:
    response = client.get(
        "/api/vehicles/search",
        params={"budget_min": 5_000_000, "budget_max": 1_000_000},
    )
    assert response.status_code == 422
    assert "budget_min" in response.json()["detail"]


def test_sliding_window_rate_limiter_blocks() -> None:
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        limiter.check("test-key")
    try:
        limiter.check("test-key")
        raised = False
    except Exception as exc:  # noqa: BLE001
        raised = True
        assert getattr(exc, "status_code", None) == 429
        assert FRIENDLY_RATE_LIMITED in str(exc.detail)
    assert raised


def test_friendly_llm_constant_present() -> None:
    assert "please try again" in FRIENDLY_LLM_UNAVAILABLE.lower()
