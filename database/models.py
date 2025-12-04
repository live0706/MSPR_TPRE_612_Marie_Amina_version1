# database/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.orm import declarative_base

# Base déclarative pour SQLAlchemy
Base = declarative_base()

class Trip(Base):
    """
    Modèle SQLAlchemy correspondant à la table 'trips'.
    Utilisé par l'API pour lire les données proprement.
    """
    __tablename__ = "trips"

    # Définition des colonnes (Doit matcher init.sql)
    trip_id = Column(String, primary_key=True, index=True)
    operator_name = Column(String, index=True)
    origin_city = Column(String, index=True)
    destination_city = Column(String)
    
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    
    service_type = Column(String, index=True) # Indexé pour filtrer Jour/Nuit
    train_type = Column(String)
    
    distance_km = Column(Float)
    co2_emissions = Column(Float)
    
    source_origin = Column(String)
    # created_at est géré automatiquement par la BDD