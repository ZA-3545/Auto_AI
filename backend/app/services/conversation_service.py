"""Session conversation service — persist and merge requirements across turns."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.models.conversation import Conversation, Message
from app.schemas.extraction import (
    ExtractedRequirements,
    ExtractResponse,
)
from app.services.conversation_memory import (
    empty_requirements,
    is_reset_message,
    merge_requirements,
    requirements_from_storage,
)
from app.services.requirement_extraction import extract_requirements


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_conversation(db: Session) -> Conversation:
    conversation = Conversation(
        id=str(uuid4()),
        requirements=empty_requirements().model_dump(),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    return db.get(Conversation, conversation_id)


def reset_conversation(db: Session, conversation_id: str) -> Conversation:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation not found: {conversation_id}")

    conversation.requirements = empty_requirements().model_dump()
    conversation.updated_at = _utc_now()
    db.add(
        Message(
            conversation_id=conversation.id,
            role="system",
            content="Conversation requirements reset — start a new search.",
            extracted_delta=None,
        )
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def extract_with_memory(
    db: Session,
    message: str,
    *,
    conversation_id: Optional[str] = None,
    reset: bool = False,
    provider: Optional[AIProvider] = None,
) -> ExtractResponse:
    """
    Extract requirements for a turn and merge into conversation memory.

    Creates a conversation when conversation_id is omitted.
    """
    text = message.strip()
    if not text:
        raise AIProviderError("Message must not be empty.")

    if conversation_id:
        conversation = get_conversation(db, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")
    else:
        conversation = create_conversation(db)

    reset_triggered = reset or is_reset_message(text)
    if reset_triggered:
        conversation.requirements = empty_requirements().model_dump()
        db.add(
            Message(
                conversation_id=conversation.id,
                role="system",
                content="Start new search — previous requirements cleared.",
                extracted_delta=None,
            )
        )

    previous = requirements_from_storage(conversation.requirements)
    turn_result = extract_requirements(text, provider=provider)
    turn_requirements = turn_result.requirements

    # If the message is only a reset phrase with no car criteria, keep empty state
    if reset_triggered and is_reset_message(text):
        # Still run extraction — user may say "start new search, cars under 40 lakh"
        merged = merge_requirements(empty_requirements(), turn_requirements)
        # If extraction found nothing useful beyond clarification noise on pure reset,
        # and message is essentially only reset, prefer empty:
        if _is_mostly_reset_only(text) and not _has_any_criteria(turn_requirements):
            merged = empty_requirements()
    else:
        merged = merge_requirements(previous, turn_requirements)

    conversation.requirements = merged.model_dump()
    conversation.updated_at = _utc_now()

    db.add(
        Message(
            conversation_id=conversation.id,
            role="user",
            content=text,
            extracted_delta=turn_requirements.model_dump(),
        )
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ExtractResponse(
        requirements=merged,
        provider=turn_result.provider,
        model=turn_result.model,
        conversation_id=conversation.id,
        turn_requirements=turn_requirements,
        reset=reset_triggered,
    )


def _has_any_criteria(req: ExtractedRequirements) -> bool:
    return any(
        [
            req.budget_min is not None,
            req.budget_max is not None,
            req.city is not None,
            req.condition is not None,
            req.transmission is not None,
            req.body_type is not None,
            req.purpose is not None,
            req.fuel_priority is not None,
            req.resale_priority is not None,
        ]
    )


def _is_mostly_reset_only(message: str) -> bool:
    """True when the message is essentially just a reset command."""
    cleaned = message.strip().lower()
    # Strip punctuation
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in cleaned)
    cleaned = " ".join(cleaned.split())
    reset_only = {
        "start a new search",
        "start new search",
        "new search",
        "start over",
        "reset",
        "reset search",
        "clear search",
        "clear my search",
        "clear filters",
        "clear requirements",
    }
    return cleaned in reset_only
