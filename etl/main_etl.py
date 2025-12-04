import time
# Import des modules que nous venons de créer
from discover import update_sources_file
from extract import UniversalFetcher
from transform import run_transform
from load import run_load
import os
from extract import UniversalFetcher # La classe s'appelle maintenant UniversalFetcher
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(BASE_DIR, 'sources.json')

def main():
    print("🚀 --- PIPELINE ETL OBRAIL DÉMARRÉ ---")
    time.sleep(3)

    # --- ÉTAPE 0 : MISE À JOUR AUTOMATIQUE DES SOURCES ---
    print("\n--- ÉTAPE 0 : DÉCOUVERTE DU CATALOGUE EUROPÉEN ---")
    # Cette fonction va créer/écraser le fichier sources.json
    update_sources_file()

    # --- ÉTAPE 1 : EXTRACTION ---
    print("\n--- ÉTAPE 1 : EXTRACTION ---")
    # L'extracteur lit le fichier sources.json tout neuf
    fetcher = UniversalFetcher(SOURCE_FILE)
    raw_dfs_list = fetcher.run()
    # 2. TRANSFORMATION
    print("\n--- ÉTAPE 2 : TRANSFORMATION ---")
    clean_df = run_transform(raw_dfs_list)
    
    # Affichage de contrôle
    if not clean_df.empty:
        print("\naperçu des données propres :")
        print(clean_df[['operator_name', 'origin_city', 'service_type', 'co2_emissions']].head())

    # 3. CHARGEMENT
    print("\n--- ÉTAPE 3 : CHARGEMENT (LOAD) ---")
    run_load(clean_df, table_name='trips')
    
    print("\n🏁 --- PIPELINE TERMINÉ AVEC SUCCÈS ---")

if __name__ == "__main__":
    main()