"""AI buying advice tests — no hallucination when retrieval is empty (Section H)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.ai.base import AIProvider
from app.schemas.advice import BUYING_ADVICE_DISCLAIMER
from app.schemas.extraction import ExtractedRequirements
from app.services.advice_qa import (
    INSUFFICIENT_BUYING_ADVICE_ANSWER,
    ask_buying_advice,
)
from app.services.knowledge_retrieval import RetrievedKnowledge
from app.models.knowledge import KnowledgeChunk


class RecordingAdviceProvider(AIProvider):
    name = "stub"

    def __init__(self) -> None:
        self.advice_calls = 0
        self.embed_calls = 0

    @property
    def model_name(self) -> str:
        return "stub-model"

    def extract_requirements(self, message: str) -> ExtractedRequirements:
        raise NotImplementedError

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls += 1
        return [[0.0] * 8 for _ in texts]

    def answer_from_buying_advice(self, *, question: str, chunks: list[dict]) -> str:
        self.advice_calls += 1
        return (
            "Hallucinated buying advice that must not appear when chunks are empty."
        )


def test_no_relevant_chunks_returns_insufficient_without_llm() -> None:
    """When retrieval yields nothing, do not call the LLM — say we don't know."""
    provider = RecordingAdviceProvider()
    result = ask_buying_advice(
        session=None,  # type: ignore[arg-type]
        question="What is the secret dealer code XYZ-9999 for instant approval?",
        provider=provider,
        retrieved_override=[],
    )

    assert result.grounded is False
    assert result.chunks == []
    assert result.answer == INSUFFICIENT_BUYING_ADVICE_ANSWER
    assert "don't have enough information" in result.answer.lower()
    assert provider.advice_calls == 0
    assert "Hallucinated" not in result.answer
    assert BUYING_ADVICE_DISCLAIMER in result.disclaimer
    assert "not individualized financial" in result.disclaimer.lower()
    assert "does not push" in result.disclaimer.lower()


def test_grounded_path_calls_llm_when_chunks_present() -> None:
    provider = RecordingAdviceProvider()
    chunk = KnowledgeChunk(
        id=1,
        source_id="sample_buying_advice_knowledge",
        title="Used vs new cars — general trade-offs",
        content="Buying used often means a lower upfront price...",
        chunk_index=0,
        embedding=[0.1] * 8,
        created_at=datetime.now(timezone.utc),
    )
    retrieved = [RetrievedKnowledge(chunk=chunk, similarity=0.82)]

    result = ask_buying_advice(
        session=None,  # type: ignore[arg-type]
        question="Should I buy a used car or new one on this budget?",
        provider=provider,
        retrieved_override=retrieved,
    )

    assert result.grounded is True
    assert provider.advice_calls == 1
    assert len(result.chunks) == 1
    assert result.chunks[0].title.startswith("Used vs new")
    assert BUYING_ADVICE_DISCLAIMER in result.disclaimer
