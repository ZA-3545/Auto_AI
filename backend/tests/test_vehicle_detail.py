"""Tests for get_car_details() — GET /api/vehicles/{id}."""

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
    session.add(
        Vehicle(
            make="Toyota",
            model="Corolla",
            year=2021,
            price=5_000_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.sedan,
            fuel_type=FuelType.petrol,
            engine_capacity=1300,
            mileage_km=40_000,
            fuel_average_kmpl=12.5,
            resale_rating=5,
        )
    )
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


def test_get_vehicle_by_id_returns_full_details(client: TestClient) -> None:
    response = client.get("/api/vehicles/1")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["make"] == "Toyota"
    assert body["model"] == "Corolla"
    assert body["year"] == 2021
    assert body["price"] == 5_000_000
    assert body["city"] == "Lahore"
    assert body["condition"] == "used"
    assert body["transmission"] == "automatic"
    assert body["body_type"] == "sedan"
    assert body["fuel_type"] == "petrol"
    assert body["engine_capacity"] == 1300
    assert body["mileage_km"] == 40_000
    assert body["fuel_average_kmpl"] == 12.5
    assert body["resale_rating"] == 5
    assert "created_at" in body


def test_get_vehicle_by_id_not_found_returns_friendly_404(client: TestClient) -> None:
    response = client.get("/api/vehicles/9999")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "couldn't find" in body["detail"].lower()
    assert "9999" in body["detail"]
