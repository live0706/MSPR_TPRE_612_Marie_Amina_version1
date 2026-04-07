import pandas as pd
import numpy as np
import logging
import uuid
import re
from datetime import datetime

# --- CONFIGURATION LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Liste officielle des colonnes attendues en base de données
OFFICIAL_COLUMNS = [
    'trip_id', 'operator_name', 'origin_city', 'destination_city',
    'departure_time', 'arrival_time', 'service_type',
    'train_type', 'co2_emissions', 'distance_km', 'source_origin',
    'origin_lat', 'origin_lon', 'destination_lat', 'destination_lon'
]

def normalize_columns(df):
    """
    Standardise les noms de colonnes et supprime les doublons immédiats.
    """
    # Mapping complet (API, CSV, Wiki)
    column_mapping = {
        # API SNCF
        'fields.recordid': 'trip_id',
        'fields.transporteur': 'operator_name',
        'fields.origine': 'origin_city',
        'fields.destination': 'destination_city',
        'fields.mode_transport': 'train_type',
        'fields.emission_co2_kg': 'co2_emissions',
        'fields.distance_km': 'distance_km',
        
        # CSV & Standards
        'recordid': 'trip_id', 'id': 'trip_id',
        'agency_name': 'operator_name', 'network': 'operator_name', 'operator': 'operator_name',
        'origine': 'origin_city', 'from': 'origin_city', 'origin': 'origin_city',
        'destination': 'destination_city', 'to': 'destination_city',
        'departure_date_time': 'departure_time', 'departure': 'departure_time', 'departure_time': 'departure_time',
        'heure_depart': 'departure_time', 'heure_departure': 'departure_time',
        'arrival_date_time': 'arrival_time', 'arrival': 'arrival_time', 'arrival_time': 'arrival_time',
        'heure_arrivee': 'arrival_time', 'heure_arrival': 'arrival_time',
        'commercial_mode': 'train_type',
        'emission_co2_kg': 'co2_emissions', 'emissions_co2e': 'co2_emissions',
        'distance': 'distance_km',

        # Back-on-Track (Open Night Train DB)
        'trip_origin': 'origin_city',
        'trip_headsign': 'destination_city',
        'origin_departure_time': 'departure_time',
        'destination_arrival_time': 'arrival_time',
        'agency_id': 'operator_name',

        # Wikipédia
        'train_name': 'agency_name',
        'endpoints': 'origin_city',
        'route': 'origin_city',
        'journey': 'origin_city',
        # Ajoutez les noms exacts que vous voyez dans vos fichiers bruts
        'ville_depart': 'origin_city',    # Exemple
        'depart_gare': 'origin_city',     # Exemple
        'departure_station': 'origin_city',
        
        'ville_arrivee': 'destination_city',
        'arrivee_gare': 'destination_city',
        'arrival_station': 'destination_city',
        
        'carrier': 'operator_name',       # Souvent utilisé dans les données européennes
        'transporteur': 'operator_name',

        # Coordonnées (GTFS ou autres)
        'origin_lat': 'origin_lat',
        'origin_lon': 'origin_lon',
        'destination_lat': 'destination_lat',
        'destination_lon': 'destination_lon',
        'stop_lat': 'origin_lat',
        'stop_lon': 'origin_lon',
    }
    
    # 1. Renommage
    df = df.rename(columns=column_mapping)
    
    # 2. SUPPRESSION DES DOUBLONS DE COLONNES (Le correctif CRITIQUE)
    # Si 'origin' et 'fields.origine' deviennent tous les deux 'origin_city', on garde un seul
    df = df.loc[:, ~df.columns.duplicated()]
    
    # 3. Création des colonnes manquantes (initialisées à None)
    for col in OFFICIAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
            
    return df

