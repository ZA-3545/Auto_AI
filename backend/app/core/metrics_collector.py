"""In-process metrics collector (Phase 8 / PLANNING.md K.1).

Lightweight counters for PoC — resets on process restart. Not a time-series DB.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EndpointStats:
    count: int = 0
    error_count: int = 0
    total_duration_ms: int = 0
    # Search / recommend outcome tracking (approximate relevance proxy)
    with_results: int = 0
    empty_results: int = 0


@dataclass
class LlmStats:
    call_count: int = 0
    failure_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    approx_cost_usd: float = 0.0
    by_operation: dict[str, int] = field(default_factory=dict)
    cost_by_conversation: dict[str, float] = field(default_factory=dict)


@dataclass
class MetricsSnapshot:
    started_at_monotonic: float
    endpoint_stats: dict[str, EndpointStats]
    llm: LlmStats
    rate_limit_hits: int
    extraction_total: int
    extraction_needs_clarification: int
    extraction_without_clarification: int


_lock = threading.Lock()
_started_at_monotonic: float = 0.0
_endpoint_stats: dict[str, EndpointStats] = {}
_llm = LlmStats()
_rate_limit_hits: int = 0
_extraction_total: int = 0
_extraction_needs_clarification: int = 0
_extraction_without_clarification: int = 0

# Paths counted for feature usage rates (normalized keys)
FEATURE_PATHS = {
    "compare": "/api/vehicles/compare",
    "listing_analyze": "/api/listings/analyze",
    "knowledge_ask": "/api/knowledge/ask",
    "buying_advice": "/api/advice/ask",
    "maintenance": "/api/vehicles/maintenance",
    "search": "/api/vehicles/search",
    "recommend": "/api/vehicles/recommend",
    "extract": "/api/chat/extract",
}


def _ensure_started(started_at: float) -> None:
    global _started_at_monotonic
    if _started_at_monotonic == 0.0:
        _started_at_monotonic = started_at


def normalize_path(path: str) -> str:
    """Collapse dynamic segments for stable endpoint keys."""
    if path.startswith("/api/vehicles/search"):
        return "/api/vehicles/search"
    if path.startswith("/api/chat/"):
        return path.rstrip("/") or path
    return path.split("?")[0]


def record_request(
    *,
    path: str,
    status_code: int,
    duration_ms: int,
    started_at_monotonic: float,
) -> None:
    _ensure_started(started_at_monotonic)
    key = normalize_path(path)
    with _lock:
        stats = _endpoint_stats.setdefault(key, EndpointStats())
        stats.count += 1
        stats.total_duration_ms += max(0, duration_ms)
        if status_code >= 400:
            stats.error_count += 1


def record_search_outcome(*, path: str, total: int) -> None:
    key = normalize_path(path)
    with _lock:
        stats = _endpoint_stats.setdefault(key, EndpointStats())
        if total > 0:
            stats.with_results += 1
        else:
            stats.empty_results += 1


def record_extraction(*, needs_clarification: bool) -> None:
    global _extraction_total, _extraction_needs_clarification
    global _extraction_without_clarification
    with _lock:
        _extraction_total += 1
        if needs_clarification:
            _extraction_needs_clarification += 1
        else:
            _extraction_without_clarification += 1


def record_llm_usage(
    *,
    operation: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    approx_cost_usd: float,
    conversation_id: Optional[str] = None,
) -> None:
    with _lock:
        _llm.call_count += 1
        _llm.prompt_tokens += prompt_tokens
        _llm.completion_tokens += completion_tokens
        _llm.total_tokens += total_tokens
        _llm.approx_cost_usd += approx_cost_usd
        _llm.by_operation[operation] = _llm.by_operation.get(operation, 0) + 1
        if conversation_id:
            _llm.cost_by_conversation[conversation_id] = (
                _llm.cost_by_conversation.get(conversation_id, 0.0) + approx_cost_usd
            )


def record_llm_failure(*, operation: str) -> None:
    with _lock:
        _llm.failure_count += 1
        key = f"{operation}:failed"
        _llm.by_operation[key] = _llm.by_operation.get(key, 0) + 1


def record_rate_limit_hit() -> None:
    global _rate_limit_hits
    with _lock:
        _rate_limit_hits += 1


def reset_metrics() -> None:
    """For tests only."""
    global _started_at_monotonic, _rate_limit_hits
    global _extraction_total, _extraction_needs_clarification
    global _extraction_without_clarification
    with _lock:
        _started_at_monotonic = 0.0
        _endpoint_stats.clear()
        _llm.call_count = 0
        _llm.failure_count = 0
        _llm.prompt_tokens = 0
        _llm.completion_tokens = 0
        _llm.total_tokens = 0
        _llm.approx_cost_usd = 0.0
        _llm.by_operation.clear()
        _llm.cost_by_conversation.clear()
        _rate_limit_hits = 0
        _extraction_total = 0
        _extraction_needs_clarification = 0
        _extraction_without_clarification = 0


def snapshot() -> MetricsSnapshot:
    import time

    with _lock:
        return MetricsSnapshot(
            started_at_monotonic=_started_at_monotonic or time.perf_counter(),
            endpoint_stats={
                k: EndpointStats(
                    count=v.count,
                    error_count=v.error_count,
                    total_duration_ms=v.total_duration_ms,
                    with_results=v.with_results,
                    empty_results=v.empty_results,
                )
                for k, v in _endpoint_stats.items()
            },
            llm=LlmStats(
                call_count=_llm.call_count,
                failure_count=_llm.failure_count,
                prompt_tokens=_llm.prompt_tokens,
                completion_tokens=_llm.completion_tokens,
                total_tokens=_llm.total_tokens,
                approx_cost_usd=_llm.approx_cost_usd,
                by_operation=dict(_llm.by_operation),
                cost_by_conversation=dict(_llm.cost_by_conversation),
            ),
            rate_limit_hits=_rate_limit_hits,
            extraction_total=_extraction_total,
            extraction_needs_clarification=_extraction_needs_clarification,
            extraction_without_clarification=_extraction_without_clarification,
        )
