import json
import logging
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from source_config import SOURCE_FILE, load_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESET_DB = os.getenv("RESET_DB", "false").lower() in ("1", "true", "yes")

COUNTRY_METADATA = {
    "AT": {"name": "Austria", "keywords": ["austria", "autriche", "osterreich", "oebb", "obb", "vienna", "wien", "wien hbf", "innsbruck", "salzburg", "graz"]},
    "BE": {"name": "Belgium", "keywords": ["belgium", "belgique", "sncb", "nmbs", "brussels", "bruxelles"]},
    "BG": {"name": "Bulgaria", "keywords": ["bulgaria", "bulgarie", "bdz", "sofia", "varna", "burgas", "dobrich", "silistra", "plovdiv"]},
    "CH": {"name": "Switzerland", "keywords": ["switzerland", "suisse", "schweiz", "sbb", "cff", "zurich", "zrich", "geneva", "lausanne", "basel", "bern"]},
    "CZ": {"name": "Czech Republic", "keywords": ["czech republic", "republique tcheque", "cesko", "cd rail", "ceske drahy", "prague", "praha"]},
    "DE": {"name": "Germany", "keywords": ["germany", "allemagne", "deutschland", "deutsche bahn", "db", "berlin", "munich", "hamburg", "frankfurt", "flixtrain"]},
    "DK": {"name": "Denmark", "keywords": ["denmark", "danemark", "dsb", "copenhagen", "kobenhavn"]},
    "EE": {"name": "Estonia", "keywords": ["estonia", "estonie", "elron", "tallinn"]},
    "ES": {"name": "Spain", "keywords": ["spain", "espagne", "espana", "renfe", "ave", "madrid", "barcelona", "sevilla", "valencia"]},
    "FI": {"name": "Finland", "keywords": ["finland", "finlande", "vr", "helsinki"]},
    "FR": {"name": "France", "keywords": ["france", "sncf", "transilien", "idf", "ile-de-france", "idfm", "ter", "tgv", "intercites", "ouigo", "atoumod", "breizhgo", "nomad", "zou", "mobigo", "remi", "grand est", "hauts-de-france", "occitanie", "bretagne", "normandie", "pays de la loire", "centre-val-de-loire", "nouvelle-aquitaine", "auvergne-rhone-alpes", "lio"]},
    "GB": {"name": "United Kingdom", "keywords": ["united kingdom", "uk", "great britain", "britain", "england", "scotland", "wales", "london", "avanti", "lner", "gwr", "eurostar international"]},
    "GR": {"name": "Greece", "keywords": ["greece", "grece", "hellas", "ose", "athens", "thessaloniki"]},
    "HR": {"name": "Croatia", "keywords": ["croatia", "croatie", "hzpp", "zagreb"]},
    "HU": {"name": "Hungary", "keywords": ["hungary", "hongrie", "mav", "budapest"]},
    "IE": {"name": "Ireland", "keywords": ["ireland", "irlande", "irish rail", "iarnrod eireann", "dublin"]},
    "IT": {"name": "Italy", "keywords": ["italy", "italie", "italia", "trenitalia", "italo", "rome", "roma", "roma termini", "milan", "milano", "venice", "venezia", "turin", "torino", "naples", "napoli"]},
    "LT": {"name": "Lithuania", "keywords": ["lithuania", "lituanie", "ltg", "vilnius"]},
    "LU": {"name": "Luxembourg", "keywords": ["luxembourg", "cfl", "luxemburg"]},
    "LV": {"name": "Latvia", "keywords": ["latvia", "lettonie", "pasa ieru vilciens", "riga"]},
    "NL": {"name": "Netherlands", "keywords": ["netherlands", "pays-bas", "nederland", "ns", "amsterdam", "rotterdam", "utrecht"]},
    "NO": {"name": "Norway", "keywords": ["norway", "norvege", "vy", "oslo"]},
    "PL": {"name": "Poland", "keywords": ["poland", "pologne", "pkp", "warsaw", "warszawa", "intercity polska", "przemysl"]},
    "PT": {"name": "Portugal", "keywords": ["portugal", "cp", "comboios", "lisbon", "lisboa", "porto"]},
    "RO": {"name": "Romania", "keywords": ["romania", "roumanie", "cfr", "bucharest", "bucuresti", "bucureti", "braov", "brasov", "bistria", "cluj", "oradea", "timioara", "iai", "iasi", "arad", "satu mare", "vatra dornei"]},
    "RS": {"name": "Serbia", "keywords": ["serbia", "serbie", "srbija voz", "beograd", "belgrade"]},
    "SE": {"name": "Sweden", "keywords": ["sweden", "suede", "sj", "stockholm", "snalltaget", "malmo"]},
    "SI": {"name": "Slovenia", "keywords": ["slovenia", "slovenie", "sz", "slovenske zeleznice", "ljubljana"]},
    "SK": {"name": "Slovakia", "keywords": ["slovakia", "slovaquie", "zssk", "bratislava"]},
    "TR": {"name": "Turkey", "keywords": ["turkey", "turkiye", "tcdd", "ankara", "istanbul", "izmir"]},
    "UA": {"name": "Ukraine", "keywords": ["ukraine", "ukraina", "uz", "kyiv", "kiev", "odesa", "odessa", "kharkiv", "lviv", "dnipro", "zaporizhzhia", "chernivtsi", "uzhhorod", "pasazhyrskyi", "holovny"]},
    "ZZ": {"name": "Unknown", "keywords": []},
}

