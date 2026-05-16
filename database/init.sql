-- database/init.sql
-- Schema ObRail Europe
-- 1. Couche transactionnelle pour l'ingestion
-- 2. Couche analytique pour l'API et le dashboard

DROP VIEW IF EXISTS dashboard_metrics;

DROP TABLE IF EXISTS facts_country_stats CASCADE;
DROP TABLE IF EXISTS facts_night_trains CASCADE;
DROP TABLE IF EXISTS dim_operators CASCADE;
DROP TABLE IF EXISTS dim_years CASCADE;
DROP TABLE IF EXISTS dim_countries CASCADE;

DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS stations CASCADE;
DROP TABLE IF EXISTS operators CASCADE;
DROP TABLE IF EXISTS ingestions CASCADE;
DROP TABLE IF EXISTS sources CASCADE;

-- =========================================================
-- Couche transactionnelle
-- =========================================================

CREATE TABLE sources (
    source_id SERIAL PRIMARY KEY,
    source_key VARCHAR(150) UNIQUE NOT NULL,
    name TEXT,
    url TEXT,
    source_type VARCHAR(50),
    provider TEXT,
    license TEXT,
    country_code VARCHAR(10),
    country_name VARCHAR(100),
    last_seen TIMESTAMP
);

CREATE TABLE ingestions (
    ingestion_id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_path TEXT,
    status VARCHAR(20),
    row_count INTEGER
);

CREATE TABLE operators (
    operator_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    country VARCHAR(100),
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stations (
    station_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, country)
);

CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    operator_id INTEGER REFERENCES operators(operator_id) ON DELETE SET NULL,
    origin_station_id INTEGER REFERENCES stations(station_id) ON DELETE SET NULL,
    destination_station_id INTEGER REFERENCES stations(station_id) ON DELETE SET NULL,
    distance_km DOUBLE PRECISION,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (operator_id, origin_station_id, destination_station_id)
);

CREATE TABLE trips (
    trip_id VARCHAR(200) PRIMARY KEY,
    route_id INTEGER REFERENCES routes(route_id) ON DELETE SET NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    service_type VARCHAR(10) CHECK (service_type IN ('Jour', 'Nuit')),
    train_type VARCHAR(100),
    co2_emissions DOUBLE PRECISION,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- Couche analytique
-- =========================================================

CREATE TABLE dim_countries (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR(10) UNIQUE NOT NULL,
    country_name VARCHAR(100) NOT NULL
);

CREATE TABLE dim_years (
    year_id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    is_after_2010 BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE dim_operators (
    operator_id SERIAL PRIMARY KEY,
    operator_name VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE facts_night_trains (
    fact_id SERIAL PRIMARY KEY,
    trip_id VARCHAR(200) UNIQUE NOT NULL,
    route_id INTEGER,
    night_train VARCHAR(200) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES dim_countries(country_id),
    year_id INTEGER NOT NULL REFERENCES dim_years(year_id),
    operator_id INTEGER NOT NULL REFERENCES dim_operators(operator_id),
    is_night BOOLEAN NOT NULL DEFAULT TRUE,
    distance_km DOUBLE PRECISION,
    co2_emissions DOUBLE PRECISION
);

CREATE TABLE facts_country_stats (
    stats_id SERIAL PRIMARY KEY,
    passengers DOUBLE PRECISION NOT NULL,
    co2_emissions DOUBLE PRECISION NOT NULL,
    co2_per_passenger DOUBLE PRECISION NOT NULL,
    country_id INTEGER NOT NULL REFERENCES dim_countries(country_id),
    year_id INTEGER NOT NULL REFERENCES dim_years(year_id),
    UNIQUE (country_id, year_id)
);

CREATE VIEW dashboard_metrics AS
SELECT
    c.country_name,
    c.country_code,
    AVG(s.passengers) AS avg_passengers,
    AVG(s.co2_emissions) AS avg_co2_emissions,
    AVG(s.co2_per_passenger) AS avg_co2_per_passenger
FROM facts_country_stats s
JOIN dim_countries c ON s.country_id = c.country_id
GROUP BY c.country_id, c.country_name, c.country_code;

-- =========================================================
-- Index
-- =========================================================

CREATE INDEX idx_trips_service_type ON trips(service_type);
CREATE INDEX idx_operators_name ON operators(name);
CREATE INDEX idx_stations_name ON stations(name);

CREATE INDEX idx_dim_countries_code ON dim_countries(country_code);
CREATE INDEX idx_dim_years_year ON dim_years(year);
CREATE INDEX idx_dim_operators_name ON dim_operators(operator_name);
CREATE INDEX idx_facts_trains_year ON facts_night_trains(year_id);
CREATE INDEX idx_facts_trains_country ON facts_night_trains(country_id);
CREATE INDEX idx_facts_trains_operator ON facts_night_trains(operator_id);
CREATE INDEX idx_facts_stats_year ON facts_country_stats(year_id);
CREATE INDEX idx_facts_stats_country ON facts_country_stats(country_id);
