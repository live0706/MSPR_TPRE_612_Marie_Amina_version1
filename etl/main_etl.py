import time
# Import des modules que nous venons de créer
from discover import update_sources_file
from extract import UniversalFetcher
from transform import run_transform
from load import run_load
from quality import write_quality_report
from model import train_co2_model
import os
# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(BASE_DIR, 'sources.json')
DATA_DIR = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

def main():
    print("ETL OBRAIL - DEMARRAGE")
    time.sleep(3)

    # --- ETAPE 0 : MISE A JOUR AUTOMATIQUE DES SOURCES ---
    print("\n--- ETAPE 0 : DECOUVERTE DU CATALOGUE EUROPEEN ---")
    # Cette fonction va créer/écraser le fichier sources.json
    update_sources_file()

    # --- ETAPE 1 : EXTRACTION ---
    print("\n--- ETAPE 1 : EXTRACTION ---")
    # L'extracteur lit le fichier sources.json tout neuf
    fetcher = UniversalFetcher(SOURCE_FILE)
    raw_dfs_list = fetcher.run()
    # 2. TRANSFORMATION
    print("\n--- ETAPE 2 : TRANSFORMATION ---")
    clean_df = run_transform(raw_dfs_list)
    
    # Affichage de controle
    if not clean_df.empty:
        print("\napercu des donnees propres :")
        try:
            preview = clean_df[['operator_name', 'origin_city', 'service_type', 'co2_emissions']].head().to_string()
            # Avoid console encoding issues on Windows terminals
            print(preview.encode("ascii", "ignore").decode("ascii"))
        except Exception:
            pass

        # Quality and model reports (for auditability and performance tracking)
        write_quality_report(clean_df, PROCESSED_DIR)
        train_co2_model(clean_df, PROCESSED_DIR)

    # 3. CHARGEMENT
    print("\n--- ETAPE 3 : CHARGEMENT (LOAD) ---")
    run_load(clean_df, table_name='trips')
    
    print("\nPIPELINE TERMINE AVEC SUCCES")

if __name__ == "__main__":
    main()
