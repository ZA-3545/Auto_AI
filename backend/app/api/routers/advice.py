"""AI buying advice API — decision guidance only (not vehicle search)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError
from app.core.database import get_db
from app.core.errors import FRIENDLY_INTERNAL, http_from_provider
from app.core.logging_config import get_logger, log_event
from app.schemas.advice import AdviceAskRequest, AdviceAskResponse
from app.services.advice_qa import ask_buying_advice

router = APIRouter(prefix="/api/advice", tags=["advice"])
logger = get_logger("autoai.advice")


@router.post("/ask", response_model=AdviceAskResponse)
def ask_buying_advice_endpoint(
    body: AdviceAskRequest,
    db: Session = Depends(get_db),
) -> AdviceAskResponse:
    """
    Ask a general car-buying decision question (Section O RAG).

    Retrieves buying-advice knowledge chunks via pgvector, then answers grounded
    in those chunks only. Does not search inventory or analyze listings.
    """
    try:
        return ask_buying_advice(db, body.question)
    except AIProviderError as exc:
        log_event(logger, "advice_llm_failed", message=str(exc)[:300])
        raise http_from_provider(exc) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "advice_ask_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc
