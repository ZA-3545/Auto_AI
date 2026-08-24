"""
Deterministic maintenance checklist rules (PLANNING.md Section D & H).

Mileage/age thresholds only — no LLM guessing. Items are educational prompts
to discuss with a mechanic, not confirmed service history.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.schemas.comparison import DataReliability
from app.schemas.maintenance import MaintenanceItem, VehicleProfile

REFERENCE_YEAR = 2026


@dataclass(frozen=True)
class _Rule:
    category: str
    item: str
    reason: str
    min_mileage: int = 0
    min_age_years: int = 0


# Threshold-based rules — applied when mileage OR age meets minimum.
RULES: tuple[_Rule, ...] = (
    _Rule(
        "Basics",
        "Review manufacturer service schedule",
        "Every vehicle has model-specific intervals in the handbook or workshop manual.",
    ),
    _Rule(
        "Basics",
        "Confirm last oil & filter change date",
        "Fresh oil is the most common routine service; records help verify upkeep.",
        min_mileage=5_000,
    ),
    _Rule(
        "Engine",
        "Engine oil & filter change interval",
        "Typical routine service around 5,000–10,000 km depending on oil type and driving.",
        min_mileage=10_000,
    ),
    _Rule(
        "Filters",
        "Air filter inspection / replacement",
        "Clogged air filters reduce performance and fuel economy.",
        min_mileage=15_000,
    ),
    _Rule(
        "Brakes",
        "Brake pad and disc inspection",
        "Wear increases stopping distance; inspect before long trips.",
        min_mileage=30_000,
    ),
    _Rule(
        "Fluids",
        "Brake fluid moisture / level check",
        "Old brake fluid can absorb moisture and reduce braking effectiveness.",
        min_mileage=30_000,
    ),
    _Rule(
        "Transmission",
        "Transmission / gearbox fluid check",
        "Fluid condition matters for smooth shifts in automatic and manual cars.",
        min_mileage=40_000,
    ),
    _Rule(
        "Engine",
        "Spark plug condition (petrol)",
        "Worn plugs can cause misfires and poor fuel average on petrol engines.",
        min_mileage=60_000,
    ),
    _Rule(
        "Cooling",
        "Coolant level and hose inspection",
        "Cooling system issues can lead to overheating in hot climates.",
        min_mileage=60_000,
    ),
    _Rule(
        "Engine",
        "Timing belt / chain inspection",
        "Many engines use a timing belt that must be replaced at a set interval — "
        "verify for your exact engine variant with a workshop.",
        min_mileage=80_000,
    ),
    _Rule(
        "Suspension",
        "Suspension bushings and shock absorbers",
        "High mileage often brings worn bushings or weak dampers affecting ride and tyre wear.",
        min_mileage=80_000,
    ),
    _Rule(
        "Brakes",
        "Full brake system review (pads, discs, lines)",
        "Higher mileage cars often need more than a quick pad glance.",
        min_mileage=100_000,
    ),
    _Rule(
        "Engine",
        "Drive belts and tensioners",
        "Cracked or glazed belts can fail suddenly; inspect at major service milestones.",
        min_mileage=100_000,
    ),
    _Rule(
        "Transmission",
        "Clutch wear check (manual transmission)",
        "Slipping or high bite point may indicate clutch replacement is due.",
        min_mileage=100_000,
    ),
    _Rule(
        "Engine",
        "Engine mount condition",
        "Excess vibration or thumping under load can indicate worn mounts.",
        min_mileage=100_000,
    ),
    _Rule(
        "Electrical",
        "Battery health test",
        "Batteries typically weaken after several years, especially in heat.",
        min_age_years=4,
    ),
    _Rule(
        "Underbody",
        "Rust / underbody inspection",
        "Older vehicles in humid or coastal areas benefit from periodic underbody checks.",
        min_age_years=6,
    ),
    _Rule(
        "Tyres",
        "Tyre age and tread depth",
        "Rubber hardens with age even if tread looks acceptable.",
        min_age_years=5,
    ),
)


def _age_years(year: int | None, *, reference: int = REFERENCE_YEAR) -> int | None:
    if year is None:
        return None
    return max(0, reference - year)


def build_maintenance_checklist(profile: VehicleProfile) -> list[MaintenanceItem]:
    """
    Build checklist from mileage/age thresholds.

    Same profile always yields the same items (deterministic).
    """
    mileage = profile.mileage_km or 0
    age = _age_years(profile.year)

    items: list[MaintenanceItem] = []
    seen: set[str] = set()

    for rule in RULES:
        mileage_ok = mileage >= rule.min_mileage
        age_ok = age is not None and age >= rule.min_age_years
        # Rules with min_mileage=0 apply to everyone; age-only rules need age_ok
        if rule.min_mileage == 0 and rule.min_age_years == 0:
            applies = True
        elif rule.min_mileage > 0 and rule.min_age_years == 0:
            applies = mileage_ok
        elif rule.min_age_years > 0 and rule.min_mileage == 0:
            applies = age_ok
        else:
            applies = mileage_ok or age_ok

        if not applies:
            continue

        key = f"{rule.category}:{rule.item}"
        if key in seen:
            continue
        seen.add(key)

        reliability = (
            DataReliability.fact
            if rule.min_mileage == 0 and rule.min_age_years == 0
            else DataReliability.inference
        )
        items.append(
            MaintenanceItem(
                category=rule.category,
                item=rule.item,
                reason=rule.reason,
                source="rule",
                reliability=reliability,
            )
        )

    return items
