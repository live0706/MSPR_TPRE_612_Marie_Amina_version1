import pandas as pd
from sqlalchemy import create_engine
import os
import logging

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def get_db_engine():
    """Establishes connection to PostgreSQL using Environment Variables."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL is missing from environment variables!")
        return None
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.error(f"❌ DB Connection Error: {e}")
        return None

def run_load(data, table_name='trips'):
    """
    Loads data into PostgreSQL 'trips' table.
    Accepts either a DataFrame or a CSV file path.
    """
    logger.info(f"💾 Starting Load process into table '{table_name}'...")
    
    engine = get_db_engine()
    if not engine: return

    # 1. Determine Input Type (DataFrame or File Path)
    df_to_load = pd.DataFrame()
    
    if isinstance(data, str) and os.path.exists(data):
        logger.info(f"📂 Reading from processed file: {data}")
        # Parse dates correctly when reading from CSV
        df_to_load = pd.read_csv(data, parse_dates=['departure_time', 'arrival_time'])
    
    elif isinstance(data, pd.DataFrame):
        df_to_load = data
    
    else:
        logger.warning("⚠️ Invalid data input provided to load function.")
        return

    if df_to_load.empty:
        logger.warning("⚠️ No data to insert.")
        return

    # 2. Insert into Database
    try:
        # We use 'append' to respect the schema created by init.sql (constraints, types)
        # We use 'multi' method for faster bulk inserts
        df_to_load.to_sql(
            table_name,
            engine,
            if_exists='append',  # Do not drop the table, append to it
            index=False,
            method='multi',
            chunksize=1000       # Insert in batches of 1000
        )
        logger.info(f"✅ SUCCESS: Loaded {len(df_to_load)} rows into PostgreSQL.")
        
    except Exception as e:
        # Common error: Duplicate Primary Key or Constraint Violation
        logger.error(f"❌ SQL Insertion Failed: {e}")

# --- LOCAL TEST ---
if __name__ == "__main__":
    # Test loading from the processed file locally
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.getenv("DATA_DIR") or os.path.abspath(os.path.join(base_dir, "..", "data"))
    processed_path = os.path.join(data_dir, "processed", "trips_cleaned_final.csv")
    if os.path.exists(processed_path):
        run_load(processed_path)
    else:
        print("Test file not found.")
