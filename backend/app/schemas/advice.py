"""Schemas for AI buying advice RAG (PLANNING.md Section O & H)."""

from typing import Optional

from pydantic import BaseModel, Field


BUYING_ADVICE_DISCLAIMER = (
    "General educational buying guidance only — not individualized financial, "
    "legal, or mechanical advice. AutoAI presents trade-offs honestly and does "
    "not push you toward a purchase. Independent proof of concept — not "
    "affiliated with PakWheels."
)


class AdviceAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)


class AdviceRetrievedChunk(BaseModel):
    id: int
    source_id: str
    title: str
    content: str
    similarity: float
    chunk_index: int


class AdviceAskResponse(BaseModel):
    question: str
    answer: str
    grounded: bool = Field(
        description="True when answer was generated from retrieved buying-advice chunks"
    )
    chunks: list[AdviceRetrievedChunk]
    disclaimer: str = BUYING_ADVICE_DISCLAIMER
    provider: Optional[str] = None
    model: Optional[str] = None
