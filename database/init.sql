-- database/init.sql

-- Nettoyage préventif (Optionnel : retirez ces lignes pour la production)
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS stations CASCADE;
DROP TABLE IF EXISTS operators CASCADE;
DROP TABLE IF EXISTS ingestions CASCADE;
DROP TABLE IF EXISTS sources CASCADE;

-- Table des sources de données (catalogue)
CREATE TABLE sources (
    source_id SERIAL PRIMARY KEY,
    source_key VARCHAR(150) UNIQUE NOT NULL,
    name TEXT,
    url TEXT,
    source_type VARCHAR(50),
    provider TEXT,
    license TEXT,
    last_seen TIMESTAMP
);

-- Historique des ingestions
CREATE TABLE ingestions (
    ingestion_id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_path TEXT,
    status VARCHAR(20),
    row_count INTEGER
);

-- Opérateurs
CREATE TABLE operators (
    operator_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    country VARCHAR(100),
    source_id INTEGER REFERENCES sources(source_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gares / stations
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

-- Routes (liaisons)
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

-- Trajets
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

-- Index pour performances API
CREATE INDEX idx_trips_service_type ON trips(service_type);
CREATE INDEX idx_operators_name ON operators(name);
CREATE INDEX idx_stations_name ON stations(name);
