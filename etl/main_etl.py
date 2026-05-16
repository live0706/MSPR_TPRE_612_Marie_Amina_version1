import os
import time

from extract import UniversalFetcher
from load import run_load
from model import train_co2_model
from quality import write_quality_report
from source_config import SOURCE_FILE, materialize_sources_file
from transform import run_transform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def main():
    print("ETL OBRAIL - DEMARRAGE")
    print("En attente de la base de donnees (15s)...")
    time.sleep(15)

    print("\n--- ETAPE 0 : CHARGEMENT DES SOURCES ---")
    refresh_sources = os.getenv("REFRESH_SOURCES", "false").lower() in ("1", "true", "yes")
    source_file, configured_sources, source_mode = materialize_sources_file(force_refresh=refresh_sources)
    print(f"Configuration source utilisee : {source_file}")
    print(f"Mode de resolution des sources : {source_mode or 'aucune source'}")
    print(f"Sources disponibles pour l'extraction : {len(configured_sources)}")

    print("\n--- ETAPE 1 : EXTRACTION ---")
    fetcher = UniversalFetcher(source_file or SOURCE_FILE)
    raw_dfs_list = fetcher.run()

    print("\n--- ETAPE 2 : TRANSFORMATION ---")
    clean_df = run_transform(raw_dfs_list)

    if not clean_df.empty:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        processed_csv_path = os.path.join(PROCESSED_DIR, "trips_cleaned_final.csv")
        clean_df.to_csv(processed_csv_path, index=False)
        print(f"Fichier transforme sauvegarde : {processed_csv_path}")

        print("\nApercu des donnees propres :")
        try:
            preview = clean_df[["operator_name", "origin_city", "service_type", "co2_emissions"]].head().to_string()
            print(preview.encode("ascii", "ignore").decode("ascii"))
        except Exception:
            pass

        write_quality_report(clean_df, PROCESSED_DIR)
        train_co2_model(clean_df, PROCESSED_DIR)
    else:
        print("Aucune donnee transformee exploitable n'a ete produite.")

    print("\n--- ETAPE 3 : CHARGEMENT (LOAD) ---")
    run_load(clean_df)

    print("\nPIPELINE TERMINE AVEC SUCCES")


if __name__ == "__main__":
    main()
