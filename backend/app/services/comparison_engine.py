"""
Deterministic vehicle comparison engine (PLANNING.md Section F).

All factor values and "best for X" conclusions come from DB records / heuristics.
The LLM must never invent comparison data — only optional narrative phrasing.
"""

from __future__ import annotations

from typing import Optional

from app.models.vehicle import BodyType, FuelType, Vehicle
from app.schemas.comparison import (
    BestForConclusion,
    DataReliability,
    FactorComparison,
    FactorValue,
)
from app.schemas.extraction import ExtractedRequirements
from app.services.recommendation_engine import PURPOSE_BODY_SCORES, family_suitability_score

# Makes with strong parts availability in Pakistani market (demo heuristic)
STRONG_PARTS_MAKES = {
    "toyota",
    "honda",
    "suzuki",
    "daihatsu",
    "hyundai",
    "kia",
}

# Relative maintenance ease heuristic by make (higher = easier / cheaper parts labor)
MAINTENANCE_MAKE_SCORE: dict[str, float] = {
    "toyota": 90,
    "honda": 88,
    "suzuki": 92,
    "daihatsu": 80,
    "hyundai": 70,
    "kia": 68,
    "changan": 55,
    "mg": 50,
    "nissan": 65,
    "proton": 45,
    "haval": 48,
    "dfsk": 40,
    "prince": 55,
    "united": 50,
    "isuzu": 70,
    "mitsubishi": 60,
    "bmw": 30,
    "mercedes-benz": 28,
    "audi": 30,
}


