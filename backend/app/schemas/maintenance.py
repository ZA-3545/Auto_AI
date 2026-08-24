"""Schemas for search_maintenance_info() tool (PLANNING.md Section D & H)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.comparison import DataReliability


MAINTENANCE_DISCLAIMER = (
    "This is general guidance based on typical maintenance intervals, not a "
    "substitute for a qualified mechanic's inspection. General educational "
    "information only — not professional mechanical advice. Independent proof "
    "of concept — not affiliated with PakWheels."
)


class ExtractedVehicleDescription(BaseModel):
    """
    Structured vehicle fields extracted from freeform text.

    LLM fills this schema only — it must NOT generate maintenance advice.
    """

    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1990, le=2100)
    mileage_km: Optional[int] = Field(default=None, ge=0)


class VehicleProfile(BaseModel):
    """Resolved vehicle used for checklist generation."""

    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    vehicle_id: Optional[int] = None
    source: Literal["database", "extracted"] = "extracted"


class MaintenanceItem(BaseModel):
    category: str
    item: str
    reason: str
    source: Literal["rule", "knowledge"] = "rule"
    reliability: DataReliability = DataReliability.inference


class KnowledgeExcerpt(BaseModel):
    title: str
    content: str
    similarity: float


class MaintenanceRequest(BaseModel):
    vehicle_id: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def exactly_one_source(self) -> "MaintenanceRequest":
        has_id = self.vehicle_id is not None
        has_text = bool(self.description and self.description.strip())
        if has_id and has_text:
            raise ValueError("Provide either vehicle_id or description, not both.")
        if not has_id and not has_text:
            raise ValueError("Provide vehicle_id or a freeform description.")
        return self


class MaintenanceResponse(BaseModel):
    vehicle: VehicleProfile
    checklist: list[MaintenanceItem]
    knowledge_excerpts: list[KnowledgeExcerpt]
    disclaimer: str = MAINTENANCE_DISCLAIMER
    extraction_provider: Optional[str] = None
    extraction_model: Optional[str] = None
