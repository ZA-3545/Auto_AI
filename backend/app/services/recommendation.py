"""
Recommendation orchestration — search (Phase 2) + scoring (Phase 4).

No LLM involvement. Deterministic end-to-end within the backend.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.vehicle import BodyType, Condition, Transmission
from app.schemas.extraction import ExtractedRequirements
from app.schemas.recommendation import RecommendResponse
from app.schemas.vehicle import SortBy, SortOrder, VehicleSearchParams
from app.services.recommendation_engine import rank_vehicles
from app.services.vehicle_search import search_vehicles

# Max candidates fetched before scoring (pagination applies after ranking)
CANDIDATE_POOL_LIMIT = 100


def requirements_to_search_params(
    requirements: ExtractedRequirements,
) -> VehicleSearchParams:
    """Map extracted requirements to Phase 2 search filters."""
    body_type = None
    if requirements.body_type:
        try:
            body_type = BodyType(requirements.body_type.lower())
        except ValueError:
            body_type = None

    condition = None
    if requirements.condition is not None:
        condition = Condition(requirements.condition.value)

    transmission = None
    if requirements.transmission is not None:
        transmission = Transmission(requirements.transmission.value)

    return VehicleSearchParams(
        budget_min=requirements.budget_min,
        budget_max=requirements.budget_max,
        city=requirements.city,
        condition=condition,
        transmission=transmission,
        body_type=body_type,
        fuel_priority=bool(requirements.fuel_priority),
        sort_by=SortBy.price,
        sort_order=SortOrder.asc,
        limit=CANDIDATE_POOL_LIMIT,
        offset=0,
    )


def recommend_vehicles(
    db: Session,
    requirements: ExtractedRequirements,
    *,
    limit: int = 20,
) -> RecommendResponse:
    """
    Search candidate vehicles, score deterministically, return ranked results.

    Raises ValueError if requirements need clarification before search.
    """
    if requirements.needs_clarification:
        question = requirements.clarification_question or "Please clarify your requirements."
        raise ValueError(question)

    search_params = requirements_to_search_params(requirements)
    search_result = search_vehicles(db, search_params)

    ranked = rank_vehicles(list(search_result.items), requirements)
    items = ranked[:limit]

    return RecommendResponse(
        total_candidates=search_result.total,
        requirements=requirements,
        items=items,
    )