def _enum_val(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _label(vehicle: Vehicle) -> str:
    return f"{vehicle.make} {vehicle.model} ({vehicle.year})"


def _pick_winner(
    values: list[FactorValue],
    *,
    higher_is_better: bool,
) -> Optional[int]:
    scored = [v for v in values if v.numeric is not None]
    if not scored:
        return None
    best = max(scored, key=lambda v: v.numeric) if higher_is_better else min(
        scored, key=lambda v: v.numeric  # type: ignore[arg-type]
    )
    # Tie → no single winner
    tied = [v for v in scored if v.numeric == best.numeric]
    if len(tied) > 1:
        return None
    return best.vehicle_id


def _parts_score(make: str) -> float:
    key = make.strip().lower()
    if key in STRONG_PARTS_MAKES:
        return 90.0
    return MAINTENANCE_MAKE_SCORE.get(key, 50.0)


def _maintenance_score(vehicle: Vehicle) -> float:
    make_score = MAINTENANCE_MAKE_SCORE.get(vehicle.make.strip().lower(), 50.0)
    mileage = vehicle.mileage_km
    if mileage <= 30_000:
        mileage_factor = 100.0
    elif mileage <= 60_000:
        mileage_factor = 80.0
    elif mileage <= 100_000:
        mileage_factor = 60.0
    else:
        mileage_factor = 40.0
    return round(make_score * 0.7 + mileage_factor * 0.3, 2)


def _comfort_score(vehicle: Vehicle) -> float:
    body = _enum_val(vehicle.body_type)
    body_scores = {
        BodyType.suv.value: 90,
        BodyType.crossover.value: 85,
        BodyType.sedan.value: 80,
        BodyType.van.value: 75,
        BodyType.hatchback.value: 65,
        BodyType.pickup.value: 50,
        BodyType.coupe.value: 60,
    }
    base = float(body_scores.get(body, 50))
    if vehicle.engine_capacity and vehicle.engine_capacity >= 1800:
        base = min(100.0, base + 5)
    return base


def _family_score(vehicle: Vehicle, requirements: ExtractedRequirements) -> float:
    purpose = (requirements.purpose or "family").strip().lower()
    if "family" in purpose or not requirements.purpose:
        return family_suitability_score(vehicle)
    body = _enum_val(vehicle.body_type)
    for key, mapping in PURPOSE_BODY_SCORES.items():
        if key in purpose:
            return float(mapping.get(body, 50))
    return float(PURPOSE_BODY_SCORES["family"].get(body, 50))


def _performance_score(vehicle: Vehicle) -> Optional[float]:
    if vehicle.engine_capacity is None:
        if _enum_val(vehicle.fuel_type) == FuelType.electric.value:
            return 75.0  # EV — no cc; mild default inference
        return None
    # Normalize roughly 660–3000 cc → 0–100
    return round(min(100.0, max(0.0, (vehicle.engine_capacity - 660) / (3000 - 660) * 100)), 2)


def build_factor_comparisons(
    vehicles: list[Vehicle],
    requirements: ExtractedRequirements,
) -> list[FactorComparison]:
    """Build Section F factor rows from DB-backed values only."""
    factors: list[FactorComparison] = []

    # --- FACT factors from DB ---
    price_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"PKR {v.price:,}",
            numeric=float(v.price),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="price",
            reliability=DataReliability.fact,
            values=price_values,
            winner_vehicle_id=_pick_winner(price_values, higher_is_better=False),
            note="Lower price wins",
        )
    )

    year_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=str(v.year),
            numeric=float(v.year),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="model_year",
            reliability=DataReliability.fact,
            values=year_values,
            winner_vehicle_id=_pick_winner(year_values, higher_is_better=True),
            note="Newer year wins",
        )
    )

    engine_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=(
                f"{v.engine_capacity} cc"
                if v.engine_capacity is not None
                else (
                    "EV (n/a)"
                    if _enum_val(v.fuel_type) == FuelType.electric.value
                    else "Unknown"
                )
            ),
            numeric=float(v.engine_capacity) if v.engine_capacity is not None else None,
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="engine",
            reliability=DataReliability.fact,
            values=engine_values,
            winner_vehicle_id=_pick_winner(engine_values, higher_is_better=True),
            note="Larger engine capacity wins when known; EVs marked n/a",
        )
    )

    transmission_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=_enum_val(v.transmission),
            numeric=None,
        )
        for v in vehicles
    ]
    preferred_tx = (
        requirements.transmission.value if requirements.transmission else None
    )
    tx_winner = None
    if preferred_tx:
        matches = [
            v
            for v in vehicles
            if _enum_val(v.transmission) == preferred_tx
        ]
        if len(matches) == 1:
            tx_winner = matches[0].id
    factors.append(
        FactorComparison(
            factor="transmission",
            reliability=DataReliability.fact,
            values=transmission_values,
            winner_vehicle_id=tx_winner,
            note=(
                f"Matches user preference ({preferred_tx})"
                if preferred_tx
                else "No preferred transmission stated — no winner"
            ),
        )
    )

    fuel_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=(
                "EV"
                if _enum_val(v.fuel_type) == FuelType.electric.value
                else (
                    f"{v.fuel_average_kmpl} km/l ({_enum_val(v.fuel_type)})"
                    if v.fuel_average_kmpl is not None
                    else f"{_enum_val(v.fuel_type)} (avg unknown)"
                )
            ),
            numeric=(
                99.0
                if _enum_val(v.fuel_type) == FuelType.electric.value
                else (
                    float(v.fuel_average_kmpl)
                    if v.fuel_average_kmpl is not None
                    else None
                )
            ),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="fuel_economy",
            reliability=DataReliability.fact,
            values=fuel_values,
            winner_vehicle_id=_pick_winner(fuel_values, higher_is_better=True),
            note="Higher km/l wins; EV treated as top economy for ranking",
        )
    )

    mileage_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"{v.mileage_km:,} km",
            numeric=float(v.mileage_km),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="mileage",
            reliability=DataReliability.fact,
            values=mileage_values,
            winner_vehicle_id=_pick_winner(mileage_values, higher_is_better=False),
            note="Lower odometer wins",
        )
    )

    resale_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"{v.resale_rating}/5",
            numeric=float(v.resale_rating),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="resale",
            reliability=DataReliability.fact,
            values=resale_values,
            winner_vehicle_id=_pick_winner(resale_values, higher_is_better=True),
            note="Higher resale_rating wins",
        )
    )

    # --- INFERENCE factors (derived from DB fields, explicitly labeled) ---
    maint_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"score {_maintenance_score(v):.0f}/100 (make + mileage heuristic)",
            numeric=_maintenance_score(v),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="maintenance",
            reliability=DataReliability.inference,
            values=maint_values,
            winner_vehicle_id=_pick_winner(maint_values, higher_is_better=True),
            note="INFERENCE from make popularity + mileage — not verified shop data",
        )
    )

    parts_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"score {_parts_score(v.make):.0f}/100 (make heuristic)",
            numeric=_parts_score(v.make),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="parts_availability",
            reliability=DataReliability.inference,
            values=parts_values,
            winner_vehicle_id=_pick_winner(parts_values, higher_is_better=True),
            note="INFERENCE from brand presence in Pakistan — not live inventory",
        )
    )

    comfort_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"score {_comfort_score(v):.0f}/100 (body type heuristic)",
            numeric=_comfort_score(v),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="comfort",
            reliability=DataReliability.inference,
            values=comfort_values,
            winner_vehicle_id=_pick_winner(comfort_values, higher_is_better=True),
            note="INFERENCE from body_type (+ engine size) — not cabin review data",
        )
    )

    family_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=f"score {_family_score(v, requirements):.0f}/100",
            numeric=_family_score(v, requirements),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="family_suitability",
            reliability=DataReliability.inference,
            values=family_values,
            winner_vehicle_id=_pick_winner(family_values, higher_is_better=True),
            note="INFERENCE from body_type vs stated purpose",
        )
    )

    perf_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display=(
                f"score {_performance_score(v):.0f}/100 (engine heuristic)"
                if _performance_score(v) is not None
                else "Unknown"
            ),
            numeric=_performance_score(v),
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="performance",
            reliability=DataReliability.inference,
            values=perf_values,
            winner_vehicle_id=_pick_winner(perf_values, higher_is_better=True),
            note="INFERENCE from engine_capacity — no dyno data in catalog",
        )
    )

    # --- UNKNOWN: no reliable safety/features fields in Phase 2 schema ---
    safety_values = [
        FactorValue(
            vehicle_id=v.id,  # type: ignore[arg-type]
            display="Unknown — not in demo catalog",
            numeric=None,
        )
        for v in vehicles
    ]
    factors.append(
        FactorComparison(
            factor="safety_features",
            reliability=DataReliability.unknown,
            values=safety_values,
            winner_vehicle_id=None,
            note="UNKNOWN — no verified safety/feature fields in current schema",
        )
    )

    return factors


