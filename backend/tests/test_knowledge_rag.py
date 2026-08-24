"""RAG knowledge Q&A tests — no hallucination when retrieval is empty."""

from __future__ import annotations

from app.ai.base import AIProvider
from app.schemas.extraction import ExtractedRequirements
from app.schemas.knowledge import EDUCATIONAL_DISCLAIMER
from app.services.knowledge_qa import (
    INSUFFICIENT_KNOWLEDGE_ANSWER,
    ask_knowledge_question,
)
from app.services.knowledge_retrieval import RetrievedKnowledge
from app.scripts.ingest_knowledge import parse_markdown_chunks


class RecordingProvider(AIProvider):
    name = "stub"

    def __init__(self) -> None:
        self.answer_calls = 0
        self.embed_calls = 0

    @property
    def model_name(self) -> str:
        return "stub-model"

    def extract_requirements(self, message: str) -> ExtractedRequirements:
        raise NotImplementedError

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls += 1
        return [[0.0] * 8 for _ in texts]

    def answer_from_knowledge(self, *, question: str, chunks: list[dict]) -> str:
        self.answer_calls += 1
        return "Hallucinated answer that must not appear when chunks are empty."


def test_no_relevant_chunks_returns_insufficient_without_llm() -> None:
    """When retrieval yields nothing, do not call the LLM — say we don't know."""
    provider = RecordingProvider()
    # session unused when retrieved_override is set
    result = ask_knowledge_question(
        session=None,  # type: ignore[arg-type]
        question="What is the secret warranty code for Model XYZ-9999?",
        provider=provider,
        retrieved_override=[],
    )

    assert result.grounded is False
    assert result.chunks == []
    assert result.answer == INSUFFICIENT_KNOWLEDGE_ANSWER
    assert "don't have enough information" in result.answer.lower()
    assert provider.answer_calls == 0
    assert "Hallucinated" not in result.answer
    assert EDUCATIONAL_DISCLAIMER in result.disclaimer
    assert "not professional" in result.disclaimer.lower()


def test_grounded_path_calls_llm_when_chunks_present() -> None:
    from datetime import datetime, timezone

    from app.models.knowledge import KnowledgeChunk

    provider = RecordingProvider()
    chunk = KnowledgeChunk(
        id=1,
        source_id="sample",
        title="Manual vs automatic vs CVT",
        content="A CVT varies ratios smoothly rather than fixed gears.",
        chunk_index=0,
        embedding=[0.1] * 8,
        created_at=datetime.now(timezone.utc),
    )
    retrieved = [RetrievedKnowledge(chunk=chunk, similarity=0.81)]

    result = ask_knowledge_question(
        session=None,  # type: ignore[arg-type]
        question="What does CVT mean?",
        provider=provider,
        retrieved_override=retrieved,
    )

    assert result.grounded is True
    assert provider.answer_calls == 1
    assert len(result.chunks) == 1
    assert result.chunks[0].title.startswith("Manual")


def test_parse_markdown_chunks_splits_on_headings() -> None:
    md = """# ignore
## First topic

Alpha paragraph.

## Second topic

Beta paragraph.
"""
    chunks = parse_markdown_chunks(md, source_id="demo")
    assert len(chunks) == 2
    assert chunks[0]["title"] == "First topic"
    assert "Alpha" in chunks[0]["content"]
    assert chunks[1]["chunk_index"] == 1
