"""Listing analyzer API — extract + deterministic price/red-flag analysis."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError
from app.core.database import get_db
from app.core.errors import FRIENDLY_INTERNAL, http_from_provider
from app.core.logging_config import get_logger, log_event
from app.schemas.listing_analysis import AnalyzeListingRequest, AnalyzeListingResponse
from app.services.listing_analysis import analyze_listing

router = APIRouter(prefix="/api/listings", tags=["listings"])
logger = get_logger("autoai.listings")


@router.post("/analyze", response_model=AnalyzeListingResponse)
def analyze_listing_endpoint(
    body: AnalyzeListingRequest,
    db: Session = Depends(get_db),
) -> AnalyzeListingResponse:
    """
    Analyze a pasted listing (PLANNING.md Sections D & H).

    LLM extracts structured fields; price assessment and labeled claims are
    deterministic backend logic against the reference vehicle catalog.
    """
    try:
        return analyze_listing(
            db,
            body.listing_text,
            include_advisor_summary=body.include_advisor_summary,
        )
    except AIProviderError as exc:
        log_event(logger, "analyze_llm_failed", message=str(exc)[:300])
        raise http_from_provider(exc) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "analyze_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc
