import json
import logging
import os
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(BASE_DIR, "sources.json")
RESET_DB = os.getenv("RESET_DB", "true").lower() in ("1", "true", "yes")


def _safe_text(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def _provider_to_text(value):
    if isinstance(value, dict):
        return value.get("name") or value.get("id") or _safe_text(value)
    return _safe_text(value)


def _license_to_text(value):
    if isinstance(value, dict):
        return value.get("id") or value.get("name") or value.get("title") or _safe_text(value)
    return _safe_text(value)


def _normalize_name(value):
    if value is None:
        return None
    text_val = str(value).strip()
    if not text_val or text_val.lower() in ("none", "nan", "null"):
        return None
    return text_val


def _stage_and_merge(engine, df, staging_table, target_table, columns, conflict_cols):
    if df.empty:
        return
    df.to_sql(staging_table, engine, if_exists="replace", index=False, method="multi", chunksize=1000)
    cols_csv = ", ".join(columns)
    conflict_csv = ", ".join(conflict_cols)
    insert_sql = f"""
        INSERT INTO {target_table} ({cols_csv})
        SELECT {cols_csv} FROM {staging_table}
        ON CONFLICT ({conflict_csv}) DO NOTHING
    """
    with engine.begin() as conn:
        conn.execute(text(insert_sql))
        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))


def _stage_and_merge_routes(engine, df):
    if df.empty:
        return
    df.to_sql("routes_staging", engine, if_exists="replace", index=False, method="multi", chunksize=1000)
    insert_sql = """
        INSERT INTO routes (operator_id, origin_station_id, destination_station_id, distance_km, source_id)
        SELECT
            o.operator_id,
            so.station_id,
            sd.station_id,
            rs.distance_km,
            rs.source_id
        FROM routes_staging rs
        LEFT JOIN operators o ON o.name = rs.operator_name
        LEFT JOIN stations so ON so.name = rs.origin_city
        LEFT JOIN stations sd ON sd.name = rs.destination_city
        WHERE rs.operator_name IS NOT NULL
          AND rs.origin_city IS NOT NULL
          AND rs.destination_city IS NOT NULL
          AND o.operator_id IS NOT NULL
          AND so.station_id IS NOT NULL
          AND sd.station_id IS NOT NULL
        ON CONFLICT (operator_id, origin_station_id, destination_station_id) DO NOTHING
    """
    with engine.begin() as conn:
        conn.execute(text(insert_sql))
        conn.execute(text("DROP TABLE IF EXISTS routes_staging"))


def _stage_and_merge_trips(engine, df):
    if df.empty:
        return
    df.to_sql("trips_staging", engine, if_exists="replace", index=False, method="multi", chunksize=2000)
    insert_sql = """
        INSERT INTO trips (trip_id, route_id, departure_time, arrival_time, service_type, train_type, co2_emissions, source_id)
        SELECT
            ts.trip_id,
            r.route_id,
            ts.departure_time,
            ts.arrival_time,
            ts.service_type,
            ts.train_type,
            ts.co2_emissions,
            ts.source_id
        FROM trips_staging ts
        LEFT JOIN operators o ON o.name = ts.operator_name
        LEFT JOIN stations so ON so.name = ts.origin_city
        LEFT JOIN stations sd ON sd.name = ts.destination_city
        LEFT JOIN routes r
            ON r.operator_id = o.operator_id
            AND r.origin_station_id = so.station_id
            AND r.destination_station_id = sd.station_id
        WHERE ts.trip_id IS NOT NULL
          AND ts.departure_time IS NOT NULL
          AND ts.arrival_time IS NOT NULL
          AND r.route_id IS NOT NULL
        ON CONFLICT (trip_id) DO NOTHING
    """
    with engine.begin() as conn:
        conn.execute(text(insert_sql))
        conn.execute(text("DROP TABLE IF EXISTS trips_staging"))


