"""Knowledge RAG API — general automotive Q&A only (not vehicle search)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError
from app.core.database import get_db
from app.core.errors import FRIENDLY_INTERNAL, http_from_provider
from app.core.logging_config import get_logger, log_event
from app.schemas.knowledge import KnowledgeAskRequest, KnowledgeAskResponse
from app.services.knowledge_qa import ask_knowledge_question

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
logger = get_logger("autoai.knowledge")


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge_endpoint(
    body: KnowledgeAskRequest,
    db: Session = Depends(get_db),
) -> KnowledgeAskResponse:
    """
    Ask a general automotive knowledge question (Phase 6 RAG).

    Retrieves sample knowledge chunks via pgvector, then answers grounded in
    those chunks only. Does not search the vehicle catalog.
    """
    try:
        return ask_knowledge_question(db, body.question)
    except AIProviderError as exc:
        log_event(logger, "knowledge_llm_failed", message=str(exc)[:300])
        raise http_from_provider(exc) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "knowledge_ask_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc
