"""
Deterministic listing analysis (PLANNING.md Sections B, D, H).

Price assessment, red flags, and missing-info notes are computed in pure Python
against the vehicles table. The LLM never judges the deal.
"""

from __future__ import annotations

import statistics
from typing import Optional

from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.vehicle import Vehicle
from app.schemas.comparison import DataReliability
from app.schemas.listing_analysis import (
    ExtractedListing,
    LabeledClaim,
    PriceAssessment,
    PriceRelative,
)

# Similarity windows for reference comps
YEAR_TOLERANCE = 2
MILEAGE_TOLERANCE_RATIO = 0.45  # ±45% of listing mileage
MILEAGE_TOLERANCE_ABS_MIN = 15_000
HIGHER_RATIO = 1.08
LOWER_RATIO = 0.92

DATASET_DISCLAIMER = (
    "Price comparison is based on AutoAI's demo reference dataset only — "
    "not authoritative real-market pricing, and not affiliated with PakWheels."
)

# PLANNING.md Section D — seller/buyer questions checklist
SELLER_QUESTIONS: list[str] = [
    "Are you the original owner?",
    "How many owners has this car had?",
    "Has the car been in any accidents? If so, what was repaired?",
    "Is the paint original, or have any panels been repainted?",
    "What is the current engine condition (noise, smoke, oil consumption)?",
    "What is the transmission condition (shifts, slips, service history)?",
    "Can the mileage be verified (service records, digital history)?",
    "Is there a complete service history available?",
    "What is the token / tax status (paid up to date)?",
    "Are the registration documents complete and clear?",
    "Is there any outstanding finance or bank hypothecation?",
    "Why are you selling?",
]


def _median(prices: list[int]) -> float:
    return float(statistics.median(prices))


def find_similar_vehicles(
    session: Session,
    extracted: ExtractedListing,
) -> list[Vehicle]:
    """
    Find reference comps: same make, overlapping model name, year ±2,
    mileage within a band when mileage is known.
    """
    if not extracted.make or not extracted.model:
        return []

    make = extracted.make.strip().lower()
    model_token = extracted.model.strip().lower()

    stmt = select(Vehicle)
    rows = list(session.execute(stmt).scalars().all())

    comps: list[Vehicle] = []
    for v in rows:
        if v.make.strip().lower() != make:
            continue
        # Model match: listing model contained in DB model or vice versa
        db_model = v.model.strip().lower()
        if model_token not in db_model and db_model not in model_token:
            # Also allow first token match (e.g. "Corolla" vs "Corolla Altis")
            listing_first = model_token.split()[0]
            db_first = db_model.split()[0]
            if listing_first != db_first:
                continue

        if extracted.year is not None:
            if abs(v.year - extracted.year) > YEAR_TOLERANCE:
                continue

        if extracted.mileage_km is not None and extracted.mileage_km > 0:
            tol = max(
                MILEAGE_TOLERANCE_ABS_MIN,
                int(extracted.mileage_km * MILEAGE_TOLERANCE_RATIO),
            )
            if abs(v.mileage_km - extracted.mileage_km) > tol:
                continue

        comps.append(v)

    return comps


