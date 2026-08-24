"""Listing analyzer orchestration — LLM extract + deterministic backend judgment."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.core.llm_retry import with_llm_retry
from app.schemas.listing_analysis import (
    AnalyzeListingResponse,
    ExtractedListing,
)
from app.services.listing_analysis_engine import (
    assess_price,
    build_missing_information,
    build_notes,
    build_red_flags,
    find_similar_vehicles,
    seller_questions,
    template_advisor_summary,
)


def analyze_listing(
    session: Session,
    listing_text: str,
    *,
    provider: Optional[AIProvider] = None,
    include_advisor_summary: bool = True,
    extracted_override: Optional[ExtractedListing] = None,
) -> AnalyzeListingResponse:
    """
    analyze_listing tool (PLANNING.md Section D).

    1) LLM (or override) extracts structured fields only.
    2) Backend compares price to DB comps and builds labeled claims.
    """
    text = listing_text.strip()
    if not text:
        raise AIProviderError("Listing text must not be empty.")

    ai = provider or get_ai_provider()

    if extracted_override is not None:
        extracted = ExtractedListing.model_validate(extracted_override.model_dump())
    else:
        extracted = with_llm_retry(
            "extract_listing",
            lambda: ai.extract_listing(text),
        )
        extracted = ExtractedListing.model_validate(extracted.model_dump())

    comps = find_similar_vehicles(session, extracted)
    price = assess_price(extracted, comps)
    red_flags = build_red_flags(text, extracted, price)
    missing = build_missing_information(extracted)
    notes = build_notes(extracted, price)
    questions = seller_questions()

    summary_source = "template"
    summary = template_advisor_summary(extracted, price, red_flags, missing)

    if include_advisor_summary:
        try:
            summary = with_llm_retry(
                "phrase_listing_summary",
                lambda: ai.phrase_listing_summary(
                    extracted=extracted,
                    price_assessment=price,
                    red_flags=red_flags,
                    missing_information=missing,
                ),
            )
            summary_source = "llm"
        except (AIProviderError, NotImplementedError):
            summary_source = "template"

    return AnalyzeListingResponse(
        extracted=extracted,
        price_assessment=price,
        red_flags=red_flags,
        missing_information=missing,
        notes=notes,
        seller_questions=questions,
        advisor_summary=summary,
        advisor_summary_source=summary_source,
        provider=ai.name,
        model=ai.model_name,
    )
