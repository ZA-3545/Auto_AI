"""LLM call retries with backoff (PLANNING.md Section I)."""

from __future__ import annotations

import time
from typing import Callable, TypeVar

from app.ai.base import AIProviderError
from app.core.config import settings
from app.core.logging_config import get_logger, log_event

T = TypeVar("T")
logger = get_logger("autoai.llm.retry")


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    non_retryable = (
        "invalid_api_key",
        "rejected the api key",
        "api_key is missing",
        "must not be empty",
        "refused",
        "schema validation",
    )
    if any(s in msg for s in non_retryable):
        return False
    retryable = (
        "timeout",
        "timed out",
        "temporarily",
        "503",
        "502",
        "429",
        "rate limit",
        "connection",
        "unavailable",
        "overloaded",
        "server error",
    )
    if any(s in msg for s in retryable):
        return True
    # Unknown provider blips — allow limited retry
    return isinstance(exc, AIProviderError)


def with_llm_retry(operation: str, fn: Callable[[], T]) -> T:
    """
    Run an LLM-bound callable with limited retries.

    Non-retryable auth/config errors fail immediately.
    """
    attempts = max(1, settings.LLM_MAX_RETRIES + 1)
    backoff = max(0.05, settings.LLM_RETRY_BACKOFF_SECONDS)
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except AIProviderError as exc:
            last_exc = exc
            retryable = _is_retryable(exc)
            log_event(
                logger,
                "llm_call_failed",
                path=operation,
                status_code=attempt,
                message=str(exc)[:300],
            )
            if not retryable or attempt >= attempts:
                if attempt >= attempts:
                    from app.core.metrics_collector import record_llm_failure

                    record_llm_failure(operation=operation)
                raise
            time.sleep(backoff * attempt)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            log_event(
                logger,
                "llm_call_failed",
                path=operation,
                status_code=attempt,
                message=str(exc)[:300],
            )
            if attempt >= attempts:
                from app.core.metrics_collector import record_llm_failure

                record_llm_failure(operation=operation)
                raise AIProviderError(
                    f"LLM operation '{operation}' failed: {exc}"
                ) from exc
            time.sleep(backoff * attempt)

    assert last_exc is not None
    raise last_exc
