import pandas as pd
import requests
import os
import json
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO  # Nécessaire pour corriger le FutureWarning

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, '../data/raw')
SOURCE_FILE = os.path.join(BASE_DIR, 'sources.json')

os.makedirs(DATA_RAW_DIR, exist_ok=True)

class UniversalFetcher:
    def __init__(self, config_path):
        self.config_path = config_path

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.error(f"❌ Config file not found: {self.config_path}")
            return []
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def download_resource(self, url, source_id, file_type):
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{source_id}_{timestamp}.{file_type}"
        file_path = os.path.join(DATA_RAW_DIR, filename)
        
        # Si le fichier existe déjà, on ne le re-télécharge pas (gain de temps pour les tests)
        if os.path.exists(file_path):
            logger.info(f"📂 File already exists, skipping download: {filename}")
            return file_path

        try:
            logger.info(f"⬇️ Downloading: {source_id} from {url}...")
            # On ajoute un User-Agent pour ne pas être bloqué par Wikipédia
            headers = {'User-Agent': 'Mozilla/5.0 (ObRail Project)'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Saved to: {filename}")
            return file_path
        except Exception as e:
            logger.error(f"⚠️ Failed to download {source_id}: {e}")
            return None

    def parse_content(self, file_path, file_type, separator=','):
        if not file_path: return pd.DataFrame()

        try:
            # 1. Handle CSV (Fix DtypeWarning)
            if file_type == 'csv':
                return pd.read_csv(file_path, sep=separator, on_bad_lines='skip', low_memory=False)

            # 2. Handle JSON
            elif file_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    return pd.DataFrame(data)
                
                for key in ['records', 'journeys', 'data', 'fields', 'results']:
                    if key in data and isinstance(data[key], list):
                        return pd.json_normalize(data[key])
                return pd.json_normalize(data)

            # 3. Handle HTML (Mise à jour pour Wikipédia "Named Trains")
            elif file_type == 'html':
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                html_buffer = StringIO(html_content)
                # On cherche un tableau contenant "Endpoints" ou "Train"
                tables = pd.read_html(html_buffer, match='Endpoints')
                
                if tables:
                    df = tables[0]
                    # Nettoyage des noms de colonnes (minuscules, sans espaces)
                    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                    
                    # Mapping pour aider transform.py
                    # La colonne "endpoints" contient "Paris – Nice"
                    # On la renomme en 'origin_city' pour qu'elle soit capturée,
                    # le split se fera dans transform.py
                    rename_map = {}
                    for col in df.columns:
                        if 'train' in col: rename_map[col] = 'agency_name'
                        if 'endpoints' in col: rename_map[col] = 'origin_city' # Astuce temporaire
                        if 'operator' in col: rename_map[col] = 'operator_name'
                    
                    df = df.rename(columns=rename_map)
                    df['service_type'] = 'Nuit' # Hypothèse par défaut pour l'exercice
                    return df
                else:
                    logger.warning(f"No tables found in {file_path}")
                    return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")
            return pd.DataFrame()

    def run(self):
        sources = self.load_config()
        extracted_data = []

        logger.info(f"🚀 Starting Extraction for {len(sources)} sources...")

        for source in sources:
            src_url = source.get('url')
            src_type = source.get('type')
            src_id = source.get('id', 'unknown')
            src_sep = source.get('separator', ',') 

            local_path = self.download_resource(src_url, src_id, src_type)
            df = self.parse_content(local_path, src_type, src_sep)
            
            if not df.empty:
                df['source_origin'] = src_id
                extracted_data.append(df)
                logger.info(f"📊 {src_id}: {len(df)} rows extracted.")
            else:
                logger.warning(f"⚠️ {src_id}: Empty or unreadable.")

        return extracted_data

if __name__ == "__main__":
    fetcher = UniversalFetcher(SOURCE_FILE)
    dfs = fetcher.run()