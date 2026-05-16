import logging
import os
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from glob import glob

import pandas as pd
import requests

from gtfs import parse_gtfs_zip
from source_config import SOURCE_FILE, load_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_ARCHIVES_DIR = os.path.join(DATA_RAW_DIR, "archives")

DEFAULT_TIMEOUT = int(os.getenv("EXTRACT_TIMEOUT", "90"))
DEFAULT_MAX_WORKERS = max(2, int(os.getenv("EXTRACT_MAX_WORKERS", "8")))
CHUNK_SIZE = 65536
HEADERS = {"User-Agent": "ObRail/1.0"}

os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_ARCHIVES_DIR, exist_ok=True)


def _sanitize_filename(value, extension):
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._")
    return f"{clean_name or 'source'}.{extension}"


def _source_url(source):
    local_path = source.get("local_path")
    if isinstance(local_path, str) and local_path.strip() and os.path.exists(local_path.strip()):
        return local_path.strip()

    url = source.get("url")
    if isinstance(url, str) and url.strip():
        return url.strip()
    return None


def _fill_metadata_column(df, column_name, default_value):
    if column_name not in df.columns:
        df[column_name] = default_value
        return

    current_values = df[column_name]
    if getattr(current_values, "dtype", None) == "object":
        current_values = current_values.replace(r"^\s*$", pd.NA, regex=True)
    df[column_name] = current_values.where(current_values.notna(), default_value)


class UniversalFetcher:
    def __init__(self, config_path=SOURCE_FILE, max_workers=None, request_timeout=None):
        self.config_path = config_path or SOURCE_FILE
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
        self.request_timeout = request_timeout or DEFAULT_TIMEOUT

    def load_config(self):
        data = load_sources(self.config_path)
        if not data:
            logger.error(f"Aucune configuration source exploitable trouvee via : {self.config_path}")
            return []

        base_sources = [
            source
            for source in data
            if isinstance(source, dict)
            and source.get("enabled") is not False
            and _source_url(source)
            and source.get("type", "gtfs").lower() in ["gtfs", "csv"]
        ]

        expanded_sources = []
        for source in base_sources:
            expanded_sources.append(source)
            expanded_sources.extend(self._discover_local_archives(source))
        return expanded_sources

    def _discover_local_archives(self, source):
        source_id = source.get("id")
        if not source_id:
            return []

        archive_dir = os.path.join(DATA_ARCHIVES_DIR, str(source_id))
        if not os.path.isdir(archive_dir):
            return []

        archive_sources = []
        for pattern in ("*.zip", "*.csv"):
            for archive_path in sorted(glob(os.path.join(archive_dir, pattern))):
                archive_name = os.path.splitext(os.path.basename(archive_path))[0]
                archive_sources.append(
                    {
                        **source,
                        "id": f"{source_id}__{archive_name}",
                        "source_origin_id": source_id,
                        "local_path": archive_path,
                        "url": archive_path,
                        "description": f"{source.get('description')} [{archive_name}]",
                        "type": "csv" if archive_path.lower().endswith(".csv") else "gtfs",
                    }
                )
        if archive_sources:
            logger.info(f"{len(archive_sources)} archive(s) locale(s) detectee(s) pour {source_id}")
        return archive_sources

    def _download_file(self, source):
        url = _source_url(source)
        source_type = source.get("type", "gtfs").lower()
        extension = "zip" if source_type == "gtfs" else "csv"

        if isinstance(url, str) and os.path.exists(url):
            return url

        file_path = os.path.join(DATA_RAW_DIR, _sanitize_filename(source.get("id"), extension))
        temp_path = f"{file_path}.part"

        if os.path.exists(file_path):
            if source_type == "gtfs" and zipfile.is_zipfile(file_path):
                return file_path
            if source_type == "csv":
                return file_path

        last_error = None
        for attempt in range(1, 3):
            try:
                with requests.get(url, headers=HEADERS, timeout=self.request_timeout, stream=True) as response:
                    response.raise_for_status()
                    with open(temp_path, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            handle.write(chunk)

                if source_type == "gtfs" and not zipfile.is_zipfile(temp_path):
                    raise ValueError("Archive GTFS invalide")

                os.replace(temp_path, file_path)
                return file_path
            except Exception as exc:
                last_error = exc
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                logger.warning(f"Echec {source.get('id')} tentative {attempt}: {exc}")

        raise last_error

    def process_one_source(self, source):
        source_id = source.get("id", "unknown")
        source_origin = source.get("source_origin_id") or source_id
        try:
            file_path = self._download_file(source)
            df = parse_gtfs_zip(file_path)

            if df is None or df.empty:
                logger.info(f"SKIP {source_id}: aucune donnee exploitable")
                return None

            working_df = df.copy()
            meta_map = {
                "source_origin": source_origin,
                "source_country": source.get("country"),
                "source_name": source.get("description"),
                "source_provider": source.get("provider"),
                "source_license": source.get("license"),
            }
            for column, value in meta_map.items():
                _fill_metadata_column(working_df, column, value)
            _fill_metadata_column(working_df, "country", source.get("country"))

            logger.info(f"OK {source_id}: {len(working_df)} lignes extraites")
            return working_df
        except Exception as exc:
            logger.error(f"ERREUR {source_id}: {exc}")
            return None

    def run(self):
        sources = self.load_config()
        if not sources:
            logger.warning("Aucune source active a extraire.")
            return []

        logger.info(f"Lancement de l'extraction sur {len(sources)} sources (GTFS/CSV)")

        all_dfs = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_one_source, source): source for source in sources}
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    all_dfs.append(result)

        logger.info(f"Extraction terminee : {len(all_dfs)} sources pretes.")
        return all_dfs


if __name__ == "__main__":
    fetcher = UniversalFetcher()
    fetcher.run()
