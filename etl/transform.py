import logging
import re
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

INVALID_TEXT_VALUES = {"", "none", "nan", "null", "nat"}
DEFAULT_DEPARTURE_TIME = datetime(2026, 4, 21, 10, 0)


def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance reelle entre deux points GPS."""
    if any(pd.isna([lat1, lon1, lat2, lon2])):
        return 0.0
    radius_km = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _clean_text(value):
    if value is None:
        return None
    if isinstance(value, pd.Series):
        for item in value.tolist():
            cleaned_item = _clean_text(item)
            if cleaned_item is not None:
                return cleaned_item
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            cleaned_item = _clean_text(item)
            if cleaned_item is not None:
                return cleaned_item
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


def _to_float(value):
    if value is None:
        return None
    if isinstance(value, pd.Series):
        for item in value.tolist():
            float_item = _to_float(item)
            if float_item is not None:
                return float_item
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            float_item = _to_float(item)
            if float_item is not None:
                return float_item
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    if isinstance(value, str):
        cleaned = value.strip().replace(" ", "").replace(",", ".")
        if not cleaned or cleaned.lower() in INVALID_TEXT_VALUES:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if not match:
            return None
        cleaned = match.group(0)
        try:
            return float(cleaned)
        except ValueError:
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_column_name(value):
    normalized = re.sub(r"[^a-z0-9.]+", "_", str(value).strip().lower())
    return normalized.strip("_")


def _pick_text(row, candidates):
    for key in candidates:
        value = _clean_text(row.get(key))
        if value is not None:
            return value
    return None


def _pick_float(row, candidates):
    for key in candidates:
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _looks_like_multiple_locations(value):
    text_value = _clean_text(value)
    if not text_value:
        return False

    patterns = [
        r"\s+(?:->|=>|\u2013|\u2014|\u2192)\s+",
        r"\s-\s",
        r"\bto\b",
        r"\bvers\b",
        r"\buntil\b",
        r"\bjusqu[' ]a\b",
    ]
    return any(re.search(pattern, text_value, flags=re.IGNORECASE) for pattern in patterns)


def _normalize_datetime(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return fallback

    return parsed.to_pydatetime() if hasattr(parsed, "to_pydatetime") else parsed


def _normalize_service_type(value, departure_time):
    raw_value = _clean_text(value)
    if raw_value:
        lowered = raw_value.lower()
        if "nuit" in lowered or "night" in lowered:
            return "Nuit"
        if "jour" in lowered or "day" in lowered:
            return "Jour"

    hour = departure_time.hour
    return "Nuit" if (hour >= 22 or hour < 6) else "Jour"


def _extract_cities(row):
    origin_city = _pick_text(
        row,
        [
            "fields.origine",
            "origin_city",
            "trip_origin",
            "origin",
            "from",
            "departure_station",
            "stop_name",
        ],
    )
    destination_city = _pick_text(
        row,
        [
            "fields.destination",
            "destination_city",
            "trip_headsign",
            "destination",
            "to",
            "arrival_station",
            "stop_name",
        ],
    )

    if _looks_like_multiple_locations(origin_city):
        origin_city = None

    return _clean_text(origin_city), _clean_text(destination_city)


def _extract_distance(row, lat_o, lon_o, lat_d, lon_d):
    explicit_distance = _pick_float(
        row,
        [
            "distance_km",
            "fields.distance_km",
            "distance",
            "fields.distance",
            "distancekm",
            "km",
        ],
    )
    if explicit_distance is None:
        for key, value in row.items():
            normalized_key = _normalize_column_name(key)
            if "distance" in normalized_key and ("km" in normalized_key or normalized_key == "distance"):
                explicit_distance = _to_float(value)
                if explicit_distance is not None:
                    break
    if explicit_distance is not None and explicit_distance > 0:
        return round(explicit_distance, 2)

    if None not in (lat_o, lon_o, lat_d, lon_d):
        computed_distance = haversine(lat_o, lon_o, lat_d, lon_d)
        if computed_distance > 0:
            return round(computed_distance, 2)

    return None


def run_transform(list_of_dfs):
    logger.info("Transformation : normalisation des trajets et filtrage longue distance")
    final_records = []

    for df in list_of_dfs:
        if df.empty:
            continue

        source_key = _clean_text(df.attrs.get("source_id"))
        working_df = df.copy()
        working_df.columns = [_normalize_column_name(col) for col in working_df.columns]

        for row_idx, row in working_df.iterrows():
            row_source = _clean_text(row.get("source_origin")) or source_key or "unknown_source"

            departure_time = _normalize_datetime(
                row.get("fields.depart", row.get("departure_time", row.get("origin_departure_time"))),
                DEFAULT_DEPARTURE_TIME,
            )
            arrival_time = _normalize_datetime(
                row.get(
                    "fields.arrivee",
                    row.get("arrival_time", row.get("destination_arrival_time")),
                ),
                departure_time + pd.Timedelta(hours=4),
            )
            service_type = _normalize_service_type(row.get("service_type"), departure_time)
            train_type = _pick_text(row, ["train_type"]) or (
                "Intercites" if service_type == "Nuit" else "TGV"
            )

            operator_name = _pick_text(
                row,
                [
                    "fields.transporteur",
                    "operator_name",
                    "operators",
                    "agency_name",
                    "agency_id",
                    "operator",
                    "agency",
                ],
            )
            origin_city, destination_city = _extract_cities(row)

            lat_o = _pick_float(row, ["origin_lat", "stop_lat"])
            lon_o = _pick_float(row, ["origin_lon", "stop_lon"])
            lat_d = _pick_float(row, ["destination_lat"])
            lon_d = _pick_float(row, ["destination_lon"])
            distance_km = _extract_distance(row, lat_o, lon_o, lat_d, lon_d)

            final_records.append(
                {
                    "trip_id": _clean_text(row.get("trip_id")) or f"{row_source}-{row_idx}",
                    "operator_name": operator_name,
                    "origin_city": origin_city,
                    "destination_city": destination_city,
                    "origin_lat": lat_o,
                    "origin_lon": lon_o,
                    "destination_lat": lat_d,
                    "destination_lon": lon_d,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "service_type": service_type,
                    "train_type": train_type,
                    "distance_km": distance_km,
                    "co2_emissions": round(distance_km * 0.002, 4) if distance_km is not None else None,
                    "source_origin": row_source,
                }
            )

    if not final_records:
        return pd.DataFrame()

    final_df = pd.DataFrame(final_records)
    for column in ["operator_name", "origin_city", "destination_city", "source_origin"]:
        final_df[column] = final_df[column].map(_clean_text)

    final_df = final_df.dropna(
        subset=["origin_city", "destination_city", "distance_km", "source_origin"]
    )
    final_df = final_df[final_df["distance_km"] >= 400].copy()

    return final_df.reset_index(drop=True)