def get_db_engine():
    """Establishes connection to PostgreSQL using Environment Variables."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL is missing from environment variables!")
        return None
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.error(f"❌ DB Connection Error: {e}")
        return None


def _load_sources_from_file():
    if not os.path.exists(SOURCE_FILE):
        logger.warning("sources.json not found, skipping sources table load.")
        return []
    try:
        with open(SOURCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        valid = []
        for src in data:
            if not isinstance(src, dict):
                continue
            if not src.get("url"):
                continue
            if src.get("enabled", True) is False:
                continue
            valid.append(src)
        return valid
    except Exception as e:
        logger.error(f"❌ Failed to read sources.json: {e}")
        return []


def _truncate_tables(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE trips, routes, stations, operators, ingestions, sources RESTART IDENTITY CASCADE"
        ))


def run_load(data):
    """
    Loads data into PostgreSQL with a relational schema:
    sources -> operators/stations -> routes -> trips + ingestions.
    Accepts either a DataFrame or a CSV file path.
    """
    logger.info("💾 Starting relational load process...")

    engine = get_db_engine()
    if not engine:
        return

    # 1. Determine Input Type (DataFrame or File Path)
    df_to_load = pd.DataFrame()

    if isinstance(data, str) and os.path.exists(data):
        logger.info(f"📂 Reading from processed file: {data}")
        df_to_load = pd.read_csv(data, parse_dates=['departure_time', 'arrival_time'])
    elif isinstance(data, pd.DataFrame):
        df_to_load = data
    else:
        logger.warning("⚠️ Invalid data input provided to load function.")
        return

    if df_to_load.empty:
        logger.warning("⚠️ No data to insert.")
        return

    # Normalize key text fields for consistent dedup/mapping
    for col in ["operator_name", "origin_city", "destination_city"]:
        if col in df_to_load.columns:
            df_to_load[col] = df_to_load[col].map(_normalize_name)

    if RESET_DB:
        logger.info("🧹 RESET_DB enabled: truncating relational tables.")
        _truncate_tables(engine)

    # 2. Load sources table
    sources_list = _load_sources_from_file()
    if sources_list:
        now = datetime.utcnow()
        df_sources = pd.DataFrame([
            {
                "source_key": s.get("id"),
                "name": s.get("description"),
                "url": s.get("url"),
                "source_type": s.get("type"),
                "provider": _provider_to_text(s.get("provider")),
                "license": _license_to_text(s.get("license")),
                "last_seen": now,
            }
            for s in sources_list
        ]).dropna(subset=["source_key", "url"]).drop_duplicates(subset=["source_key"])

        if not df_sources.empty:
            df_sources.to_sql("sources", engine, if_exists="append", index=False, method="multi", chunksize=1000)

    # 3. Build source_id mapping
    src_map_df = pd.read_sql("SELECT source_id, source_key FROM sources", engine)
    source_key_to_id = dict(zip(src_map_df["source_key"], src_map_df["source_id"]))
    valid_source_ids = set(src_map_df["source_id"].dropna().tolist())
    df_to_load["source_id"] = df_to_load["source_origin"].map(source_key_to_id)
    df_to_load.loc[~df_to_load["source_id"].isin(valid_source_ids), "source_id"] = None

    # 4. Ingestions (audit)
    try:
        ing_df = (
            df_to_load.groupby("source_origin", dropna=False)
            .size()
            .reset_index(name="row_count")
        )
        ing_df["source_id"] = ing_df["source_origin"].map(source_key_to_id)
        ing_df["fetched_at"] = datetime.utcnow()
        ing_df["status"] = "success"
        ing_df["raw_path"] = None
        ing_df = ing_df[["source_id", "fetched_at", "raw_path", "status", "row_count"]]
        ing_df.to_sql("ingestions", engine, if_exists="append", index=False, method="multi", chunksize=1000)
    except Exception as e:
        logger.warning(f"⚠️ Ingestion log skipped: {e}")

    # 5. Operators
    operators_df = df_to_load[["operator_name", "source_origin"]].copy()
    operators_df["operator_name"] = operators_df["operator_name"].map(_normalize_name)
    operators_df = operators_df.dropna(subset=["operator_name"]).drop_duplicates(subset=["operator_name"])
    operators_df["source_id"] = operators_df["source_origin"].map(source_key_to_id)
    operators_df.loc[~operators_df["source_id"].isin(valid_source_ids), "source_id"] = None
    operators_df["country"] = None
    operators_df = operators_df.rename(columns={"operator_name": "name"})
    operators_df["name"] = operators_df["name"].map(_normalize_name)
    operators_df = operators_df.dropna(subset=["name"]).drop_duplicates(subset=["name"])
    operators_df = operators_df[["name", "country", "source_id"]]

    if not operators_df.empty:
        logger.info(f"Operators staged: {len(operators_df)}")
        _stage_and_merge(
            engine,
            operators_df,
            "operators_staging",
            "operators",
            ["name", "country", "source_id"],
            ["name"],
        )

    # 6. Stations
    origin_df = df_to_load[["origin_city", "origin_lat", "origin_lon", "source_origin"]].rename(
        columns={"origin_city": "name", "origin_lat": "lat", "origin_lon": "lon"}
    )
    dest_df = df_to_load[["destination_city", "destination_lat", "destination_lon", "source_origin"]].rename(
        columns={"destination_city": "name", "destination_lat": "lat", "destination_lon": "lon"}
    )
    stations_df = pd.concat([origin_df, dest_df], ignore_index=True)
    stations_df["name"] = stations_df["name"].map(_normalize_name)
    stations_df = stations_df.dropna(subset=["name"])
    stations_df["source_id"] = stations_df["source_origin"].map(source_key_to_id)
    stations_df.loc[~stations_df["source_id"].isin(valid_source_ids), "source_id"] = None
    stations_df["country"] = stations_df.get("country")
    stations_df["country"] = stations_df["country"].fillna("Unknown")
    stations_df = stations_df[["name", "country", "lat", "lon", "source_id"]]

    if not stations_df.empty:
        logger.info(f"Stations staged: {len(stations_df)}")
        # Collapse duplicates by name+country (keep first non-null lat/lon)
        stations_df = stations_df.groupby(["name", "country"], as_index=False).agg(
            {
                "country": "first",
                "lat": "first",
                "lon": "first",
                "source_id": "first",
            }
        )
        _stage_and_merge(
            engine,
            stations_df,
            "stations_staging",
            "stations",
            ["name", "country", "lat", "lon", "source_id"],
            ["name", "country"],
        )

    # 7. Routes (join-based to avoid mapping misses)
    routes_df = df_to_load[
        ["operator_name", "origin_city", "destination_city", "distance_km", "source_id"]
    ].dropna(subset=["operator_name", "origin_city", "destination_city"])
    routes_df = routes_df.drop_duplicates(subset=["operator_name", "origin_city", "destination_city"])

    if not routes_df.empty:
        logger.info(f"Routes staged: {len(routes_df)}")
        _stage_and_merge_routes(engine, routes_df)

    # 8. Trips (join-based)
    trips_df = df_to_load[
        [
            "trip_id",
            "operator_name",
            "origin_city",
            "destination_city",
            "departure_time",
            "arrival_time",
            "service_type",
            "train_type",
            "co2_emissions",
            "source_id",
        ]
    ].dropna(subset=["trip_id", "origin_city", "destination_city", "departure_time", "arrival_time"])
    trips_df = trips_df.drop_duplicates(subset=["trip_id"])

    if not trips_df.empty:
        logger.info(f"Trips staged: {len(trips_df)}")
        _stage_and_merge_trips(engine, trips_df)

    logger.info(f"✅ SUCCESS: Loaded {len(trips_df)} trips into relational schema.")


# --- LOCAL TEST ---
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(base_dir, "..", "data"))
    processed_path = os.path.join(data_dir, "processed", "trips_cleaned_final.csv")
    if os.path.exists(processed_path):
        run_load(processed_path)
    else:
        print("Test file not found.")
