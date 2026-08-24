"""Deterministic vehicle search — no LLM involvement."""

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    SortBy,
    SortOrder,
    VehicleRead,
    VehicleSearchParams,
    VehicleSearchResponse,
)


def search_vehicles(db: Session, params: VehicleSearchParams) -> VehicleSearchResponse:
    """
    Filter and paginate vehicles using only SQL predicates and ordering.

    All logic is deterministic and unit-testable independently of any AI layer.
    """
    filters = []

    if params.budget_min is not None:
        filters.append(Vehicle.price >= params.budget_min)
    if params.budget_max is not None:
        filters.append(Vehicle.price <= params.budget_max)
    if params.city:
        filters.append(func.lower(Vehicle.city) == params.city.strip().lower())
    if params.condition is not None:
        filters.append(Vehicle.condition == params.condition.value)
    if params.transmission is not None:
        filters.append(Vehicle.transmission == params.transmission.value)
    if params.body_type is not None:
        filters.append(Vehicle.body_type == params.body_type.value)
    if params.fuel_type is not None:
        filters.append(Vehicle.fuel_type == params.fuel_type.value)

    count_stmt = select(func.count()).select_from(Vehicle)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int(db.execute(count_stmt).scalar_one())

    stmt = select(Vehicle)
    if filters:
        stmt = stmt.where(*filters)

    # Primary sort from query params
    sort_column = {
        SortBy.price: Vehicle.price,
        SortBy.year: Vehicle.year,
        SortBy.mileage: Vehicle.mileage_km,
    }[params.sort_by]

    primary = sort_column.asc() if params.sort_order == SortOrder.asc else sort_column.desc()

    # fuel_priority: secondary preference for better fuel economy (higher km/l first).
    # Nulls last so EVs / missing averages don't dominate when priority is set.
    if params.fuel_priority:
        stmt = stmt.order_by(
            primary,
            Vehicle.fuel_average_kmpl.desc().nulls_last(),
            Vehicle.id.asc(),
        )
    else:
        stmt = stmt.order_by(primary, Vehicle.id.asc())

    stmt = stmt.offset(params.offset).limit(params.limit)
    items = list(db.execute(stmt).scalars().all())

    return VehicleSearchResponse(
        total=total,
        limit=params.limit,
        offset=params.offset,
        items=items,
    )


def get_vehicle_by_id(db: Session, vehicle_id: int) -> VehicleRead:
    """
    get_car_details() — single vehicle lookup by primary key (PLANNING.md Section D).

    Pure deterministic DB read; no LLM.
    """
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id)
    ).scalar_one_or_none()
    if vehicle is None:
        raise ValueError(
            f"We couldn't find a vehicle with id {vehicle_id} in the demo catalog."
        )
    return VehicleRead.model_validate(vehicle)
