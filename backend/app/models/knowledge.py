"""Knowledge chunk model for RAG (PLANNING.md Phase 6 / Section C.1)."""

from datetime import datetime, timezone
from typing import Any, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, SQLModel

# text-embedding-3-small
EMBEDDING_DIMENSIONS = 1536


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeChunk(SQLModel, table=True):
    """
    Embedded educational text for general automotive Q&A.

    Not used for vehicle inventory search — structured filtering stays on `vehicles`.
    """

    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("source_id", "chunk_index", name="uq_knowledge_source_chunk"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    source_id: str = Field(max_length=128, index=True)
    title: str = Field(max_length=256)
    content: str = Field(sa_column=Column(Text, nullable=False))
    chunk_index: int = Field(default=0, ge=0)

    # pgvector column — cosine similarity via <=>
    embedding: Any = Field(sa_column=Column(Vector(EMBEDDING_DIMENSIONS), nullable=False))

    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=_utc_now,
        ),
    )
