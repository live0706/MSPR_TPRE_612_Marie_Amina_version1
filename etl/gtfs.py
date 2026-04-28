import logging
import os
import zipfile
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger()

RAIL_ROUTE_TYPES = {2, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113}
RAIL_KEYWORDS = [
    "rail", "train", "nightjet", "sleeper", "bahn", "db", "sncf", "renfe",
    "trenitalia", "railway", "intercity", "eurostar", "thalys", "cff", "sbb",
]


def _gtfs_time_to_datetime(value, base_date):
    if pd.isna(value) or not isinstance(value, str):
        return pd.NaT

    parts = value.strip().split(":")
    if len(parts) < 2:
        return pd.NaT

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2]) if len(parts) == 3 else 0
    except (TypeError, ValueError):
        return pd.NaT

    day_offset = hours // 24
    normalized_hours = hours % 24
    return base_date + timedelta(days=day_offset, hours=normalized_hours, minutes=minutes, seconds=seconds)


def _parse_gtfs_date(value):
    if pd.isna(value):
        return None
    raw_value = str(value).strip()
    if len(raw_value) != 8 or not raw_value.isdigit():
        return None
    try:
        return datetime.strptime(raw_value, "%Y%m%d")
    except ValueError:
        return None


def _find_member_name(zip_file, filename):
    target = filename.lower()
    for member_name in zip_file.namelist():
        normalized = member_name.lower()
        if normalized == target or normalized.endswith(f"/{target}") or normalized.endswith(f"\\{target}"):
            return member_name
    return None


def _read_csv(zip_file, filename):
    member_name = _find_member_name(zip_file, filename)
    if not member_name:
        return pd.DataFrame()

    with zip_file.open(member_name) as handle:
        return pd.read_csv(handle, low_memory=False)


def _infer_base_date(feed_info, calendar, calendar_dates):
    for dataframe, columns in (
        (feed_info, ("feed_start_date", "feed_end_date")),
        (calendar, ("start_date", "end_date")),
        (calendar_dates, ("date",)),
    ):
        if dataframe.empty:
            continue
        for column in columns:
            if column not in dataframe.columns:
                continue
            for value in dataframe[column].dropna().tolist():
                parsed = _parse_gtfs_date(value)
                if parsed is not None:
                    return parsed
    return datetime(2010, 1, 1)


def _text_keyword_mask(df, columns):
    available_columns = [column for column in columns if column in df.columns]
    if not available_columns:
        return pd.Series(False, index=df.index)

    text_series = pd.Series("", index=df.index, dtype="object")
    for column in available_columns:
        text_series = text_series + " " + df[column].fillna("").astype(str)

    lowered = text_series.str.lower()
    mask = pd.Series(False, index=df.index)
    for keyword in RAIL_KEYWORDS:
        mask = mask | lowered.str.contains(keyword, regex=False)
    return mask


