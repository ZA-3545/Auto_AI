"""Conversation and message models for session-based memory (PLANNING.md §G)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Text
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """
    Anonymous session conversation (no auth yet — Phase 8).

    Stores the merged requirements JSON so later turns can update fields
    without wiping earlier ones.
    """

    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, max_length=36)
    requirements: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now),
    )


class Message(SQLModel, table=True):
    """Single turn in a conversation."""

    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(
        foreign_key="conversations.id",
        max_length=36,
        index=True,
    )
    role: str = Field(max_length=32)  # user | system | assistant
    content: str = Field(sa_column=Column(Text, nullable=False))
    extracted_delta: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=_utc_now),
    )