COUNTRY_ALIASES = {
    "autriche": "AT",
    "osterreich": "AT",
    "belgique": "BE",
    "bulgarie": "BG",
    "suisse": "CH",
    "schweiz": "CH",
    "republique tcheque": "CZ",
    "czechia": "CZ",
    "allemagne": "DE",
    "danemark": "DK",
    "estonie": "EE",
    "espagne": "ES",
    "espana": "ES",
    "finlande": "FI",
    "france": "FR",
    "united kingdom": "GB",
    "great britain": "GB",
    "britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "uk": "GB",
    "grece": "GR",
    "croatie": "HR",
    "hongrie": "HU",
    "irlande": "IE",
    "italie": "IT",
    "italia": "IT",
    "lituanie": "LT",
    "lettonie": "LV",
    "pays-bas": "NL",
    "norvege": "NO",
    "pologne": "PL",
    "roumanie": "RO",
    "serbie": "RS",
    "suede": "SE",
    "slovenie": "SI",
    "slovaquie": "SK",
    "turkiye": "TR",
    "turquie": "TR",
    "ukraine": "UA",
}

for _country_code, _metadata in COUNTRY_METADATA.items():
    COUNTRY_ALIASES.setdefault(_metadata["name"].lower(), _country_code)


def _normalize_search_text(value):
    normalized_name = _normalize_name(value)
    if normalized_name is None:
        return None

    ascii_text = unicodedata.normalize("NFKD", normalized_name)
    ascii_text = "".join(char for char in ascii_text if not unicodedata.combining(char))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    ascii_text = re.sub(r"\s+", " ", ascii_text).strip()
    return ascii_text or None


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


NORMALIZED_COUNTRY_ALIASES = {
    normalized_alias: country_code
    for alias, country_code in COUNTRY_ALIASES.items()
    for normalized_alias in [_normalize_search_text(alias)]
    if normalized_alias
}
NORMALIZED_COUNTRY_KEYWORDS = {
    country_code: [
        normalized_keyword
        for keyword in metadata["keywords"]
        for normalized_keyword in [_normalize_search_text(keyword)]
        if normalized_keyword
    ]
    for country_code, metadata in COUNTRY_METADATA.items()
}
UNKNOWN_COUNTRY_CODES = {"ZZ"}


def _normalize_scalar(value):
    if pd.isna(value):
        return None
    return value


