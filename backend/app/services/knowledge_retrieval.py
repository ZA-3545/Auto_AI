"""Deterministic RAG retrieval over knowledge_chunks (pgvector)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.knowledge import KnowledgeChunk


@dataclass(frozen=True)
class RetrievedKnowledge:
    chunk: KnowledgeChunk
    similarity: float


def retrieve_knowledge_chunks(
    session: Session,
    query_embedding: list[float],
    *,
    top_k: int | None = None,
    min_similarity: float | None = None,
    source_id: str | None = None,
) -> list[RetrievedKnowledge]:
    """
    Cosine similarity search via pgvector (`<=>` = cosine distance).

    similarity = 1 - cosine_distance. Chunks below min_similarity are dropped.
    """
    k = top_k if top_k is not None else settings.RAG_TOP_K
    threshold = (
        min_similarity
        if min_similarity is not None
        else settings.RAG_MIN_SIMILARITY
    )
    if k < 1 or not query_embedding:
        return []

    # Bind embedding as a pgvector literal string
    vector_literal = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"

    if source_id:
        sql = text(
            """
            SELECT
                id,
                source_id,
                title,
                content,
                chunk_index,
                created_at,
                embedding,
                1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
            FROM knowledge_chunks
            WHERE source_id = :source_id
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :limit
            """
        )
        params = {"qvec": vector_literal, "limit": k, "source_id": source_id}
    else:
        sql = text(
            """
            SELECT
                id,
                source_id,
                title,
                content,
                chunk_index,
                created_at,
                embedding,
                1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
            FROM knowledge_chunks
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :limit
            """
        )
        params = {"qvec": vector_literal, "limit": k}

    rows = session.execute(sql, params).mappings().all()

    results: list[RetrievedKnowledge] = []
    for row in rows:
        sim = float(row["similarity"])
        if sim < threshold:
            continue
        chunk = KnowledgeChunk(
            id=row["id"],
            source_id=row["source_id"],
            title=row["title"],
            content=row["content"],
            chunk_index=row["chunk_index"],
            embedding=row["embedding"],
            created_at=row["created_at"],
        )
        results.append(RetrievedKnowledge(chunk=chunk, similarity=sim))
    return results
