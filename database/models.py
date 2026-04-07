# database/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import declarative_base

# Base déclarative pour SQLAlchemy
Base = declarative_base()

class Source(Base):
    __tablename__ = "sources"

    source_id = Column(Integer, primary_key=True)
    source_key = Column(String, unique=True, index=True)
    name = Column(String)
    url = Column(String)
    source_type = Column(String)
    provider = Column(String)
    license = Column(String)
    last_seen = Column(DateTime)


class Ingestion(Base):
    __tablename__ = "ingestions"

    ingestion_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    fetched_at = Column(DateTime)
    raw_path = Column(String)
    status = Column(String)
    row_count = Column(Integer)


class Operator(Base):
    __tablename__ = "operators"

    operator_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    country = Column(String)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    created_at = Column(DateTime)


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    country = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    created_at = Column(DateTime)


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True)
    operator_id = Column(Integer, ForeignKey("operators.operator_id"))
    origin_station_id = Column(Integer, ForeignKey("stations.station_id"))
    destination_station_id = Column(Integer, ForeignKey("stations.station_id"))
    distance_km = Column(Float)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    created_at = Column(DateTime)


class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"))
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    service_type = Column(String, index=True)
    train_type = Column(String)
    co2_emissions = Column(Float)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    created_at = Column(DateTime)
