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
LONG_DISTANCE_MIN_KM = float(os.getenv("LONG_DISTANCE_MIN_KM", "400"))
GTFS_MIN_DISTANCE_KM = float(
    os.getenv("GTFS_MIN_DISTANCE_KM", str(max(250.0, LONG_DISTANCE_MIN_KM * 0.75)))
)
GTFS_MAX_SERVICE_DAYS = max(0, int(os.getenv("GTFS_MAX_SERVICE_DAYS", "0")))
GTFS_MIN_SERVICE_DATE = os.getenv("GTFS_MIN_SERVICE_DATE")
GTFS_MAX_SERVICE_DATE = os.getenv("GTFS_MAX_SERVICE_DATE")


def _normalize_identifier(value):
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text_value = str(value).strip()
    return text_value or None


def _parse_clock_to_datetime(value, base_date):
    if pd.isna(value):
        return pd.NaT

    text_value = str(value).strip()
    if not text_value:
        return pd.NaT

    parts = text_value.split(":")
    if len(parts) < 2:
        return pd.NaT

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2]) if len(parts) >= 3 else 0
    except (TypeError, ValueError):
        return pd.NaT

    return base_date + timedelta(hours=hours, minutes=minutes, seconds=seconds)


def _gtfs_time_to_seconds(value):
    if pd.isna(value) or not isinstance(value, str):
        return None

    parts = value.strip().split(":")
    if len(parts) < 2:
        return None

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2]) if len(parts) == 3 else 0
    except (TypeError, ValueError):
        return None

    return (hours * 3600) + (minutes * 60) + seconds


def _gtfs_time_to_datetime(value, base_date):
    total_seconds = _gtfs_time_to_seconds(value)
    if total_seconds is None:
        return pd.NaT

    return base_date + timedelta(seconds=total_seconds)


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


def _parse_env_date(value):
    if not value:
        return None

    for pattern in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(str(value).strip(), pattern).date()
        except ValueError:
            continue
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


def _service_date_is_allowed(service_date, min_service_date, max_service_date):
    if min_service_date and service_date < min_service_date:
        return False
    if max_service_date and service_date > max_service_date:
        return False
    return True


def _build_service_dates(calendar, calendar_dates, used_service_ids):
    normalized_service_ids = {
        service_id
        for service_id in (_normalize_identifier(value) for value in used_service_ids)
        if service_id
    }
    if not normalized_service_ids:
        return {}

    min_service_date = _parse_env_date(GTFS_MIN_SERVICE_DATE)
    max_service_date = _parse_env_date(GTFS_MAX_SERVICE_DATE)
    service_dates = {service_id: set() for service_id in normalized_service_ids}
    weekday_columns = (
        ("monday", 0),
        ("tuesday", 1),
        ("wednesday", 2),
        ("thursday", 3),
        ("friday", 4),
        ("saturday", 5),
        ("sunday", 6),
    )

    if not calendar.empty and {"service_id", "start_date", "end_date"}.issubset(set(calendar.columns)):
        working_calendar = calendar.copy()
        working_calendar["service_id"] = working_calendar["service_id"].map(_normalize_identifier)
        working_calendar = working_calendar[working_calendar["service_id"].isin(normalized_service_ids)].copy()

        for _, row in working_calendar.iterrows():
            service_id = row.get("service_id")
            if not service_id:
                continue

            start_date = _parse_gtfs_date(row.get("start_date"))
            end_date = _parse_gtfs_date(row.get("end_date"))
            if start_date is None or end_date is None or end_date < start_date:
                continue

            current_date = start_date.date()
            last_date = end_date.date()
            if GTFS_MAX_SERVICE_DAYS > 0:
                last_date = min(last_date, current_date + timedelta(days=GTFS_MAX_SERVICE_DAYS - 1))

            active_weekdays = {
                weekday
                for column_name, weekday in weekday_columns
                if str(row.get(column_name, "")).strip() == "1"
            }
            if not active_weekdays:
                continue

            while current_date <= last_date:
                if current_date.weekday() in active_weekdays and _service_date_is_allowed(
                    current_date,
                    min_service_date,
                    max_service_date,
                ):
                    service_dates[service_id].add(current_date)
                current_date += timedelta(days=1)

    if not calendar_dates.empty and {"service_id", "date", "exception_type"}.issubset(set(calendar_dates.columns)):
        working_exceptions = calendar_dates.copy()
        working_exceptions["service_id"] = working_exceptions["service_id"].map(_normalize_identifier)
        working_exceptions = working_exceptions[working_exceptions["service_id"].isin(normalized_service_ids)].copy()

        for _, row in working_exceptions.iterrows():
            service_id = row.get("service_id")
            service_date = _parse_gtfs_date(row.get("date"))
            if not service_id or service_date is None:
                continue

            service_day = service_date.date()
            if not _service_date_is_allowed(service_day, min_service_date, max_service_date):
                continue

            exception_type = str(row.get("exception_type", "")).strip()
            if exception_type == "1":
                service_dates[service_id].add(service_day)
            elif exception_type == "2":
                service_dates[service_id].discard(service_day)

    return {service_id: sorted(dates) for service_id, dates in service_dates.items() if dates}


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


def _first_country_code(value):
    if pd.isna(value):
        return None

    text_value = str(value).strip()
    if not text_value:
        return None

    primary_country = text_value.split(",")[0].strip().upper()
    return primary_country or None


