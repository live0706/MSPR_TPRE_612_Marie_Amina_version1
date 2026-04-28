import json
import logging
import os
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from gtfs import parse_gtfs_zip

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
SOURCE_FILE = os.path.join(BASE_DIR, "sources.json")

DEFAULT_TIMEOUT = int(os.getenv("EXTRACT_TIMEOUT", "90"))
DEFAULT_MAX_WORKERS = max(2, int(os.getenv("EXTRACT_MAX_WORKERS", "8")))
CHUNK_SIZE = 65536
HEADERS = {"User-Agent": "ObRail/1.0"}

os.makedirs(DATA_RAW_DIR, exist_ok=True)


def _sanitize_filename(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._") or "source"


def _source_url(source):
    url = source.get("url")
    if isinstance(url, str) and url.strip():
        return url.strip()
    return None


class UniversalFetcher:
    def __init__(self, config_path=SOURCE_FILE, max_workers=None, request_timeout=None):
        self.config_path = config_path or SOURCE_FILE
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
        self.request_timeout = request_timeout or DEFAULT_TIMEOUT

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.error(f"Configuration introuvable : {self.config_path}")
            return []

        try:
            with open(self.config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.error(f"Lecture config impossible : {exc}")
            return []

        if not isinstance(data, list):
            return []

        return [
            source
            for source in data
            if isinstance(source, dict)
            and source.get("enabled") is not False
            and _source_url(source)
            and source.get("type", "gtfs") == "gtfs"
        ]

    def _target_path(self, source):
        source_id = _sanitize_filename(source.get("id") or "unknown_source")
        return os.path.join(DATA_RAW_DIR, f"{source_id}.zip")

    def _download_gtfs(self, source):
        file_path = self._target_path(source)
        temp_path = f"{file_path}.part"

        if os.path.exists(file_path):
            if zipfile.is_zipfile(file_path):
                return file_path
            logger.warning(f"Archive invalide detectee, retelechargement : {os.path.basename(file_path)}")
            try:
                os.remove(file_path)
            except OSError:
                pass

        url = _source_url(source)
        if not url:
            raise ValueError("URL de source manquante")

        last_error = None
        for attempt in range(1, 3):
            try:
                with requests.get(url, headers=HEADERS, timeout=self.request_timeout, stream=True) as response:
                    response.raise_for_status()
                    with open(temp_path, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            if chunk:
                                handle.write(chunk)

                if not zipfile.is_zipfile(temp_path):
                    raise ValueError("Le fichier telecharge n'est pas une archive GTFS valide")

                os.replace(temp_path, file_path)
                return file_path
            except Exception as exc:
                last_error = exc
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                logger.warning(
                    "%s tentative %s/2 en echec : %s",
                    source.get("id", "unknown_source"),
                    attempt,
                    exc,
                )

        raise last_error or RuntimeError("Echec du telechargement GTFS")

    def process_one_source(self, source):
        source_id = source.get("id", "unknown_source")
        try:
            file_path = self._download_gtfs(source)
            df = parse_gtfs_zip(file_path)
            if df is None or df.empty:
                logger.info(f"INFO {source_id}: aucun trajet rail exploitable")
                return None

            working_df = df.copy()
            working_df["source_origin"] = source_id
            working_df["country"] = source.get("country")
            working_df["source_name"] = source.get("description")
            working_df["source_provider"] = source.get("provider")
            working_df["source_license"] = source.get("license")

            working_df.attrs["source_id"] = source_id
            working_df.attrs["country"] = source.get("country")
            working_df.attrs["source_name"] = source.get("description")
            working_df.attrs["source_provider"] = source.get("provider")
            working_df.attrs["source_license"] = source.get("license")

            logger.info(f"OK {source_id}: {len(working_df)} trajets rail extraits")
            return working_df
        except Exception as exc:
            logger.error(f"ERREUR {source_id}: {exc}")
            return None

    def run(self):
        sources = self.load_config()
        if not sources:
            logger.warning("Aucune source GTFS active a extraire")
            return []

        logger.info(f"Extraction parallele lancee sur {len(sources)} sources GTFS")

        all_dfs = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_one_source, source): source for source in sources}
            for future in as_completed(futures):
                result = future.result()
                if result is not None and not result.empty:
                    all_dfs.append(result)

        logger.info(f"Extraction terminee : {len(all_dfs)} sources GTFS exploitables")
        return all_dfs


class MassiveFetcher(UniversalFetcher):
    pass


if __name__ == "__main__":
    fetcher = UniversalFetcher()
    fetcher.run()
