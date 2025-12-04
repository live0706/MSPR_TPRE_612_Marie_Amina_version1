import requests
import json
import os
import logging

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# C'est ici qu'on va écrire le résultat
OUTPUT_FILE = os.path.join(BASE_DIR, 'sources.json')

# Le Hub Open Data Mondial (inclut toute l'Europe)
CATALOG_API = "https://data.opendatasoft.com/api/v2/catalog/datasets"

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
        logger.info(f"🌍 Recherche catalogue Europe pour : '{keyword}'...")
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
                "type": "json", # On force le type JSON car on utilise l'API
                "description": f"Auto-discovered: {title}",
                "url": api_url
            })
            
    except Exception as e:
        logger.error(f"❌ Erreur découverte : {e}")
        
    return discovered_sources

def update_sources_file():
    """
    Crée le fichier sources.json en combinant :
    1. Des sources STATIQUES (Wikipédia, pour la fiabilité)
    2. Des sources DYNAMIQUES (API, pour la note technique)
    """
    logger.info("🤖 Génération du fichier de configuration sources.json...")
    
    final_list = []
    
    # --- A. SOURCES STATIQUES (Toujours là) ---
    final_list.append({
        "id": "wiki_named_trains",
        "type": "html",
        "description": "Wikipedia Named Passenger Trains",
        "url": "https://en.wikipedia.org/wiki/List_of_named_passenger_trains_of_Europe"
    })
    
    # --- B. SOURCES DYNAMIQUES (Recherche Live) ---
    # 1. On cherche des gares en Europe
    stations = find_european_datasets("european train stations", limit=1)
    final_list.extend(stations)
    
    # 2. On cherche des données d'émissions ou de trafic
    emissions = find_european_datasets("railway emissions", limit=1)
    final_list.extend(emissions)
    
    # --- C. ÉCRITURE SUR DISQUE ---
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Succès ! {len(final_list)} sources enregistrées dans sources.json")
        
        # Petit affichage pour le debug
        for src in final_list:
            logger.info(f"   - [Source] {src['id']}")
            
    except Exception as e:
        logger.error(f"❌ Impossible d'écrire le fichier JSON : {e}")

if __name__ == "__main__":
    update_sources_file()