def clean_and_enrich(df):
    """
    Applique la logique métier.
    """
    # Normalise common empty markers
    df = df.replace({"#N/A": None, "N/A": None, "": None, "None": None, "nan": None})

    # --- A. SPECIAL WIKIPEDIA : Découpage "Origin – Destination" ---
    def split_endpoints(row):
        origin = str(row['origin_city'])
        dest = row['destination_city']
        
        if pd.isna(dest) or dest == 'None':
            # Nettoyage des tirets
            origin_clean = origin.replace('–', '-').replace('—', '-').replace(' to ', '-')
            if '-' in origin_clean:
                try:
                    parts = origin_clean.split('-')
                    return pd.Series([parts[0].strip(), parts[-1].strip()])
                except:
                    pass
        return pd.Series([row['origin_city'], row['destination_city']])

    df[['origin_city', 'destination_city']] = df.apply(split_endpoints, axis=1)

    # --- B. Nettoyage Dates & Distances ---
    base_date = datetime(2000, 1, 1)

    def parse_datetime(value):
        if pd.isna(value):
            return pd.NaT
        if isinstance(value, str):
            # Handle time-only values like HH:MM or HH:MM:SS
            if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", value.strip()):
                parts = value.strip().split(":")
                h = int(parts[0]) % 24
                m = int(parts[1])
                s = int(parts[2]) if len(parts) == 3 else 0
                return base_date.replace(hour=h, minute=m, second=s)
        return pd.to_datetime(value, errors='coerce')

    df['departure_time'] = df['departure_time'].apply(parse_datetime)
    df['arrival_time'] = df['arrival_time'].apply(parse_datetime)

    def clean_dist(val):
        if pd.isna(val): return None
        try:
            found = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
            if found: return float(found[0])
        except: pass
        return None
    df['distance_km'] = df['distance_km'].apply(clean_dist)

    # --- C. Imputation des heures manquantes ---

    def estimate_duration_hours(distance_km, service_type, train_type):
        speed = 120.0
        stype = str(service_type).lower() if pd.notna(service_type) else ""
        ttype = str(train_type).lower() if pd.notna(train_type) else ""
        if stype in ["nuit", "night"]:
            speed = 100.0
        if "tgv" in ttype or "high" in ttype:
            speed = 200.0
        if distance_km and distance_km > 0:
            return distance_km / speed
        return 2.0 if stype == "jour" else 6.0

    def default_departure_time(service_type):
        stype = str(service_type).lower() if pd.notna(service_type) else "jour"
        if stype in ["nuit", "night"]:
            return base_date.replace(hour=23, minute=0, second=0)
        return base_date.replace(hour=9, minute=0, second=0)

    def fill_times(row):
        dep = row['departure_time']
        arr = row['arrival_time']
        stype = row['service_type'] if pd.notna(row['service_type']) else "Jour"
        duration_hours = estimate_duration_hours(row['distance_km'], stype, row['train_type'])
        duration = pd.Timedelta(hours=duration_hours)

        if pd.isna(dep) and pd.isna(arr):
            dep = default_departure_time(stype)
            arr = dep + duration
        elif pd.isna(dep) and pd.notna(arr):
            dep = arr - duration
        elif pd.notna(dep) and pd.isna(arr):
            arr = dep + duration

        return pd.Series([dep, arr])

    df[['departure_time', 'arrival_time']] = df.apply(fill_times, axis=1)

    # --- D. Classification Jour / Nuit ---
    def classify_service(row):
        if pd.notna(row['service_type']) and str(row['service_type']).lower() in ['nuit', 'night', 'jour', 'day']:
            return 'Nuit' if str(row['service_type']).lower() in ['nuit', 'night'] else 'Jour'
        if pd.notna(row['departure_time']):
            hour = row['departure_time'].hour
            if hour >= 22 or hour <= 6:
                return 'Nuit'
        return 'Jour'

    df['service_type'] = df.apply(classify_service, axis=1)

    # --- E. Default train type for rail-only datasets ---
    if "train_type" in df.columns:
        df["train_type"] = df["train_type"].fillna("Rail")

    # --- E2. Default operator name ---
    if "operator_name" in df.columns:
        df["operator_name"] = df["operator_name"].fillna("Unknown")

    # --- F. Calcul CO2 ---
    def calculate_co2(row):
        if pd.notna(row['co2_emissions']):
            try: return float(row['co2_emissions'])
            except: pass
        if pd.notna(row['distance_km']):
            return round(row['distance_km'] * 0.005, 3)
        return 0.0

    df['co2_emissions'] = df.apply(calculate_co2, axis=1)

    # On garde les lignes sans distance_km pour ne pas perdre du volume (CO2 sera estimé à 0)

    # --- F. ID Unique ---
    def generate_id(row):
        src = row.get('source_origin') or "unknown"
        if pd.notna(row['trip_id']):
            return f"{src}:{row['trip_id']}"
        return f"{src}:AUTO-{uuid.uuid4().hex[:8]}"
    df['trip_id'] = df.apply(generate_id, axis=1)

    # Nettoyage final des lignes vides
    df = df.dropna(subset=['origin_city', 'destination_city'])
    
    return df

def run_transform(list_of_dfs):
    """
    Fonction principale.
    """
    logger.info("🧹 Démarrage de la transformation...")
    
    if not list_of_dfs:
        logger.warning("⚠️ Aucune donnée brute en entrée.")
        return pd.DataFrame()

    cleaned_dfs = []
    
    for i, df in enumerate(list_of_dfs):
        if df.empty: continue
        
        try:
            # 1. Normalisation + Suppression doublons colonnes
            df = normalize_columns(df)
            
            # 2. Enrichissement
            df = clean_and_enrich(df)
            
            # 3. FILTRE FINAL STRICT (Sécurité absolue pour le concat)
            # On ne garde QUE les colonnes officielles, dans le bon ordre.
            # Cela garantit que tous les DF ont exactement la même structure.
            df_final = df[OFFICIAL_COLUMNS].copy()
            
            if not df_final.empty:
                cleaned_dfs.append(df_final)
                logger.info(f"   -> Batch {i+1}: {len(df_final)} lignes propres.")
                
        except Exception as e:
            logger.error(f"❌ Erreur transformation batch {i+1}: {e}")

    if not cleaned_dfs:
        logger.warning("⚠️ Tous les dataframes sont vides après transformation.")
        return pd.DataFrame()

    # Fusion finale (Maintenant sécurisée car tous les DFs ont les mêmes colonnes)
    master_df = pd.concat(cleaned_dfs, ignore_index=True)
    
    # Dédoublonnage sur l'ID
    master_df = master_df.drop_duplicates(subset=['trip_id'])
    
    logger.info(f"✅ Transformation terminée : {len(master_df)} lignes prêtes pour la BDD.")
    return master_df
