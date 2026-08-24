"""Maintenance checklist tests — mileage thresholds & disclaimer (Section D & H)."""

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
from app.schemas.maintenance import (
    MAINTENANCE_DISCLAIMER,
    VehicleProfile,
)
from app.services.maintenance import search_maintenance_info
from app.services.maintenance_engine import build_maintenance_checklist


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

    vehicle = Vehicle(
        make="Honda",
        model="Civic",
        year=2018,
        price=3_500_000,
        city="Lahore",
        condition=Condition.used,
        transmission=Transmission.automatic,
        body_type=BodyType.sedan,
        fuel_type=FuelType.petrol,
        engine_capacity=1800,
        mileage_km=80_000,
        fuel_average_kmpl=12.0,
        resale_rating=5,
    )
    session.add(vehicle)
    session.commit()
    session.refresh(vehicle)

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


def test_high_mileage_checklist_has_more_items_than_low_mileage() -> None:
    low = build_maintenance_checklist(
        VehicleProfile(make="Toyota", model="Corolla", year=2024, mileage_km=10_000)
    )
    high = build_maintenance_checklist(
        VehicleProfile(make="Toyota", model="Corolla", year=2015, mileage_km=100_000)
    )

    assert len(high) > len(low)
    high_items = {item.item for item in high}
    assert "Full brake system review (pads, discs, lines)" in high_items
    assert "Full brake system review (pads, discs, lines)" not in {
        item.item for item in low
    }


def test_search_maintenance_info_always_includes_disclaimer(
    db_session: Session,
) -> None:
    profile = VehicleProfile(
        make="Honda",
        model="Civic",
        year=2018,
        mileage_km=80_000,
        source="extracted",
    )
    response = search_maintenance_info(
        db_session,
        profile_override=profile,
        skip_rag=True,
    )

    assert response.disclaimer == MAINTENANCE_DISCLAIMER
    assert "qualified mechanic" in response.disclaimer.lower()
    assert "not professional mechanical advice" in response.disclaimer.lower()
    assert len(response.checklist) >= 1


def test_maintenance_endpoint_by_vehicle_id(client: TestClient) -> None:
    response = client.post("/api/vehicles/maintenance", json={"vehicle_id": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["vehicle"]["make"] == "Honda"
    assert body["vehicle"]["model"] == "Civic"
    assert body["vehicle"]["mileage_km"] == 80_000
    assert MAINTENANCE_DISCLAIMER in body["disclaimer"]
    assert len(body["checklist"]) >= 5


def test_maintenance_endpoint_rejects_both_sources(client: TestClient) -> None:
    response = client.post(
        "/api/vehicles/maintenance",
        json={"vehicle_id": 1, "description": "2018 Civic"},
    )
    assert response.status_code == 422


def test_maintenance_endpoint_rejects_neither_source(client: TestClient) -> None:
    response = client.post("/api/vehicles/maintenance", json={})
    assert response.status_code == 422
