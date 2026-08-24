"""Chunk + embed sample knowledge into knowledge_chunks (Phase 6)."""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy.orm import Session
from sqlmodel import select

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeChunk

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
DEFAULT_SOURCES = (
    KNOWLEDGE_DIR / "sample_automotive_knowledge.md",
    KNOWLEDGE_DIR / "sample_buying_advice_knowledge.md",
)


def parse_markdown_chunks(text: str, *, source_id: str) -> list[dict]:
    """Split markdown on ## headings into {title, content, chunk_index} dicts."""
    # Drop leading comment block lines starting with #
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            body_start = i
            break
    body = "\n".join(lines[body_start:]).strip()
    if not body:
        return []

    parts = re.split(r"(?m)^##\s+", body)
    chunks: list[dict] = []
    index = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        title_line, _, rest = part.partition("\n")
        title = title_line.strip() or f"Chunk {index + 1}"
        content = rest.strip()
        if not content:
            continue
        chunks.append(
            {
                "source_id": source_id,
                "title": title,
                "content": content,
                "chunk_index": index,
            }
        )
        index += 1
    return chunks


def ingest_knowledge_file(
    session: Session,
    path: Path,
    *,
    provider: AIProvider | None = None,
    replace_source: bool = True,
) -> int:
    """Embed and upsert all chunks from a markdown knowledge file. Returns count."""
    ai = provider or get_ai_provider()
    source_id = path.stem
    raw = path.read_text(encoding="utf-8")
    parsed = parse_markdown_chunks(raw, source_id=source_id)
    if not parsed:
        return 0

    if replace_source:
        existing = session.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.source_id == source_id)
        ).scalars().all()
        for row in existing:
            session.delete(row)
        session.flush()

    texts = [f"{c['title']}\n\n{c['content']}" for c in parsed]
    embeddings = ai.embed_texts(texts)
    if len(embeddings) != len(parsed):
        raise RuntimeError(
            f"Embedding count mismatch: got {len(embeddings)} for {len(parsed)} chunks"
        )

    for chunk, emb in zip(parsed, embeddings, strict=True):
        session.add(
            KnowledgeChunk(
                source_id=chunk["source_id"],
                title=chunk["title"],
                content=chunk["content"],
                chunk_index=chunk["chunk_index"],
                embedding=emb,
            )
        )
    session.commit()
    return len(parsed)


def ingest_all_default_sources(session: Session) -> int:
    """Ingest bundled markdown knowledge files. Returns total chunk count."""
    total = 0
    for path in DEFAULT_SOURCES:
        if not path.exists():
            continue
        total += ingest_knowledge_file(session, path)
    return total


def main() -> None:
    session = SessionLocal()
    try:
        total = ingest_all_default_sources(session)
        for path in DEFAULT_SOURCES:
            if path.exists():
                print(f"Processed {path.name}")
        if total == 0:
            raise SystemExit("No knowledge files ingested.")
        print(f"Ingested {total} knowledge chunks total.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
