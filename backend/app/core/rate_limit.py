"""Simple in-memory rate limiting (Phase 8 / PLANNING.md Section I)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.errors import FRIENDLY_RATE_LIMITED


class SlidingWindowRateLimiter:
    """Per-key sliding window counter (process-local — fine for single-instance PoC)."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max(1, max_requests)
        self.window_seconds = max(1.0, float(window_seconds))
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.max_requests:
                raise HTTPException(status_code=429, detail=FRIENDLY_RATE_LIMITED)
            q.append(now)


# Shared limiter for AI-adjacent endpoints
_ai_limiter = SlidingWindowRateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60.0,
)

# Paths that should be rate-limited (prefix match)
RATE_LIMITED_PREFIXES = (
    "/api/chat/extract",
    "/api/chat/conversations",
    "/api/chat/reset",
    "/api/vehicles/compare",
    "/api/vehicles/maintenance",
    "/api/listings/analyze",
    "/api/knowledge/ask",
    "/api/advice/ask",
)


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(request: Request) -> None:
    path = request.url.path
    if not any(path.startswith(p) for p in RATE_LIMITED_PREFIXES):
        return
    _ai_limiter.check(f"{client_key(request)}:{path}")


def rate_limit_dependency() -> Callable[[Request], None]:
    def _dep(request: Request) -> None:
        enforce_rate_limit(request)

    return _dep
