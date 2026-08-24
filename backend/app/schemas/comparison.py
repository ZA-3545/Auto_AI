"""Pydantic schemas for vehicle comparison API (Phase 5)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.extraction import ExtractedRequirements
from app.schemas.vehicle import VehicleRead


class DataReliability(str, Enum):
    """How trustworthy the factor value is (PLANNING.md Section H)."""

    fact = "fact"  # Direct DB field
    inference = "inference"  # Derived heuristically from DB fields
    unknown = "unknown"  # No reliable data in catalog


class FactorValue(BaseModel):
    vehicle_id: int
    display: str
    numeric: Optional[float] = None  # Used for deterministic winner selection


class FactorComparison(BaseModel):
    factor: str
    reliability: DataReliability
    values: list[FactorValue]
    winner_vehicle_id: Optional[int] = None
    note: Optional[str] = None


class BestForConclusion(BaseModel):
    category: str
    vehicle_id: int
    vehicle_label: str
    reason: str


class CompareRequest(BaseModel):
    vehicle_ids: list[int] = Field(min_length=2, max_length=4)
    requirements: ExtractedRequirements
    include_narrative: bool = True


class CompareResponse(BaseModel):
    vehicles: list[VehicleRead]
    factors: list[FactorComparison]
    best_for: list[BestForConclusion]
    best_overall: BestForConclusion
    narrative: Optional[str] = None
    narrative_source: str = Field(
        description="'llm' if phrased by provider, else 'template'"
    )
