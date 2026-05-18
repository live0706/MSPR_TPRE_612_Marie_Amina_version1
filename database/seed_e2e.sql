INSERT INTO sources (source_key, name, url, source_type, provider, license, country_code, country_name, last_seen)
VALUES (
    'playwright_source',
    'Playwright Source',
    'https://playwright.local/source',
    'test',
    'playwright',
    'internal',
    'PWT',
    'Playwright Land',
    NOW()
)
ON CONFLICT (source_key) DO UPDATE
SET
    name = EXCLUDED.name,
    url = EXCLUDED.url,
    source_type = EXCLUDED.source_type,
    provider = EXCLUDED.provider,
    license = EXCLUDED.license,
    country_code = EXCLUDED.country_code,
    country_name = EXCLUDED.country_name,
    last_seen = EXCLUDED.last_seen;

INSERT INTO ingestions (source_id, fetched_at, raw_path, status, row_count)
SELECT source_id, NOW(), '/tmp/playwright.csv', 'success', 2
FROM sources
WHERE source_key = 'playwright_source';

INSERT INTO operators (name, country, source_id)
SELECT 'Playwright Rail', 'Playwright Land', source_id
FROM sources
WHERE source_key = 'playwright_source'
ON CONFLICT (name) DO UPDATE
SET
    country = EXCLUDED.country,
    source_id = EXCLUDED.source_id;

INSERT INTO stations (name, country, lat, lon, source_id)
SELECT 'Playwright City Alpha', 'Playwright Land', 48.8566, 2.3522, source_id
FROM sources
WHERE source_key = 'playwright_source'
ON CONFLICT (name, country) DO UPDATE
SET
    lat = EXCLUDED.lat,
    lon = EXCLUDED.lon,
    source_id = EXCLUDED.source_id;

INSERT INTO stations (name, country, lat, lon, source_id)
SELECT 'Playwright City Beta', 'Playwright Land', 50.8503, 4.3517, source_id
FROM sources
WHERE source_key = 'playwright_source'
ON CONFLICT (name, country) DO UPDATE
SET
    lat = EXCLUDED.lat,
    lon = EXCLUDED.lon,
    source_id = EXCLUDED.source_id;

INSERT INTO stations (name, country, lat, lon, source_id)
SELECT 'Playwright City Gamma', 'Playwright Land', 52.52, 13.405, source_id
FROM sources
WHERE source_key = 'playwright_source'
ON CONFLICT (name, country) DO UPDATE
SET
    lat = EXCLUDED.lat,
    lon = EXCLUDED.lon,
    source_id = EXCLUDED.source_id;

INSERT INTO routes (operator_id, origin_station_id, destination_station_id, distance_km, source_id)
SELECT
    o.operator_id,
    so.station_id,
    sd.station_id,
    615.0,
    s.source_id
FROM operators o
JOIN sources s ON s.source_key = 'playwright_source'
JOIN stations so ON so.name = 'Playwright City Alpha' AND so.country = 'Playwright Land'
JOIN stations sd ON sd.name = 'Playwright City Beta' AND sd.country = 'Playwright Land'
WHERE o.name = 'Playwright Rail'
ON CONFLICT (operator_id, origin_station_id, destination_station_id) DO UPDATE
SET
    distance_km = EXCLUDED.distance_km,
    source_id = EXCLUDED.source_id;

INSERT INTO routes (operator_id, origin_station_id, destination_station_id, distance_km, source_id)
SELECT
    o.operator_id,
    so.station_id,
    sd.station_id,
    782.0,
    s.source_id
FROM operators o
JOIN sources s ON s.source_key = 'playwright_source'
JOIN stations so ON so.name = 'Playwright City Beta' AND so.country = 'Playwright Land'
JOIN stations sd ON sd.name = 'Playwright City Gamma' AND sd.country = 'Playwright Land'
WHERE o.name = 'Playwright Rail'
ON CONFLICT (operator_id, origin_station_id, destination_station_id) DO UPDATE
SET
    distance_km = EXCLUDED.distance_km,
    source_id = EXCLUDED.source_id;

INSERT INTO trips (
    trip_id,
    route_id,
    departure_time,
    arrival_time,
    service_type,
    train_type,
    co2_emissions,
    source_id
)
SELECT
    'playwright-night-2026',
    r.route_id,
    '2026-05-18 21:30:00',
    '2026-05-19 06:20:00',
    'Nuit',
    'Rail',
    1.42,
    s.source_id
FROM routes r
JOIN operators o ON o.operator_id = r.operator_id
JOIN stations so ON so.station_id = r.origin_station_id
JOIN stations sd ON sd.station_id = r.destination_station_id
JOIN sources s ON s.source_key = 'playwright_source'
WHERE o.name = 'Playwright Rail'
  AND so.name = 'Playwright City Alpha'
  AND sd.name = 'Playwright City Beta'
ON CONFLICT (trip_id) DO UPDATE
SET
    route_id = EXCLUDED.route_id,
    departure_time = EXCLUDED.departure_time,
    arrival_time = EXCLUDED.arrival_time,
    service_type = EXCLUDED.service_type,
    train_type = EXCLUDED.train_type,
    co2_emissions = EXCLUDED.co2_emissions,
    source_id = EXCLUDED.source_id;

