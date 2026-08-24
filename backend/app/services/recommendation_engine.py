"""
Deterministic recommendation engine (PLANNING.md Section E).

Pure Python scoring — no LLM. Unit-testable independently of the AI layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.recommendation_weights import (
    DEFAULT_RECOMMENDATION_WEIGHTS,
    RecommendationWeights,
    validate_weights,
)
from app.models.vehicle import BodyType, Condition, FuelType, Vehicle
from app.schemas.extraction import ConditionPreference, ExtractedRequirements
from app.schemas.recommendation import FactorScores, RecommendedVehicle
from app.schemas.vehicle import VehicleRead

# Neutral score when a requirement dimension is not specified
NEUTRAL_SCORE = 50.0

# Fuel economy normalization (Pakistani market typical range, km/l)
FUEL_KMPL_MIN = 8.0
FUEL_KMPL_MAX = 22.0

# Purpose → body-type suitability (0–100).
# For "family", hatchbacks are refined further by engine size in
# score_purpose_suitability() — small city/kei hatches must not score like sedans.
PURPOSE_BODY_SCORES: dict[str, dict[str, float]] = {
    "family": {
        BodyType.suv.value: 100,
        BodyType.crossover.value: 95,
        BodyType.van.value: 92,
        BodyType.sedan.value: 90,
        # Mid/large hatch baseline; small hatches overridden below
        BodyType.hatchback.value: 72,
        BodyType.pickup.value: 45,
        BodyType.coupe.value: 28,
    },
    "commute": {
        BodyType.sedan.value: 95,
        BodyType.hatchback.value: 90,
        BodyType.crossover.value: 75,
        BodyType.suv.value: 65,
        BodyType.coupe.value: 60,
        BodyType.van.value: 50,
        BodyType.pickup.value: 40,
    },
    "business": {
        BodyType.sedan.value: 100,
        BodyType.crossover.value: 80,
        BodyType.suv.value: 75,
        BodyType.hatchback.value: 60,
        BodyType.van.value: 55,
        BodyType.pickup.value: 50,
        BodyType.coupe.value: 45,
    },
}

# Family purpose: engine capacity bands for hatchbacks (cc).
# Kei / micro city cars (Alto, Mira, Dayz, etc.) are poor family fits.
FAMILY_HATCH_SMALL_CC = 800  # inclusive — city/kei hatch
FAMILY_HATCH_COMPACT_CC = 1100  # inclusive — compact hatch (Cultus-class)


def _body_value(vehicle: Vehicle) -> str:
    return (
        vehicle.body_type.value
        if isinstance(vehicle.body_type, BodyType)
        else str(vehicle.body_type)
    )


def family_suitability_score(vehicle: Vehicle) -> float:
    """
    Deterministic family-fit score from body_type + size signals.

    Sedans / SUVs / crossovers / vans score high.
    Small city hatchbacks (≤800cc) score low; compact hatches mid; larger hatches OK.
    Explainable and independent of budget / fuel scoring.
    """
    body = _body_value(vehicle)
    base = PURPOSE_BODY_SCORES["family"].get(body, NEUTRAL_SCORE)

    if body != BodyType.hatchback.value:
        return float(base)

    cc = vehicle.engine_capacity
    if cc is None:
        # Unknown displacement — treat cautiously below mid-hatch baseline
        return 50.0
    if cc <= FAMILY_HATCH_SMALL_CC:
        # Alto / kei-class — not suitable as a primary family car
        return 32.0
    if cc <= FAMILY_HATCH_COMPACT_CC:
        # Compact hatch — limited space vs sedan/SUV
        return 55.0
    # Mid hatch (e.g. Swift 1200cc) — acceptable family compromise
    return float(base)


@dataclass(frozen=True)
class ScoredVehicle:
    vehicle: Vehicle
    match_score: float
    factor_scores: FactorScores
    explanation: str


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_budget_fit(vehicle: Vehicle, requirements: ExtractedRequirements) -> float:
    """
    How well the price fits the stated budget without exceeding budget_max.

    Within budget: higher score when price uses more of the available budget
    (closer to budget_max). Over budget → 0.
    """
    price = vehicle.price

    if requirements.budget_max is not None:
        if price > requirements.budget_max:
            return 0.0
        if requirements.budget_min is not None:
            if price < requirements.budget_min:
                return 0.0
            span = requirements.budget_max - requirements.budget_min
            if span <= 0:
                return 100.0 if price == requirements.budget_max else 0.0
            # Prefer upper half of the budget range
            position = (price - requirements.budget_min) / span
            return _clamp(50.0 + position * 50.0)
        if requirements.budget_max <= 0:
            return NEUTRAL_SCORE
        return _clamp(100.0 * price / requirements.budget_max)

    if requirements.budget_min is not None:
        if price < requirements.budget_min:
            return _clamp(100.0 * price / requirements.budget_min * 0.5)
        return 100.0

    return NEUTRAL_SCORE


def score_purpose_suitability(
    vehicle: Vehicle, requirements: ExtractedRequirements
) -> float:
    """Map stated purpose to body-type (and size) suitability."""
    if not requirements.purpose:
        return NEUTRAL_SCORE

    purpose_key = requirements.purpose.strip().lower()
    body = _body_value(vehicle)

    if "family" in purpose_key:
        return family_suitability_score(vehicle)

    for key, mapping in PURPOSE_BODY_SCORES.items():
        if key in purpose_key:
            return mapping.get(body, NEUTRAL_SCORE)

    # Unknown purpose — slight boost if user also specified matching body_type
    if requirements.body_type and requirements.body_type.lower() == body.lower():
        return 85.0
    return NEUTRAL_SCORE


def score_fuel_economy(vehicle: Vehicle, requirements: ExtractedRequirements) -> float:
    """Higher km/l → higher score; EVs score well; unknown averages score lower."""
    if vehicle.fuel_type == FuelType.electric:
        base = 95.0
    elif vehicle.fuel_average_kmpl is not None:
        kmpl = vehicle.fuel_average_kmpl
        span = FUEL_KMPL_MAX - FUEL_KMPL_MIN
        base = _clamp((kmpl - FUEL_KMPL_MIN) / span * 100.0)
    elif vehicle.fuel_type == FuelType.hybrid:
        base = 80.0
    else:
        base = 35.0

    # fuel_priority does not change weights (fixed per Section E) but boosts
    # interpretation in explanations; score itself stays catalog-based.
    if requirements.fuel_priority and base >= 60:
        return _clamp(base + 5.0)
    return base


def score_resale(vehicle: Vehicle, requirements: ExtractedRequirements) -> float:
    """resale_rating is 1–5 in demo data → scale to 0–100."""
    base = (vehicle.resale_rating / 5.0) * 100.0
    if requirements.resale_priority and base >= 60:
        return _clamp(base + 5.0)
    return base


def score_mileage_condition(
    vehicle: Vehicle, requirements: ExtractedRequirements
) -> float:
    """Condition match + mileage bands for used cars."""
    condition_score = NEUTRAL_SCORE
    if requirements.condition is not None:
        vehicle_cond = (
            vehicle.condition.value
            if isinstance(vehicle.condition, Condition)
            else str(vehicle.condition)
        )
        if vehicle_cond == requirements.condition.value:
            condition_score = 100.0
        else:
            condition_score = 20.0

    mileage = vehicle.mileage_km
    if mileage <= 500:
        mileage_score = 100.0
    elif mileage <= 30_000:
        mileage_score = 90.0
    elif mileage <= 60_000:
        mileage_score = 75.0
    elif mileage <= 100_000:
        mileage_score = 55.0
    else:
        mileage_score = 35.0

    if requirements.condition is None:
        return mileage_score
    return (condition_score * 0.6) + (mileage_score * 0.4)


def _label(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "good"
    if score >= 40:
        return "moderate"
    return "weak"


def build_explanation(factors: FactorScores, requirements: ExtractedRequirements) -> str:
    """Template-based deterministic explanation — not LLM-generated."""
    parts: list[str] = []

    if factors.budget_fit >= 80:
        parts.append("Strong budget fit")
    elif factors.budget_fit <= 20:
        parts.append("Over budget or poor budget fit")
    else:
        parts.append(f"{_label(factors.budget_fit).capitalize()} budget fit")

    if requirements.purpose:
        parts.append(f"{_label(factors.purpose_suitability)} {requirements.purpose} suitability")

    if requirements.fuel_priority or factors.fuel_economy >= 70:
        parts.append(f"{_label(factors.fuel_economy)} fuel economy")
    elif factors.fuel_economy <= 40:
        parts.append("Limited fuel economy data")

    if requirements.resale_priority or factors.resale >= 70:
        parts.append(f"{_label(factors.resale)} resale value")
    else:
        parts.append(f"{_label(factors.resale)} resale")

    parts.append(f"{_label(factors.mileage_condition)} mileage/condition")

    return ", ".join(parts) + "."


def compute_factor_scores(
    vehicle: Vehicle, requirements: ExtractedRequirements
) -> FactorScores:
    return FactorScores(
        budget_fit=round(score_budget_fit(vehicle, requirements), 2),
        purpose_suitability=round(score_purpose_suitability(vehicle, requirements), 2),
        fuel_economy=round(score_fuel_economy(vehicle, requirements), 2),
        resale=round(score_resale(vehicle, requirements), 2),
        mileage_condition=round(score_mileage_condition(vehicle, requirements), 2),
    )


def compute_match_score(
    factors: FactorScores,
    weights: RecommendationWeights = DEFAULT_RECOMMENDATION_WEIGHTS,
) -> float:
    validate_weights(weights)
    total = (
        factors.budget_fit * weights["budget_fit"]
        + factors.purpose_suitability * weights["purpose_suitability"]
        + factors.fuel_economy * weights["fuel_economy"]
        + factors.resale * weights["resale"]
        + factors.mileage_condition * weights["mileage_condition"]
    )
    return round(_clamp(total), 2)


def score_vehicle(
    vehicle: Vehicle,
    requirements: ExtractedRequirements,
    weights: RecommendationWeights = DEFAULT_RECOMMENDATION_WEIGHTS,
) -> ScoredVehicle:
    factors = compute_factor_scores(vehicle, requirements)
    match = compute_match_score(factors, weights)
    explanation = build_explanation(factors, requirements)
    return ScoredVehicle(
        vehicle=vehicle,
        match_score=match,
        factor_scores=factors,
        explanation=explanation,
    )


def rank_vehicles(
    vehicles: list[Vehicle],
    requirements: ExtractedRequirements,
    weights: RecommendationWeights = DEFAULT_RECOMMENDATION_WEIGHTS,
) -> list[RecommendedVehicle]:
    """Score and sort vehicles by match_score descending."""
    scored = [score_vehicle(v, requirements, weights) for v in vehicles]
    scored.sort(key=lambda s: (-s.match_score, s.vehicle.id or 0))

    return [
        RecommendedVehicle(
            vehicle=VehicleRead.model_validate(s.vehicle),
            match_score=s.match_score,
            factor_scores=s.factor_scores,
            explanation=s.explanation,
        )
        for s in scored
    ]