def _stage_and_merge(engine, df, staging_table, target_table, columns, conflict_cols):
    if df.empty:
        return
    cleaned_df = df.copy()
    for column in cleaned_df.columns:
        cleaned_df[column] = cleaned_df[column].map(_normalize_scalar)
    cleaned_df.to_sql(staging_table, engine, if_exists="replace", index=False, method="multi", chunksize=1000)
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
    working_df = df.copy()
    working_df.to_sql("routes_staging", engine, if_exists="replace", index=False, method="multi", chunksize=1000)
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
        LEFT JOIN stations so
            ON so.name = rs.origin_city
            AND COALESCE(so.country, '') = COALESCE(rs.origin_country, '')
        LEFT JOIN stations sd
            ON sd.name = rs.destination_city
            AND COALESCE(sd.country, '') = COALESCE(rs.destination_country, '')
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
    working_df = df.copy()
    working_df.to_sql("trips_staging", engine, if_exists="replace", index=False, method="multi", chunksize=2000)
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
        LEFT JOIN stations so
            ON so.name = ts.origin_city
            AND COALESCE(so.country, '') = COALESCE(ts.origin_country, '')
        LEFT JOIN stations sd
            ON sd.name = ts.destination_city
            AND COALESCE(sd.country, '') = COALESCE(ts.destination_country, '')
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


def _stage_and_merge_analytic_trains(engine, df):
    if df.empty:
        return
    working_df = df.copy()
    working_df.to_sql("facts_night_trains_staging", engine, if_exists="replace", index=False, method="multi", chunksize=2000)
    insert_sql = """
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
            s.trip_id,
            s.route_id,
            s.night_train,
            c.country_id,
            y.year_id,
            o.operator_id,
            s.is_night,
            s.distance_km,
            s.co2_emissions
        FROM facts_night_trains_staging s
        JOIN dim_countries c ON c.country_code = s.country_code
        JOIN dim_years y ON y.year = s.year
        JOIN dim_operators o ON o.operator_name = s.operator_name
        ON CONFLICT (trip_id) DO NOTHING
    """
    with engine.begin() as conn:
        conn.execute(text(insert_sql))
        conn.execute(text("DROP TABLE IF EXISTS facts_night_trains_staging"))


def _stage_and_merge_country_stats(engine, df):
    if df.empty:
        return
    working_df = df.copy()
    working_df.to_sql("facts_country_stats_staging", engine, if_exists="replace", index=False, method="multi", chunksize=1000)
    insert_sql = """
        INSERT INTO facts_country_stats (
            passengers,
            co2_emissions,
            co2_per_passenger,
            country_id,
            year_id
        )
        SELECT
            s.passengers,
            s.co2_emissions,
            s.co2_per_passenger,
            c.country_id,
            y.year_id
        FROM facts_country_stats_staging s
        JOIN dim_countries c ON c.country_code = s.country_code
        JOIN dim_years y ON y.year = s.year
        ON CONFLICT (country_id, year_id) DO NOTHING
    """
    with engine.begin() as conn:
        conn.execute(text(insert_sql))
        conn.execute(text("DROP TABLE IF EXISTS facts_country_stats_staging"))


def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL missing from environment variables")
        return None
    try:
        return create_engine(db_url)
    except Exception as exc:
        logger.error(f"DB Connection Error: {exc}")
        return None


def _ensure_source_columns(engine):
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS country_code VARCHAR(10)"))
        conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS country_name VARCHAR(100)"))


def _load_sources_from_file():
    sources = load_sources(SOURCE_FILE)
    if not sources:
        logger.warning("No source configuration available for load")
    return sources


def _truncate_tables(engine):
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                TRUNCATE
                    facts_country_stats,
                    facts_night_trains,
                    dim_operators,
                    dim_years,
                    dim_countries,
                    trips,
                    routes,
                    stations,
                    operators,
                    ingestions,
                    sources
                RESTART IDENTITY CASCADE
                """
            )
        )


def _truncate_analytic_tables(engine):
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                TRUNCATE
                    facts_country_stats,
                    facts_night_trains,
                    dim_operators,
                    dim_years,
                    dim_countries
                RESTART IDENTITY CASCADE
                """
            )
        )


def _country_name_from_code(country_code):
    return COUNTRY_METADATA.get(country_code, COUNTRY_METADATA["ZZ"])["name"]


