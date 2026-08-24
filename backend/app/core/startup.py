"""One-time bootstrap on API startup (migrations + demo seed if empty)."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

from app.core.config import database_url_looks_local, settings
from app.core.database import SessionLocal
from app.models.vehicle import Vehicle

logger = logging.getLogger("autoai.startup")

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    """Apply Alembic migrations to head."""
    ini_path = _BACKEND_DIR / "alembic.ini"
    if not ini_path.is_file():
        logger.warning("alembic.ini not found at %s — skipping migrations", ini_path)
        return
    command.upgrade(Config(str(ini_path)), "head")
    logger.info("Database migrations applied")


def seed_demo_catalog_if_empty() -> None:
    """Load demo vehicles when the catalog table exists but has no rows."""
    from app.scripts.seed_vehicles import seed_vehicles

    db = SessionLocal()
    try:
        count = db.scalar(select(func.count()).select_from(Vehicle)) or 0
        if count > 0:
            logger.info("Vehicle catalog already has %s rows — skip seed", count)
            return
        seeded = seed_vehicles(db, clear_existing=False)
        logger.info("Seeded %s demo vehicles", seeded)
    finally:
        db.close()


def bootstrap_database() -> None:
    """Run migrations and ensure demo catalog exists (production-safe, idempotent)."""
    if database_url_looks_local(settings.DATABASE_URL):
        logger.error(
            "DATABASE_URL points to localhost (%s). On Railway, link Postgres and set "
            "DATABASE_URL to the Railway Postgres connection string (not 127.0.0.1).",
            settings.DATABASE_URL.split("@")[-1][:80],
        )
        return
    try:
        run_migrations()
        seed_demo_catalog_if_empty()
    except Exception:
        logger.exception("Database bootstrap failed — API may return errors until fixed")
        # Do not crash the process; /health stays up for platform probes.
