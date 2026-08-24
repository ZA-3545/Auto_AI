"""
Seed script for AutoAI demo vehicle catalog.

IMPORTANT — DEMO / SAMPLE DATA ONLY
-----------------------------------
These records are manually authored, realistic approximations for Pakistan's
automotive market (common makes/models, typical PKR price bands, major cities).
They are NOT scraped from PakWheels or any other website, and must not be
presented as live inventory or official listings.

Independent proof of concept — not affiliated with or endorsed by PakWheels.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.vehicle import (
    BodyType,
    Condition,
    FuelType,
    Transmission,
    Vehicle,
)

# ---------------------------------------------------------------------------
# Demo dataset — ~80 vehicles across brands listed in PLANNING.md Section C
# ---------------------------------------------------------------------------

DEMO_VEHICLES: list[dict] = [
    # Toyota
    {"make": "Toyota", "model": "Corolla Gli", "year": 2021, "price": 5850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1300, "mileage_km": 42000, "fuel_average_kmpl": 12.5, "resale_rating": 5},
    {"make": "Toyota", "model": "Corolla Altis X", "year": 2023, "price": 7950000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1800, "mileage_km": 18000, "fuel_average_kmpl": 11.0, "resale_rating": 5},
    {"make": "Toyota", "model": "Corolla XE", "year": 2018, "price": 3950000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1300, "mileage_km": 98000, "fuel_average_kmpl": 13.0, "resale_rating": 5},
    {"make": "Toyota", "model": "Yaris ATIV", "year": 2022, "price": 4650000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 35000, "fuel_average_kmpl": 14.0, "resale_rating": 4},
    {"make": "Toyota", "model": "Yaris Gli", "year": 2024, "price": 5850000, "city": "Lahore", "condition": Condition.new, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 50, "fuel_average_kmpl": 14.2, "resale_rating": 4},
    {"make": "Toyota", "model": "Fortuner", "year": 2020, "price": 14500000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.diesel, "engine_capacity": 2800, "mileage_km": 62000, "fuel_average_kmpl": 9.5, "resale_rating": 5},
    {"make": "Toyota", "model": "Fortuner Legender", "year": 2023, "price": 19800000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.diesel, "engine_capacity": 2800, "mileage_km": 22000, "fuel_average_kmpl": 9.8, "resale_rating": 5},
    {"make": "Toyota", "model": "Hilux Revo", "year": 2021, "price": 12500000, "city": "Peshawar", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.pickup, "fuel_type": FuelType.diesel, "engine_capacity": 2800, "mileage_km": 55000, "fuel_average_kmpl": 10.0, "resale_rating": 5},
    {"make": "Toyota", "model": "Aqua", "year": 2017, "price": 3850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.hybrid, "engine_capacity": 1500, "mileage_km": 110000, "fuel_average_kmpl": 22.0, "resale_rating": 4},
    {"make": "Toyota", "model": "Prius", "year": 2016, "price": 4250000, "city": "Rawalpindi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.hybrid, "engine_capacity": 1800, "mileage_km": 125000, "fuel_average_kmpl": 20.5, "resale_rating": 4},
    # Honda
    {"make": "Honda", "model": "City 1.5 Aspire", "year": 2022, "price": 5450000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 28000, "fuel_average_kmpl": 13.5, "resale_rating": 5},
    {"make": "Honda", "model": "City 1.2", "year": 2019, "price": 3650000, "city": "Multan", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1200, "mileage_km": 72000, "fuel_average_kmpl": 14.5, "resale_rating": 4},
    {"make": "Honda", "model": "Civic Oriel", "year": 2021, "price": 7250000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 40000, "fuel_average_kmpl": 12.0, "resale_rating": 5},
    {"make": "Honda", "model": "Civic RS", "year": 2023, "price": 9850000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 15000, "fuel_average_kmpl": 11.5, "resale_rating": 5},
    {"make": "Honda", "model": "BR-V i-VTEC S", "year": 2020, "price": 4850000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.crossover, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 58000, "fuel_average_kmpl": 11.0, "resale_rating": 4},
    {"make": "Honda", "model": "Vezel", "year": 2018, "price": 5150000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.crossover, "fuel_type": FuelType.hybrid, "engine_capacity": 1500, "mileage_km": 85000, "fuel_average_kmpl": 18.0, "resale_rating": 4},
    {"make": "Honda", "model": "Fit", "year": 2017, "price": 3350000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.hybrid, "engine_capacity": 1500, "mileage_km": 95000, "fuel_average_kmpl": 19.5, "resale_rating": 3},
    {"make": "Honda", "model": "City Aspire CVT", "year": 2024, "price": 6550000, "city": "Lahore", "condition": Condition.new, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 30, "fuel_average_kmpl": 13.8, "resale_rating": 5},
    # Suzuki
    {"make": "Suzuki", "model": "Alto VXR", "year": 2022, "price": 2650000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 25000, "fuel_average_kmpl": 18.0, "resale_rating": 4},
    {"make": "Suzuki", "model": "Alto AGS", "year": 2023, "price": 2950000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 12000, "fuel_average_kmpl": 17.5, "resale_rating": 4},
    {"make": "Suzuki", "model": "Cultus VXL", "year": 2021, "price": 3150000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 1000, "mileage_km": 38000, "fuel_average_kmpl": 15.5, "resale_rating": 4},
    {"make": "Suzuki", "model": "Wagon R VXL", "year": 2020, "price": 2550000, "city": "Multan", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 1000, "mileage_km": 65000, "fuel_average_kmpl": 16.0, "resale_rating": 3},
    {"make": "Suzuki", "model": "Swift GLX", "year": 2023, "price": 4650000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 1200, "mileage_km": 14000, "fuel_average_kmpl": 14.0, "resale_rating": 4},
    {"make": "Suzuki", "model": "Swift Manual", "year": 2022, "price": 3850000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 1200, "mileage_km": 32000, "fuel_average_kmpl": 15.0, "resale_rating": 4},
    {"make": "Suzuki", "model": "Jimny", "year": 2024, "price": 7200000, "city": "Islamabad", "condition": Condition.new, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 80, "fuel_average_kmpl": 11.5, "resale_rating": 4},
    {"make": "Suzuki", "model": "Bolan", "year": 2019, "price": 1450000, "city": "Peshawar", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.van, "fuel_type": FuelType.petrol, "engine_capacity": 800, "mileage_km": 88000, "fuel_average_kmpl": 14.0, "resale_rating": 2},
    {"make": "Suzuki", "model": "Every", "year": 2018, "price": 1950000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.van, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 102000, "fuel_average_kmpl": 15.0, "resale_rating": 2},
    # Hyundai
    {"make": "Hyundai", "model": "Tucson AWD", "year": 2022, "price": 9850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 30000, "fuel_average_kmpl": 10.5, "resale_rating": 4},
    {"make": "Hyundai", "model": "Tucson FWD", "year": 2021, "price": 8250000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 45000, "fuel_average_kmpl": 11.0, "resale_rating": 4},
    {"make": "Hyundai", "model": "Elantra", "year": 2023, "price": 7850000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 16000, "fuel_average_kmpl": 12.0, "resale_rating": 3},
    {"make": "Hyundai", "model": "Sonata", "year": 2020, "price": 6950000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 2500, "mileage_km": 52000, "fuel_average_kmpl": 10.0, "resale_rating": 3},
    {"make": "Hyundai", "model": "Santa Fe", "year": 2021, "price": 12500000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2500, "mileage_km": 38000, "fuel_average_kmpl": 9.0, "resale_rating": 3},
    {"make": "Hyundai", "model": "Porter H-100", "year": 2019, "price": 2850000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.pickup, "fuel_type": FuelType.diesel, "engine_capacity": 2500, "mileage_km": 110000, "fuel_average_kmpl": 11.0, "resale_rating": 2},
    # Kia
    {"make": "Kia", "model": "Sportage AWD", "year": 2022, "price": 9450000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 32000, "fuel_average_kmpl": 10.8, "resale_rating": 4},
    {"make": "Kia", "model": "Sportage FWD", "year": 2023, "price": 8950000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 18000, "fuel_average_kmpl": 11.2, "resale_rating": 4},
    {"make": "Kia", "model": "Sorento", "year": 2021, "price": 11800000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2500, "mileage_km": 42000, "fuel_average_kmpl": 9.5, "resale_rating": 3},
    {"make": "Kia", "model": "Picanto", "year": 2022, "price": 3250000, "city": "Multan", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 1000, "mileage_km": 22000, "fuel_average_kmpl": 16.5, "resale_rating": 3},
    {"make": "Kia", "model": "Stonic", "year": 2023, "price": 5650000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.crossover, "fuel_type": FuelType.petrol, "engine_capacity": 1400, "mileage_km": 15000, "fuel_average_kmpl": 13.0, "resale_rating": 3},
    {"make": "Kia", "model": "Carnival", "year": 2020, "price": 10500000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.van, "fuel_type": FuelType.diesel, "engine_capacity": 2200, "mileage_km": 48000, "fuel_average_kmpl": 10.0, "resale_rating": 3},
    # Changan
    {"make": "Changan", "model": "Alsvin 1.5 Comfort", "year": 2023, "price": 3850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 20000, "fuel_average_kmpl": 14.0, "resale_rating": 3},
    {"make": "Changan", "model": "Alsvin Lumiere", "year": 2024, "price": 4450000, "city": "Karachi", "condition": Condition.new, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 40, "fuel_average_kmpl": 14.2, "resale_rating": 3},
    {"make": "Changan", "model": "Oshan X7", "year": 2022, "price": 7850000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 35000, "fuel_average_kmpl": 11.5, "resale_rating": 3},
    {"make": "Changan", "model": "Karvaan", "year": 2021, "price": 2650000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.van, "fuel_type": FuelType.petrol, "engine_capacity": 1000, "mileage_km": 55000, "fuel_average_kmpl": 13.5, "resale_rating": 2},
    {"make": "Changan", "model": "M9", "year": 2023, "price": 15500000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 12000, "fuel_average_kmpl": 9.0, "resale_rating": 3},
    # MG
    {"make": "MG", "model": "HS", "year": 2022, "price": 8850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 28000, "fuel_average_kmpl": 11.0, "resale_rating": 3},
    {"make": "MG", "model": "ZS", "year": 2023, "price": 6850000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.crossover, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 16000, "fuel_average_kmpl": 12.5, "resale_rating": 3},
    {"make": "MG", "model": "ZS EV", "year": 2022, "price": 9250000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.crossover, "fuel_type": FuelType.electric, "engine_capacity": None, "mileage_km": 25000, "fuel_average_kmpl": None, "resale_rating": 2},
    {"make": "MG", "model": "5", "year": 2021, "price": 4850000, "city": "Multan", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 40000, "fuel_average_kmpl": 13.0, "resale_rating": 2},
    {"make": "MG", "model": "Extender", "year": 2023, "price": 7950000, "city": "Peshawar", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.pickup, "fuel_type": FuelType.diesel, "engine_capacity": 2000, "mileage_km": 18000, "fuel_average_kmpl": 10.5, "resale_rating": 3},
    # Nissan
    {"make": "Nissan", "model": "Dayz", "year": 2019, "price": 2550000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 78000, "fuel_average_kmpl": 17.0, "resale_rating": 3},
    {"make": "Nissan", "model": "Note", "year": 2018, "price": 3150000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.hybrid, "engine_capacity": 1200, "mileage_km": 92000, "fuel_average_kmpl": 20.0, "resale_rating": 3},
    {"make": "Nissan", "model": "Clipper", "year": 2017, "price": 1850000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.van, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 115000, "fuel_average_kmpl": 14.5, "resale_rating": 2},
    {"make": "Nissan", "model": "Navara", "year": 2020, "price": 8950000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.pickup, "fuel_type": FuelType.diesel, "engine_capacity": 2500, "mileage_km": 50000, "fuel_average_kmpl": 10.0, "resale_rating": 3},
    {"make": "Nissan", "model": "X-Trail", "year": 2019, "price": 7850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2500, "mileage_km": 68000, "fuel_average_kmpl": 10.5, "resale_rating": 3},
    # Daihatsu
    {"make": "Daihatsu", "model": "Mira", "year": 2018, "price": 2150000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 85000, "fuel_average_kmpl": 18.5, "resale_rating": 3},
    {"make": "Daihatsu", "model": "Move", "year": 2017, "price": 1950000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 98000, "fuel_average_kmpl": 17.5, "resale_rating": 2},
    {"make": "Daihatsu", "model": "Hijet", "year": 2016, "price": 1650000, "city": "Multan", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.van, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 120000, "fuel_average_kmpl": 15.0, "resale_rating": 2},
    {"make": "Daihatsu", "model": "Cuore", "year": 2010, "price": 850000, "city": "Peshawar", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 800, "mileage_km": 145000, "fuel_average_kmpl": 16.0, "resale_rating": 2},
    {"make": "Daihatsu", "model": "Terios", "year": 2015, "price": 2850000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 110000, "fuel_average_kmpl": 11.0, "resale_rating": 3},
    # Other relevant Pakistani-market brands
    {"make": "Proton", "model": "Saga", "year": 2022, "price": 3450000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1300, "mileage_km": 24000, "fuel_average_kmpl": 13.5, "resale_rating": 2},
    {"make": "Proton", "model": "X70", "year": 2021, "price": 6850000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1800, "mileage_km": 36000, "fuel_average_kmpl": 11.0, "resale_rating": 2},
    {"make": "Haval", "model": "Jolion", "year": 2023, "price": 7950000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 14000, "fuel_average_kmpl": 11.5, "resale_rating": 3},
    {"make": "Haval", "model": "H6", "year": 2022, "price": 9850000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 27000, "fuel_average_kmpl": 10.5, "resale_rating": 3},
    {"make": "DFSK", "model": "Glory 580", "year": 2021, "price": 5250000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 42000, "fuel_average_kmpl": 11.0, "resale_rating": 2},
    {"make": "Prince", "model": "Pearl", "year": 2020, "price": 1850000, "city": "Multan", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 800, "mileage_km": 55000, "fuel_average_kmpl": 16.5, "resale_rating": 2},
    {"make": "United", "model": "Bravo", "year": 2019, "price": 1250000, "city": "Peshawar", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.van, "fuel_type": FuelType.petrol, "engine_capacity": 800, "mileage_km": 70000, "fuel_average_kmpl": 14.0, "resale_rating": 1},
    {"make": "Isuzu", "model": "D-Max", "year": 2021, "price": 8950000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.pickup, "fuel_type": FuelType.diesel, "engine_capacity": 3000, "mileage_km": 45000, "fuel_average_kmpl": 10.5, "resale_rating": 4},
    {"make": "Mitsubishi", "model": "Pajero Mini", "year": 2016, "price": 2650000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 105000, "fuel_average_kmpl": 13.0, "resale_rating": 3},
    {"make": "Mitsubishi", "model": "Lancer", "year": 2014, "price": 2250000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 1500, "mileage_km": 130000, "fuel_average_kmpl": 12.0, "resale_rating": 3},
    {"make": "BMW", "model": "3 Series", "year": 2018, "price": 12500000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 60000, "fuel_average_kmpl": 9.5, "resale_rating": 3},
    {"make": "Mercedes-Benz", "model": "C200", "year": 2017, "price": 13500000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 72000, "fuel_average_kmpl": 9.0, "resale_rating": 3},
    {"make": "Audi", "model": "A4", "year": 2019, "price": 14500000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 48000, "fuel_average_kmpl": 10.0, "resale_rating": 3},
    {"make": "Toyota", "model": "Passo", "year": 2018, "price": 2750000, "city": "Rawalpindi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 1000, "mileage_km": 88000, "fuel_average_kmpl": 16.5, "resale_rating": 3},
    {"make": "Honda", "model": "N WGN", "year": 2019, "price": 2450000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 70000, "fuel_average_kmpl": 18.0, "resale_rating": 3},
    {"make": "Suzuki", "model": "Ravi", "year": 2021, "price": 1650000, "city": "Faisalabad", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.pickup, "fuel_type": FuelType.petrol, "engine_capacity": 800, "mileage_km": 48000, "fuel_average_kmpl": 13.0, "resale_rating": 2},
    {"make": "Toyota", "model": "Land Cruiser Prado", "year": 2019, "price": 28500000, "city": "Lahore", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.suv, "fuel_type": FuelType.petrol, "engine_capacity": 2700, "mileage_km": 55000, "fuel_average_kmpl": 8.0, "resale_rating": 5},
    {"make": "Honda", "model": "Grace Hybrid", "year": 2018, "price": 4450000, "city": "Islamabad", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.hybrid, "engine_capacity": 1500, "mileage_km": 90000, "fuel_average_kmpl": 21.0, "resale_rating": 4},
    {"make": "Kia", "model": "Grand Carnival", "year": 2024, "price": 14500000, "city": "Lahore", "condition": Condition.new, "transmission": Transmission.automatic, "body_type": BodyType.van, "fuel_type": FuelType.diesel, "engine_capacity": 2200, "mileage_km": 100, "fuel_average_kmpl": 10.5, "resale_rating": 3},
    {"make": "Hyundai", "model": "Ioniq 5", "year": 2023, "price": 18500000, "city": "Karachi", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.crossover, "fuel_type": FuelType.electric, "engine_capacity": None, "mileage_km": 12000, "fuel_average_kmpl": None, "resale_rating": 2},
    {"make": "Changan", "model": "Hunter", "year": 2023, "price": 6850000, "city": "Peshawar", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.pickup, "fuel_type": FuelType.petrol, "engine_capacity": 2000, "mileage_km": 20000, "fuel_average_kmpl": 10.0, "resale_rating": 3},
    {"make": "Suzuki", "model": "Alto VX", "year": 2021, "price": 2250000, "city": "Quetta", "condition": Condition.used, "transmission": Transmission.manual, "body_type": BodyType.hatchback, "fuel_type": FuelType.petrol, "engine_capacity": 660, "mileage_km": 40000, "fuel_average_kmpl": 18.5, "resale_rating": 4},
    {"make": "Toyota", "model": "Corolla Axio Hybrid", "year": 2017, "price": 4150000, "city": "Sialkot", "condition": Condition.used, "transmission": Transmission.automatic, "body_type": BodyType.sedan, "fuel_type": FuelType.hybrid, "engine_capacity": 1500, "mileage_km": 108000, "fuel_average_kmpl": 22.5, "resale_rating": 4},
]


def seed_vehicles(db: Session, *, clear_existing: bool = False) -> int:
    """Insert demo vehicles. Returns number of rows inserted."""
    if clear_existing:
        db.query(Vehicle).delete()
        db.commit()

    existing = db.query(Vehicle).count()
    if existing > 0 and not clear_existing:
        print(f"Skipping seed: vehicles table already has {existing} row(s).")
        print("Re-run with --clear to replace demo data.")
        return 0

    rows = [Vehicle(**row) for row in DEMO_VEHICLES]
    db.add_all(rows)
    db.commit()
    return len(rows)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed AutoAI demo vehicles (sample data only).")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing vehicles before seeding.",
    )
    args = parser.parse_args()

    # Ensure metadata is bound (tables must already exist via Alembic).
    _ = engine

    db = SessionLocal()
    try:
        count = seed_vehicles(db, clear_existing=args.clear)
        print(f"Seeded {count} demo vehicles (sample data — not scraped).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