def _vehicle_by_id(vehicles: list[Vehicle], vehicle_id: int) -> Vehicle:
    for v in vehicles:
        if v.id == vehicle_id:
            return v
    raise KeyError(vehicle_id)


def build_best_for_conclusions(
    vehicles: list[Vehicle],
    factors: list[FactorComparison],
) -> list[BestForConclusion]:
    """Deterministic best-for-X from factor winners (DB-backed)."""
    category_map = {
        "price": "best_for_price",
        "fuel_economy": "best_for_fuel_economy",
        "resale": "best_for_resale",
        "mileage": "best_for_low_mileage",
        "family_suitability": "best_for_family",
        "model_year": "best_for_newer_model",
    }
    conclusions: list[BestForConclusion] = []
    by_factor = {f.factor: f for f in factors}

    for factor_key, category in category_map.items():
        row = by_factor.get(factor_key)
        if not row or row.winner_vehicle_id is None:
            continue
        winner = _vehicle_by_id(vehicles, row.winner_vehicle_id)
        winner_display = next(
            (v.display for v in row.values if v.vehicle_id == row.winner_vehicle_id),
            "",
        )
        conclusions.append(
            BestForConclusion(
                category=category,
                vehicle_id=winner.id,  # type: ignore[arg-type]
                vehicle_label=_label(winner),
                reason=f"{row.note or factor_key}: {winner_display}",
            )
        )
    return conclusions


