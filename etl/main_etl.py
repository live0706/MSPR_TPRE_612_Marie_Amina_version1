import os
import time

from extract import UniversalFetcher
from load import run_load
from model import train_co2_model
from quality import write_quality_report
from transform import run_transform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(BASE_DIR, "sources.json")
DATA_DIR = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def main():
    print("ETL OBRAIL - DEMARRAGE")
    print("En attente de la base de donnees (15s)...")
    time.sleep(15)

    print("\n--- ETAPE 0 : CHARGEMENT DES SOURCES ---")
    print(f"Configuration source utilisee : {SOURCE_FILE}")

    print("\n--- ETAPE 1 : EXTRACTION ---")
    fetcher = UniversalFetcher(SOURCE_FILE)
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

    print("\n--- ETAPE 3 : CHARGEMENT (LOAD) ---")
    run_load(clean_df)

    print("\nPIPELINE TERMINE AVEC SUCCES")


if __name__ == "__main__":
    main()
