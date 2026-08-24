"""Comparison tests — data must match DB records (PLANNING.md Section K)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from app.core.database import get_db
from app.main import app
from app.models.vehicle import (
    BodyType,
    Condition,
    FuelType,
    Transmission,
    Vehicle,
)
from app.schemas.extraction import (
    ExtractedRequirements,
    TransmissionPreference,
)
from app.services.comparison import compare_vehicles
from app.services.comparison_engine import (
    build_factor_comparisons,
    compute_best_overall,
)


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
            make="Honda",
            model="City",
            year=2022,
            price=4_500_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1500,
            mileage_km=25_000,
            fuel_average_kmpl=13.5,
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
    for v in fixtures:
        session.refresh(v)

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


def _requirements(**kwargs) -> ExtractedRequirements:
    defaults = {
        "budget_min": None,
        "budget_max": 5_000_000,
        "city": "Lahore",
        "condition": None,
        "transmission": TransmissionPreference.automatic,
        "body_type": None,
        "purpose": "family",
        "fuel_priority": False,
        "resale_priority": None,
        "needs_clarification": False,
        "clarification_question": None,
    }
    defaults.update(kwargs)
    return ExtractedRequirements(**defaults)


def test_comparison_price_matches_database(db_session: Session) -> None:
    vehicles = db_session.query(Vehicle).order_by(Vehicle.id).all()
    a, b = vehicles[0], vehicles[1]
    result = compare_vehicles(
        db_session,
        [a.id, b.id],
        _requirements(),
        include_narrative=False,
    )

    returned = {v.id: v for v in result.vehicles}
    assert returned[a.id].price == a.price
    assert returned[b.id].price == b.price
    assert returned[a.id].make == a.make
    assert returned[b.id].model == b.model

    price_row = next(f for f in result.factors if f.factor == "price")
    by_id = {v.vehicle_id: v for v in price_row.values}
    assert by_id[a.id].numeric == float(a.price)
    assert by_id[b.id].numeric == float(b.price)
    # Cheaper car wins price
    assert price_row.winner_vehicle_id == (a.id if a.price < b.price else b.id)


def test_comparison_fuel_and_mileage_from_db(db_session: Session) -> None:
    vehicles = db_session.query(Vehicle).order_by(Vehicle.id).all()
    a, b = vehicles[0], vehicles[2]  # Corolla vs Alto
    factors = build_factor_comparisons([a, b], _requirements())

    fuel = next(f for f in factors if f.factor == "fuel_economy")
    fuel_by_id = {v.vehicle_id: v for v in fuel.values}
    assert fuel_by_id[a.id].numeric == a.fuel_average_kmpl
    assert fuel_by_id[b.id].numeric == b.fuel_average_kmpl
    assert fuel.winner_vehicle_id == b.id  # Alto 18 km/l > Corolla 12.5

    mileage = next(f for f in factors if f.factor == "mileage")
    mileage_by_id = {v.vehicle_id: v for v in mileage.values}
    assert mileage_by_id[a.id].numeric == float(a.mileage_km)
    assert mileage_by_id[b.id].numeric == float(b.mileage_km)


def test_safety_features_marked_unknown(db_session: Session) -> None:
    vehicles = db_session.query(Vehicle).order_by(Vehicle.id).limit(2).all()
    factors = build_factor_comparisons(vehicles, _requirements())
    safety = next(f for f in factors if f.factor == "safety_features")
    assert safety.reliability.value == "unknown"
    assert safety.winner_vehicle_id is None


def test_best_overall_respects_fuel_priority(db_session: Session) -> None:
    vehicles = db_session.query(Vehicle).order_by(Vehicle.id).all()
    a, b = vehicles[0], vehicles[2]  # Corolla vs efficient Alto

    without = compute_best_overall([a, b], build_factor_comparisons([a, b], _requirements()), _requirements())
    with_fuel = compute_best_overall(
        [a, b],
        build_factor_comparisons([a, b], _requirements(fuel_priority=True)),
        _requirements(fuel_priority=True),
    )
    # Alto should win or at least not lose when fuel is prioritized (higher km/l)
    assert with_fuel.vehicle_id == b.id or with_fuel.vehicle_id == without.vehicle_id
    assert "fuel" in with_fuel.reason.lower() or with_fuel.vehicle_id == b.id


def test_compare_endpoint_returns_db_backed_data(client: TestClient, db_session: Session) -> None:
    vehicles = db_session.query(Vehicle).order_by(Vehicle.id).limit(2).all()
    a, b = vehicles[0], vehicles[1]
    response = client.post(
        "/api/vehicles/compare",
        json={
            "vehicle_ids": [a.id, b.id],
            "requirements": _requirements().model_dump(),
            "include_narrative": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["vehicles"]) == 2
    assert payload["vehicles"][0]["price"] == a.price
    assert payload["vehicles"][1]["year"] == b.year
    assert payload["best_overall"]["vehicle_id"] in {a.id, b.id}
    factor_names = {f["factor"] for f in payload["factors"]}
    assert {
        "price",
        "model_year",
        "engine",
        "transmission",
        "fuel_economy",
        "mileage",
        "resale",
        "maintenance",
        "parts_availability",
        "comfort",
        "family_suitability",
        "performance",
        "safety_features",
    }.issubset(factor_names)


def test_compare_endpoint_404_for_missing_vehicle(client: TestClient, db_session: Session) -> None:
    vehicles = db_session.query(Vehicle).order_by(Vehicle.id).limit(1).all()
    response = client.post(
        "/api/vehicles/compare",
        json={
            "vehicle_ids": [vehicles[0].id, 99999],
            "requirements": _requirements().model_dump(),
            "include_narrative": False,
        },
    )
    assert response.status_code == 404
