"""HTTP middleware — request logging + rate limits + metrics."""

from __future__ import annotations

import json
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.errors import FRIENDLY_RATE_LIMITED
from app.core.logging_config import get_logger, log_event
from app.core.metrics_collector import (
    FEATURE_PATHS,
    normalize_path,
    record_rate_limit_hit,
    record_request,
    record_search_outcome,
)
from app.core.rate_limit import RATE_LIMITED_PREFIXES, SlidingWindowRateLimiter, client_key

logger = get_logger("autoai.http")

_OUTCOME_PATHS = {
    FEATURE_PATHS["search"],
    FEATURE_PATHS["recommend"],
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._limiter = SlidingWindowRateLimiter(
            max_requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60.0,
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        path = request.url.path
        method = request.method
        ip = client_key(request)

        if any(path.startswith(p) for p in RATE_LIMITED_PREFIXES):
            try:
                self._limiter.check(f"{ip}:{path}")
            except Exception as exc:
                from fastapi import HTTPException

                if isinstance(exc, HTTPException) and exc.status_code == 429:
                    record_rate_limit_hit()
                    log_event(
                        logger,
                        "rate_limited",
                        request_id=request_id,
                        path=path,
                        method=method,
                        client_ip=ip,
                        status_code=429,
                    )
                    return JSONResponse(
                        status_code=429,
                        content={"detail": FRIENDLY_RATE_LIMITED},
                        headers={"X-Request-Id": request_id},
                    )
                raise

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            record_request(
                path=path,
                status_code=500,
                duration_ms=duration_ms,
                started_at_monotonic=started,
            )
            log_event(
                logger,
                "request_error",
                request_id=request_id,
                path=path,
                method=method,
                client_ip=ip,
                duration_ms=duration_ms,
                status_code=500,
            )
            raise

        duration_ms = int((time.perf_counter() - started) * 1000)
        record_request(
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            started_at_monotonic=started,
        )

        norm = normalize_path(path)
        if (
            response.status_code == 200
            and norm in _OUTCOME_PATHS
            and "application/json" in response.headers.get("content-type", "")
        ):
            response = await self._tap_total_outcome(response, norm)

        response.headers["X-Request-Id"] = request_id
        log_event(
            logger,
            "request",
            request_id=request_id,
            path=path,
            method=method,
            client_ip=ip,
            duration_ms=duration_ms,
            status_code=response.status_code,
        )
        return response

    @staticmethod
    async def _tap_total_outcome(response: Response, path: str) -> Response:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        try:
            payload = json.loads(body)
            total = payload.get("total")
            if total is None:
                items = payload.get("items")
                if isinstance(items, list):
                    total = len(items)
            if isinstance(total, int):
                record_search_outcome(path=path, total=total)
        except (json.JSONDecodeError, TypeError):
            pass
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
