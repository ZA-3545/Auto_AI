"""Structured logging setup (Phase 8 / PLANNING.md Section I)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line — easy to ship later without a full APM stack."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "conversation_id",
            "provider",
            "model",
            "event",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "approx_cost_usd",
            "client_ip",
            "field_message",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if hasattr(record, "field_message"):
            payload["detail"] = record.field_message
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(*, debug: bool = False) -> None:
    root = logging.getLogger()
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        # Avoid duplicate handlers on reload
        for h in list(root.handlers):
            root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Quiet noisy libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not debug else logging.INFO
    )


def get_logger(name: str = "autoai") -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    # Avoid colliding with LogRecord reserved attributes (e.g. "message")
    safe = {}
    for key, value in fields.items():
        if key in {"message", "msg", "args", "name", "levelname", "levelno"}:
            safe[f"field_{key}"] = value
        else:
            safe[key] = value
    extra = {"event": event, **safe}
    logger.info(event, extra=extra)


def estimate_cost_usd(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> float:
    """
    Rough USD estimate for logging only — not billing-accurate.

    Defaults approximate gpt-4o-mini / similar mini chat rates.
    """
    # per 1M tokens
    input_per_m = 0.15
    output_per_m = 0.60
    lowered = model.lower()
    if "embedding" in lowered:
        input_per_m = 0.02
        output_per_m = 0.0
    return round(
        (prompt_tokens / 1_000_000) * input_per_m
        + (completion_tokens / 1_000_000) * output_per_m,
        6,
    )


def log_llm_usage(
    *,
    provider: str,
    model: str,
    operation: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    conversation_id: Optional[str] = None,
) -> None:
    pt = prompt_tokens or 0
    ct = completion_tokens or 0
    tt = total_tokens if total_tokens is not None else pt + ct
    cost = estimate_cost_usd(prompt_tokens=pt, completion_tokens=ct, model=model)
    from app.core.metrics_collector import record_llm_usage as record_llm_metric

    record_llm_metric(
        operation=operation,
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
        approx_cost_usd=cost,
        conversation_id=conversation_id,
    )
    log_event(
        get_logger("autoai.llm"),
        "llm_usage",
        provider=provider,
        model=model,
        path=operation,
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
        approx_cost_usd=cost,
        conversation_id=conversation_id,
    )
