import json
import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(BASE_DIR, "sources.json")
STATIC_SOURCE_FILE = os.path.join(BASE_DIR, "sources_static.json")
TRUTHY_VALUES = ("1", "true", "yes")

logger = logging.getLogger(__name__)


def _normalize_source(source):
    if not isinstance(source, dict):
        return None

    url = source.get("url")
    if not isinstance(url, str) or not url.strip():
        return None
    if source.get("enabled") is False:
        return None

    normalized = dict(source)
    normalized["url"] = url.strip()
    normalized.setdefault("type", "gtfs")

    country = normalized.get("country")
    if country is None:
        normalized["country"] = None
    else:
        country_text = str(country).strip().upper()
        normalized["country"] = country_text or None

    return normalized


def _read_sources_file(path):
    if not path or not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        logger.warning("Impossible de lire %s: %s", path, exc)
        return []

    if not isinstance(payload, list):
        logger.warning("Format invalide pour %s: liste attendue", path)
        return []

    normalized_sources = []
    for source in payload:
        normalized_source = _normalize_source(source)
        if normalized_source:
            normalized_sources.append(normalized_source)
    return normalized_sources


def load_sources(config_path=None, prefer_dynamic=True):
    candidate_paths = []
    if config_path:
        candidate_paths.append(config_path)

    default_paths = [SOURCE_FILE, STATIC_SOURCE_FILE] if prefer_dynamic else [STATIC_SOURCE_FILE, SOURCE_FILE]
    for default_path in default_paths:
        if default_path not in candidate_paths:
            candidate_paths.append(default_path)

    for candidate_path in candidate_paths:
        sources = _read_sources_file(candidate_path)
        if sources:
            return sources
    return []


def materialize_sources_file(force_refresh=False, allow_discovery=None):
    if allow_discovery is None:
        allow_discovery = os.getenv("TRANSITLAND_ENABLED", "true").lower() in TRUTHY_VALUES

    if not force_refresh and allow_discovery:
        existing_sources = _read_sources_file(SOURCE_FILE)
        if existing_sources:
            return SOURCE_FILE, existing_sources, "dynamic"

    if allow_discovery:
        try:
            from discover import run_discovery

            run_discovery()
        except Exception as exc:
            logger.warning("Generation dynamique des sources indisponible: %s", exc)

        discovered_sources = _read_sources_file(SOURCE_FILE)
        if discovered_sources:
            return SOURCE_FILE, discovered_sources, "dynamic"

    static_sources = _read_sources_file(STATIC_SOURCE_FILE)
    if not static_sources:
        return SOURCE_FILE, [], None

    try:
        with open(SOURCE_FILE, "w", encoding="utf-8") as handle:
            json.dump(static_sources, handle, indent=2, ensure_ascii=False)
        return SOURCE_FILE, static_sources, "static"
    except Exception as exc:
        logger.warning("Impossible de materialiser %s depuis %s: %s", SOURCE_FILE, STATIC_SOURCE_FILE, exc)
        return STATIC_SOURCE_FILE, static_sources, "static"
