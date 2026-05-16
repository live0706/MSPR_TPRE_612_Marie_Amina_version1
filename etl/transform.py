import os
import logging
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

DEFAULT_DEPARTURE_TIME = datetime(1900, 1, 1)
DEFAULT_TRIP_DURATION = timedelta(hours=4)
INVALID_TEXT_VALUES = {"", "none", "nan", "null", "nat"}
LONG_DISTANCE_MIN_KM = float(os.getenv("LONG_DISTANCE_MIN_KM", "400"))


def _clean_text(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    text_value = str(value).strip()
    if not text_value or text_value.lower() in INVALID_TEXT_VALUES:
        return None
    return text_value


def _clean_country_value(value):
    normalized = _clean_text(value)
    if normalized is None:
        return None
    if normalized.upper() == "ZZ" or normalized.lower() == "unknown":
        return None
    return normalized


def haversine(lat1, lon1, lat2, lon2):
    if any(pd.isna([lat1, lon1, lat2, lon2])):
        return 0.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def _normalize_datetime(value, fallback):
    if isinstance(value, datetime):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.to_pydatetime() if not pd.isna(parsed) else fallback


def _normalize_arrival_time(departure_time, raw_arrival_time):
    fallback = departure_time + DEFAULT_TRIP_DURATION
    arrival_time = _normalize_datetime(raw_arrival_time, fallback)
    if arrival_time < departure_time:
        arrival_time += timedelta(days=1)
    return arrival_time


def _normalize_service_type(departure_time, arrival_time, raw_service_type):
    normalized = _clean_text(raw_service_type)
    if normalized:
        lowered = normalized.lower()
        if "night" in lowered or "nuit" in lowered or "sleeper" in lowered:
            return "Nuit"
        if "day" in lowered or "jour" in lowered:
            return "Jour"

    if departure_time.hour >= 22 or departure_time.hour < 6:
        return "Nuit"
    if arrival_time.date() > departure_time.date() and departure_time.hour >= 19:
        return "Nuit"
    return "Jour"


def _normalize_distance(row):
    explicit_distance = pd.to_numeric(row.get("distance_km"), errors="coerce")
    if pd.notna(explicit_distance) and explicit_distance > 0:
        return float(explicit_distance)

    computed_distance = haversine(
        row.get("origin_lat"),
        row.get("origin_lon"),
        row.get("destination_lat"),
        row.get("destination_lon"),
    )
    return float(computed_distance) if computed_distance > 0 else None


def _infer_operator_name(row, source_name):
    for key in ("operator_name", "agency_name", "route_long_name", "route_short_name", "trip_headsign"):
        normalized = _clean_text(row.get(key))
        if normalized:
            return normalized
    return _clean_text(source_name) or "Unknown Operator"


def _build_global_trip_id(raw_trip_id, source_id, row_idx):
    normalized_trip_id = _clean_text(raw_trip_id)
    if normalized_trip_id and normalized_trip_id.startswith(f"{source_id}::"):
        return normalized_trip_id
    if normalized_trip_id:
        return f"{source_id}::{normalized_trip_id}"
    return f"{source_id}::{row_idx}"


def run_transform(list_of_dfs):
    logger.info("Transformation : conservation des trajets rail longue distance et enrichissement metadata")

    final_records = []
    for df in list_of_dfs:
        if df is None or df.empty:
            continue

        working_df = df.copy()
        for column in ("origin_lat", "origin_lon", "destination_lat", "destination_lon", "distance_km"):
            if column in working_df.columns:
                working_df[column] = pd.to_numeric(working_df[column], errors="coerce")

        source_id = _clean_text(working_df.get("source_origin", pd.Series([df.attrs.get("source_id")])).iloc[0]) or "unknown_source"
        source_name = _clean_text(working_df.get("source_name", pd.Series([df.attrs.get("source_name")])).iloc[0])
        source_provider = _clean_text(working_df.get("source_provider", pd.Series([df.attrs.get("source_provider")])).iloc[0])
        source_country = _clean_country_value(working_df.get("source_country", pd.Series([df.attrs.get("source_country")])).iloc[0])
        if source_country is None:
            source_country = _clean_country_value(working_df.get("country", pd.Series([df.attrs.get("country")])).iloc[0])

        for row_idx, row in working_df.iterrows():
            origin_city = _clean_text(row.get("origin_city"))
            destination_city = _clean_text(row.get("destination_city"))
            if not origin_city or not destination_city:
                continue

            departure_time = _normalize_datetime(row.get("departure_time"), DEFAULT_DEPARTURE_TIME)
            arrival_time = _normalize_arrival_time(departure_time, row.get("arrival_time"))
            distance_km = _normalize_distance(row)

            if distance_km is None or distance_km < LONG_DISTANCE_MIN_KM:
                continue

            trip_id = _build_global_trip_id(row.get("trip_id"), source_id, row_idx)
            operator_name = _infer_operator_name(row, source_name)
            service_type = _normalize_service_type(departure_time, arrival_time, row.get("service_type"))
            train_type = _clean_text(row.get("train_type")) or "Rail"
            row_country = _clean_country_value(row.get("country"))
            row_source_country = _clean_country_value(row.get("source_country"))

            final_records.append(
                {
                    "trip_id": trip_id,
                    "operator_name": operator_name,
                    "origin_city": origin_city,
                    "destination_city": destination_city,
                    "origin_lat": row.get("origin_lat"),
                    "origin_lon": row.get("origin_lon"),
                    "destination_lat": row.get("destination_lat"),
                    "destination_lon": row.get("destination_lon"),
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "service_type": service_type,
                    "train_type": train_type,
                    "distance_km": round(distance_km, 2),
                    "co2_emissions": round(distance_km * 0.002, 4),
                    "source_origin": source_id,
                    "source_name": source_name,
                    "source_provider": source_provider,
                    "source_country": row_source_country or row_country or source_country,
                    "origin_country": _clean_country_value(row.get("origin_country")),
                    "destination_country": _clean_country_value(row.get("destination_country")),
                    "country": row_country or row_source_country or source_country,
                }
            )

    if not final_records:
        return pd.DataFrame(
            columns=[
                "trip_id",
                "operator_name",
                "origin_city",
                "destination_city",
                "origin_lat",
                "origin_lon",
                "destination_lat",
                "destination_lon",
                "departure_time",
                "arrival_time",
                "service_type",
                "train_type",
                "distance_km",
                "co2_emissions",
                "source_origin",
                "source_name",
                "source_provider",
                "source_country",
                "origin_country",
                "destination_country",
                "country",
            ]
        )

    final_df = pd.DataFrame(final_records)
    final_df = final_df.drop_duplicates(subset=["trip_id"]).reset_index(drop=True)
    logger.info("Transformation terminee : %s trajets conserves", len(final_df))
    return final_df