def assess_price(
    extracted: ExtractedListing,
    comparables: list[Vehicle],
) -> PriceAssessment:
    """
    Deterministic asking-price vs reference median.

    Same inputs always yield the same relative assessment.
    """
    asking = extracted.asking_price
    ids = [v.id for v in comparables if v.id is not None]
    prices = [v.price for v in comparables]

    if asking is None:
        return PriceAssessment(
            relative=PriceRelative.insufficient_data,
            summary=(
                "Asking price was not found in the listing text, so a relative "
                "price assessment cannot be made."
            ),
            reliability=DataReliability.unknown,
            dataset_disclaimer=DATASET_DISCLAIMER,
            asking_price=None,
            reference_median=None,
            reference_count=len(prices),
            reference_min=min(prices) if prices else None,
            reference_max=max(prices) if prices else None,
            similar_vehicle_ids=ids,
        )

    if len(prices) < 1:
        return PriceAssessment(
            relative=PriceRelative.insufficient_data,
            summary=(
                "Not enough similar vehicles in our reference dataset to compare "
                "this asking price. Treat any market judgment as unknown."
            ),
            reliability=DataReliability.unknown,
            dataset_disclaimer=DATASET_DISCLAIMER,
            asking_price=asking,
            reference_median=None,
            reference_count=0,
            reference_min=None,
            reference_max=None,
            similar_vehicle_ids=[],
        )

    median = _median(prices)
    lo = min(prices)
    hi = max(prices)

    if asking > median * HIGHER_RATIO:
        relative = PriceRelative.higher
        summary = (
            f"Asking price PKR {asking:,} appears higher than similar listings "
            f"in our reference data (median PKR {int(median):,} across "
            f"{len(prices)} comparable vehicle(s))."
        )
    elif asking < median * LOWER_RATIO:
        relative = PriceRelative.lower
        summary = (
            f"Asking price PKR {asking:,} appears lower than similar listings "
            f"in our reference data (median PKR {int(median):,} across "
            f"{len(prices)} comparable vehicle(s)). Verify why before assuming "
            "a bargain."
        )
    else:
        relative = PriceRelative.in_line
        summary = (
            f"Asking price PKR {asking:,} appears in line with similar listings "
            f"in our reference data (median PKR {int(median):,} across "
            f"{len(prices)} comparable vehicle(s))."
        )

    return PriceAssessment(
        relative=relative,
        summary=summary,
        reliability=DataReliability.inference,
        dataset_disclaimer=DATASET_DISCLAIMER,
        asking_price=asking,
        reference_median=int(median),
        reference_count=len(prices),
        reference_min=lo,
        reference_max=hi,
        similar_vehicle_ids=ids,
    )


def _years_of_age(year: Optional[int], *, reference_year: int = 2026) -> Optional[int]:
    if year is None:
        return None
    return max(0, reference_year - year)


def build_red_flags(
    listing_text: str,
    extracted: ExtractedListing,
    price: PriceAssessment,
) -> list[LabeledClaim]:
    """Heuristic red flags — never assert accident-free or mechanical perfection."""
    flags: list[LabeledClaim] = []
    text_l = listing_text.lower()

    if price.relative == PriceRelative.higher:
        flags.append(
            LabeledClaim(
                text=(
                    "Asking price sits above the reference median for similar "
                    "vehicles in our demo dataset — negotiate or seek more comps."
                ),
                reliability=DataReliability.inference,
                category="red_flag",
            )
        )

    age = _years_of_age(extracted.year)
    if (
        age is not None
        and age > 0
        and extracted.mileage_km is not None
        and extracted.mileage_km > age * 28_000
    ):
        flags.append(
            LabeledClaim(
                text=(
                    f"Reported mileage ({extracted.mileage_km:,} km) is high for a "
                    f"{extracted.year} vehicle relative to a rough annual average — "
                    "verify odometer and usage history."
                ),
                reliability=DataReliability.inference,
                category="red_flag",
            )
        )

    if extracted.claims_accident_free or "accident free" in text_l or "accident-free" in text_l:
        flags.append(
            LabeledClaim(
                text=(
                    "The listing claims the car is accident-free, but that is an "
                    "unverified seller claim — not confirmed evidence. Treat "
                    "accident history as unknown until inspected."
                ),
                reliability=DataReliability.unknown,
                category="red_flag",
            )
        )

    if any(
        phrase in text_l
        for phrase in (
            "urgent sale",
            "must sell",
            "need cash",
            "leaving country",
            "price negotiable heavily",
        )
    ):
        flags.append(
            LabeledClaim(
                text=(
                    "Listing language suggests urgency to sell — may help negotiation, "
                    "but also warrants careful document and condition checks."
                ),
                reliability=DataReliability.inference,
                category="red_flag",
            )
        )

    # Explicit: never invent mechanical certainty
    if "perfect condition" in text_l or "like new" in text_l or "zero issues" in text_l:
        flags.append(
            LabeledClaim(
                text=(
                    "Seller describes near-perfect mechanical condition without "
                    "supporting inspection evidence — treat mechanical condition "
                    "as unknown until verified."
                ),
                reliability=DataReliability.unknown,
                category="red_flag",
            )
        )

    return flags


