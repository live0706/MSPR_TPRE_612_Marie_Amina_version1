import pandas as pd
import numpy as np
import logging
import uuid
import re

# --- CONFIGURATION LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Liste officielle des colonnes attendues en base de données
OFFICIAL_COLUMNS = [
    'trip_id', 'operator_name', 'origin_city', 'destination_city',
    'departure_time', 'arrival_time', 'service_type', 
    'train_type', 'co2_emissions', 'distance_km', 'source_origin'
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
        'departure_date_time': 'departure_time', 'departure': 'departure_time',
        'arrival_date_time': 'arrival_time', 'arrival': 'arrival_time',
        'commercial_mode': 'train_type',
        'emission_co2_kg': 'co2_emissions', 'distance': 'distance_km',

        # Wikipédia
        'train_name': 'agency_name',
        'endpoints': 'origin_city',
        'route': 'origin_city',
        'journey': 'origin_city'
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
    df['departure_time'] = pd.to_datetime(df['departure_time'], errors='coerce')
    df['arrival_time'] = pd.to_datetime(df['arrival_time'], errors='coerce')

    def clean_dist(val):
        if pd.isna(val): return None
        try:
            found = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
            if found: return float(found[0])
        except: pass
        return None
    df['distance_km'] = df['distance_km'].apply(clean_dist)

    # --- C. Classification Jour / Nuit ---
    def classify_service(row):
        if pd.notna(row['service_type']) and str(row['service_type']).lower() in ['nuit', 'night']:
            return 'Nuit'
        if pd.notna(row['departure_time']):
            hour = row['departure_time'].hour
            if hour >= 22 or hour <= 6:
                return 'Nuit'
        return 'Jour'

    df['service_type'] = df.apply(classify_service, axis=1)

    # --- D. Calcul CO2 ---
    def calculate_co2(row):
        if pd.notna(row['co2_emissions']):
            try: return float(row['co2_emissions'])
            except: pass
        if pd.notna(row['distance_km']):
            return round(row['distance_km'] * 0.005, 3)
        return 0.0

    df['co2_emissions'] = df.apply(calculate_co2, axis=1)

    # --- E. ID Unique ---
    def generate_id(row):
        if pd.notna(row['trip_id']): return str(row['trip_id'])
        return f"AUTO-{uuid.uuid4().hex[:8]}"
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