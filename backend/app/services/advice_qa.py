"""AI buying advice Q&A — RAG over buying-decision knowledge (Section O)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.ai.base import AIProvider, AIProviderError
from app.ai.factory import get_ai_provider
from app.core.llm_retry import with_llm_retry
from app.schemas.advice import (
    BUYING_ADVICE_DISCLAIMER,
    AdviceAskResponse,
    AdviceRetrievedChunk,
)
from app.services.knowledge_retrieval import retrieve_knowledge_chunks

# Ingested from sample_buying_advice_knowledge.md (path.stem)
BUYING_ADVICE_SOURCE_ID = "sample_buying_advice_knowledge"

INSUFFICIENT_BUYING_ADVICE_ANSWER = (
    "I don't have enough information in AutoAI's sample buying-advice knowledge "
    "base to answer that reliably. Try asking about used vs new trade-offs, "
    "dealer vs private seller considerations, first-time buyer mistakes, "
    "negotiation basics, or general financing education — or use Find a car "
    "when you want inventory matched to your budget."
)


def ask_buying_advice(
    session: Session,
    question: str,
    *,
    provider: Optional[AIProvider] = None,
    query_embedding_override: Optional[list[float]] = None,
    retrieved_override: Optional[list] = None,
) -> AdviceAskResponse:
    """
    RAG buying-advice flow (separate from /api/knowledge/ask and vehicle search).

    Retrieves only buying-advice chunks. If none are relevant, returns a
    don't-know template and does NOT call the LLM (anti-hallucination).
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
                "embed_advice_question",
                lambda: ai.embed_texts([text]),
            )
            if not vectors:
                raise AIProviderError("Failed to embed question.")
            embedding = vectors[0]
        retrieved = retrieve_knowledge_chunks(
            session,
            embedding,
            source_id=BUYING_ADVICE_SOURCE_ID,
        )

    chunk_payload = [
        AdviceRetrievedChunk(
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
        return AdviceAskResponse(
            question=text,
            answer=INSUFFICIENT_BUYING_ADVICE_ANSWER,
            grounded=False,
            chunks=[],
            disclaimer=BUYING_ADVICE_DISCLAIMER,
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
        "answer_from_buying_advice",
        lambda: ai.answer_from_buying_advice(question=text, chunks=llm_chunks),
    )

    return AdviceAskResponse(
        question=text,
        answer=answer,
        grounded=True,
        chunks=chunk_payload,
        disclaimer=BUYING_ADVICE_DISCLAIMER,
        provider=ai.name,
        model=ai.model_name,
    )
