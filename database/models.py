from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

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


class DimCountry(Base):
    __tablename__ = "dim_countries"

    country_id = Column(Integer, primary_key=True)
    country_code = Column(String, unique=True, index=True)
    country_name = Column(String)


class DimYear(Base):
    __tablename__ = "dim_years"

    year_id = Column(Integer, primary_key=True)
    year = Column(Integer, unique=True, index=True)
    is_after_2010 = Column(Boolean, nullable=False, default=True)


class DimOperator(Base):
    __tablename__ = "dim_operators"

    operator_id = Column(Integer, primary_key=True)
    operator_name = Column(String, unique=True, index=True)


class FactNightTrain(Base):
    __tablename__ = "facts_night_trains"

    fact_id = Column(Integer, primary_key=True)
    trip_id = Column(String, unique=True, index=True)
    route_id = Column(Integer)
    night_train = Column(String, index=True)
    country_id = Column(Integer, ForeignKey("dim_countries.country_id"))
    year_id = Column(Integer, ForeignKey("dim_years.year_id"))
    operator_id = Column(Integer, ForeignKey("dim_operators.operator_id"))
    is_night = Column(Boolean, nullable=False, default=True)
    distance_km = Column(Float)
    co2_emissions = Column(Float)


class FactCountryStat(Base):
    __tablename__ = "facts_country_stats"

    stats_id = Column(Integer, primary_key=True)
    passengers = Column(Float, nullable=False)
    co2_emissions = Column(Float, nullable=False)
    co2_per_passenger = Column(Float, nullable=False)
    country_id = Column(Integer, ForeignKey("dim_countries.country_id"))
    year_id = Column(Integer, ForeignKey("dim_years.year_id"))


class DashboardMetric(Base):
    __tablename__ = "dashboard_metrics"

    country_name = Column(String, primary_key=True)
    country_code = Column(String)
    avg_passengers = Column(Float)
    avg_co2_emissions = Column(Float)
    avg_co2_per_passenger = Column(Float)