def _haversine(lat1, lon1, lat2, lon2):
    if any(pd.isna([lat1, lon1, lat2, lon2])):
        return None

    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    from math import asin, cos, radians, sin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def _expand_services(df, base_date, service_dates_by_id):
    fallback_service_date = base_date.date()
    working_df = df.copy()

    if "service_id" in working_df.columns and service_dates_by_id:
        working_df["service_date"] = working_df["service_id"].map(
            lambda value: service_dates_by_id.get(_normalize_identifier(value), [fallback_service_date])
        )
    else:
        working_df["service_date"] = [[fallback_service_date] for _ in range(len(working_df))]

    working_df = working_df.explode("service_date", ignore_index=True)
    working_df["service_date"] = pd.to_datetime(working_df["service_date"], errors="coerce")
    working_df = working_df.dropna(subset=["service_date"]).copy()
    if working_df.empty:
        return working_df

    departure_seconds = pd.to_numeric(working_df["_raw_departure_time"].map(_gtfs_time_to_seconds), errors="coerce")
    arrival_seconds = pd.to_numeric(working_df["_raw_arrival_time"].map(_gtfs_time_to_seconds), errors="coerce")
    working_df["departure_time"] = working_df["service_date"] + pd.to_timedelta(departure_seconds, unit="s")
    working_df["arrival_time"] = working_df["service_date"] + pd.to_timedelta(arrival_seconds, unit="s")
    working_df["trip_id"] = (
        working_df["trip_id"].astype(str).str.strip()
        + "::"
        + working_df["service_date"].dt.strftime("%Y%m%d")
    )
    return working_df


def _parse_back_on_track_trip_export(file_path):
    raw_df = pd.read_csv(file_path, low_memory=False)
    required_columns = {
        "trip_id",
        "trip_origin",
        "origin_departure_time",
        "trip_headsign",
        "destination_arrival_time",
        "countries",
        "distance",
    }
    if not required_columns.issubset(set(raw_df.columns)):
        return pd.DataFrame()

    working_df = raw_df.copy()
    working_df["distance_km"] = pd.to_numeric(working_df.get("distance"), errors="coerce")
    working_df = working_df.dropna(subset=["trip_id", "trip_origin", "trip_headsign", "distance_km"]).copy()
    working_df = working_df[working_df["distance_km"] > 0].copy()
    if working_df.empty:
        return pd.DataFrame()

    base_date = datetime(datetime.utcnow().year, 1, 1)
    working_df["departure_time"] = working_df["origin_departure_time"].apply(
        lambda value: _parse_clock_to_datetime(value, base_date)
    )
    working_df["arrival_time"] = working_df["destination_arrival_time"].apply(
        lambda value: _parse_clock_to_datetime(value, base_date)
    )
    overnight_mask = (
        working_df["departure_time"].notna()
        & working_df["arrival_time"].notna()
        & (working_df["arrival_time"] < working_df["departure_time"])
    )
    if overnight_mask.any():
        working_df.loc[overnight_mask, "arrival_time"] = working_df.loc[overnight_mask, "arrival_time"] + timedelta(days=1)

    standardized_df = pd.DataFrame(
        {
            "trip_id": working_df["trip_id"],
            "origin_city": working_df["trip_origin"],
            "destination_city": working_df["trip_headsign"],
            "origin_lat": pd.NA,
            "origin_lon": pd.NA,
            "destination_lat": pd.NA,
            "destination_lon": pd.NA,
            "departure_time": working_df["departure_time"],
            "arrival_time": working_df["arrival_time"],
            "service_type": "Nuit",
            "train_type": "Rail",
            "distance_km": working_df["distance_km"],
            "co2_emissions": pd.to_numeric(working_df.get("emissions_co2e"), errors="coerce"),
            "operator_name": working_df.get("agency_id"),
            "country": working_df["countries"].apply(_first_country_code),
        }
    )
    standardized_df["co2_emissions"] = standardized_df["co2_emissions"].fillna(standardized_df["distance_km"] * 0.002)
    standardized_df = standardized_df.drop_duplicates(subset=["trip_id"]).reset_index(drop=True)
    return standardized_df


def parse_gtfs_zip(file_path):
    if file_path.endswith(".csv"):
        csv_name = os.path.basename(file_path).lower()
        if csv_name.endswith("back_on_track_trip_export.csv"):
            return _parse_back_on_track_trip_export(file_path)
        return pd.DataFrame()
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
                "_raw_departure_time": first_stops["departure_time"],
                "_raw_arrival_time": last_stops["arrival_time"],
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
        df["distance_km"] = df.apply(
            lambda row: _haversine(
                row.get("origin_lat"),
                row.get("origin_lon"),
                row.get("destination_lat"),
                row.get("destination_lon"),
            ),
            axis=1,
        )
        df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
        df = df[df["distance_km"].fillna(0) >= GTFS_MIN_DISTANCE_KM].copy()
        if df.empty:
            return pd.DataFrame()

        service_dates_by_id = {}
        if "service_id" in df.columns:
            service_dates_by_id = _build_service_dates(calendar, calendar_dates, df["service_id"].dropna().tolist())

        df = _expand_services(df, base_date, service_dates_by_id)
        if df.empty:
            return pd.DataFrame()

        df = df.dropna(subset=["departure_time", "arrival_time"])
        df = df.drop_duplicates(subset=["trip_id"])

        return df.reset_index(drop=True)
    except Exception as exc:
        logger.error(f"Erreur parsing GTFS: {exc}")
        return pd.DataFrame()
