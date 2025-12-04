-- database/init.sql

-- 1. Nettoyage préventif (Optionnel : retirez cette ligne pour la production)
DROP TABLE IF EXISTS trips;

-- 2. Création de la table principale
CREATE TABLE trips (
    trip_id VARCHAR(100) PRIMARY KEY, -- ID unique (ex: SNCF-12345)
    
    operator_name VARCHAR(100) NOT NULL,
    origin_city VARCHAR(100) NOT NULL,
    destination_city VARCHAR(100) NOT NULL,
    
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    
    -- Contrainte IMPORTANTE : Seules les valeurs 'Jour' ou 'Nuit' sont acceptées
    service_type VARCHAR(10) CHECK (service_type IN ('Jour', 'Nuit')),
    
    train_type VARCHAR(100),
    distance_km FLOAT,
    co2_emissions FLOAT,
    
    -- Traçabilité
    source_origin VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Création des Index (Pour que l'API soit rapide)
-- Accélère les filtres "Trains de Nuit"
CREATE INDEX idx_service_type ON trips(service_type);
-- Accélère les recherches par opérateur
CREATE INDEX idx_operator ON trips(operator_name);
-- Accélère les recherches par ville de départ
CREATE INDEX idx_origin ON trips(origin_city);