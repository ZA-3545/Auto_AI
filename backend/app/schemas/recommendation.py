"""Pydantic schemas for recommendation API (Phase 4)."""

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.extraction import ExtractedRequirements
from app.schemas.vehicle import VehicleRead


class FactorScores(BaseModel):
    """Per-factor scores (0–100) for transparency."""

    budget_fit: float
    purpose_suitability: float
    fuel_economy: float
    resale: float
    mileage_condition: float


class RecommendedVehicle(BaseModel):
    vehicle: VehicleRead
    match_score: float = Field(ge=0, le=100, description="Weighted match score out of 100")
    factor_scores: FactorScores
    explanation: str


class RecommendRequest(BaseModel):
    requirements: ExtractedRequirements
    limit: int = Field(default=20, ge=1, le=100)


class RecommendResponse(BaseModel):
    total_candidates: int
    requirements: ExtractedRequirements
    items: list[RecommendedVehicle]
