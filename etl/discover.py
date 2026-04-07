import requests
import json
import os
import logging

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# C'est ici qu'on va Ã©crire le rÃ©sultat
OUTPUT_FILE = os.path.join(BASE_DIR, 'sources.json')
STATIC_SOURCES_FILE = os.path.join(BASE_DIR, 'sources_static.json')

# Le Hub Open Data Mondial (inclut toute l'Europe)
CATALOG_API = "https://data.opendatasoft.com/api/v2/catalog/datasets"
TRANSITLAND_REST_URL = os.getenv("TRANSITLAND_REST_URL", "https://transit.land/api/v2/rest/feeds")
TRANSITLAND_ENABLED = os.getenv("TRANSITLAND_ENABLED", "true").lower() in ("1", "true", "yes")
TRANSITLAND_PER_PAGE = int(os.getenv("TRANSITLAND_PER_PAGE", "500"))
TRANSITLAND_MAX_FEEDS = int(os.getenv("TRANSITLAND_MAX_FEEDS", "0")) or None
TRANSITLAND_LICENSE = os.getenv("TRANSITLAND_LICENSE", "exclude_no")

# PAN (transport.data.gouv.fr) API
PAN_API_URL = os.getenv("PAN_API_URL", "https://transport.data.gouv.fr/api/datasets")
PAN_MAX_FEEDS = int(os.getenv("PAN_MAX_FEEDS", "50"))
PAN_ONLY_GTFS = os.getenv("PAN_ONLY_GTFS", "true").lower() in ("1", "true", "yes")
PAN_ONLY_RAIL = os.getenv("PAN_ONLY_RAIL", "true").lower() in ("1", "true", "yes")


def _clean_id(value: str) -> str:
    if not value:
        return "unknown"
    return (
        str(value)
        .replace("@", "_")
        .replace(".", "_")
        .replace("-", "_")
        .replace(" ", "_")
        .lower()
    )


def _resource_url(resource: dict):
    for key in ["download_url", "url", "original_url", "file", "href"]:
        val = resource.get(key)
        if isinstance(val, str) and val:
            return val
    return None


def _is_gtfs_resource(resource: dict):
    fmt = str(resource.get("format", "")).lower()
    rtype = str(resource.get("type", "")).lower()
    mime = str(resource.get("mime", "")).lower()
    url = str(_resource_url(resource) or "").lower()
    # Exclude GTFS-RT / realtime endpoints (not zip)
    for val in (fmt, rtype, mime, url):
        if "gtfs-rt" in val or "gtfs_rt" in val or "gtfsrt" in val or "realtime" in val or "real-time" in val:
            return False
    if "gtfs" in fmt or "gtfs" in rtype or "gtfs" in mime:
        return True
    if url.endswith(".zip") and ("gtfs" in url or "gtfs-" in url):
        return True
    return False


def _looks_rail_dataset(dataset: dict):
    if not PAN_ONLY_RAIL:
        return True
    modes = dataset.get("modes") or dataset.get("transport_modes") or dataset.get("transport_mode") or []
    if isinstance(modes, str):
        modes = [modes]
    modes = [str(m).lower() for m in modes]
    if any(m in ["rail", "train", "fer", "railway"] for m in modes):
        return True
    tags = dataset.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tags = [str(t).lower() for t in tags]
    if any(t in ["rail", "railway", "train", "fer", "ferroviaire"] for t in tags):
        return True
    # Si on n'a pas d'info, on garde pour ne pas rater des feeds rail
    return True


def find_pan_gtfs_feeds():
    """
    Récupère les datasets PAN (transport.data.gouv.fr) et extrait les ressources GTFS.
    """
    feeds = []
    seen_urls = set()

    try:
        logger.info("📡 Récupération du catalogue PAN (transport.data.gouv.fr)...")
        response = requests.get(PAN_API_URL, timeout=60)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logger.error(f"❌ Erreur PAN API: {e}")
        return feeds

    datasets = payload
    if isinstance(payload, dict):
        datasets = (
            payload.get("datasets")
            or payload.get("data")
            or payload.get("items")
            or []
        )

    if not isinstance(datasets, list):
        logger.error("❌ Format PAN inattendu (datasets non-list).")
        return feeds

    for dataset in datasets:
        if not isinstance(dataset, dict):
            continue
        if not _looks_rail_dataset(dataset):
            continue

        resources = dataset.get("resources") or dataset.get("dataset_resources") or []
        if not isinstance(resources, list):
            continue

        for res in resources:
            if not isinstance(res, dict):
                continue
            if PAN_ONLY_GTFS and not _is_gtfs_resource(res):
                continue

            url = _resource_url(res)
            if not url or url in seen_urls:
                continue

            ds_id = dataset.get("id") or dataset.get("dataset_id") or dataset.get("slug") or dataset.get("name")
            res_id = res.get("id") or res.get("resource_id") or res.get("name")
            clean_id = _clean_id(f"pan_{ds_id}_{res_id}")
            title = dataset.get("title") or dataset.get("name") or ds_id or "PAN GTFS"
            provider = dataset.get("publisher") or dataset.get("organisation") or dataset.get("organization")
            license_name = dataset.get("license") or dataset.get("licence")

            feeds.append({
                "id": clean_id,
                "type": "gtfs",
                "description": f"PAN GTFS: {title}",
                "url": url,
                "provider": provider,
                "license": license_name,
            })
            seen_urls.add(url)

            if PAN_MAX_FEEDS and len(feeds) >= PAN_MAX_FEEDS:
                return feeds

    return feeds


