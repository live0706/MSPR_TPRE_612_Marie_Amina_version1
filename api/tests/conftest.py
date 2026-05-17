import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

TESTS_DIR = Path(__file__).resolve().parent
if (TESTS_DIR.parent / "main.py").exists():
    API_DIR = TESTS_DIR.parent
else:
    API_DIR = TESTS_DIR.parents[1] / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from database import get_engine, ping_database
from main import app

TEST_SOURCE_KEY = "pytest_source"
TEST_COUNTRY_CODE = "PYTEST"
TEST_COUNTRY_NAME = "PyTest Land"
TEST_OPERATOR_NAME = "PyTest Rail"
TEST_TRIP_ID = "pytest-trip-2026"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def db_ready():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL absente: tests d'integration ignores.")
    if not ping_database():
        pytest.skip("PostgreSQL indisponible: tests d'integration ignores.")
    return True


@pytest.fixture(scope="session")
def seeded_db(db_ready):
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO sources (source_key, name, url, source_type, provider, license, country_code, country_name, last_seen)
                VALUES (:source_key, :name, :url, :source_type, :provider, :license, :country_code, :country_name, NOW())
                ON CONFLICT (source_key) DO NOTHING
                """
            ),
            {
                "source_key": TEST_SOURCE_KEY,
                "name": "PyTest Source",
                "url": "https://pytest.local/source",
                "source_type": "test",
                "provider": "pytest",
                "license": "internal",
                "country_code": TEST_COUNTRY_CODE,
                "country_name": TEST_COUNTRY_NAME,
            },
        )
        source_id = connection.execute(
            text("SELECT source_id FROM sources WHERE source_key = :source_key"),
            {"source_key": TEST_SOURCE_KEY},
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO operators (name, country, source_id)
                VALUES (:name, :country, :source_id)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": TEST_OPERATOR_NAME, "country": TEST_COUNTRY_NAME, "source_id": source_id},
        )
        operator_id = connection.execute(
            text("SELECT operator_id FROM operators WHERE name = :name"),
            {"name": TEST_OPERATOR_NAME},
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO stations (name, country, lat, lon, source_id)
                VALUES
                    ('PyTest City A', :country, 48.8566, 2.3522, :source_id),
                    ('PyTest City B', :country, 45.7640, 4.8357, :source_id)
                ON CONFLICT (name, country) DO NOTHING
                """
            ),
            {"country": TEST_COUNTRY_NAME, "source_id": source_id},
        )
        origin_station_id = connection.execute(
            text("SELECT station_id FROM stations WHERE name = 'PyTest City A' AND country = :country"),
            {"country": TEST_COUNTRY_NAME},
        ).scalar_one()
        destination_station_id = connection.execute(
            text("SELECT station_id FROM stations WHERE name = 'PyTest City B' AND country = :country"),
            {"country": TEST_COUNTRY_NAME},
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO routes (operator_id, origin_station_id, destination_station_id, distance_km, source_id)
                VALUES (:operator_id, :origin_station_id, :destination_station_id, 512.4, :source_id)
                ON CONFLICT (operator_id, origin_station_id, destination_station_id) DO NOTHING
                """
            ),
            {
                "operator_id": operator_id,
                "origin_station_id": origin_station_id,
                "destination_station_id": destination_station_id,
                "source_id": source_id,
            },
        )
        route_id = connection.execute(
            text(
                """
                SELECT route_id
                FROM routes
                WHERE operator_id = :operator_id
                  AND origin_station_id = :origin_station_id
                  AND destination_station_id = :destination_station_id
                """
            ),
            {
                "operator_id": operator_id,
                "origin_station_id": origin_station_id,
                "destination_station_id": destination_station_id,
            },
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO trips (
                    trip_id, route_id, departure_time, arrival_time, service_type, train_type, co2_emissions, source_id
                )
                VALUES (
                    :trip_id, :route_id, '2026-05-16 22:15:00', '2026-05-17 06:45:00', 'Nuit', 'Rail', 1.234, :source_id
                )
                ON CONFLICT (trip_id) DO NOTHING
                """
            ),
            {"trip_id": TEST_TRIP_ID, "route_id": route_id, "source_id": source_id},
        )

        connection.execute(
            text(
                """
                INSERT INTO dim_countries (country_code, country_name)
                VALUES (:country_code, :country_name)
                ON CONFLICT (country_code) DO UPDATE SET country_name = EXCLUDED.country_name
                """
            ),
            {"country_code": TEST_COUNTRY_CODE, "country_name": TEST_COUNTRY_NAME},
        )
        country_id = connection.execute(
            text("SELECT country_id FROM dim_countries WHERE country_code = :country_code"),
            {"country_code": TEST_COUNTRY_CODE},
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO dim_years (year, is_after_2010)
                VALUES (2026, TRUE)
                ON CONFLICT (year) DO NOTHING
                """
            )
        )
        year_id = connection.execute(text("SELECT year_id FROM dim_years WHERE year = 2026")).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO dim_operators (operator_name)
                VALUES (:operator_name)
                ON CONFLICT (operator_name) DO NOTHING
                """
            ),
            {"operator_name": TEST_OPERATOR_NAME},
        )
        dim_operator_id = connection.execute(
            text("SELECT operator_id FROM dim_operators WHERE operator_name = :operator_name"),
            {"operator_name": TEST_OPERATOR_NAME},
        ).scalar_one()

        connection.execute(
            text(
                """
                INSERT INTO facts_night_trains (
                    trip_id, route_id, night_train, country_id, year_id, operator_id, is_night, distance_km, co2_emissions
                )
                VALUES (
                    :trip_id, :route_id, 'PyTest City A - PyTest City B', :country_id, :year_id, :operator_id, TRUE, 512.4, 1.234
                )
                ON CONFLICT (trip_id) DO UPDATE
                SET country_id = EXCLUDED.country_id,
                    year_id = EXCLUDED.year_id,
                    operator_id = EXCLUDED.operator_id,
                    is_night = EXCLUDED.is_night,
                    distance_km = EXCLUDED.distance_km,
                    co2_emissions = EXCLUDED.co2_emissions
                """
            ),
            {
                "trip_id": TEST_TRIP_ID,
                "route_id": route_id,
                "country_id": country_id,
                "year_id": year_id,
                "operator_id": dim_operator_id,
            },
        )

        connection.execute(
            text(
                """
                INSERT INTO facts_country_stats (passengers, co2_emissions, co2_per_passenger, country_id, year_id)
                VALUES (120.0, 1.234, 0.0103, :country_id, :year_id)
                ON CONFLICT (country_id, year_id) DO UPDATE
                SET passengers = EXCLUDED.passengers,
                    co2_emissions = EXCLUDED.co2_emissions,
                    co2_per_passenger = EXCLUDED.co2_per_passenger
                """
            ),
            {"country_id": country_id, "year_id": year_id},
        )

    yield {
        "trip_id": TEST_TRIP_ID,
        "country_code": TEST_COUNTRY_CODE,
        "operator_name": TEST_OPERATOR_NAME,
    }

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM facts_country_stats WHERE country_id IN (SELECT country_id FROM dim_countries WHERE country_code = :country_code)"), {"country_code": TEST_COUNTRY_CODE})
        connection.execute(text("DELETE FROM facts_night_trains WHERE trip_id = :trip_id"), {"trip_id": TEST_TRIP_ID})
        connection.execute(text("DELETE FROM trips WHERE trip_id = :trip_id"), {"trip_id": TEST_TRIP_ID})
        connection.execute(
            text(
                "DELETE FROM routes WHERE source_id IN (SELECT source_id FROM sources WHERE source_key = :source_key)"
            ),
            {"source_key": TEST_SOURCE_KEY},
        )
        connection.execute(text("DELETE FROM stations WHERE name IN ('PyTest City A', 'PyTest City B')"))
        connection.execute(text("DELETE FROM operators WHERE name = :name"), {"name": TEST_OPERATOR_NAME})
        connection.execute(text("DELETE FROM dim_operators WHERE operator_name = :operator_name"), {"operator_name": TEST_OPERATOR_NAME})
        connection.execute(text("DELETE FROM dim_countries WHERE country_code = :country_code"), {"country_code": TEST_COUNTRY_CODE})
        connection.execute(text("DELETE FROM sources WHERE source_key = :source_key"), {"source_key": TEST_SOURCE_KEY})
