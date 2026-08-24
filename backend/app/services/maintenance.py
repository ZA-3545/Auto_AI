"""search_maintenance_info() orchestration — extract, rules, RAG excerpts."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session
from sqlmodel import select

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.core.llm_retry import with_llm_retry
from app.models.vehicle import Vehicle
from app.schemas.comparison import DataReliability
from app.schemas.maintenance import (
    ExtractedVehicleDescription,
    KnowledgeExcerpt,
    MaintenanceItem,
    MaintenanceResponse,
    VehicleProfile,
)
from app.services.knowledge_retrieval import retrieve_knowledge_chunks
from app.services.maintenance_engine import build_maintenance_checklist

MAINTENANCE_RAG_QUERY = (
    "car maintenance service intervals oil change brake pads timing belt "
    "transmission fluid coolant inspection Pakistan"
)

# Slightly lower threshold — maintenance chunks may be broader educational text
MAINTENANCE_RAG_MIN_SIMILARITY = 0.22


def _profile_from_vehicle(vehicle: Vehicle) -> VehicleProfile:
    return VehicleProfile(
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        mileage_km=vehicle.mileage_km,
        vehicle_id=vehicle.id,
        source="database",
    )


def _profile_from_extracted(
    extracted: ExtractedVehicleDescription,
) -> VehicleProfile:
    return VehicleProfile(
        make=extracted.make,
        model=extracted.model,
        year=extracted.year,
        mileage_km=extracted.mileage_km,
        vehicle_id=None,
        source="extracted",
    )


def _load_vehicle(session: Session, vehicle_id: int) -> Vehicle:
    vehicle = session.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id)
    ).scalar_one_or_none()
    if vehicle is None:
        raise ValueError(f"Vehicle not found: id={vehicle_id}")
    return vehicle


def _retrieve_maintenance_knowledge(
    session: Session,
    provider: AIProvider,
) -> tuple[list[KnowledgeExcerpt], list[MaintenanceItem]]:
    """Reuse pgvector retrieval — separate from /api/knowledge/ask flow."""
    vectors = with_llm_retry(
        "maintenance_rag_embed",
        lambda: provider.embed_texts([MAINTENANCE_RAG_QUERY]),
    )
    if not vectors:
        return [], []

    retrieved = retrieve_knowledge_chunks(
        session,
        vectors[0],
        top_k=3,
        min_similarity=MAINTENANCE_RAG_MIN_SIMILARITY,
    )

    excerpts: list[KnowledgeExcerpt] = []
    knowledge_items: list[MaintenanceItem] = []

    for hit in retrieved:
        chunk = hit.chunk
        excerpts.append(
            KnowledgeExcerpt(
                title=chunk.title,
                content=chunk.content,
                similarity=round(float(hit.similarity), 4),
            )
        )
        knowledge_items.append(
            MaintenanceItem(
                category="Knowledge base",
                item=chunk.title,
                reason=chunk.content[:400]
                + ("…" if len(chunk.content) > 400 else ""),
                source="knowledge",
                reliability=DataReliability.inference,
            )
        )

    return excerpts, knowledge_items


def search_maintenance_info(
    session: Session,
    *,
    vehicle_id: Optional[int] = None,
    description: Optional[str] = None,
    provider: Optional[AIProvider] = None,
    profile_override: Optional[VehicleProfile] = None,
    skip_rag: bool = False,
) -> MaintenanceResponse:
    """
    search_maintenance_info tool (PLANNING.md Section D).

    1) Resolve vehicle profile from DB or LLM extraction.
    2) Deterministic mileage/age checklist.
    3) Optional RAG excerpts for general maintenance education.
    """
    ai = provider or get_ai_provider()
    extraction_provider: Optional[str] = None
    extraction_model: Optional[str] = None

    if profile_override is not None:
        profile = profile_override
    elif vehicle_id is not None:
        profile = _profile_from_vehicle(_load_vehicle(session, vehicle_id))
    elif description:
        extracted = with_llm_retry(
            "extract_vehicle_description",
            lambda: ai.extract_vehicle_description(description.strip()),
        )
        validated = ExtractedVehicleDescription.model_validate(
            extracted.model_dump()
        )
        profile = _profile_from_extracted(validated)
        extraction_provider = ai.name
        extraction_model = ai.model_name
    else:
        raise AIProviderError("Provide vehicle_id or description.")

    checklist = build_maintenance_checklist(profile)

    excerpts: list[KnowledgeExcerpt] = []
    if not skip_rag:
        try:
            excerpts, knowledge_items = _retrieve_maintenance_knowledge(session, ai)
            # Append knowledge titles as supplementary items (dedupe by item text)
            existing = {i.item for i in checklist}
            for ki in knowledge_items:
                if ki.item not in existing:
                    checklist.append(ki)
                    existing.add(ki.item)
        except (AIProviderError, NotImplementedError):
            excerpts = []
        except Exception:
            # RAG enrichment is optional (e.g. pgvector unavailable in test SQLite)
            excerpts = []

    return MaintenanceResponse(
        vehicle=profile,
        checklist=checklist,
        knowledge_excerpts=excerpts,
        extraction_provider=extraction_provider,
        extraction_model=extraction_model,
    )
