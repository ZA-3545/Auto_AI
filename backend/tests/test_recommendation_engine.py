"""Unit tests for deterministic recommendation scoring (PLANNING.md Section E)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.core.database import get_db
from app.core.recommendation_weights import DEFAULT_RECOMMENDATION_WEIGHTS
from app.main import app
from app.models.vehicle import (
    BodyType,
    Condition,
    FuelType,
    Transmission,
    Vehicle,
)
from app.schemas.extraction import (
    ConditionPreference,
    ExtractedRequirements,
    TransmissionPreference,
)
from app.services.recommendation_engine import (
    compute_match_score,
    rank_vehicles,
    score_budget_fit,
    score_fuel_economy,
    score_mileage_condition,
    score_purpose_suitability,
    score_resale,
    score_vehicle,
)


def _vehicle(
    *,
    price: int = 3_000_000,
    body_type: BodyType = BodyType.sedan,
    fuel_average_kmpl: float | None = 12.0,
    resale_rating: int = 4,
    mileage_km: int = 40_000,
    condition: Condition = Condition.used,
    fuel_type: FuelType = FuelType.petrol,
    vehicle_id: int = 1,
) -> Vehicle:
    return Vehicle(
        id=vehicle_id,
        make="Toyota",
        model="Corolla",
        year=2021,
        price=price,
        city="Lahore",
        condition=condition,
        transmission=Transmission.automatic,
        body_type=body_type,
        fuel_type=fuel_type,
        engine_capacity=1300,
        mileage_km=mileage_km,
        fuel_average_kmpl=fuel_average_kmpl,
        resale_rating=resale_rating,
    )


def _requirements(**kwargs) -> ExtractedRequirements:
    defaults = {
        "budget_min": None,
        "budget_max": 3_500_000,
        "city": "Lahore",
        "condition": ConditionPreference.used,
        "transmission": TransmissionPreference.automatic,
        "body_type": None,
        "purpose": "family",
        "fuel_priority": None,
        "resale_priority": None,
        "needs_clarification": False,
        "clarification_question": None,
    }
    defaults.update(kwargs)
    return ExtractedRequirements(**defaults)


def test_budget_fit_within_budget_scores_higher_than_over_budget() -> None:
    req = _requirements(budget_max=3_000_000)
    within = _vehicle(price=2_900_000)
    over = _vehicle(price=3_500_000, vehicle_id=2)

    within_score = score_budget_fit(within, req)
    over_score = score_budget_fit(over, req)

    assert within_score > 0
    assert over_score == 0.0
    assert within_score > over_score


def test_budget_fit_closer_to_max_scores_higher() -> None:
    req = _requirements(budget_max=4_000_000)
    near_max = _vehicle(price=3_800_000, vehicle_id=1)
    far_below = _vehicle(price=1_000_000, vehicle_id=2)

    assert score_budget_fit(near_max, req) > score_budget_fit(far_below, req)


def test_purpose_family_prefers_suv_over_coupe() -> None:
    req = _requirements(purpose="family")
    suv = _vehicle(body_type=BodyType.suv, vehicle_id=1)
    coupe = _vehicle(body_type=BodyType.coupe, vehicle_id=2)

    assert score_purpose_suitability(suv, req) > score_purpose_suitability(coupe, req)


def test_purpose_family_sedan_scores_higher_than_small_hatch() -> None:
    """Family purpose: mid-size sedan beats small city hatch on suitability alone."""
    req = _requirements(purpose="family", budget_max=None, city=None, transmission=None)
    sedan = _vehicle(
        body_type=BodyType.sedan,
        price=3_200_000,
        vehicle_id=1,
    )
    sedan.engine_capacity = 1300
    sedan.model = "Corolla"
    small_hatch = _vehicle(
        body_type=BodyType.hatchback,
        price=2_200_000,
        fuel_average_kmpl=18.0,
        vehicle_id=2,
    )
    small_hatch.engine_capacity = 660
    small_hatch.make = "Suzuki"
    small_hatch.model = "Alto"

    sedan_fit = score_purpose_suitability(sedan, req)
    hatch_fit = score_purpose_suitability(small_hatch, req)
    assert sedan_fit > hatch_fit
    assert sedan_fit >= 85
    assert hatch_fit <= 40


def test_purpose_family_suv_scores_higher_than_small_hatch() -> None:
    req = _requirements(purpose="family", budget_max=None)
    suv = _vehicle(body_type=BodyType.suv, vehicle_id=1)
    suv.engine_capacity = 2000
    small_hatch = _vehicle(body_type=BodyType.hatchback, vehicle_id=2)
    small_hatch.engine_capacity = 660

    assert score_purpose_suitability(suv, req) > score_purpose_suitability(
        small_hatch, req
    )


def test_purpose_family_mid_hatch_scores_above_small_hatch() -> None:
    req = _requirements(purpose="family")
    mid = _vehicle(body_type=BodyType.hatchback, vehicle_id=1)
    mid.engine_capacity = 1200
    mid.model = "Swift"
    small = _vehicle(body_type=BodyType.hatchback, vehicle_id=2)
    small.engine_capacity = 660
    small.model = "Alto"

    assert score_purpose_suitability(mid, req) > score_purpose_suitability(small, req)


def test_family_rank_prefers_sedan_over_alto_when_both_in_budget() -> None:
    """
    Similar budget fit: sedan should outrank small hatch for purpose=family
    even if the hatch has better fuel average.
    """
    req = _requirements(
        purpose="family",
        budget_max=5_000_000,
        city=None,
        transmission=None,
        condition=None,
    )
    sedan = _vehicle(
        price=3_200_000,
        body_type=BodyType.sedan,
        fuel_average_kmpl=12.5,
        resale_rating=5,
        vehicle_id=1,
    )
    sedan.engine_capacity = 1300
    sedan.make = "Toyota"
    sedan.model = "Corolla"

    alto = _vehicle(
        price=2_200_000,
        body_type=BodyType.hatchback,
        fuel_average_kmpl=18.0,
        resale_rating=4,
        vehicle_id=2,
    )
    alto.engine_capacity = 660
    alto.make = "Suzuki"
    alto.model = "Alto"

    ranked = rank_vehicles([alto, sedan], req)
    assert ranked[0].vehicle.model == "Corolla"
    assert (
        ranked[0].factor_scores.purpose_suitability
        > ranked[1].factor_scores.purpose_suitability
    )


def test_over_budget_family_car_still_loses_to_in_budget() -> None:
    """Budget fit still dominates: over-budget SUV must not beat in-budget hatch."""
    req = _requirements(purpose="family", budget_max=2_500_000, city=None, transmission=None)
    over_budget_suv = _vehicle(
        price=9_000_000,
        body_type=BodyType.suv,
        vehicle_id=1,
    )
    over_budget_suv.engine_capacity = 2000
    in_budget_hatch = _vehicle(
        price=2_200_000,
        body_type=BodyType.hatchback,
        vehicle_id=2,
    )
    in_budget_hatch.engine_capacity = 660

    assert score_budget_fit(over_budget_suv, req) == 0.0
    assert score_budget_fit(in_budget_hatch, req) > 0
    ranked = rank_vehicles([over_budget_suv, in_budget_hatch], req)
    assert ranked[0].vehicle.id == in_budget_hatch.id


def test_fuel_economy_higher_kmpl_scores_higher() -> None:
    req = _requirements()
    efficient = _vehicle(fuel_average_kmpl=20.0, vehicle_id=1)
    thirsty = _vehicle(fuel_average_kmpl=9.0, vehicle_id=2)

    assert score_fuel_economy(efficient, req) > score_fuel_economy(thirsty, req)


def test_resale_rating_maps_to_score() -> None:
    req = _requirements()
    high = _vehicle(resale_rating=5, vehicle_id=1)
    low = _vehicle(resale_rating=2, vehicle_id=2)

    assert score_resale(high, req) > score_resale(low, req)


def test_mileage_condition_lower_mileage_scores_higher() -> None:
    req = _requirements(condition=ConditionPreference.used)
    low_mileage = _vehicle(mileage_km=20_000, vehicle_id=1)
    high_mileage = _vehicle(mileage_km=150_000, vehicle_id=2)

    assert score_mileage_condition(low_mileage, req) > score_mileage_condition(
        high_mileage, req
    )


def test_match_score_uses_configured_weights() -> None:
    from app.schemas.recommendation import FactorScores

    factors = FactorScores(
        budget_fit=100.0,
        purpose_suitability=100.0,
        fuel_economy=100.0,
        resale=100.0,
        mileage_condition=100.0,
    )
    assert compute_match_score(factors) == 100.0

    factors_zero = FactorScores(
        budget_fit=0.0,
        purpose_suitability=0.0,
        fuel_economy=0.0,
        resale=0.0,
        mileage_condition=0.0,
    )
    assert compute_match_score(factors_zero) == 0.0

    # Spot-check weighted sum
    factors_mixed = FactorScores(
        budget_fit=100.0,
        purpose_suitability=0.0,
        fuel_economy=0.0,
        resale=0.0,
        mileage_condition=0.0,
    )
    expected = 100.0 * DEFAULT_RECOMMENDATION_WEIGHTS["budget_fit"]
    assert compute_match_score(factors_mixed) == pytest.approx(expected, abs=0.01)


def test_score_vehicle_includes_explanation() -> None:
    req = _requirements()
    result = score_vehicle(_vehicle(), req)
    assert 0 <= result.match_score <= 100
    assert result.explanation
    assert "budget" in result.explanation.lower()


def test_rank_vehicles_sorted_by_match_score_desc() -> None:
    req = _requirements(budget_max=3_500_000, purpose="family")
    good = _vehicle(price=3_200_000, body_type=BodyType.suv, fuel_average_kmpl=18.0, vehicle_id=1)
    poor = _vehicle(price=4_500_000, body_type=BodyType.coupe, fuel_average_kmpl=8.0, vehicle_id=2)

    ranked = rank_vehicles([poor, good], req)
    assert len(ranked) == 2
    assert ranked[0].match_score >= ranked[1].match_score
    assert ranked[0].vehicle.id == good.id


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
            model="Corolla",
            year=2021,
            price=3_200_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1300,
            mileage_km=40_000,
            fuel_average_kmpl=12.5,
            resale_rating=5,
        ),
        Vehicle(
            make="Suzuki",
            model="Alto",
            year=2020,
            price=2_200_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.manual,
            body_type=BodyType.hatchback,
            fuel_type=FuelType.petrol,
            engine_capacity=660,
            mileage_km=55_000,
            fuel_average_kmpl=18.0,
            resale_rating=4,
        ),
    ]
    session.add_all(fixtures)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        SQLModel.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_recommend_endpoint_returns_ranked_results(client: TestClient) -> None:
    requirements = _requirements(
        budget_max=3_500_000,
        city="Lahore",
        transmission=TransmissionPreference.automatic,
        purpose="family",
    )
    response = client.post(
        "/api/vehicles/recommend",
        json={"requirements": requirements.model_dump(), "limit": 10},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_candidates"] >= 1
    assert len(payload["items"]) >= 1
    item = payload["items"][0]
    assert "match_score" in item
    assert "explanation" in item
    assert "factor_scores" in item


def test_recommend_endpoint_rejects_clarification_needed(client: TestClient) -> None:
    requirements = ExtractedRequirements(
        needs_clarification=True,
        clarification_question="Do you mean PKR 30 lakh?",
    )
    response = client.post(
        "/api/vehicles/recommend",
        json={"requirements": requirements.model_dump()},
    )
    assert response.status_code == 422
    assert "lakh" in response.json()["detail"].lower()
