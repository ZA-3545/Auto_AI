"""Chat / AI orchestration routes — extraction + conversation memory."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError
from app.core.database import get_db
from app.core.errors import FRIENDLY_INTERNAL, http_from_provider
from app.core.logging_config import get_logger, log_event
from app.core.metrics_collector import record_extraction
from app.schemas.extraction import (
    ConversationCreateResponse,
    ExtractRequest,
    ExtractResponse,
    ResetRequest,
    ResetResponse,
)
from app.services.conversation_memory import empty_requirements
from app.services.conversation_service import (
    create_conversation,
    extract_with_memory,
    reset_conversation,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger("autoai.chat")


@router.post("/conversations", response_model=ConversationCreateResponse)
def create_chat_conversation(db: Session = Depends(get_db)) -> ConversationCreateResponse:
    """Create an empty anonymous conversation session."""
    try:
        conversation = create_conversation(db)
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "conversation_create_failed", message=str(exc)[:200])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc
    return ConversationCreateResponse(
        conversation_id=conversation.id,
        requirements=empty_requirements(),
    )


@router.post("/extract", response_model=ExtractResponse)
def extract_chat_requirements(
    body: ExtractRequest,
    db: Session = Depends(get_db),
) -> ExtractResponse:
    """
    Extract structured requirements and merge into conversation memory.

    Previous session fields are retained unless reset (button / phrase).
    """
    try:
        result = extract_with_memory(
            db,
            body.message,
            conversation_id=body.conversation_id,
            reset=body.reset,
        )
        record_extraction(
            needs_clarification=bool(result.requirements.needs_clarification),
        )
        log_event(
            logger,
            "extract_ok",
            conversation_id=result.conversation_id,
            provider=result.provider,
            model=result.model,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIProviderError as exc:
        log_event(logger, "extract_llm_failed", message=str(exc)[:300])
        raise http_from_provider(exc) from exc
    except Exception as exc:  # noqa: BLE001
        log_event(logger, "extract_failed", message=str(exc)[:300])
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc


@router.post("/reset", response_model=ResetResponse)
def reset_chat_conversation(
    body: ResetRequest,
    db: Session = Depends(get_db),
) -> ResetResponse:
    """Clear stored requirements for a conversation (Section G reset)."""
    try:
        conversation = reset_conversation(db, body.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=FRIENDLY_INTERNAL) from exc

    return ResetResponse(
        conversation_id=conversation.id,
        requirements=empty_requirements(),
    )
