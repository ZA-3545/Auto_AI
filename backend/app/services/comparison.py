"""Comparison orchestration — DB fetch + deterministic engine + optional LLM phrasing."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from sqlmodel import select

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.core.llm_retry import with_llm_retry
from app.models.vehicle import Vehicle
from app.schemas.comparison import CompareResponse
from app.schemas.extraction import ExtractedRequirements
from app.schemas.vehicle import VehicleRead
from app.services.comparison_engine import (
    build_best_for_conclusions,
    build_factor_comparisons,
    build_template_narrative,
    compute_best_overall,
)


def fetch_vehicles_by_ids(db: Session, vehicle_ids: list[int]) -> list[Vehicle]:
    """Load vehicles from DB in the requested order. Raises ValueError if any missing."""
    unique_ids = list(dict.fromkeys(vehicle_ids))
    if len(unique_ids) < 2:
        raise ValueError("At least two distinct vehicle IDs are required.")
    if len(unique_ids) > 4:
        raise ValueError("Compare at most 4 vehicles at a time.")

    rows = list(db.execute(select(Vehicle).where(Vehicle.id.in_(unique_ids))).scalars().all())
    by_id = {v.id: v for v in rows}
    missing = [vid for vid in unique_ids if vid not in by_id]
    if missing:
        raise ValueError(f"Vehicles not found: {missing}")

    return [by_id[vid] for vid in unique_ids]


def compare_vehicles(
    db: Session,
    vehicle_ids: list[int],
    requirements: ExtractedRequirements,
    *,
    include_narrative: bool = True,
    provider: Optional[AIProvider] = None,
) -> CompareResponse:
    """
    Deterministic factor comparison from DB records.

    LLM (if available) only phrases the narrative — never invents factor data.
    """
    vehicles = fetch_vehicles_by_ids(db, vehicle_ids)
    factors = build_factor_comparisons(vehicles, requirements)
    best_for = build_best_for_conclusions(vehicles, factors)
    best_overall = compute_best_overall(vehicles, factors, requirements)

    narrative: Optional[str] = None
    narrative_source = "template"

    if include_narrative:
        template = build_template_narrative(vehicles, best_for, best_overall)
        narrative = template
        if provider is None:
            try:
                provider = get_ai_provider()
            except AIProviderError:
                provider = None

        if provider is not None:
            try:
                narrative = with_llm_retry(
                    "phrase_comparison",
                    lambda: provider.phrase_comparison(
                        vehicles=[VehicleRead.model_validate(v) for v in vehicles],
                        factors=factors,
                        best_for=best_for,
                        best_overall=best_overall,
                        requirements=requirements,
                    ),
                )
                narrative_source = "llm"
            except (AIProviderError, NotImplementedError, AttributeError):
                narrative = template
                narrative_source = "template"

    return CompareResponse(
        vehicles=[VehicleRead.model_validate(v) for v in vehicles],
        factors=factors,
        best_for=best_for,
        best_overall=best_overall,
        narrative=narrative,
        narrative_source=narrative_source,
    )
