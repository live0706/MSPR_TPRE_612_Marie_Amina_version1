import json
import logging
import os
import re

import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Chemins des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "sources.json")
STATIC_SOURCES_FILE = os.path.join(BASE_DIR, "sources_static.json")

# Parametres Transitland
TRANSITLAND_REST_URL = os.getenv("TRANSITLAND_REST_URL", "https://transit.land/api/v2/rest/feeds")
TRANSITLAND_PER_PAGE = max(25, int(os.getenv("TRANSITLAND_PER_PAGE", "100")))
TRANSITLAND_MAX_PAGES = max(1, int(os.getenv("TRANSITLAND_MAX_PAGES", "3")))
TRANSITLAND_TIMEOUT = int(os.getenv("TRANSITLAND_TIMEOUT", "45"))
TRANSITLAND_API_KEY = os.getenv("TRANSITLAND_API_KEY")

# Liste des pays Europeens cibles
EUROPE_COUNTRIES = [
    "AT", "BE", "BG", "CH", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GB", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
    "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK",
]

# Mots-cles pour filtrer le ferroviaire (Rail)
RAIL_KEYWORDS = [
    "rail", "railway", "train", "trains", "night train", "nightjet", "sleeper",
    "bahn", "db", "oebb", "obb", "sncf", "renfe", "trenitalia", "cff", "sbb",
    "railteam", "intercity", "eurostar", "thalys", "rail shuttle", "railway service",
    "ferroviaire", "ferroviario", "ferrocarril", "ferrovie", "helsinki train",
]


def _clean_id(value):
    """Genere un ID propre a partir d'une chaine."""
    if not value:
        return "unknown_source"
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_") or "unknown_source"


def _extract_feed_url(feed):
    """Cherche l'URL la plus pertinente dans les donnees Transitland."""
    urls = feed.get("urls") or {}
    if isinstance(urls, dict):
        for key in ("static_current", "static_planned", "static_historic"):
            value = urls.get(key)
            if isinstance(value, list) and value:
                return value[0]
            if isinstance(value, str) and value:
                return value
    return feed.get("url")


def _looks_like_rail_feed(feed):
    """Analyse si le flux concerne le train via ses metadonnees."""
    search_zone = str(feed).lower()
    return any(keyword in search_zone for keyword in RAIL_KEYWORDS)


def load_static_sources():
    """Charge sources_static.json en preservant les types (CSV, HTML, etc.)."""
    if not os.path.exists(STATIC_SOURCES_FILE):
        return []

    try:
        with open(STATIC_SOURCES_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        logger.error(f"Erreur lecture statique : {exc}")
        return []

    valid_sources = []
    for source in data:
        if not isinstance(source, dict) or not source.get("url"):
            continue
        if source.get("enabled") is False:
            continue

        source.setdefault("type", "gtfs")
        source.setdefault("id", _clean_id(source.get("id") or source.get("description")))
        valid_sources.append(source)

    return valid_sources


def discover_transitland_country(country_code):
    """Interroge l'API pour un pays donne."""
    discovered = []
    seen_urls = set()

    if not TRANSITLAND_API_KEY:
        return discovered

    for page_idx in range(TRANSITLAND_MAX_PAGES):
        params = {
            "spec": "gtfs",
            "geographical_area": country_code,
            "per_page": TRANSITLAND_PER_PAGE,
            "offset": page_idx * TRANSITLAND_PER_PAGE,
            "apikey": TRANSITLAND_API_KEY,
        }

        try:
            response = requests.get(TRANSITLAND_REST_URL, params=params, timeout=TRANSITLAND_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.error(f"Erreur API {country_code}: {exc}")
            break

        feeds = payload.get("feeds") or payload.get("results") or []
        if not feeds:
            break

        for feed in feeds:
            url = _extract_feed_url(feed)
            if not url or url in seen_urls:
                continue
            if not _looks_like_rail_feed(feed):
                continue

            discovered.append(
                {
                    "id": _clean_id(feed.get("onestop_id") or feed.get("id")),
                    "type": "gtfs",
                    "description": feed.get("name") or feed.get("description"),
                    "url": url,
                    "provider": feed.get("provider") or feed.get("feed_publisher_name"),
                    "country": country_code,
                    "enabled": True,
                }
            )
            seen_urls.add(url)

    return discovered


def _deduplicate_sources(sources):
    """Supprime les doublons bases sur l'URL et l'ID."""
    deduplicated = []
    seen_urls = set()
    seen_ids = set()

    for source in sources:
        url, source_id = source.get("url"), source.get("id")
        if url in seen_urls or source_id in seen_ids:
            continue
        deduplicated.append(source)
        seen_urls.add(url)
        seen_ids.add(source_id)
    return deduplicated


def run_discovery():
    """Lance la prospection globale."""
    logger.info("Debut de la prospection (API + Statique)...")

    all_sources = []

    static_sources = load_static_sources()
    logger.info("%s sources statiques chargees.", len(static_sources))
    all_sources.extend(static_sources)

    if not TRANSITLAND_API_KEY:
        logger.info("TRANSITLAND_API_KEY absente : decouverte Transitland ignoree, sources statiques uniquement.")
    else:
        for country in EUROPE_COUNTRIES:
            found = discover_transitland_country(country)
            all_sources.extend(found)
            logger.info("Pays %s : %s flux rail identifies.", country, len(found))

    final_sources = _deduplicate_sources(all_sources)
    final_sources = sorted(final_sources, key=lambda source: (source.get("country") or "ZZ", source.get("id")))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(final_sources, handle, indent=2, ensure_ascii=False)

    logger.info("Termine : %s sources ecrites dans %s", len(final_sources), OUTPUT_FILE)


if __name__ == "__main__":
    run_discovery()