def parse_gtfs_zip(file_path):
    if not file_path or not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        with zipfile.ZipFile(file_path, "r") as zip_file:
            stop_times = _read_csv(zip_file, "stop_times.txt")
            stops = _read_csv(zip_file, "stops.txt")
            trips = _read_csv(zip_file, "trips.txt")
            routes = _read_csv(zip_file, "routes.txt")
            agency = _read_csv(zip_file, "agency.txt")
            feed_info = _read_csv(zip_file, "feed_info.txt")
            calendar = _read_csv(zip_file, "calendar.txt")
            calendar_dates = _read_csv(zip_file, "calendar_dates.txt")

        base_date = _infer_base_date(feed_info, calendar, calendar_dates)

        required_stop_time_columns = {"trip_id", "stop_id", "stop_sequence", "departure_time", "arrival_time"}
        if stop_times.empty or stops.empty or not required_stop_time_columns.issubset(set(stop_times.columns)):
            return pd.DataFrame()
        if "stop_id" not in stops.columns:
            return pd.DataFrame()

        stop_times = stop_times.copy()
        stop_times["stop_sequence"] = pd.to_numeric(stop_times["stop_sequence"], errors="coerce")
        stop_times = stop_times.sort_values(["trip_id", "stop_sequence"], na_position="last")

        first_stops = stop_times.groupby("trip_id", as_index=False).first()
        last_stops = stop_times.groupby("trip_id", as_index=False).last()

        stops_lookup = stops.drop_duplicates(subset=["stop_id"]).set_index("stop_id")

        def _mapped_stop_values(stop_ids, column_name):
            if column_name not in stops_lookup.columns:
                return pd.Series(pd.NA, index=stop_ids.index, dtype="object")
            return stop_ids.map(stops_lookup[column_name])

        df = pd.DataFrame(
            {
                "trip_id": first_stops["trip_id"],
                "origin_city": _mapped_stop_values(first_stops["stop_id"], "stop_name"),
                "destination_city": _mapped_stop_values(last_stops["stop_id"], "stop_name"),
                "origin_lat": _mapped_stop_values(first_stops["stop_id"], "stop_lat"),
                "origin_lon": _mapped_stop_values(first_stops["stop_id"], "stop_lon"),
                "destination_lat": _mapped_stop_values(last_stops["stop_id"], "stop_lat"),
                "destination_lon": _mapped_stop_values(last_stops["stop_id"], "stop_lon"),
                "departure_time": first_stops["departure_time"].apply(lambda value: _gtfs_time_to_datetime(value, base_date)),
                "arrival_time": last_stops["arrival_time"].apply(lambda value: _gtfs_time_to_datetime(value, base_date)),
            }
        )

        if not trips.empty and {"trip_id", "route_id"}.issubset(set(trips.columns)):
            trip_columns = [column for column in ("trip_id", "route_id", "trip_headsign", "service_id") if column in trips.columns]
            df = df.merge(trips[trip_columns], on="trip_id", how="left")

        if not agency.empty:
            agency = agency.copy()
            if "agency_id" not in agency.columns:
                agency["agency_id"] = "__default_agency__"

        if not routes.empty and "route_id" in routes.columns:
            routes = routes.copy()
            if "agency_id" not in routes.columns and not agency.empty and len(agency) == 1:
                routes["agency_id"] = agency["agency_id"].iloc[0]
            if "agency_id" in routes.columns and not agency.empty and len(agency) == 1:
                routes["agency_id"] = routes["agency_id"].fillna(agency["agency_id"].iloc[0])

            route_columns = [
                column
                for column in ("route_id", "agency_id", "route_type", "route_long_name", "route_short_name")
                if column in routes.columns
            ]
            df = df.merge(routes[route_columns], on="route_id", how="left")

        if not agency.empty and {"agency_id", "agency_name"}.issubset(set(agency.columns)):
            df = df.merge(agency[["agency_id", "agency_name"]], on="agency_id", how="left")

        for column in ("origin_lat", "origin_lon", "destination_lat", "destination_lon"):
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        route_type_series = pd.to_numeric(df["route_type"], errors="coerce") if "route_type" in df.columns else pd.Series(pd.NA, index=df.index)
        keyword_mask = _text_keyword_mask(df, ["agency_name", "route_long_name", "route_short_name", "trip_headsign"])

        if route_type_series.notna().any():
            rail_mask = route_type_series.isin(RAIL_ROUTE_TYPES)
            df = df[rail_mask | (route_type_series.isna() & keyword_mask)].copy()
        elif keyword_mask.any():
            df = df[keyword_mask].copy()

        if df.empty:
            return pd.DataFrame()

        df["operator_name"] = pd.NA
        for candidate in ("agency_name", "route_long_name", "route_short_name", "trip_headsign"):
            if candidate in df.columns:
                df["operator_name"] = df["operator_name"].fillna(df[candidate])

        df["train_type"] = "Rail"
        df = df.dropna(subset=["trip_id", "origin_city", "destination_city"])
        df = df.drop_duplicates(subset=["trip_id"])

        return df.reset_index(drop=True)
    except Exception as exc:
        logger.error(f"Erreur parsing GTFS: {exc}")
        return pd.DataFrame()
