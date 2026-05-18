import { useEffect } from "react";
import {
  CircleMarker,
  MapContainer,
  Pane,
  Polyline,
  Popup,
  TileLayer,
  Tooltip,
  useMap
} from "react-leaflet";

const EUROPE_CENTER = [50.4, 10.2];
const EUROPE_ZOOM = 5;
const MAX_CORRIDOR_PILLS = 6;

function FitBounds({ journeys }) {
  const map = useMap();

  useEffect(() => {
    const bounds = [];
    journeys.forEach((journey) => {
      if (
        Number.isFinite(journey.origin_lat) &&
        Number.isFinite(journey.origin_lon) &&
        Number.isFinite(journey.destination_lat) &&
        Number.isFinite(journey.destination_lon)
      ) {
        bounds.push([journey.origin_lat, journey.origin_lon]);
        bounds.push([journey.destination_lat, journey.destination_lon]);
      }
    });

    if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [30, 30] });
    } else {
      map.setView(EUROPE_CENTER, EUROPE_ZOOM);
    }
  }, [journeys, map]);

  return null;
}

function journeyColor(journey, selectedTripId) {
  if (journey.trip_id === selectedTripId) {
    return "#ef233c";
  }
  return journey.service_type === "Nuit" ? "#0057b8" : "#ff6b1a";
}

function journeyWeight(journey, selectedTripId) {
  return journey.trip_id === selectedTripId ? 5.2 : 3.4;
}

function haloWeight(journey, selectedTripId) {
  return journey.trip_id === selectedTripId ? 10 : 7;
}

function summarizeCorridors(journeys) {
  const buckets = new Map();

  journeys.forEach((journey) => {
    const key = [
      journey.origin_city || "Origine",
      journey.destination_city || "Destination",
      journey.operator_name || "Operateur inconnu"
    ].join("|");

    const current = buckets.get(key) || {
      key,
      label: `${journey.origin_city || "Origine"} -> ${journey.destination_city || "Destination"}`,
      operator: journey.operator_name || "Operateur inconnu",
      tripId: journey.trip_id,
      count: 0
    };

    current.count += 1;
    buckets.set(key, current);
  });

  return Array.from(buckets.values())
    .sort((left, right) => right.count - left.count)
    .slice(0, MAX_CORRIDOR_PILLS);
}