INSERT INTO trips (
    trip_id,
    route_id,
    departure_time,
    arrival_time,
    service_type,
    train_type,
    co2_emissions,
    source_id
)
SELECT
    'playwright-day-2026',
    r.route_id,
    '2026-05-18 08:00:00',
    '2026-05-18 14:10:00',
    'Jour',
    'Rail',
    0.88,
    s.source_id
FROM routes r
JOIN operators o ON o.operator_id = r.operator_id
JOIN stations so ON so.station_id = r.origin_station_id
JOIN stations sd ON sd.station_id = r.destination_station_id
JOIN sources s ON s.source_key = 'playwright_source'
WHERE o.name = 'Playwright Rail'
  AND so.name = 'Playwright City Beta'
  AND sd.name = 'Playwright City Gamma'
ON CONFLICT (trip_id) DO UPDATE
SET
    route_id = EXCLUDED.route_id,
    departure_time = EXCLUDED.departure_time,
    arrival_time = EXCLUDED.arrival_time,
    service_type = EXCLUDED.service_type,
    train_type = EXCLUDED.train_type,
    co2_emissions = EXCLUDED.co2_emissions,
    source_id = EXCLUDED.source_id;

INSERT INTO dim_countries (country_code, country_name)
VALUES ('PWT', 'Playwright Land')
ON CONFLICT (country_code) DO UPDATE
SET
    country_name = EXCLUDED.country_name;

INSERT INTO dim_years (year, is_after_2010)
VALUES (2026, TRUE)
ON CONFLICT (year) DO NOTHING;

INSERT INTO dim_operators (operator_name)
VALUES ('Playwright Rail')
ON CONFLICT (operator_name) DO NOTHING;

INSERT INTO facts_night_trains (
    trip_id,
    route_id,
    night_train,
    country_id,
    year_id,
    operator_id,
    is_night,
    distance_km,
    co2_emissions
)
SELECT
    'playwright-night-2026',
    r.route_id,
    'Playwright City Alpha - Playwright City Beta',
    c.country_id,
    y.year_id,
    o.operator_id,
    TRUE,
    615.0,
    1.42
FROM routes r
JOIN operators ot ON ot.operator_id = r.operator_id
JOIN stations so ON so.station_id = r.origin_station_id
JOIN stations sd ON sd.station_id = r.destination_station_id
JOIN dim_countries c ON c.country_code = 'PWT'
JOIN dim_years y ON y.year = 2026
JOIN dim_operators o ON o.operator_name = 'Playwright Rail'
WHERE ot.name = 'Playwright Rail'
  AND so.name = 'Playwright City Alpha'
  AND sd.name = 'Playwright City Beta'
ON CONFLICT (trip_id) DO UPDATE
SET
    route_id = EXCLUDED.route_id,
    night_train = EXCLUDED.night_train,
    country_id = EXCLUDED.country_id,
    year_id = EXCLUDED.year_id,
    operator_id = EXCLUDED.operator_id,
    is_night = EXCLUDED.is_night,
    distance_km = EXCLUDED.distance_km,
    co2_emissions = EXCLUDED.co2_emissions;

INSERT INTO facts_night_trains (
    trip_id,
    route_id,
    night_train,
    country_id,
    year_id,
    operator_id,
    is_night,
    distance_km,
    co2_emissions
)
SELECT
    'playwright-day-2026',
    r.route_id,
    'Playwright City Beta - Playwright City Gamma',
    c.country_id,
    y.year_id,
    o.operator_id,
    FALSE,
    782.0,
    0.88
FROM routes r
JOIN operators ot ON ot.operator_id = r.operator_id
JOIN stations so ON so.station_id = r.origin_station_id
JOIN stations sd ON sd.station_id = r.destination_station_id
JOIN dim_countries c ON c.country_code = 'PWT'
JOIN dim_years y ON y.year = 2026
JOIN dim_operators o ON o.operator_name = 'Playwright Rail'
WHERE ot.name = 'Playwright Rail'
  AND so.name = 'Playwright City Beta'
  AND sd.name = 'Playwright City Gamma'
ON CONFLICT (trip_id) DO UPDATE
SET
    route_id = EXCLUDED.route_id,
    night_train = EXCLUDED.night_train,
    country_id = EXCLUDED.country_id,
    year_id = EXCLUDED.year_id,
    operator_id = EXCLUDED.operator_id,
    is_night = EXCLUDED.is_night,
    distance_km = EXCLUDED.distance_km,
    co2_emissions = EXCLUDED.co2_emissions;

INSERT INTO facts_country_stats (passengers, co2_emissions, co2_per_passenger, country_id, year_id)
SELECT
    245.0,
    2.30,
    0.0094,
    c.country_id,
    y.year_id
FROM dim_countries c
JOIN dim_years y ON y.year = 2026
WHERE c.country_code = 'PWT'
ON CONFLICT (country_id, year_id) DO UPDATE
SET
    passengers = EXCLUDED.passengers,
    co2_emissions = EXCLUDED.co2_emissions,
    co2_per_passenger = EXCLUDED.co2_per_passenger;
