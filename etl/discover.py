import json
import logging
import os
import re

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "sources.json")
STATIC_SOURCES_FILE = os.path.join(BASE_DIR, "sources_static.json")

TRANSITLAND_REST_URL = os.getenv("TRANSITLAND_REST_URL", "https://transit.land/api/v2/rest/feeds")
TRANSITLAND_PER_PAGE = max(25, int(os.getenv("TRANSITLAND_PER_PAGE", "100")))
TRANSITLAND_MAX_PAGES = max(1, int(os.getenv("TRANSITLAND_MAX_PAGES", "3")))
TRANSITLAND_TIMEOUT = int(os.getenv("TRANSITLAND_TIMEOUT", "45"))

EUROPE_COUNTRIES = [
    "AT", "BE", "BG", "CH", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GB", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
    "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK",
]

RAIL_KEYWORDS = [
    "rail", "railway", "train", "trains", "night train", "nightjet", "sleeper",
    "bahn", "db", "oebb", "obb", "sncf", "renfe", "trenitalia", "cff", "sbb",
    "railteam", "intercity", "eurostar", "thalys", "rail shuttle", "railway service",
    "ferroviaire", "ferroviario", "ferrocarril", "ferrovie", "helsinki train",
]


def _clean_id(value):
    if not value:
        return "unknown_source"
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_") or "unknown_source"


def _safe_json_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def _extract_feed_url(feed):
    urls = feed.get("urls") or {}
    if isinstance(urls, dict):
        for key in ("static_historic", "static_current", "static_planned"):
            value = urls.get(key)
            if isinstance(value, list) and value:
                return value[0]
            if isinstance(value, str) and value:
                return value
    direct_url = feed.get("url")
    if isinstance(direct_url, str) and direct_url:
        return direct_url
    return None


def _feed_haystack(feed):
    keys = [
        "id",
        "onestop_id",
        "name",
        "feed_name",
        "description",
        "spec",
        "operators",
        "provider",
        "license",
        "urls",
    ]
    return " ".join(_safe_json_text(feed.get(key)) for key in keys if feed.get(key) is not None).lower()


def _looks_like_rail_feed(feed):
    haystack = _feed_haystack(feed)
    return any(keyword in haystack for keyword in RAIL_KEYWORDS)


def load_static_sources():
    if not os.path.exists(STATIC_SOURCES_FILE):
        return []

    try:
        with open(STATIC_SOURCES_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        logger.error(f"Impossible de lire sources_static.json : {exc}")
        return []

    if not isinstance(data, list):
        return []

    valid_sources = []
    for source in data:
        if not isinstance(source, dict):
            continue
        if source.get("enabled") is False or not source.get("url"):
            continue
        source.setdefault("id", _clean_id(source.get("description") or source.get("url")))
        source.setdefault("type", "gtfs")
        source.setdefault("enabled", True)
        valid_sources.append(source)
    return valid_sources


def discover_transitland_country(country_code):
    discovered = []
    seen_urls = set()

    for page_idx in range(TRANSITLAND_MAX_PAGES):
        params = {
            "spec": "gtfs",
            "geographical_area": country_code,
            "per_page": TRANSITLAND_PER_PAGE,
            "offset": page_idx * TRANSITLAND_PER_PAGE,
        }

        try:
            response = requests.get(TRANSITLAND_REST_URL, params=params, timeout=TRANSITLAND_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.error(f"Erreur Transitland sur {country_code} page {page_idx + 1}: {exc}")
            break

        feeds = (
            payload.get("feeds")
            or payload.get("results")
            or payload.get("data")
            or payload.get("items")
            or []
        )
        if not feeds:
            break

        kept_this_page = 0
        for feed in feeds:
            if not isinstance(feed, dict):
                continue

            url = _extract_feed_url(feed)
            if not url or url in seen_urls:
                continue
            if not _looks_like_rail_feed(feed):
                continue

            source_id = _clean_id(
                feed.get("onestop_id")
                or feed.get("id")
                or f"transitland_{country_code}_{len(discovered) + 1}"
            )
            description = (
                feed.get("name")
                or feed.get("feed_name")
                or feed.get("description")
                or f"Transitland rail feed {country_code}"
            )

            discovered.append(
                {
                    "id": source_id,
                    "type": "gtfs",
                    "description": description,
                    "url": url,
                    "provider": feed.get("provider") or feed.get("operators") or feed.get("feed_publisher_name"),
                    "license": feed.get("license") or feed.get("license_name"),
                    "country": country_code,
                    "enabled": True,
                }
            )
            seen_urls.add(url)
            kept_this_page += 1

        logger.info("%s page %s : %s feeds rail retenus", country_code, page_idx + 1, kept_this_page)

        if len(feeds) < TRANSITLAND_PER_PAGE:
            break

    return discovered


def _deduplicate_sources(sources):
    deduplicated = []
    seen_urls = set()
    seen_ids = set()

    for source in sources:
        if not isinstance(source, dict):
            continue
        url = source.get("url")
        source_id = source.get("id")
        if not url or url in seen_urls or source_id in seen_ids:
            continue
        deduplicated.append(source)
        seen_urls.add(url)
        seen_ids.add(source_id)

    return deduplicated


def discover_massive_europe():
    logger.info("Debut de la prospection ferroviaire europeenne elargie...")

    all_sources = []
    for country_code in EUROPE_COUNTRIES:
        country_sources = discover_transitland_country(country_code)
        all_sources.extend(country_sources)
        logger.info(
            "OK %s : %s feeds rail ajoutes, %s sources cumulees",
            country_code,
            len(country_sources),
            len(all_sources),
        )

    static_sources = load_static_sources()
    if static_sources:
        logger.info("%s sources statiques ajoutees", len(static_sources))
        all_sources.extend(static_sources)

    final_sources = _deduplicate_sources(all_sources)
    final_sources = sorted(
        final_sources,
        key=lambda source: (
            source.get("country") or "ZZ",
            source.get("description") or source.get("id") or "",
        ),
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(final_sources, handle, indent=2, ensure_ascii=False)

    logger.info("Termine : %s sources europeennes ecrites dans %s", len(final_sources), OUTPUT_FILE)


if __name__ == "__main__":
    discover_massive_europe()
