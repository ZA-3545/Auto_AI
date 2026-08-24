"""Schemas for knowledge RAG Q&A (Phase 6)."""

from typing import Optional

from pydantic import BaseModel, Field


EDUCATIONAL_DISCLAIMER = (
    "General educational information only — not professional mechanical or "
    "financial advice. Independent proof of concept — not affiliated with PakWheels."
)


class KnowledgeAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)


class RetrievedChunk(BaseModel):
    id: int
    source_id: str
    title: str
    content: str
    similarity: float
    chunk_index: int


class KnowledgeAskResponse(BaseModel):
    question: str
    answer: str
    grounded: bool = Field(
        description="True when answer was generated from retrieved chunks"
    )
    chunks: list[RetrievedChunk]
    disclaimer: str = EDUCATIONAL_DISCLAIMER
    provider: Optional[str] = None
    model: Optional[str] = None
