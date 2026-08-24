"""Listing analyzer tests — deterministic price + no false certainty (Section H)."""

from __future__ import annotations

import re

import pytest
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.ai.base import AIProvider
from app.models.vehicle import (
    BodyType,
    Condition,
    FuelType,
    Transmission,
    Vehicle,
)
from app.schemas.comparison import DataReliability
from app.schemas.extraction import ExtractedRequirements
from app.schemas.listing_analysis import ExtractedListing, PriceRelative
from app.services.listing_analysis import analyze_listing
from app.services.listing_analysis_engine import (
    SELLER_QUESTIONS,
    assess_price,
    build_missing_information,
    build_notes,
    build_red_flags,
    find_similar_vehicles,
)


class StubListingProvider(AIProvider):
    name = "stub"

    def __init__(self, extracted: ExtractedListing) -> None:
        self._extracted = extracted

    @property
    def model_name(self) -> str:
        return "stub-model"

    def extract_requirements(self, message: str) -> ExtractedRequirements:
        raise NotImplementedError

    def extract_listing(self, listing_text: str) -> ExtractedListing:
        return self._extracted


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()

    fixtures = [
        Vehicle(
            make="Toyota",
            model="Corolla Altis",
            year=2019,
            price=3_800_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1800,
            mileage_km=70_000,
            fuel_average_kmpl=12.0,
            resale_rating=5,
        ),
        Vehicle(
            make="Toyota",
            model="Corolla Gli",
            year=2018,
            price=3_500_000,
            city="Karachi",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1300,
            mileage_km=80_000,
            fuel_average_kmpl=13.0,
            resale_rating=5,
        ),
        Vehicle(
            make="Toyota",
            model="Corolla Altis",
            year=2020,
            price=4_200_000,
            city="Islamabad",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1800,
            mileage_km=55_000,
            fuel_average_kmpl=12.5,
            resale_rating=5,
        ),
        Vehicle(
            make="Honda",
            model="City",
            year=2019,
            price=3_400_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1500,
            mileage_km=60_000,
            fuel_average_kmpl=14.0,
            resale_rating=4,
        ),
    ]
    session.add_all(fixtures)
    session.commit()
    yield session
    session.close()


def _corolla_extracted(*, asking: int) -> ExtractedListing:
    return ExtractedListing(
        make="Toyota",
        model="Corolla",
        variant="Altis",
        year=2019,
        asking_price=asking,
        mileage_km=75_000,
        location="Lahore",
        claims_accident_free=False,
        claims_original_paint=False,
        claims_service_history=False,
        mentions_owners=False,
    )


def test_price_assessment_is_deterministic(db_session: Session) -> None:
    extracted = _corolla_extracted(asking=4_200_000)
    comps = find_similar_vehicles(db_session, extracted)
    assert len(comps) >= 2

    a = assess_price(extracted, comps)
    b = assess_price(extracted, comps)
    assert a.relative == b.relative
    assert a.summary == b.summary
    assert a.reference_median == b.reference_median
    assert a.dataset_disclaimer


def test_price_higher_vs_lower_vs_inline(db_session: Session) -> None:
    comps = find_similar_vehicles(db_session, _corolla_extracted(asking=4_000_000))
    medianish = assess_price(_corolla_extracted(asking=3_800_000), comps)
    high = assess_price(_corolla_extracted(asking=6_000_000), comps)
    low = assess_price(_corolla_extracted(asking=2_000_000), comps)

    assert medianish.relative == PriceRelative.in_line
    assert high.relative == PriceRelative.higher
    assert low.relative == PriceRelative.lower
    assert high.reliability == DataReliability.inference
    assert "reference" in high.summary.lower() or "reference" in high.dataset_disclaimer.lower()


def test_insufficient_comps_is_unknown(db_session: Session) -> None:
    extracted = ExtractedListing(
        make="Bugatti",
        model="Chiron",
        year=2020,
        asking_price=50_000_000,
        mileage_km=5_000,
    )
    comps = find_similar_vehicles(db_session, extracted)
    assessment = assess_price(extracted, comps)
    assert assessment.relative == PriceRelative.insufficient_data
    assert assessment.reliability == DataReliability.unknown


