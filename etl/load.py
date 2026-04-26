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
DATABASE_URL = os.getenv("DATABASE_URL")

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
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL missing from environment variables")
        return None
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.error(f"DB Connection Error: {e}")
        return None

def _load_sources_from_file():
    if not os.path.exists(SOURCE_FILE):
        logger.warning("sources.json not found, skipping sources load")
        return []
    try:
        with open(SOURCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        valid = []
        for src in data:
            if not isinstance(src, dict) or not src.get("url") or src.get("enabled") is False:
                continue
            valid.append(src)
        return valid
    except Exception as e:
        logger.error(f"Failed to read sources.json: {e}")
        return []

def _truncate_tables(engine):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE trips, routes, stations, operators, ingestions, sources RESTART IDENTITY CASCADE"
        ))

def run_load(data):
    logger.info("Starting data load process...")
    engine = get_db_engine()
    if not engine:
        return

    df_to_load = pd.DataFrame()
    if isinstance(data, str) and os.path.exists(data):
        logger.info(f"Reading file: {data}")
        df_to_load = pd.read_csv(data, parse_dates=['departure_time', 'arrival_time'])
    elif isinstance(data, pd.DataFrame):
        df_to_load = data
    else:
        logger.warning("Invalid data input provided")
        return

    if df_to_load.empty:
        logger.warning("No data to process")
        return

    for col in ["operator_name", "origin_city", "destination_city"]:
        if col in df_to_load.columns:
            df_to_load[col] = df_to_load[col].map(_normalize_name)

    for col in [
        "origin_lat",
        "origin_lon",
        "destination_lat",
        "destination_lon",
        "distance_km",
        "co2_emissions",
    ]:
        if col in df_to_load.columns:
            df_to_load[col] = pd.to_numeric(df_to_load[col], errors="coerce")

    if RESET_DB:
        logger.info("RESET_DB active: truncating tables")
        _truncate_tables(engine)

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
            df_sources.to_sql("sources", engine, if_exists="append", index=False, method="multi")

    src_map_df = pd.read_sql("SELECT source_id, source_key FROM sources", engine)
    source_key_to_id = dict(zip(src_map_df["source_key"], src_map_df["source_id"]))
    df_to_load["source_id"] = df_to_load["source_origin"].map(source_key_to_id)

    try:
        ing_df = df_to_load.groupby("source_origin", dropna=False).size().reset_index(name="row_count")
        ing_df["source_id"] = ing_df["source_origin"].map(source_key_to_id)
        ing_df["fetched_at"] = datetime.utcnow()
        ing_df["status"] = "success"
        ing_df["raw_path"] = None
        ing_df = ing_df[["source_id", "fetched_at", "raw_path", "status", "row_count"]]
        ing_df.to_sql("ingestions", engine, if_exists="append", index=False, method="multi")
    except Exception as e:
        logger.warning(f"Ingestion log skipped: {e}")

    # Process Operators
    ops = df_to_load[["operator_name", "source_id"]].rename(columns={"operator_name": "name"})
    ops = ops.dropna(subset=["name"]).drop_duplicates(subset=["name"])
    ops["country"] = None
    if not ops.empty:
        _stage_and_merge(engine, ops, "operators_staging", "operators", ["name", "country", "source_id"], ["name"])

    # Process Stations
    origin_df = df_to_load[["origin_city", "origin_lat", "origin_lon", "source_id"]].rename(
        columns={"origin_city": "name", "origin_lat": "lat", "origin_lon": "lon"}
    )
    dest_df = df_to_load[["destination_city", "destination_lat", "destination_lon", "source_id"]].rename(
        columns={"destination_city": "name", "destination_lat": "lat", "destination_lon": "lon"}
    )
    stations = pd.concat([origin_df, dest_df], ignore_index=True).dropna(subset=["name"])
    stations["country"] = "Unknown"
    stations = stations.groupby(["name", "country"], as_index=False).first()
    if not stations.empty:
        _stage_and_merge(engine, stations, "stations_staging", "stations", ["name", "country", "lat", "lon", "source_id"], ["name", "country"])

    # Final merges for Routes and Trips
    _stage_and_merge_routes(engine, df_to_load)
    _stage_and_merge_trips(engine, df_to_load)

    logger.info("Load process completed successfully")

if __name__ == "__main__":
    processed_path = os.path.join(BASE_DIR, "..", "data", "processed", "trips_cleaned_final.csv")
    if os.path.exists(processed_path):
        run_load(processed_path)
