"""
Configurable recommendation scoring weights (PLANNING.md Section E).

Weights must sum to 1.0. Adjust here — do not hardcode inline in scoring logic.
"""

from typing import TypedDict


class RecommendationWeights(TypedDict):
    budget_fit: float
    purpose_suitability: float
    fuel_economy: float
    resale: float
    mileage_condition: float


# Default weights per PLANNING.md Section E
DEFAULT_RECOMMENDATION_WEIGHTS: RecommendationWeights = {
    "budget_fit": 0.30,
    "purpose_suitability": 0.25,
    "fuel_economy": 0.20,
    "resale": 0.15,
    "mileage_condition": 0.10,
}


def validate_weights(weights: RecommendationWeights) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Recommendation weights must sum to 1.0, got {total}")