FORBIDDEN_CERTAINTY = re.compile(
    r"(?<!cannot certify that any vehicle )\b("
    r"this car is accident[- ]free|"
    r"vehicle is accident[- ]free|"
    r"is mechanically perfect|"
    r"guaranteed accident|"
    r"definitely accident[- ]free|"
    r"confirmed accident[- ]free|"
    r"zero accidents verified"
    r")\b",
    re.IGNORECASE,
)


def test_never_claims_accident_free_or_perfect_without_evidence(
    db_session: Session,
) -> None:
    listing = (
        "2019 Corolla Altis, 75,000 km, Lahore, PKR 42 lakh. "
        "Accident free, perfect condition, original paint."
    )
    extracted = ExtractedListing(
        make="Toyota",
        model="Corolla",
        variant="Altis",
        year=2019,
        asking_price=4_200_000,
        mileage_km=75_000,
        location="Lahore",
        claims_accident_free=True,
        claims_original_paint=True,
        claims_service_history=False,
        mentions_owners=False,
        accident_text="Accident free",
    )
    provider = StubListingProvider(extracted)
    result = analyze_listing(
        db_session,
        listing,
        provider=provider,
        include_advisor_summary=False,
    )

    blobs = [
        result.advisor_summary or "",
        result.price_assessment.summary,
        *[c.text for c in result.red_flags],
        *[c.text for c in result.missing_information],
        *[c.text for c in result.notes],
    ]
    joined = "\n".join(blobs)
    assert FORBIDDEN_CERTAINTY.search(joined) is None

    # Seller claim must stay UNKNOWN / unverified — never FACT that the car is clean
    assert any(
        c.reliability == DataReliability.unknown
        and "unverified" in c.text.lower()
        and "accident" in c.text.lower()
        for c in result.red_flags
    )


def test_seller_questions_cover_planning_checklist() -> None:
    required_keywords = [
        "original owner",
        "owners",
        "accident",
        "paint",
        "engine",
        "transmission",
        "mileage",
        "service",
        "token",
        "registration",
        "finance",
        "selling",
    ]
    joined = " ".join(SELLER_QUESTIONS).lower()
    for word in required_keywords:
        assert word in joined


def test_analyze_listing_end_to_end_with_stub(db_session: Session) -> None:
    extracted = _corolla_extracted(asking=4_200_000)
    result = analyze_listing(
        db_session,
        "2019 Corolla Altis, 75,000 km, Lahore, PKR 42 lakh",
        provider=StubListingProvider(extracted),
        include_advisor_summary=False,
    )
    assert result.extracted.asking_price == 4_200_000
    assert result.price_assessment.reference_count >= 1
    assert result.seller_questions == SELLER_QUESTIONS
    assert result.advisor_summary_source == "template"
    assert "demo" in result.price_assessment.dataset_disclaimer.lower() or (
        "reference" in result.price_assessment.dataset_disclaimer.lower()
    )


def test_missing_info_flags_ownership_and_service() -> None:
    extracted = ExtractedListing(make="Toyota", model="Corolla", year=2019)
    missing = build_missing_information(extracted)
    texts = " ".join(m.text.lower() for m in missing)
    assert "ownership" in texts or "owners" in texts
    assert "service" in texts
    assert any(m.reliability == DataReliability.unknown for m in missing)


def test_red_flag_high_mileage() -> None:
    extracted = ExtractedListing(
        make="Toyota",
        model="Corolla",
        year=2022,
        mileage_km=200_000,
        asking_price=3_000_000,
    )
    price = assess_price(extracted, [])
    flags = build_red_flags("high km car", extracted, price)
    assert any("mileage" in f.text.lower() for f in flags)


def test_notes_never_certify_mechanical_perfection() -> None:
    extracted = _corolla_extracted(asking=3_800_000)
    price = assess_price(extracted, [])
    notes = build_notes(extracted, price)
    joined = " ".join(n.text for n in notes)
    assert FORBIDDEN_CERTAINTY.search(joined) is None
    assert "inspection" in joined.lower()
    assert "cannot certify" in joined.lower()
