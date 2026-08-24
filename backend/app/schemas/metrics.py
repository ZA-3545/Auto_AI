"""Schemas for evaluation metrics dashboard (PLANNING.md K.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

MetricStatus = Literal["computed", "not_available", "manual"]


class MetricCard(BaseModel):
    """Single K.1 metric for the admin dashboard."""

    id: str
    label: str
    status: MetricStatus
    value: Optional[str | float | int] = None
    unit: Optional[str] = None
    detail: Optional[str] = None
    note: Optional[str] = None


class EndpointLatencyRow(BaseModel):
    path: str
    request_count: int
    error_count: int
    avg_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None


class AdminMetricsResponse(BaseModel):
    generated_at: datetime
    disclaimer: str = (
        "Internal PoC metrics only — in-process counters reset on server restart. "
        "Not affiliated with PakWheels. Access control required before public deployment."
    )
    metrics: list[MetricCard]
    endpoint_latency: list[EndpointLatencyRow]
    llm_by_operation: dict[str, int] = Field(default_factory=dict)
    conversations_with_llm_cost: int = 0
