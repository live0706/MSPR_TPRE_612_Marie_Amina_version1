import time
import os
# Import des modules locaux
from extract import UniversalFetcher
from transform import run_transform
from load import run_load
from quality import write_quality_report
from model import train_co2_model

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(BASE_DIR, 'sources.json')
DATA_DIR = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

def main():
    print("ETL OBRAIL - DEMARRAGE")
    # On attend 15 secondes que la DB soit prête au premier lancement
    print("En attente de la base de données (15s)...")
    time.sleep(15)

    # --- ETAPE 0 : CHARGEMENT DES SOURCES ---
    print("\n--- ETAPE 0 : CHARGEMENT DES SOURCES ---")
    print(f"Configuration source utilisee : {SOURCE_FILE}")

    # --- ETAPE 1 : EXTRACTION ---
    print("\n--- ETAPE 1 : EXTRACTION ---")
    fetcher = UniversalFetcher(SOURCE_FILE)
    raw_dfs_list = fetcher.run()
    
    # --- ETAPE 2 : TRANSFORMATION ---
    print("\n--- ETAPE 2 : TRANSFORMATION ---")
    clean_df = run_transform(raw_dfs_list)
    
    if not clean_df.empty:
        print("\nAperçu des données propres :")
        try:
            preview = clean_df[['operator_name', 'origin_city', 'service_type', 'co2_emissions']].head().to_string()
            print(preview.encode("ascii", "ignore").decode("ascii"))
        except Exception:
            pass

        write_quality_report(clean_df, PROCESSED_DIR)
        train_co2_model(clean_df, PROCESSED_DIR)

    # --- ETAPE 3 : CHARGEMENT (LOAD) ---
    print("\n--- ETAPE 3 : CHARGEMENT (LOAD) ---")
    run_load(clean_df)
    
    print("\nPIPELINE TERMINE AVEC SUCCES")

if __name__ == "__main__":
    main()
