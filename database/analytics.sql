-- database/02_add_analytics.sql
-- Migration non destructive pour une base deja initialisee.

CREATE TABLE IF NOT EXISTS dim_countries (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR(10) UNIQUE NOT NULL,
    country_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_years (
    year_id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    is_after_2010 BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dim_operators (
    operator_id SERIAL PRIMARY KEY,
    operator_name VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS facts_night_trains (
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

CREATE TABLE IF NOT EXISTS facts_country_stats (
    stats_id SERIAL PRIMARY KEY,
    passengers DOUBLE PRECISION NOT NULL,
    co2_emissions DOUBLE PRECISION NOT NULL,
    co2_per_passenger DOUBLE PRECISION NOT NULL,
    country_id INTEGER NOT NULL REFERENCES dim_countries(country_id),
    year_id INTEGER NOT NULL REFERENCES dim_years(year_id),
    UNIQUE (country_id, year_id)
);

CREATE OR REPLACE VIEW dashboard_metrics AS
SELECT
    c.country_name,
    c.country_code,
    AVG(s.passengers) AS avg_passengers,
    AVG(s.co2_emissions) AS avg_co2_emissions,
    AVG(s.co2_per_passenger) AS avg_co2_per_passenger
FROM facts_country_stats s
JOIN dim_countries c ON s.country_id = c.country_id
GROUP BY c.country_id, c.country_name, c.country_code;

CREATE INDEX IF NOT EXISTS idx_dim_countries_code ON dim_countries(country_code);
CREATE INDEX IF NOT EXISTS idx_dim_years_year ON dim_years(year);
CREATE INDEX IF NOT EXISTS idx_dim_operators_name ON dim_operators(operator_name);
CREATE INDEX IF NOT EXISTS idx_facts_trains_year ON facts_night_trains(year_id);
CREATE INDEX IF NOT EXISTS idx_facts_trains_country ON facts_night_trains(country_id);
CREATE INDEX IF NOT EXISTS idx_facts_trains_operator ON facts_night_trains(operator_id);
CREATE INDEX IF NOT EXISTS idx_facts_stats_year ON facts_country_stats(year_id);
CREATE INDEX IF NOT EXISTS idx_facts_stats_country ON facts_country_stats(country_id);
