"""Vehicle search, recommendation & comparison API."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError
from app.core.database import get_db
from app.core.errors import FRIENDLY_INTERNAL, http_from_provider
from app.core.logging_config import get_logger, log_event
from app.models.vehicle import BodyType, Condition, FuelType, Transmission
from app.schemas.comparison import CompareRequest, CompareResponse
from app.schemas.maintenance import MaintenanceRequest, MaintenanceResponse
from app.schemas.recommendation import RecommendRequest, RecommendResponse
from app.schemas.vehicle import (
    SortBy,
    SortOrder,
    VehicleRead,
    VehicleSearchParams,
    VehicleSearchResponse,
)
from app.services.comparison import compare_vehicles
from app.services.maintenance import search_maintenance_info
from app.services.recommendation import recommend_vehicles
from app.services.vehicle_search import get_vehicle_by_id, search_vehicles

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])
logger = get_logger("autoai.vehicles")


@router.get("/search", response_model=VehicleSearchResponse)
def search_vehicles_endpoint(
    budget_min: Optional[int] = Query(default=None, ge=0),
    budget_max: Optional[int] = Query(default=None, ge=0),
    city: Optional[str] = Query(default=None, max_length=64),
    condition: Optional[Condition] = Query(default=None),
    transmission: Optional[Transmission] = Query(default=None),
    body_type: Optional[BodyType] = Query(default=None),
    fuel_type: Optional[FuelType] = Query(default=None),
    fuel_priority: bool = Query(default=False),
    sort_by: SortBy = Query(default=SortBy.price),
    sort_order: SortOrder = Query(default=SortOrder.asc),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> VehicleSearchResponse:
    """
    Search vehicles with deterministic filters, sort, and offset/limit pagination.

    No LLM is involved — filters map directly to SQL WHERE / ORDER BY clauses.
    """
    if (
        budget_min is not None
        and budget_max is not None
        and budget_min > budget_max
    ):
        raise HTTPException(
            status_code=422,
            detail="budget_min cannot be greater than budget_max.",
        )
    try:
        params = VehicleSearchParams(
            budget_min=budget_min,
            budget_max=budget_max,
            city=city,
            condition=condition,
            transmission=transmission,
            body_type=body_type,
            fuel_type=fuel_type,
            fuel_priority=fuel_priority,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        return search_vehicles(db, params)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "search_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle_detail_endpoint(
    vehicle_id: int,
    db: Session = Depends(get_db),
) -> VehicleRead:
    """
    get_car_details() — full catalog record for one vehicle (PLANNING.md Section D).

    Deterministic DB lookup only — no LLM.
    """
    try:
        return get_vehicle_by_id(db, vehicle_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "vehicle_detail_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc


@router.post("/recommend", response_model=RecommendResponse)
def recommend_vehicles_endpoint(
    body: RecommendRequest,
    db: Session = Depends(get_db),
) -> RecommendResponse:
    """
    Search + score + rank vehicles from structured requirements (Phase 4).

    Fully deterministic — no LLM. Uses Phase 2 search then weighted scoring
    per PLANNING.md Section E.
    """
    try:
        return recommend_vehicles(db, body.requirements, limit=body.limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "recommend_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc


@router.post("/compare", response_model=CompareResponse)
def compare_vehicles_endpoint(
    body: CompareRequest,
    db: Session = Depends(get_db),
) -> CompareResponse:
    """
    Factor-by-factor comparison from DB records (Phase 5).

    Winners and factor values are deterministic. Optional LLM narrative only
    rephrases the structured result — it never invents specs (PLANNING.md §B/F).
    """
    try:
        return compare_vehicles(
            db,
            body.vehicle_ids,
            body.requirements,
            include_narrative=body.include_narrative,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIProviderError as exc:
        # Narrative failures fall back inside the service; this is defensive.
        raise http_from_provider(exc) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "compare_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc


@router.post("/maintenance", response_model=MaintenanceResponse)
def maintenance_checklist_endpoint(
    body: MaintenanceRequest,
    db: Session = Depends(get_db),
) -> MaintenanceResponse:
    """
    search_maintenance_info() — general maintenance checklist (Section D).

    Accepts vehicle_id (DB lookup) or freeform description (LLM extract only).
    Checklist items are deterministic mileage/age rules plus optional RAG excerpts.
    """
    try:
        return search_maintenance_info(
            db,
            vehicle_id=body.vehicle_id,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIProviderError as exc:
        log_event(logger, "maintenance_llm_failed", message=str(exc)[:300])
        raise http_from_provider(exc) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "maintenance_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc
