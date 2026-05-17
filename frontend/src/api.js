const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function requestJson(path, params = {}) {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url.toString(), {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`${response.status} ${response.statusText} - ${message}`);
  }

  return response.json();
}

export async function fetchBootstrapData(filters) {
  const [
    health,
    kpis,
    countries,
    operators,
    journeys,
    volumes,
    monitoring,
    comparison
  ] = await Promise.all([
    requestJson("/health"),
    requestJson("/api/dashboard/kpis"),
    requestJson("/api/countries", { limit: 500 }),
    requestJson("/api/operators", { limit: 500 }),
    requestJson("/trajets", filters),
    requestJson("/stats/volumes", {
      country_code: filters.country_code,
      year: filters.year,
      limit: 200
    }),
    requestJson("/api/monitoring/summary"),
    requestJson("/api/analysis/train-types-comparison")
  ]);

  return {
    health,
    kpis,
    countries,
    operators,
    journeys,
    volumes,
    monitoring,
    comparison
  };
}

export async function fetchJourneyDetail(tripId) {
  return requestJson(`/trajets/${tripId}`);
}