def find_european_datasets(keyword, limit=2):
    """
    Interroge le Hub OpenDataSoft pour trouver des datasets ferroviaires (API JSON).
    """
    params = {
        'search': keyword,
        'limit': limit,
        # On peut filtrer pour exclure la France si on veut forcer l'aspect "Europe"
        # 'refine.country': 'DE' (Allemagne), etc.
    }
    
    discovered_sources = []
    
    try:
        logger.info(f"ðŸŒ Recherche catalogue Europe pour : '{keyword}'...")
        response = requests.get(CATALOG_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get('datasets', []):
            ds = item.get('dataset', {})
            ds_id = ds.get('dataset_id')
            title = ds.get('metas', {}).get('default', {}).get('title', ds_id)
            
            # Construction de l'URL API V1 (Format standard JSON)
            # Cette URL renvoie toujours du JSON propre, peu importe le format d'origine
            api_url = f"https://data.opendatasoft.com/api/records/1.0/search/?dataset={ds_id}&rows=50"
            
            # Nettoyage de l'ID pour qu'il soit un nom de fichier valide
            clean_id = ds_id.replace('@', '_').replace('.', '_').replace('-', '_')
            
            discovered_sources.append({
                "id": clean_id,
                "type": "json",  # On force le type JSON car on utilise l'API
                "description": f"Auto-discovered: {title}",
                "url": api_url
            })
            
    except Exception as e:
        logger.error(f"âŒ Erreur dÃ©couverte : {e}")
        
    return discovered_sources


def load_static_sources():
    if not os.path.exists(STATIC_SOURCES_FILE):
        return []
    try:
        with open(STATIC_SOURCES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        valid = []
        for src in data:
            if not isinstance(src, dict):
                continue
            if src.get("enabled", True) and src.get("url"):
                valid.append(src)
        return valid
    except Exception as e:
        logger.error(f"âŒ Erreur lecture sources_static.json : {e}")
        return []


def _extract_transitland_url(feed):
    urls = feed.get("urls") or {}
    if isinstance(urls, dict):
        for key in ["static_current", "static_historic", "static_planned"]:
            val = urls.get(key)
            if isinstance(val, list) and val:
                return val[0]
            if isinstance(val, str) and val:
                return val
    if isinstance(feed.get("url"), str):
        return feed.get("url")
    return None


def find_transitland_gtfs_feeds():
    if not TRANSITLAND_ENABLED:
        return []

    feeds = []
    seen_urls = set()
    offset = 0

    while True:
        params = {
            "spec": "gtfs",
            "license_redistribution_allowed": TRANSITLAND_LICENSE,
            "per_page": TRANSITLAND_PER_PAGE,
            "offset": offset,
        }
        try:
            response = requests.get(TRANSITLAND_REST_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            logger.error(f"âŒ Erreur Transitland : {e}")
            break

        items = (
            payload.get("feeds")
            or payload.get("results")
            or payload.get("data")
            or payload.get("items")
            or []
        )
        if not items:
            break

        for feed in items:
            url = _extract_transitland_url(feed)
            if not url or url in seen_urls:
                continue
            feed_id = feed.get("onestop_id") or feed.get("id") or f"transitland_{len(feeds) + 1}"
            feeds.append(
                {
                    "id": f"transitland_{feed_id}",
                    "type": "gtfs",
                    "description": "Transitland GTFS feed",
                    "url": url,
                }
            )
            seen_urls.add(url)

            if TRANSITLAND_MAX_FEEDS and len(feeds) >= TRANSITLAND_MAX_FEEDS:
                return feeds

        if len(items) < TRANSITLAND_PER_PAGE:
            break
        offset += TRANSITLAND_PER_PAGE

    return feeds


def update_sources_file():
    """
    CrÃ©e le fichier sources.json en combinant :
    1. Des sources STATIQUES (WikipÃ©dia, pour la fiabilitÃ©)
    2. Des sources DYNAMIQUES (API, pour la note technique)
    3. Des sources STATIQUES additionnelles (fichier local)
    """
    logger.info("ðŸ¤– GÃ©nÃ©ration du fichier de configuration sources.json...")
    
    final_list = []
    
    # --- A. SOURCES STATIQUES (Toujours lÃ ) ---
    final_list.append({
        "id": "wiki_named_trains",
        "type": "html",
        "description": "Wikipedia Named Passenger Trains",
        "url": "https://en.wikipedia.org/wiki/List_of_named_passenger_trains_of_Europe"
    })
    
    # --- B. SOURCES DYNAMIQUES (Recherche Live - Opendatasoft) ---
    # 1. On cherche des gares en Europe
    stations = find_european_datasets("european train stations", limit=1)
    final_list.extend(stations)
    
    # 2. On cherche des donnÃ©es d'Ã©missions ou de trafic
    emissions = find_european_datasets("railway emissions", limit=1)
    final_list.extend(emissions)

    # --- C. SOURCES GTFS (PAN) ---
    pan_feeds = find_pan_gtfs_feeds()
    final_list.extend(pan_feeds)

    # --- D. SOURCES GTFS (Transitland) ---
    transitland_feeds = find_transitland_gtfs_feeds()
    final_list.extend(transitland_feeds)

    # --- E. SOURCES STATIQUES SUPPLEMENTAIRES ---
    static_sources = load_static_sources()
    final_list.extend(static_sources)
    
    # --- E. ECRITURE SUR DISQUE ---
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)
        logger.info(f"ðŸ’¾ SuccÃ¨s ! {len(final_list)} sources enregistrÃ©es dans sources.json")
        
        # Petit affichage pour le debug
        for src in final_list:
            logger.info(f"   - [Source] {src['id']}")
            
    except Exception as e:
        logger.error(f"âŒ Impossible d'Ã©crire le fichier JSON : {e}")


if __name__ == "__main__":
    update_sources_file()
