"""User-facing error helpers (Phase 8 — no raw stack traces to clients)."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.ai.base import AIProviderError

FRIENDLY_LLM_UNAVAILABLE = (
    "We couldn't process that right now, please try again."
)

FRIENDLY_INTERNAL = (
    "Something went wrong on our side. Please try again in a moment."
)

FRIENDLY_RATE_LIMITED = (
    "Too many requests. Please wait a moment and try again."
)


def map_provider_http_status(message: str) -> int:
    lowered = message.lower()
    if (
        "insufficient_quota" in lowered
        or "exceeded your current quota" in lowered
        or "credit/quota" in lowered
        or "payment required" in lowered
        or "rate limit" in lowered
    ):
        return 429
    if (
        "invalid_api_key" in lowered
        or "incorrect api key" in lowered
        or "rejected the api key" in lowered
    ):
        return 401
    if "api_key is missing" in lowered:
        return 503
    if "must not be empty" in lowered or "empty" in lowered:
        return 400
    if "timeout" in lowered or "timed out" in lowered:
        return 504
    return 502


def friendly_provider_detail(exc: AIProviderError, *, status_code: int) -> str:
    """Prefer actionable short messages; never dump stack traces."""
    raw = str(exc).strip()
    if status_code in (401, 429, 503):
        # Keep concise provider-facing guidance already written in AIProviderError
        return raw or FRIENDLY_LLM_UNAVAILABLE
    return FRIENDLY_LLM_UNAVAILABLE


def http_from_provider(exc: AIProviderError) -> HTTPException:
    status = map_provider_http_status(str(exc))
    return HTTPException(
        status_code=status,
        detail=friendly_provider_detail(exc, status_code=status),
    )


def register_exception_handlers(app) -> None:
    """Attach global handlers so clients never see raw traces."""

    @app.exception_handler(AIProviderError)
    async def ai_provider_handler(
        request: Request, exc: AIProviderError
    ) -> JSONResponse:
        status = map_provider_http_status(str(exc))
        return JSONResponse(
            status_code=status,
            content={
                "detail": friendly_provider_detail(exc, status_code=status),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Compact 422 without dumping huge body internals
        errors = []
        for err in exc.errors()[:8]:
            loc = " → ".join(str(x) for x in err.get("loc", ()))
            errors.append({"field": loc, "message": err.get("msg", "Invalid value")})
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Invalid request. Please check your input and try again.",
                "errors": errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if not isinstance(detail, str):
            detail = str(detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        # Logged by middleware / logging; client gets a safe message only.
        import logging

        logging.getLogger("autoai.errors").exception(
            "Unhandled error on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": FRIENDLY_INTERNAL},
        )
