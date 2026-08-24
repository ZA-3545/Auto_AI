"""Pydantic schemas for vehicle search API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.vehicle import BodyType, Condition, FuelType, Transmission


class SortBy(str, Enum):
    price = "price"
    year = "year"
    mileage = "mileage"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class VehicleRead(BaseModel):
    id: int
    make: str
    model: str
    year: int
    price: int
    city: str
    condition: Condition
    transmission: Transmission
    body_type: BodyType
    fuel_type: FuelType
    engine_capacity: Optional[int] = None
    mileage_km: int
    fuel_average_kmpl: Optional[float] = None
    resale_rating: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VehicleSearchParams(BaseModel):
    budget_min: Optional[int] = Field(default=None, ge=0)
    budget_max: Optional[int] = Field(default=None, ge=0)
    city: Optional[str] = None
    condition: Optional[Condition] = None
    transmission: Optional[Transmission] = None
    body_type: Optional[BodyType] = None
    fuel_type: Optional[FuelType] = None
    # When true, prefer / require vehicles with better fuel economy (sorted by
    # fuel_average_kmpl desc as a secondary signal; still a deterministic filter
    # bias via sort default — see search service).
    fuel_priority: bool = False
    sort_by: SortBy = SortBy.price
    sort_order: SortOrder = SortOrder.asc
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class VehicleSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[VehicleRead]
