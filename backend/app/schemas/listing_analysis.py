"""Schemas for listing analyzer (PLANNING.md Sections D & H)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.comparison import DataReliability


class PriceRelative(str, Enum):
    """Deterministic relative price vs reference dataset."""

    higher = "higher"
    in_line = "in_line"
    lower = "lower"
    insufficient_data = "insufficient_data"


class ExtractedListing(BaseModel):
    """
    Structured fields extracted from pasted listing text.

    LLM fills this schema only — it must NOT judge price or invent certainty
    about accident history / mechanical condition.
    """

    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1990, le=2100)
    asking_price: Optional[int] = Field(
        default=None,
        ge=0,
        description="Asking price in whole PKR (convert lakh/crore).",
    )
    mileage_km: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    condition: Optional[str] = None
    engine_capacity: Optional[int] = Field(default=None, ge=0)
    color: Optional[str] = None
    # Free-text echoes of what the listing claimed (null if not mentioned)
    ownership_text: Optional[str] = None
    accident_text: Optional[str] = None
    service_history_text: Optional[str] = None
    other_details: Optional[str] = None
    # Explicit claim flags — presence of a claim is not proof of truth
    claims_accident_free: bool = False
    claims_original_paint: bool = False
    claims_service_history: bool = False
    mentions_owners: bool = False


class LabeledClaim(BaseModel):
    """A single analysis note with mandatory Section H reliability label."""

    text: str
    reliability: DataReliability
    category: str = Field(
        description="red_flag | missing_information | note | negotiation"
    )


class PriceAssessment(BaseModel):
    relative: PriceRelative
    summary: str
    reliability: DataReliability
    dataset_disclaimer: str
    asking_price: Optional[int] = None
    reference_median: Optional[int] = None
    reference_count: int = 0
    reference_min: Optional[int] = None
    reference_max: Optional[int] = None
    similar_vehicle_ids: list[int] = Field(default_factory=list)


class AnalyzeListingRequest(BaseModel):
    listing_text: str = Field(min_length=1, max_length=20_000)
    include_advisor_summary: bool = True


class AnalyzeListingResponse(BaseModel):
    extracted: ExtractedListing
    price_assessment: PriceAssessment
    red_flags: list[LabeledClaim]
    missing_information: list[LabeledClaim]
    notes: list[LabeledClaim]
    seller_questions: list[str]
    advisor_summary: Optional[str] = None
    advisor_summary_source: str = Field(
        description="'llm' if phrased by provider, else 'template'"
    )
    provider: str
    model: str
