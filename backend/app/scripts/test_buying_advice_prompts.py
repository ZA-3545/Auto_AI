"""Smoke-test UI quick-prompt questions against buying-advice RAG."""

from __future__ import annotations

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.advice_qa import ask_buying_advice

QUESTIONS = [
    "Should I buy a used car or new one on this budget?",
    "Is it better to buy from a dealer or private seller in Pakistan?",
    "What's the biggest mistake first-time car buyers make?",
    "What should I know about car financing in general?",
]


def main() -> None:
    session = SessionLocal()
    try:
        rows = session.execute(
            text(
                """
                SELECT source_id, COUNT(*) AS cnt
                FROM knowledge_chunks
                GROUP BY source_id
                ORDER BY source_id
                """
            )
        ).fetchall()
        print("knowledge_chunks by source:")
        for source_id, cnt in rows:
            print(f"  {source_id}: {cnt}")

        print(f"\nRAG_MIN_SIMILARITY={settings.RAG_MIN_SIMILARITY}\n")

        passed = 0
        for i, question in enumerate(QUESTIONS, 1):
            result = ask_buying_advice(session, question)
            top_title = result.chunks[0].title if result.chunks else None
            top_sim = result.chunks[0].similarity if result.chunks else None
            ok = result.grounded and len(result.chunks) > 0
            if ok:
                passed += 1
            print(f"--- Question {i} ---")
            print(f"Q: {question}")
            print(f"grounded: {result.grounded}")
            print(f"chunks: {len(result.chunks)}")
            print(f"top_match: {top_title!r} (similarity={top_sim})")
            preview = result.answer.replace("\n", " ")[:160]
            print(f"answer: {preview}...")
            print(f"status: {'PASS' if ok else 'FAIL'}")
            print()

        print(f"Summary: {passed}/{len(QUESTIONS)} grounded")
        if passed != len(QUESTIONS):
            raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