def _normalize_country_code(value):
    normalized = _normalize_name(value)
    if normalized is None:
        return None

    upper_value = normalized.upper()
    if upper_value in COUNTRY_METADATA:
        return upper_value

    normalized_search = _normalize_search_text(normalized)
    if normalized_search is None:
        return None

    return NORMALIZED_COUNTRY_ALIASES.get(normalized_search)


def _normalize_informative_country_code(value):
    normalized_country = _normalize_country_code(value)
    if normalized_country in UNKNOWN_COUNTRY_CODES:
        return None
    return normalized_country


def _country_name_from_value(value):
    country_code = _normalize_country_code(value)
    if country_code:
        return _country_name_from_code(country_code)
    return _normalize_name(value)


def _fill_source_metadata_column(df, column_name, mapping):
    existing_values = (
        df[column_name].map(_normalize_name)
        if column_name in df.columns
        else pd.Series(index=df.index, dtype="object")
    )
    mapped_values = df["source_origin"].map(mapping).map(_normalize_name)
    df[column_name] = existing_values.fillna(mapped_values)


def _infer_country_code_from_values(*values):
    haystack = " ".join(
        normalized_chunk
        for normalized_chunk in (_normalize_search_text(value) for value in values)
        if normalized_chunk
    )
    if not haystack:
        return None

    for country_code, keywords in NORMALIZED_COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in haystack:
                return country_code
    return None


def _infer_country_code(row):
    for direct_key in (
        "country_code",
        "country",
        "source_country_code",
        "source_country",
        "source_country_name",
        "operator_country",
        "origin_country",
        "destination_country",
    ):
        normalized_country = _normalize_informative_country_code(row.get(direct_key))
        if normalized_country:
            return normalized_country

    return _infer_country_code_from_values(
        row.get("source_key"),
        row.get("source_name"),
        row.get("source_provider"),
        row.get("source_country_name"),
        row.get("operator_name"),
        row.get("operator_country"),
        row.get("origin_city"),
        row.get("origin_country"),
        row.get("destination_city"),
        row.get("destination_country"),
    ) or "ZZ"


def _build_night_train_name(row):
    origin_city = _normalize_name(row.get("origin_city"))
    destination_city = _normalize_name(row.get("destination_city"))
    if origin_city and destination_city:
        return f"{origin_city} - {destination_city}"
    if origin_city:
        return origin_city
    if destination_city:
        return destination_city
    return row.get("trip_id") or "unknown_trip"


