"""Admin metrics API — internal evaluation dashboard (PLANNING.md K.1)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metrics import AdminMetricsResponse
from app.services.metrics_service import build_admin_metrics

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_admin_metrics(db: Session = Depends(get_db)) -> AdminMetricsResponse:
    """
    On-demand evaluation metrics for internal PoC review.

    Read-only aggregation over in-process counters + DB tables.
    No authentication yet (Phase 8 limitation).
    """
    return build_admin_metrics(db)
