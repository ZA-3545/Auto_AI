from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import database_url_looks_local, settings
from app.core.database import SessionLocal

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    detail: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic liveness probe — no database dependency."""
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/ready", response_model=ReadyResponse)
def readiness_check() -> ReadyResponse:
    """Readiness probe — verifies Postgres is reachable (migrations/seed may still be needed)."""
    if database_url_looks_local(settings.DATABASE_URL):
        return ReadyResponse(
            status="degraded",
            database="misconfigured",
            detail=(
                "DATABASE_URL uses localhost. Set Railway Postgres URL in dashboard "
                "(Variables → reference ${{Postgres.DATABASE_URL}})."
            ),
        )
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        return ReadyResponse(status="ok", database="up")
    except Exception as exc:  # noqa: BLE001
        return ReadyResponse(
            status="degraded",
            database="down",
            detail=str(exc.__class__.__name__),
        )
