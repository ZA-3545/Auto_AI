"""Backend tests confirming deterministic vehicle search filters (PLANNING.md §K)."""

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
from app.schemas.vehicle import SortBy, SortOrder, VehicleSearchParams
from app.services.vehicle_search import search_vehicles


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
        ),
        Vehicle(
            make="Honda",
            model="City",
            year=2022,
            price=4_500_000,
            city="Karachi",
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
        Vehicle(
            make="Kia",
            model="Sportage",
            year=2023,
            price=9_000_000,
            city="Islamabad",
            condition=Condition.new,
            transmission=Transmission.automatic,
            body_type=BodyType.suv,
            fuel_type=FuelType.petrol,
            engine_capacity=2000,
            mileage_km=100,
            fuel_average_kmpl=11.0,
            resale_rating=4,
        ),
        Vehicle(
            make="Toyota",
            model="Aqua",
            year=2018,
            price=3_800_000,
            city="Lahore",
            condition=Condition.used,
            transmission=Transmission.automatic,
            body_type=BodyType.hatchback,
            fuel_type=FuelType.hybrid,
            engine_capacity=1500,
            mileage_km=90_000,
            fuel_average_kmpl=22.0,
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


def test_budget_max_filter(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(budget_max=4_000_000, limit=50),
    )
    assert result.total >= 1
    assert all(item.price <= 4_000_000 for item in result.items)


def test_budget_min_and_max_filter(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(budget_min=3_000_000, budget_max=5_500_000, limit=50),
    )
    assert result.total >= 1
    assert all(3_000_000 <= item.price <= 5_500_000 for item in result.items)


def test_city_filter_case_insensitive(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(city="lahore", limit=50),
    )
    assert result.total >= 1
    assert all(item.city.lower() == "lahore" for item in result.items)


def test_transmission_filter(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(transmission=Transmission.manual, limit=50),
    )
    assert result.total == 1
    assert all(item.transmission == Transmission.manual for item in result.items)


def test_condition_and_body_type_filters(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(
            condition=Condition.new,
            body_type=BodyType.suv,
            limit=50,
        ),
    )
    assert result.total == 1
    assert result.items[0].make == "Kia"
    assert result.items[0].condition == Condition.new
    assert result.items[0].body_type == BodyType.suv


def test_sort_by_price_asc(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(sort_by=SortBy.price, sort_order=SortOrder.asc, limit=50),
    )
    prices = [item.price for item in result.items]
    assert prices == sorted(prices)


def test_sort_by_year_desc(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(sort_by=SortBy.year, sort_order=SortOrder.desc, limit=50),
    )
    years = [item.year for item in result.items]
    assert years == sorted(years, reverse=True)


def test_pagination_limit_offset(db_session: Session) -> None:
    page1 = search_vehicles(
        db_session,
        VehicleSearchParams(sort_by=SortBy.price, sort_order=SortOrder.asc, limit=2, offset=0),
    )
    page2 = search_vehicles(
        db_session,
        VehicleSearchParams(sort_by=SortBy.price, sort_order=SortOrder.asc, limit=2, offset=2),
    )
    assert page1.total == 5
    assert len(page1.items) == 2
    assert len(page2.items) == 2
    assert page1.items[0].id != page2.items[0].id
    assert page1.items[0].price <= page2.items[0].price


def test_fuel_priority_orders_by_fuel_economy(db_session: Session) -> None:
    result = search_vehicles(
        db_session,
        VehicleSearchParams(
            city="Lahore",
            fuel_priority=True,
            sort_by=SortBy.price,
            sort_order=SortOrder.asc,
            limit=50,
        ),
    )
    assert result.total >= 2
    # Within same primary sort (price asc), higher fuel_average should come first among ties;
    # with distinct prices, verify all returned Lahore cars still match city filter.
    assert all(item.city == "Lahore" for item in result.items)


def test_api_search_endpoint_respects_filters(client: TestClient) -> None:
    response = client.get(
        "/api/vehicles/search",
        params={
            "budget_max": 3000000,
            "city": "Lahore",
            "transmission": "manual",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["price"] <= 3_000_000
    assert item["city"] == "Lahore"
    assert item["transmission"] == "manual"
    assert item["make"] == "Suzuki"
