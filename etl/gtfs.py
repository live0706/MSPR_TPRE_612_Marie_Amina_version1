import logging
import os
import zipfile
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger()


def _gtfs_time_to_datetime(value, base_date):
    if pd.isna(value):
        return pd.NaT
    if not isinstance(value, str):
        return pd.NaT
    parts = value.strip().split(":")
    if len(parts) < 2:
        return pd.NaT
    try:
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        return pd.NaT
    day_offset = h // 24
    h = h % 24
    return base_date + timedelta(days=day_offset, hours=h, minutes=m, seconds=s)


def parse_gtfs_zip(file_path):
    """
    Parse a GTFS zip file and return a DataFrame with columns aligned
    to the pipeline (trip_id, origin_city, destination_city, departure_time, arrival_time, operator_name, train_type).
    """
    if not file_path or not os.path.exists(file_path):
        logger.warning("GTFS file not found.")
        return pd.DataFrame()

    base_date = datetime(2000, 1, 1)

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            def _read_csv(name):
                if name not in zf.namelist():
                    return pd.DataFrame()
                with zf.open(name) as f:
                    return pd.read_csv(f)

            stop_times = _read_csv("stop_times.txt")
            trips = _read_csv("trips.txt")
            routes = _read_csv("routes.txt")
            agency = _read_csv("agency.txt")
            stops = _read_csv("stops.txt")

        if stop_times.empty:
            logger.warning("GTFS stop_times.txt missing or empty.")
            return pd.DataFrame()

        # Ensure required columns exist
        required_cols = {"trip_id", "stop_id", "stop_sequence", "departure_time", "arrival_time"}
        if not required_cols.issubset(set(stop_times.columns)):
            logger.warning("GTFS stop_times.txt missing required columns.")
            return pd.DataFrame()

        stop_times = stop_times.sort_values(["trip_id", "stop_sequence"])
        first_stop = stop_times.groupby("trip_id").first().reset_index()
        last_stop = stop_times.groupby("trip_id").last().reset_index()

        stops_map_name = {}
        stops_map_lat = {}
        stops_map_lon = {}
        if not stops.empty and "stop_id" in stops.columns:
            if "stop_name" in stops.columns:
                stops_map_name = dict(zip(stops["stop_id"], stops["stop_name"]))
            if "stop_lat" in stops.columns:
                stops_map_lat = dict(zip(stops["stop_id"], stops["stop_lat"]))
            if "stop_lon" in stops.columns:
                stops_map_lon = dict(zip(stops["stop_id"], stops["stop_lon"]))

        df = pd.DataFrame(
            {
                "trip_id": first_stop["trip_id"],
                "origin_city": first_stop["stop_id"].map(stops_map_name),
                "destination_city": last_stop["stop_id"].map(stops_map_name),
                "origin_lat": first_stop["stop_id"].map(stops_map_lat),
                "origin_lon": first_stop["stop_id"].map(stops_map_lon),
                "destination_lat": last_stop["stop_id"].map(stops_map_lat),
                "destination_lon": last_stop["stop_id"].map(stops_map_lon),
                "departure_time": first_stop["departure_time"].apply(lambda v: _gtfs_time_to_datetime(v, base_date)),
                "arrival_time": last_stop["arrival_time"].apply(lambda v: _gtfs_time_to_datetime(v, base_date)),
            }
        )

        # Join to routes and agency when possible
        if not trips.empty and "trip_id" in trips.columns and "route_id" in trips.columns:
            df = df.merge(trips[["trip_id", "route_id"]], on="trip_id", how="left")
        if not routes.empty and "route_id" in routes.columns:
            route_cols = [c for c in ["route_id", "agency_id", "route_long_name", "route_short_name", "route_type"] if c in routes.columns]
            df = df.merge(routes[route_cols], on="route_id", how="left")
        if not agency.empty and "agency_id" in agency.columns and "agency_name" in agency.columns:
            df = df.merge(agency[["agency_id", "agency_name"]], on="agency_id", how="left")

        # Operator name
        if "agency_name" in df.columns:
            df["operator_name"] = df["agency_name"]
        elif "route_long_name" in df.columns:
            df["operator_name"] = df["route_long_name"]
        elif "route_short_name" in df.columns:
            df["operator_name"] = df["route_short_name"]

        # Train type from GTFS route_type
        if "route_type" in df.columns:
            route_type_map = {
                0: "Tram",
                1: "Metro",
                2: "Rail",
                3: "Bus",
                4: "Ferry",
                5: "Cable",
                6: "Gondola",
                7: "Funicular",
                100: "Rail",
                101: "Rail",
                102: "Rail",
                103: "Rail",
                104: "Rail",
                105: "Rail",
                106: "Rail",
                107: "Rail",
                108: "Rail",
            }
            df["train_type"] = df["route_type"].map(route_type_map)

            # Keep only rail services (exclude Bus/Tram/Metro/etc.)
            allowed_rail_types = {2, 100, 101, 102, 103, 104, 105, 106, 107, 108}
            df = df[df["route_type"].isin(allowed_rail_types)].copy()

        return df

    except Exception as e:
        logger.error(f"GTFS parsing error: {e}")
        return pd.DataFrame()
