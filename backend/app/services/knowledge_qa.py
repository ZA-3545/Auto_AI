"""Knowledge Q&A orchestration — retrieve then LLM-ground (Phase 6)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.core.llm_retry import with_llm_retry
from app.schemas.knowledge import (
    EDUCATIONAL_DISCLAIMER,
    KnowledgeAskResponse,
    RetrievedChunk,
)
from app.services.knowledge_retrieval import retrieve_knowledge_chunks

INSUFFICIENT_KNOWLEDGE_ANSWER = (
    "I don't have enough information in AutoAI's sample knowledge base to "
    "answer that reliably. Try asking about general topics like checking a "
    "used car, resale value factors, CVT vs manual, engine capacity, or "
    "basic maintenance intervals — or use Find a car for inventory search."
)


def ask_knowledge_question(
    session: Session,
    question: str,
    *,
    provider: Optional[AIProvider] = None,
    query_embedding_override: Optional[list[float]] = None,
    retrieved_override: Optional[list] = None,
) -> KnowledgeAskResponse:
    """
    RAG ask flow (separate from vehicle search/recommendation).

    If no relevant chunks are retrieved, returns a don't-know template and
    does NOT call the LLM (anti-hallucination).
    """
    text = question.strip()
    if not text:
        raise AIProviderError("Question must not be empty.")

    ai = provider or get_ai_provider()

    if retrieved_override is not None:
        retrieved = list(retrieved_override)
    else:
        if query_embedding_override is not None:
            embedding = query_embedding_override
        else:
            vectors = with_llm_retry(
                "embed_question",
                lambda: ai.embed_texts([text]),
            )
            if not vectors:
                raise AIProviderError("Failed to embed question.")
            embedding = vectors[0]
        retrieved = retrieve_knowledge_chunks(session, embedding)

    chunk_payload = [
        RetrievedChunk(
            id=item.chunk.id or 0,
            source_id=item.chunk.source_id,
            title=item.chunk.title,
            content=item.chunk.content,
            similarity=round(float(item.similarity), 4),
            chunk_index=item.chunk.chunk_index,
        )
        for item in retrieved
    ]

    if not chunk_payload:
        return KnowledgeAskResponse(
            question=text,
            answer=INSUFFICIENT_KNOWLEDGE_ANSWER,
            grounded=False,
            chunks=[],
            disclaimer=EDUCATIONAL_DISCLAIMER,
            provider=ai.name,
            model=ai.model_name,
        )

    llm_chunks = [
        {
            "title": c.title,
            "content": c.content,
            "similarity": c.similarity,
        }
        for c in chunk_payload
    ]
    answer = with_llm_retry(
        "answer_from_knowledge",
        lambda: ai.answer_from_knowledge(question=text, chunks=llm_chunks),
    )

    return KnowledgeAskResponse(
        question=text,
        answer=answer,
        grounded=True,
        chunks=chunk_payload,
        disclaimer=EDUCATIONAL_DISCLAIMER,
        provider=ai.name,
        model=ai.model_name,
    )
