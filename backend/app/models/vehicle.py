"""Vehicle ORM model for the Pakistani automotive demo catalog."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Index, Text
from sqlmodel import Field, SQLModel


class Condition(str, Enum):
    new = "new"
    used = "used"


class Transmission(str, Enum):
    automatic = "automatic"
    manual = "manual"


class BodyType(str, Enum):
    sedan = "sedan"
    hatchback = "hatchback"
    suv = "suv"
    crossover = "crossover"
    pickup = "pickup"
    van = "van"
    coupe = "coupe"


class FuelType(str, Enum):
    petrol = "petrol"
    diesel = "diesel"
    hybrid = "hybrid"
    electric = "electric"
    cng = "cng"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Vehicle(SQLModel, table=True):
    """
    Main vehicle inventory table (Phase 2).

    Intentionally denormalized for the MVP demo. A separate
    `vehicle_variants` table can be introduced later if needed.
    """

    __tablename__ = "vehicles"
    __table_args__ = (Index("ix_vehicles_make_model", "make", "model"),)

    id: Optional[int] = Field(default=None, primary_key=True)

    make: str = Field(max_length=64, index=True)
    model: str = Field(max_length=128, index=True)
    year: int = Field(ge=1990, le=2100, index=True)

    # Price in PKR (whole rupees)
    price: int = Field(ge=0, index=True)

    city: str = Field(max_length=64, index=True)
    condition: Condition = Field(sa_column=Column(Text, nullable=False, index=True))
    transmission: Transmission = Field(
        sa_column=Column(Text, nullable=False, index=True)
    )
    body_type: BodyType = Field(sa_column=Column(Text, nullable=False, index=True))
    fuel_type: FuelType = Field(sa_column=Column(Text, nullable=False, index=True))

    # Engine capacity in cc (e.g. 1300, 1800). Null for EV where not applicable.
    engine_capacity: Optional[int] = Field(default=None, ge=0)

    # Odometer reading in kilometres
    mileage_km: int = Field(default=0, ge=0)

    # Approximate fuel average in km/l (higher is better). Null for EV.
    fuel_average_kmpl: Optional[float] = Field(default=None, ge=0)

    # Relative resale strength for Pakistani market (1 = poor, 5 = excellent)
    resale_rating: int = Field(default=3, ge=1, le=5)

    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=_utc_now,
        ),
    )
