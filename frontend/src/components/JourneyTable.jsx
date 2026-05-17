function formatDate(value) {
  if (!value) {
    return "Non renseigne";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Non renseigne";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function formatDistance(value) {
  if (!Number.isFinite(value)) {
    return "0 km";
  }
  return `${Math.round(value)} km`;
}

export default function JourneyTable({ journeys, selectedTripId, onSelectTrip }) {
  return (
    <section className="table-panel">
      <div className="table-panel__meta">
        {journeys.length} trajets affiches{selectedTripId ? " - 1 selection active" : ""}
      </div>
      <div className="table-shell" role="region" aria-label="Tableau des trajets">
        <table className="journey-table">
          <thead>
            <tr>
              <th>Operateur</th>
              <th>Corridor</th>
              <th>Depart</th>
              <th>Service</th>
              <th>Pays</th>
              <th>Distance</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {journeys.map((journey) => {
              const selected = journey.trip_id === selectedTripId;
              return (
                <tr key={journey.trip_id} data-selected={selected}>
                  <td>
                    <div className="table-operator">
                      <strong>{journey.operator_name || "Operateur inconnu"}</strong>
                      <span>{journey.train_type || "Rail"}</span>
                    </div>
                  </td>
                  <td>
                    <div className="table-route">
                      <strong>
                        {journey.origin_city || "Origine"} -&gt;{" "}
                        {journey.destination_city || "Destination"}
                      </strong>
                      <span>{journey.country_name || journey.country_code || "Unknown"}</span>
                    </div>
                  </td>
                  <td>{formatDate(journey.departure_time)}</td>
                  <td>
                    <span className={`pill pill--${journey.service_type === "Nuit" ? "night" : "day"}`}>
                      {journey.service_type || "Indefini"}
                    </span>
                  </td>
                  <td>
                    <span className="country-chip">{journey.country_code || "ZZ"}</span>
                  </td>
                  <td>{formatDistance(journey.distance_km)}</td>
                  <td>
                    <button
                      type="button"
                      className="table-button"
                      onClick={() => onSelectTrip(journey.trip_id)}
                    >
                      {selected ? "Selectionne" : "Voir"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