def build_missing_information(
    extracted: ExtractedListing,
) -> list[LabeledClaim]:
    missing: list[LabeledClaim] = []

    def add(text: str, reliability: DataReliability = DataReliability.fact) -> None:
        missing.append(
            LabeledClaim(
                text=text,
                reliability=reliability,
                category="missing_information",
            )
        )

    if extracted.asking_price is None:
        add("Asking price is not stated clearly in the pasted text.")
    if extracted.year is None:
        add("Model year is missing.")
    if extracted.mileage_km is None:
        add("Mileage (odometer) is missing.")
    if not extracted.location:
        add("Location / city is missing.")
    if not extracted.make or not extracted.model:
        add("Make and/or model could not be identified confidently.")

    if not extracted.mentions_owners and not extracted.ownership_text:
        add(
            "Ownership history (original owner / number of owners) is not mentioned."
        )
    if not extracted.claims_service_history and not extracted.service_history_text:
        add("Service history is not mentioned.")
    if not extracted.accident_text and not extracted.claims_accident_free:
        add(
            "Accident history is not mentioned — status is unknown without seller "
            "confirmation and inspection.",
            reliability=DataReliability.unknown,
        )
    else:
        # Even if mentioned, we do not elevate to FACT that history is clean
        add(
            "No independent inspection evidence for accident history was provided "
            "in the text — treat mechanical/accident status as unverified.",
            reliability=DataReliability.unknown,
        )

    if not extracted.claims_original_paint:
        add("Original paint / panel work status is not mentioned.")

    add(
        "Token/tax status, registration documents, and outstanding finance are "
        "not confirmed in the listing text."
    )

    return missing


def build_notes(
    extracted: ExtractedListing,
    price: PriceAssessment,
) -> list[LabeledClaim]:
    notes: list[LabeledClaim] = []

    notes.append(
        LabeledClaim(
            text=DATASET_DISCLAIMER,
            reliability=DataReliability.fact,
            category="note",
        )
    )

    if extracted.year is not None:
        notes.append(
            LabeledClaim(
                text=f"Listing year extracted as {extracted.year}.",
                reliability=DataReliability.fact,
                category="note",
            )
        )
    if extracted.mileage_km is not None:
        notes.append(
            LabeledClaim(
                text=f"Listing mileage extracted as {extracted.mileage_km:,} km.",
                reliability=DataReliability.fact,
                category="note",
            )
        )
    if extracted.location:
        notes.append(
            LabeledClaim(
                text=f"Location extracted as {extracted.location}.",
                reliability=DataReliability.fact,
                category="note",
            )
        )

    if price.relative == PriceRelative.lower:
        notes.append(
            LabeledClaim(
                text=(
                    "A below-median asking price can signal a genuine deal or "
                    "undisclosed issues — ask about finance, accidents, and "
                    "reconditioning before negotiating hard."
                ),
                reliability=DataReliability.inference,
                category="negotiation",
            )
        )
    elif price.relative == PriceRelative.higher:
        notes.append(
            LabeledClaim(
                text=(
                    "Consider negotiating toward the reference median, or ask what "
                    "justifies the premium (options, service record, low owners)."
                ),
                reliability=DataReliability.inference,
                category="negotiation",
            )
        )

    notes.append(
        LabeledClaim(
            text=(
                "AutoAI cannot certify accident history or mechanical condition "
                "from listing text alone — inspection evidence is required."
            ),
            reliability=DataReliability.fact,
            category="note",
        )
    )

    return notes


def template_advisor_summary(
    extracted: ExtractedListing,
    price: PriceAssessment,
    red_flags: list[LabeledClaim],
    missing: list[LabeledClaim],
) -> str:
    label = " / ".join(
        p
        for p in (extracted.make, extracted.model, extracted.variant)
        if p
    ) or "This listing"
    year = f" ({extracted.year})" if extracted.year else ""
    parts = [
        f"{label}{year}: {price.summary}",
        DATASET_DISCLAIMER,
    ]
    if red_flags:
        parts.append(f"{len(red_flags)} caution note(s) were flagged for review.")
    if missing:
        parts.append(
            f"{len(missing)} information gap(s) should be clarified with the seller."
        )
    parts.append(
        "Do not treat seller claims about accidents or mechanical condition as "
        "verified facts without inspection evidence."
    )
    return " ".join(parts)


def seller_questions() -> list[str]:
    return list(SELLER_QUESTIONS)
