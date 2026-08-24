"""
Delete conversations (and messages) older than the retention window.

PLANNING.md Section J — default 30 days (CONVERSATION_RETENTION_DAYS).

Usage:
  python -m app.scripts.purge_old_conversations
  python -m app.scripts.purge_old_conversations --days 30 --dry-run
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import configure_logging, get_logger, log_event
from app.models.conversation import Conversation, Message

logger = get_logger("autoai.privacy")


def purge_older_than(days: int, *, dry_run: bool = False) -> dict[str, int]:
    if days < 1:
        raise ValueError("days must be >= 1")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    session = SessionLocal()
    try:
        stale = list(
            session.execute(
                select(Conversation).where(Conversation.updated_at < cutoff)
            ).scalars().all()
        )
        conversation_ids = [c.id for c in stale]
        msg_count = 0
        if conversation_ids:
            messages = list(
                session.execute(
                    select(Message).where(Message.conversation_id.in_(conversation_ids))
                ).scalars().all()
            )
            msg_count = len(messages)
            if not dry_run:
                for m in messages:
                    session.delete(m)
                for c in stale:
                    session.delete(c)
                session.commit()
        result = {
            "conversations": len(conversation_ids),
            "messages": msg_count,
            "dry_run": int(dry_run),
            "retention_days": days,
        }
        log_event(logger, "privacy_purge", **result)
        return result
    finally:
        session.close()


def main() -> None:
    configure_logging(debug=False)
    parser = argparse.ArgumentParser(description="Purge old AutoAI conversations")
    parser.add_argument(
        "--days",
        type=int,
        default=settings.CONVERSATION_RETENTION_DAYS,
        help="Delete conversations with updated_at older than this many days",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count only; do not delete",
    )
    args = parser.parse_args()
    result = purge_older_than(args.days, dry_run=args.dry_run)
    print(result)


if __name__ == "__main__":
    main()