def compute_best_overall(
    vehicles: list[Vehicle],
    factors: list[FactorComparison],
    requirements: ExtractedRequirements,
) -> BestForConclusion:
    """
    Weighted overall winner based on user priorities (Section F).

    Base weights; boost fuel / resale / family when user prioritized them.
    """
    weights = {
        "price": 0.20,
        "fuel_economy": 0.15,
        "resale": 0.10,
        "mileage": 0.10,
        "family_suitability": 0.15,
        "model_year": 0.10,
        "maintenance": 0.05,
        "parts_availability": 0.05,
        "comfort": 0.05,
        "performance": 0.05,
    }

    if requirements.fuel_priority:
        weights["fuel_economy"] += 0.10
        weights["price"] -= 0.05
        weights["model_year"] -= 0.05
    if requirements.resale_priority:
        weights["resale"] += 0.10
        weights["price"] -= 0.05
        weights["comfort"] -= 0.05
    purpose = (requirements.purpose or "").lower()
    if "family" in purpose:
        weights["family_suitability"] += 0.08
        weights["performance"] -= 0.04
        weights["price"] -= 0.04

    # Normalize
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    by_factor = {f.factor: f for f in factors}
    scores: dict[int, float] = {v.id: 0.0 for v in vehicles if v.id is not None}

    for factor_name, weight in weights.items():
        row = by_factor.get(factor_name)
        if not row:
            continue
        nums = [v.numeric for v in row.values if v.numeric is not None]
        if not nums:
            continue
        lo, hi = min(nums), max(nums)
        span = hi - lo if hi != lo else 1.0
        # price & mileage: lower is better
        lower_better = factor_name in {"price", "mileage"}
        for val in row.values:
            if val.numeric is None or val.vehicle_id not in scores:
                continue
            if lower_better:
                norm = 1.0 - (val.numeric - lo) / span
            else:
                norm = (val.numeric - lo) / span
            scores[val.vehicle_id] += weight * norm * 100.0

    best_id = max(scores, key=lambda vid: scores[vid])
    best = _vehicle_by_id(vehicles, best_id)

    priority_bits: list[str] = []
    if requirements.fuel_priority:
        priority_bits.append("fuel economy priority")
    if requirements.resale_priority:
        priority_bits.append("resale priority")
    if purpose:
        priority_bits.append(f"purpose={requirements.purpose}")
    if requirements.budget_max is not None:
        priority_bits.append(f"budget_max={requirements.budget_max}")

    reason = (
        f"Deterministic weighted score {scores[best_id]:.1f}/100"
        + (f" using user priorities ({', '.join(priority_bits)})" if priority_bits else "")
    )

    return BestForConclusion(
        category="best_overall_for_user",
        vehicle_id=best.id,  # type: ignore[arg-type]
        vehicle_label=_label(best),
        reason=reason,
    )


def build_template_narrative(
    vehicles: list[Vehicle],
    best_for: list[BestForConclusion],
    best_overall: BestForConclusion,
) -> str:
    """Deterministic fallback narrative — no LLM required."""
    labels = ", ".join(_label(v) for v in vehicles)
    lines = [
        f"Comparing {labels} using catalog data only (demo sample — not live listings).",
        f"Best overall for your priorities: {best_overall.vehicle_label} — {best_overall.reason}.",
    ]
    for c in best_for:
        lines.append(f"{c.category.replace('_', ' ').title()}: {c.vehicle_label} ({c.reason}).")
    lines.append(
        "Safety/features could not be compared — those fields are not in the demo catalog."
    )
    return " ".join(lines)