export default function MapPanel({ journeys, selectedTripId, selectedJourney, onSelectTrip }) {
  const mappableJourneys = journeys.filter(
    (journey) =>
      Number.isFinite(journey.origin_lat) &&
      Number.isFinite(journey.origin_lon) &&
      Number.isFinite(journey.destination_lat) &&
      Number.isFinite(journey.destination_lon)
  );
  const uniqueOperators = new Set(
    mappableJourneys.map((journey) => journey.operator_name).filter(Boolean)
  );
  const corridorHighlights = summarizeCorridors(mappableJourneys);

  if (!mappableJourneys.length) {
    return (
      <section
        className="map-panel map-panel--empty"
        aria-live="polite"
        data-testid="journey-map-panel-empty"
      >
        <div>
          <h2>Aucun trajet cartographiable</h2>
          <p>
            Les filtres actuels ne renvoient pas de trajets avec coordonnees d&apos;origine et de
            destination.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="map-panel" data-testid="journey-map-panel">
      <div className="map-toolbar">
        <div className="map-legend" aria-label="Legende de la carte" data-testid="map-legend">
          <span>
            <i className="legend-dot legend-dot--night" />
            Nuit
          </span>
          <span>
            <i className="legend-dot legend-dot--day" />
            Jour
          </span>
          <span>
            <i className="legend-dot legend-dot--selected" />
            Selection
          </span>
        </div>

        <div className="map-stats" aria-label="Resume de la carte" data-testid="map-stats">
          <span className="map-chip">{mappableJourneys.length} routes visibles</span>
          <span className="map-chip">{uniqueOperators.size} operateurs</span>
          <span className="map-chip">{selectedJourney ? "1 route active" : "Clique sur une ligne"}</span>
        </div>
      </div>

      {corridorHighlights.length ? (
        <div className="route-pills" aria-label="Corridors visibles" data-testid="route-pills">
          {corridorHighlights.map((corridor) => (
            <button
              key={corridor.key}
              type="button"
              className={`route-pill ${corridor.tripId === selectedTripId ? "route-pill--active" : ""}`}
              data-testid={`route-pill-${corridor.tripId}`}
              onClick={() => onSelectTrip(corridor.tripId)}
            >
              <strong>{corridor.label}</strong>
              <span>{corridor.operator}</span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="map-shell">
        <div className="map-overlay-note">
          <strong>Lecture de la carte</strong>
          <span>
            {selectedJourney
              ? `${selectedJourney.operator_name || "Operateur"} - ${selectedJourney.service_type || "Service"}`
              : "La ligne active synchronise la carte et le tableau"}
          </span>
        </div>

        <MapContainer
          className="map-canvas"
          center={EUROPE_CENTER}
          zoom={EUROPE_ZOOM}
          scrollWheelZoom
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution="&copy; OpenStreetMap contributors &copy; CARTO"
          />
          <FitBounds journeys={mappableJourneys} />

          <Pane name="route-halos" style={{ zIndex: 330 }}>
            {mappableJourneys.map((journey) => (
              <Polyline
                key={`halo-${journey.trip_id}`}
                positions={[
                  [journey.origin_lat, journey.origin_lon],
                  [journey.destination_lat, journey.destination_lon]
                ]}
                pathOptions={{
                  color: journey.trip_id === selectedTripId ? "#111827" : "#f8fafc",
                  weight: haloWeight(journey, selectedTripId),
                  opacity: journey.trip_id === selectedTripId ? 0.9 : 0.84,
                  lineCap: "round",
                  lineJoin: "round"
                }}
              />
            ))}
          </Pane>

          <Pane name="routes" style={{ zIndex: 350 }}>
            {mappableJourneys.map((journey) => (
              <Polyline
                key={`line-${journey.trip_id}`}
                positions={[
                  [journey.origin_lat, journey.origin_lon],
                  [journey.destination_lat, journey.destination_lon]
                ]}
                pathOptions={{
                  color: journeyColor(journey, selectedTripId),
                  weight: journeyWeight(journey, selectedTripId),
                  opacity: journey.trip_id === selectedTripId ? 1 : 0.88,
                  dashArray:
                    journey.trip_id === selectedTripId
                      ? null
                      : journey.service_type === "Jour"
                        ? "8 10"
                        : null,
                  lineCap: "round",
                  lineJoin: "round"
                }}
                eventHandlers={{
                  click: () => onSelectTrip(journey.trip_id)
                }}
              >
                <Tooltip sticky>
                  {journey.operator_name || "Operateur inconnu"} - {journey.origin_city || "Origine"} -&gt;{" "}
                  {journey.destination_city || "Destination"}
                </Tooltip>
                <Popup>
                  <strong>{journey.operator_name || "Operateur inconnu"}</strong>
                  <br />
                  {journey.origin_city || "Origine"} -&gt; {journey.destination_city || "Destination"}
                  <br />
                  {journey.service_type || "Service"} - {Math.round(journey.distance_km || 0)} km
                </Popup>
              </Polyline>
            ))}
          </Pane>

          <Pane name="stations" style={{ zIndex: 400 }}>
            {mappableJourneys.map((journey) => {
              const selected = journey.trip_id === selectedTripId;
              const color = journeyColor(journey, selectedTripId);

              return (
                <CircleMarker
                  key={`origin-${journey.trip_id}`}
                  center={[journey.origin_lat, journey.origin_lon]}
                  radius={selected ? 7 : 4}
                  pathOptions={{
                    color,
                    fillColor: "#ffffff",
                    fillOpacity: selected ? 1 : 0.9,
                    weight: selected ? 3 : 2
                  }}
                  eventHandlers={{
                    click: () => onSelectTrip(journey.trip_id)
                  }}
                >
                  <Tooltip direction="top" offset={[0, -4]}>
                    {journey.origin_city || "Origine"}
                  </Tooltip>
                </CircleMarker>
              );
            })}

            {mappableJourneys.map((journey) => {
              const selected = journey.trip_id === selectedTripId;
              const color = journeyColor(journey, selectedTripId);

              return (
                <CircleMarker
                  key={`destination-${journey.trip_id}`}
                  center={[journey.destination_lat, journey.destination_lon]}
                  radius={selected ? 7 : 4}
                  pathOptions={{
                    color,
                    fillColor: color,
                    fillOpacity: selected ? 1 : 0.92,
                    weight: selected ? 3 : 2
                  }}
                  eventHandlers={{
                    click: () => onSelectTrip(journey.trip_id)
                  }}
                >
                  <Tooltip direction="top" offset={[0, -4]}>
                    {journey.destination_city || "Destination"}
                  </Tooltip>
                </CircleMarker>
              );
            })}
          </Pane>
        </MapContainer>
      </div>
    </section>
  );
}