def _infer_year(row):
    departure_time = row.get("departure_time")
    if pd.notna(departure_time):
        year = int(departure_time.year)
        if 2010 <= year <= 2100:
            return year

    trip_id = str(row.get("trip_id") or "")
    match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", trip_id)
    if match:
        return int(match.group(1))

    match = re.search(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", trip_id)
    if match:
        return int(match.group(1))

    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", trip_id)
    if match:
        return int(match.group(1))

    return datetime.utcnow().year


def _load_analytic_layer(engine):
    query = """
        SELECT
            t.trip_id,
            t.route_id,
            t.departure_time,
            t.service_type,
            t.train_type,
            t.co2_emissions,
            r.distance_km,
            o.name AS operator_name,
            o.country AS operator_country,
            so.name AS origin_city,
            so.country AS origin_country,
            sd.name AS destination_city,
            sd.country AS destination_country,
            s.source_key,
            s.name AS source_name,
            s.provider AS source_provider,
            s.country_code AS source_country_code,
            s.country_name AS source_country_name
        FROM trips t
        LEFT JOIN routes r ON t.route_id = r.route_id
        LEFT JOIN operators o ON r.operator_id = o.operator_id
        LEFT JOIN stations so ON r.origin_station_id = so.station_id
        LEFT JOIN stations sd ON r.destination_station_id = sd.station_id
        LEFT JOIN sources s ON t.source_id = s.source_id
    """
    analytic_df = pd.read_sql(query, engine)
    if analytic_df.empty:
        logger.warning("Analytic layer skipped: no trips found in database")
        return

    analytic_df["departure_time"] = pd.to_datetime(analytic_df["departure_time"], errors="coerce")
    analytic_df = analytic_df.dropna(subset=["trip_id", "departure_time"]).copy()
    if analytic_df.empty:
        logger.warning("Analytic layer skipped: trips missing identifiers or dates")
        return

    analytic_df["operator_name"] = analytic_df["operator_name"].map(_normalize_name).fillna("Unknown Operator")
    analytic_df["distance_km"] = pd.to_numeric(analytic_df["distance_km"], errors="coerce").fillna(0.0)
    analytic_df["co2_emissions"] = pd.to_numeric(analytic_df["co2_emissions"], errors="coerce").fillna(0.0)
    analytic_df["year"] = analytic_df.apply(_infer_year, axis=1)
    analytic_df["is_night"] = analytic_df["service_type"].fillna("").eq("Nuit")
    analytic_df["country_code"] = analytic_df.apply(_infer_country_code, axis=1)
    analytic_df["country_name"] = analytic_df["country_code"].map(_country_name_from_code)
    analytic_df["night_train"] = analytic_df.apply(_build_night_train_name, axis=1)

    countries_df = (
        analytic_df[["country_code", "country_name"]]
        .drop_duplicates()
        .sort_values(["country_name", "country_code"])
    )
    _stage_and_merge(
        engine,
        countries_df,
        "dim_countries_staging",
        "dim_countries",
        ["country_code", "country_name"],
        ["country_code"],
    )

    years_df = (
        analytic_df[["year"]]
        .drop_duplicates()
        .sort_values("year")
        .assign(is_after_2010=lambda frame: frame["year"] >= 2010)
    )
    _stage_and_merge(
        engine,
        years_df,
        "dim_years_staging",
        "dim_years",
        ["year", "is_after_2010"],
        ["year"],
    )

    analytic_operators_df = (
        analytic_df[["operator_name"]]
        .drop_duplicates()
        .rename(columns={"operator_name": "operator_name"})
        .sort_values("operator_name")
    )
    _stage_and_merge(
        engine,
        analytic_operators_df,
        "dim_operators_staging",
        "dim_operators",
        ["operator_name"],
        ["operator_name"],
    )

    fact_trains_df = analytic_df[
        [
            "trip_id",
            "route_id",
            "night_train",
            "country_code",
            "year",
            "operator_name",
            "is_night",
            "distance_km",
            "co2_emissions",
        ]
    ].drop_duplicates(subset=["trip_id"])
    _stage_and_merge_analytic_trains(engine, fact_trains_df)

    country_stats_df = (
        analytic_df.groupby(["country_code", "country_name", "year"], as_index=False)
        .agg(
            passengers=("trip_id", "nunique"),
            co2_emissions=("co2_emissions", "sum"),
        )
    )
    country_stats_df["passengers"] = country_stats_df["passengers"].astype(float)
    country_stats_df["co2_per_passenger"] = country_stats_df.apply(
        lambda row: round(row["co2_emissions"] / row["passengers"], 6) if row["passengers"] else 0.0,
        axis=1,
    )
    _stage_and_merge_country_stats(
        engine,
        country_stats_df[
            ["country_code", "year", "passengers", "co2_emissions", "co2_per_passenger"]
        ],
    )

    logger.info("Analytic layer loaded successfully")


def run_load(data):
    logger.info("Starting data load process...")
    engine = get_db_engine()
    if not engine:
        return
    _ensure_source_columns(engine)

    if isinstance(data, str) and os.path.exists(data):
        logger.info(f"Reading file: {data}")
        df_to_load = pd.read_csv(data, parse_dates=["departure_time", "arrival_time"])
    elif isinstance(data, pd.DataFrame):
        df_to_load = data.copy()
    else:
        logger.warning("Invalid data input provided")
        return

    if df_to_load.empty:
        logger.warning("No data to process")
        return

    for column in ["operator_name", "origin_city", "destination_city"]:
        if column in df_to_load.columns:
            df_to_load[column] = df_to_load[column].map(_normalize_name)

    for column in [
        "origin_lat",
        "origin_lon",
        "destination_lat",
        "destination_lon",
        "distance_km",
        "co2_emissions",
    ]:
        if column in df_to_load.columns:
            df_to_load[column] = pd.to_numeric(df_to_load[column], errors="coerce")

    if RESET_DB:
        logger.info("RESET_DB active: truncating tables")
        _truncate_tables(engine)
    else:
        logger.info("RESET_DB inactive: cumulative transactional load enabled")

    sources_list = _load_sources_from_file()
    if sources_list:
        now = datetime.utcnow()
        df_sources = pd.DataFrame(
            [
                {
                    "source_key": src.get("id"),
                    "name": src.get("description"),
                    "url": src.get("url"),
                    "source_type": src.get("type"),
                    "provider": _provider_to_text(src.get("provider")),
                    "license": _license_to_text(src.get("license")),
                    "country_code": _normalize_country_code(src.get("country")),
                    "country_name": (
                        _country_name_from_code(_normalize_country_code(src.get("country")))
                        if _normalize_country_code(src.get("country"))
                        else None
                    ),
                    "last_seen": now,
                }
                for src in sources_list
            ]
        ).dropna(subset=["source_key", "url"]).drop_duplicates(subset=["source_key"])

        if not df_sources.empty:
            _stage_and_merge(
                engine,
                df_sources,
                "sources_staging",
                "sources",
                [
                    "source_key",
                    "name",
                    "url",
                    "source_type",
                    "provider",
                    "license",
                    "country_code",
                    "country_name",
                    "last_seen",
                ],
                ["source_key"],
            )

    src_map_df = pd.read_sql("SELECT source_id, source_key FROM sources", engine)
    source_key_to_id = dict(zip(src_map_df["source_key"], src_map_df["source_id"]))
    df_to_load["source_id"] = df_to_load["source_origin"].map(source_key_to_id)
    source_metadata_map = {
        src.get("id"): {
            "source_name": src.get("description"),
            "source_provider": _provider_to_text(src.get("provider")),
            "source_country": _normalize_country_code(src.get("country")),
            "source_country_name": (
                _country_name_from_code(_normalize_country_code(src.get("country")))
                if _normalize_country_code(src.get("country"))
                else None
            ),
        }
        for src in sources_list
    }
    _fill_source_metadata_column(
        df_to_load,
        "source_name",
        {key: value.get("source_name") for key, value in source_metadata_map.items()},
    )
    _fill_source_metadata_column(
        df_to_load,
        "source_provider",
        {key: value.get("source_provider") for key, value in source_metadata_map.items()},
    )
    _fill_source_metadata_column(
        df_to_load,
        "source_country",
        {key: value.get("source_country") for key, value in source_metadata_map.items()},
    )
    _fill_source_metadata_column(
        df_to_load,
        "source_country_name",
        {key: value.get("source_country_name") for key, value in source_metadata_map.items()},
    )

    if "country" in df_to_load.columns:
        df_to_load["country"] = df_to_load["country"].map(_normalize_name)
    if "source_country" in df_to_load.columns:
        df_to_load["source_country"] = df_to_load["source_country"].map(_normalize_name)

    origin_country_code_series = df_to_load.apply(
        lambda row: _infer_country_code_from_values(row.get("origin_country"), row.get("origin_city")),
        axis=1,
    )
    destination_country_code_series = df_to_load.apply(
        lambda row: _infer_country_code_from_values(row.get("destination_country"), row.get("destination_city")),
        axis=1,
    )

    country_code_series = pd.Series(index=df_to_load.index, dtype="object")
    for column in ("country_code", "country", "source_country"):
        if column in df_to_load.columns:
            country_code_series = country_code_series.fillna(df_to_load[column].map(_normalize_informative_country_code))

    country_code_series = country_code_series.fillna(origin_country_code_series).fillna(destination_country_code_series)

    df_to_load["country_code"] = country_code_series
    missing_country_mask = df_to_load["country_code"].isna()
    if missing_country_mask.any():
        df_to_load.loc[missing_country_mask, "country_code"] = df_to_load.loc[missing_country_mask].apply(
            _infer_country_code,
            axis=1,
        )
    df_to_load["country_code"] = df_to_load["country_code"].fillna("ZZ")
    df_to_load["country_name"] = df_to_load["country_code"].map(_country_name_from_code)

    if "country" in df_to_load.columns:
        current_country_codes = df_to_load["country"].map(_normalize_informative_country_code)
        df_to_load["country"] = current_country_codes.fillna(df_to_load["country_code"])
    else:
        df_to_load["country"] = df_to_load["country_code"]

    if "source_country" in df_to_load.columns:
        current_source_country_codes = df_to_load["source_country"].map(_normalize_informative_country_code)
        df_to_load["source_country"] = current_source_country_codes.fillna(df_to_load["country_code"])
    else:
        df_to_load["source_country"] = df_to_load["country_code"]

    if "origin_country" in df_to_load.columns:
        df_to_load["origin_country"] = df_to_load["origin_country"].map(_country_name_from_value)
    else:
        df_to_load["origin_country"] = None

    if "destination_country" in df_to_load.columns:
        df_to_load["destination_country"] = df_to_load["destination_country"].map(_country_name_from_value)
    else:
        df_to_load["destination_country"] = None

    df_to_load["origin_country"] = df_to_load["origin_country"].fillna(origin_country_code_series.map(_country_name_from_code))
    df_to_load["destination_country"] = df_to_load["destination_country"].fillna(destination_country_code_series.map(_country_name_from_code))
    df_to_load["origin_country"] = df_to_load["origin_country"].fillna(df_to_load["country_name"])
    df_to_load["destination_country"] = df_to_load["destination_country"].fillna(df_to_load["country_name"])

    try:
        ingestions_df = df_to_load.groupby("source_origin", dropna=False).size().reset_index(name="row_count")
        ingestions_df["source_id"] = ingestions_df["source_origin"].map(source_key_to_id)
        ingestions_df["fetched_at"] = datetime.utcnow()
        ingestions_df["status"] = "success"
        ingestions_df["raw_path"] = None
        ingestions_df = ingestions_df[["source_id", "fetched_at", "raw_path", "status", "row_count"]]
        ingestions_df.to_sql("ingestions", engine, if_exists="append", index=False, method="multi")
    except Exception as exc:
        logger.warning(f"Ingestion log skipped: {exc}")

    operators_df = df_to_load[["operator_name", "source_id"]].rename(columns={"operator_name": "name"})
    operators_df = operators_df.dropna(subset=["name"]).drop_duplicates(subset=["name"])
    operators_df["country"] = (
        df_to_load.groupby("operator_name")["country_name"].first().reindex(operators_df["name"]).tolist()
    )
    if not operators_df.empty:
        _stage_and_merge(
            engine,
            operators_df,
            "operators_staging",
            "operators",
            ["name", "country", "source_id"],
            ["name"],
        )

    origin_df = df_to_load[["origin_city", "origin_lat", "origin_lon", "source_id", "origin_country"]].rename(
        columns={"origin_city": "name", "origin_lat": "lat", "origin_lon": "lon", "origin_country": "country"}
    )
    dest_df = df_to_load[
        ["destination_city", "destination_lat", "destination_lon", "source_id", "destination_country"]
    ].rename(
        columns={"destination_city": "name", "destination_lat": "lat", "destination_lon": "lon", "destination_country": "country"}
    )
    stations_df = pd.concat([origin_df, dest_df], ignore_index=True).dropna(subset=["name"])
    stations_df = stations_df.groupby(["name", "country"], as_index=False).first()
    if not stations_df.empty:
        _stage_and_merge(
            engine,
            stations_df,
            "stations_staging",
            "stations",
            ["name", "country", "lat", "lon", "source_id"],
            ["name", "country"],
        )

    _stage_and_merge_routes(engine, df_to_load)
    _stage_and_merge_trips(engine, df_to_load)
    logger.info("Refreshing analytic layer from all transactional trips")
    _truncate_analytic_tables(engine)
    _load_analytic_layer(engine)

    logger.info("Load process completed successfully")


if __name__ == "__main__":
    processed_path = os.path.join(BASE_DIR, "..", "data", "processed", "trips_cleaned_final.csv")
    if os.path.exists(processed_path):
        run_load(processed_path)
