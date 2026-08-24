"""Aggregate evaluation metrics for GET /api/admin/metrics (PLANNING.md K.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.metrics_collector import FEATURE_PATHS, EndpointStats, snapshot
from app.models.conversation import Conversation, Message
from app.models.vehicle import Vehicle
from app.schemas.metrics import AdminMetricsResponse, EndpointLatencyRow, MetricCard

ANTI_HALLUCINATION_TEST_COUNT = 3


def _pct(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round(100.0 * numerator / denominator, 1)


def _path_count(stats: dict[str, EndpointStats], path: str) -> int:
    entry = stats.get(path)
    return entry.count if entry else 0


def build_admin_metrics(session: Session) -> AdminMetricsResponse:
    snap = snapshot()
    metrics: list[MetricCard] = []

    ext_total = snap.extraction_total
    ext_ok = snap.extraction_without_clarification
    success_rate = _pct(ext_ok, ext_total)

    metrics.append(
        MetricCard(
            id="extraction_accuracy",
            label="Requirement-extraction accuracy (approx.)",
            status="computed" if ext_total > 0 else "not_available",
            value=success_rate,
            unit="%",
            detail=(
                f"{ext_ok}/{ext_total} extractions did not request clarification"
                if ext_total > 0
                else None
            ),
            note=(
                "Proxy: % of /api/chat/extract calls where needs_clarification=false. "
                "Not ground-truth accuracy vs human labels."
            ),
        )
    )
    if ext_total > 0:
        metrics.append(
            MetricCard(
                id="extraction_clarification_rate",
                label="Extraction clarification rate",
                status="computed",
                value=_pct(snap.extraction_needs_clarification, ext_total),
                unit="%",
                detail=(
                    f"{snap.extraction_needs_clarification}/{ext_total} asked for clarification"
                ),
            )
        )

    search_stats = snap.endpoint_stats.get(FEATURE_PATHS["search"])
    if search_stats and (search_stats.with_results + search_stats.empty_results) > 0:
        denom = search_stats.with_results + search_stats.empty_results
        metrics.append(
            MetricCard(
                id="search_relevance",
                label="Search relevance (approx.)",
                status="computed",
                value=_pct(search_stats.with_results, denom),
                unit="%",
                detail=f"{search_stats.with_results}/{denom} searches returned ≥1 vehicle",
                note="Proxy: non-empty catalog results, not human relevance judgment.",
            )
        )
    else:
        metrics.append(
            MetricCard(
                id="search_relevance",
                label="Search relevance (approx.)",
                status="not_available",
                note="No search requests with recorded outcomes yet.",
            )
        )

    rec_stats = snap.endpoint_stats.get(FEATURE_PATHS["recommend"])
    if rec_stats and (rec_stats.with_results + rec_stats.empty_results) > 0:
        denom = rec_stats.with_results + rec_stats.empty_results
        metrics.append(
            MetricCard(
                id="recommend_nonempty_rate",
                label="Recommendation non-empty rate (approx.)",
                status="computed",
                value=_pct(rec_stats.with_results, denom),
                unit="%",
                detail=f"{rec_stats.with_results}/{denom} recommendations returned ≥1 match",
                note="Not the same as true recommendation relevance (needs human review).",
            )
        )

    metrics.append(
        MetricCard(
            id="recommendation_relevance",
            label="Recommendation relevance",
            status="not_available",
            note=(
                "Requires human judgment or real user feedback — not faked for this PoC."
            ),
        )
    )

    metrics.append(
        MetricCard(
            id="hallucination_rate",
            label="Hallucination rate (production)",
            status="manual",
            value=ANTI_HALLUCINATION_TEST_COUNT,
            unit="automated tests",
            detail="test_knowledge_rag, test_advice, listing certainty tests",
            note=(
                "No runtime production rate without log review. Run pytest for the PoC gate."
            ),
        )
    )

    llm = snap.llm
    conv_count = len(llm.cost_by_conversation)
    avg_cost = round(llm.approx_cost_usd / conv_count, 6) if conv_count > 0 else None

    metrics.append(
        MetricCard(
            id="api_cost_total",
            label="Approx. API cost (session)",
            status="computed" if llm.call_count > 0 else "not_available",
            value=round(llm.approx_cost_usd, 4) if llm.call_count > 0 else None,
            unit="USD",
            detail=f"{llm.total_tokens:,} tokens across {llm.call_count} LLM calls",
            note="Rough estimate — not billing-accurate. Resets on server restart.",
        )
    )
    metrics.append(
        MetricCard(
            id="api_cost_per_conversation",
            label="API cost per conversation (approx.)",
            status="computed" if conv_count > 0 else "not_available",
            value=avg_cost,
            unit="USD",
            detail=f"{conv_count} conversations with linked LLM cost",
            note="Only calls that passed conversation_id to LLM usage logging.",
        )
    )

    extract_n = _path_count(snap.endpoint_stats, FEATURE_PATHS["extract"])
    compare_n = _path_count(snap.endpoint_stats, FEATURE_PATHS["compare"])
    metrics.append(
        MetricCard(
            id="comparison_usage_rate",
            label="Comparison usage rate",
            status="computed" if extract_n > 0 else "not_available",
            value=_pct(compare_n, extract_n),
            unit="%",
            detail=f"{compare_n} compare vs {extract_n} extract requests",
            note="Proxy for this process lifetime.",
        )
    )

    listing_n = _path_count(snap.endpoint_stats, FEATURE_PATHS["listing_analyze"])
    metrics.append(
        MetricCard(
            id="listing_analysis_usage",
            label="Listing-analysis usage",
            status="computed" if listing_n > 0 else "not_available",
            value=listing_n,
            unit="requests",
        )
    )

    for feature_id, path in (
        ("knowledge_usage", FEATURE_PATHS["knowledge_ask"]),
        ("buying_advice_usage", FEATURE_PATHS["buying_advice"]),
        ("maintenance_usage", FEATURE_PATHS["maintenance"]),
    ):
        n = _path_count(snap.endpoint_stats, path)
        metrics.append(
            MetricCard(
                id=feature_id,
                label=feature_id.replace("_", " ").title(),
                status="computed" if n > 0 else "not_available",
                value=n if n > 0 else None,
                unit="requests",
            )
        )

    metrics.append(
        MetricCard(
            id="user_satisfaction",
            label="User satisfaction",
            status="not_available",
            note="Requires real users and feedback — not simulated.",
        )
    )
    metrics.append(
        MetricCard(
            id="click_through_rate",
            label="Click-through rate",
            status="not_available",
            note="Frontend clicks not instrumented yet.",
        )
    )
    metrics.append(
        MetricCard(
            id="rate_limit_hits",
            label="Rate-limit hits (session)",
            status="computed",
            value=snap.rate_limit_hits,
            unit="blocked",
        )
    )
    metrics.append(
        MetricCard(
            id="llm_failures",
            label="LLM failures (session)",
            status="computed",
            value=llm.failure_count,
            unit="failures",
        )
    )

    conv_total = session.execute(select(func.count()).select_from(Conversation)).scalar() or 0
    msg_total = session.execute(select(func.count()).select_from(Message)).scalar() or 0
    vehicle_total = session.execute(select(func.count()).select_from(Vehicle)).scalar() or 0
    chunk_rows = session.execute(
        text(
            "SELECT source_id, COUNT(*) FROM knowledge_chunks GROUP BY source_id ORDER BY source_id"
        )
    ).fetchall()

    metrics.append(
        MetricCard(
            id="db_conversations",
            label="Stored conversations (DB)",
            status="computed",
            value=conv_total,
            unit="sessions",
            detail=f"{msg_total} messages",
        )
    )
    metrics.append(
        MetricCard(
            id="db_catalog",
            label="Demo catalog size",
            status="computed",
            value=vehicle_total,
            unit="vehicles",
        )
    )
    metrics.append(
        MetricCard(
            id="db_knowledge_chunks",
            label="Knowledge chunks (DB)",
            status="computed" if chunk_rows else "not_available",
            value=sum(r[1] for r in chunk_rows) if chunk_rows else None,
            unit="chunks",
            detail=", ".join(f"{r[0]}:{r[1]}" for r in chunk_rows) if chunk_rows else None,
        )
    )

    if ext_total == 0 and msg_total > 0:
        deltas = session.execute(
            select(Message.extracted_delta).where(Message.extracted_delta.isnot(None))
        ).scalars().all()
        needs = sum(1 for d in deltas if d and d.get("needs_clarification"))
        ok = sum(1 for d in deltas if d and not d.get("needs_clarification"))
        total_d = needs + ok
        if total_d > 0:
            for m in metrics:
                if m.id == "extraction_accuracy":
                    m.status = "computed"
                    m.value = _pct(ok, total_d)
                    m.detail = f"{ok}/{total_d} stored extractions without clarification (DB)"
                    m.note = "From persisted message deltas."

    api_stats = [s for p, s in snap.endpoint_stats.items() if p.startswith("/api/")]
    total_req = sum(s.count for s in api_stats)
    total_ms = sum(s.total_duration_ms for s in api_stats)
    metrics.insert(
        5,
        MetricCard(
            id="response_latency",
            label="Response latency (avg, API)",
            status="computed" if total_req > 0 else "not_available",
            value=round(total_ms / total_req, 1) if total_req > 0 else None,
            unit="ms",
            detail=f"Across {total_req} API requests this process lifetime",
            note="Per-endpoint breakdown below. Resets on restart.",
        ),
    )

    endpoint_latency: list[EndpointLatencyRow] = []
    for path, stats in sorted(
        snap.endpoint_stats.items(), key=lambda x: x[1].count, reverse=True
    ):
        if not path.startswith("/api/"):
            continue
        endpoint_latency.append(
            EndpointLatencyRow(
                path=path,
                request_count=stats.count,
                error_count=stats.error_count,
                avg_latency_ms=(
                    round(stats.total_duration_ms / stats.count, 1)
                    if stats.count > 0
                    else None
                ),
            )
        )

    return AdminMetricsResponse(
        generated_at=datetime.now(timezone.utc),
        metrics=metrics,
        endpoint_latency=endpoint_latency,
        llm_by_operation=snap.llm.by_operation,
        conversations_with_llm_cost=conv_count,
    )
