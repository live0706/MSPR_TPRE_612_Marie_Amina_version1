import { startTransition, useDeferredValue, useEffect, useState } from "react";

import { fetchBootstrapData, fetchJourneyDetail, getApiPublicUrl } from "./api";
import JourneyTable from "./components/JourneyTable";
import MapPanel from "./components/MapPanel";
import StatusBadge from "./components/StatusBadge";
import {
  buildOperatorHighlights,
  formatCompact,
  formatMetric,
  formatTimestamp,
  serviceSplit
} from "./utils";

const INITIAL_FILTERS = {
  country_code: "",
  operator_name: "",
  service_type: "",
  year: "",
  limit: 120,
  sort_by: "departure_time",
  sort_order: "desc"
};

export default function App() {
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [searchInput, setSearchInput] = useState("");
  const deferredSearch = useDeferredValue(searchInput);
  const [data, setData] = useState({
    health: null,
    kpis: null,
    countries: [],
    operators: [],
    journeys: [],
    volumes: [],
    monitoring: null,
    comparison: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTripId, setSelectedTripId] = useState(null);
  const [selectedJourney, setSelectedJourney] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    startTransition(() => {
      setFilters((current) => ({
        ...current,
        search: deferredSearch.trim()
      }));
    });
  }, [deferredSearch]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const payload = await fetchBootstrapData({
          ...filters,
          year: filters.year || undefined
        });

        if (!active) {
          return;
        }

        startTransition(() => {
          setData(payload);

          const currentExists = payload.journeys.some((journey) => journey.trip_id === selectedTripId);
          if (!currentExists) {
            setSelectedTripId(payload.journeys[0]?.trip_id || null);
            setSelectedJourney(payload.journeys[0] || null);
          } else {
            const summary = payload.journeys.find((journey) => journey.trip_id === selectedTripId) || null;
            setSelectedJourney(summary);
          }
        });
      } catch (loadError) {
        if (!active) {
          return;
        }
        setError(loadError.message || "Chargement impossible");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [filters]);

  useEffect(() => {
    if (!selectedTripId) {
      return;
    }

    let active = true;
    setDetailLoading(true);

    fetchJourneyDetail(selectedTripId)
      .then((detail) => {
        if (active) {
          setSelectedJourney(detail);
        }
      })
      .catch(() => {
        if (active) {
          const summary = data.journeys.find((journey) => journey.trip_id === selectedTripId) || null;
          setSelectedJourney(summary);
        }
      })
      .finally(() => {
        if (active) {
          setDetailLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [data.journeys, selectedTripId]);

  const journeys = data.journeys || [];
  const mapJourneys = journeys.slice(0, 120);
  const operatorHighlights = buildOperatorHighlights(journeys);
  const split = serviceSplit(data.comparison || []);
  const healthStatus = data.health?.status || "degraded";
  const visibleCountryCount = new Set(journeys.map((journey) => journey.country_code).filter(Boolean)).size;
  const activeRouteLabel = selectedJourney
    ? `${selectedJourney.origin_city || "Origine"} -> ${selectedJourney.destination_city || "Destination"}`
    : "Aucun trajet actif";
  const dominantOperator = operatorHighlights[0] || null;
  const leadingCountry = [...(data.volumes || [])].sort(
    (left, right) => right.total_trajets - left.total_trajets
  )[0] || null;
  const dayStats = (data.comparison || []).find((item) => item.train_type === "day") || null;
  const nightStats = (data.comparison || []).find((item) => item.train_type === "night") || null;
  const highestCo2 = Math.max(
    Number(dayStats?.avg_co2_emissions || 0),
    Number(nightStats?.avg_co2_emissions || 0)
  );
  const lowestCo2Candidates = [dayStats?.avg_co2_emissions, nightStats?.avg_co2_emissions].filter(
    (value) => Number(value) > 0
  );
  const lowestCo2 = lowestCo2Candidates.length ? Math.min(...lowestCo2Candidates) : 0;
  const reductionPotential =
    highestCo2 > 0 && lowestCo2 > 0 ? Math.max(0, (1 - lowestCo2 / highestCo2) * 100) : 0;

  const comparisonBlocks = [
    {
      label: "Trajets",
      dayValue: Number(dayStats?.train_count || 0),
      nightValue: Number(nightStats?.train_count || 0),
      formatter: (value) => formatCompact(value)
    },
    {
      label: "Distance moyenne",
      dayValue: Number(dayStats?.avg_distance_km || 0),
      nightValue: Number(nightStats?.avg_distance_km || 0),
      formatter: (value) => `${Math.round(value)} km`
    },
    {
      label: "CO2 moyen",
      dayValue: Number(dayStats?.avg_co2_emissions || 0),
      nightValue: Number(nightStats?.avg_co2_emissions || 0),
      formatter: (value) => formatMetric(value, 3)
    }
  ];
  const apiDocsUrl = getApiPublicUrl("/api/docs");

  return (
    <div className="app-shell app-shell--mockup" data-testid="app-shell">
      <header className="topbar panel">
        <div className="brand">
          <div className="brand__mark" aria-hidden="true">
            O
          </div>
          <div className="brand__copy">
            <strong>ObRail Europe</strong>
            <span>Tableau de pilotage ferroviaire europeen</span>
          </div>
        </div>

        <nav className="topbar__nav">
          <a href={apiDocsUrl} target="_blank" rel="noreferrer">
            API Documentation
          </a>
        </nav>

        <div className="topbar__actions">
          <a
            className="topbar__button"
            href={data.monitoring?.grafana_url || "http://localhost:3000"}
            target="_blank"
            rel="noreferrer"
          >
            Supervision
          </a>
        </div>
      </header>

      <section className="workspace-frame panel">
        <aside className="search-panel" data-testid="search-panel">
          <div className="search-panel__title">Filtres de Recherche</div>
          <div className="search-panel__body">
            <div className="form-grid form-grid--mockup">
              <label>
                Recherche
                <input
                  data-testid="search-input"
                  type="search"
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                  placeholder="Operateur, ville, trip id"
                />
              </label>

              <label>
                Pays / Zone
                <select
                  data-testid="country-filter"
                  value={filters.country_code}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, country_code: event.target.value }))
                  }
                >
                  <option value="">Tous les pays</option>
                  {data.countries.map((country) => (
                    <option key={country.country_code} value={country.country_code}>
                      {country.country_name} ({country.country_code})
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Operateur
                <select
                  data-testid="operator-filter"
                  value={filters.operator_name}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, operator_name: event.target.value }))
                  }
                >
                  <option value="">Tous les operateurs</option>
                  {data.operators.map((operator) => (
                    <option key={operator.operator_id} value={operator.operator_name}>
                      {operator.operator_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Type de service
                <select
                  data-testid="service-filter"
                  value={filters.service_type}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, service_type: event.target.value }))
                  }
                >
                  <option value="">Jour + Nuit</option>
                  <option value="Jour">Jour</option>
                  <option value="Nuit">Nuit</option>
                </select>
              </label>

              <label>
                Annee
                <input
                  data-testid="year-filter"
                  type="number"
                  min="2015"
                  max="2100"
                  value={filters.year}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, year: event.target.value }))
                  }
                  placeholder="2026"
                />
              </label>

              <label>
                Volume affiche
                <select
                  data-testid="limit-filter"
                  value={String(filters.limit)}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, limit: Number(event.target.value) }))
                  }
                >
                  <option value="60">60 trajets</option>
                  <option value="120">120 trajets</option>
                  <option value="200">200 trajets</option>
                </select>
              </label>
            </div>

            <div className="filters__actions filters__actions--stacked">
              <button
                type="button"
                className="button button--primary"
                data-testid="search-button"
                onClick={() => setFilters((current) => ({ ...current }))}
              >
                Rechercher
              </button>
              <button
                type="button"
                className="button button--secondary"
                data-testid="reset-button"
                onClick={() => {
                  setSearchInput("");
                  setFilters(INITIAL_FILTERS);
                }}
              >
                Reinitialiser
              </button>
            </div>

            <div className="search-panel__status" data-testid="api-health-card">
              <div>
                <span>Etat API</span>
                <StatusBadge status={healthStatus} dataTestId="api-status-badge" />
              </div>
              <div>
                <span>Derniere ingestion</span>
                <strong>{formatTimestamp(data.monitoring?.latest_ingestion_at)}</strong>
              </div>
            </div>

            <div className="selected-compact" data-testid="selected-journey-card">
              <span>Trajet actif</span>
              <strong>{selectedJourney?.operator_name || "Aucune selection"}</strong>
              <p>{activeRouteLabel}</p>
              <p>
                {detailLoading
                  ? "Chargement..."
                  : selectedJourney
                    ? `${Math.round(selectedJourney.distance_km || 0)} km - ${selectedJourney.service_type || "Service"}`
                    : "Selectionne une ligne sur la carte ou dans le tableau"}
              </p>
            </div>
          </div>
        </aside>

        <div className="content-panel">
          <section className="headline-card panel" data-testid="headline-card">
            <div className="headline-card__inner">
              <p className="eyebrow">Impact Carbone</p>
              <h1>Reduction de CO2</h1>
              <div className="headline-card__value" data-testid="co2-reduction-value">
                {Math.round(reductionPotential)}%
              </div>
              <p className="headline-card__note">
                Potentielle entre le segment le plus emetteur et le segment le plus efficace
                observe sur les trajets visibles.
              </p>
            </div>
          </section>

          <section className="summary-row" data-testid="summary-row">
            <article className="summary-card panel" data-testid="summary-operator-card">
              <span className="summary-card__label">Operateur dominant</span>
              <strong>{dominantOperator?.operator || "Non disponible"}</strong>
              <p>{dominantOperator ? `${dominantOperator.count} trajets visibles` : "Aucune donnee"}</p>
            </article>

            <article className="summary-card panel" data-testid="summary-country-card">
              <span className="summary-card__label">Pays leader</span>
              <strong>
                {leadingCountry
                  ? `${leadingCountry.country_name} (${leadingCountry.country_code})`
                  : "Non disponible"}
              </strong>
              <p>
                {leadingCountry
                  ? `${formatCompact(leadingCountry.total_trajets)} trajets en ${leadingCountry.year}`
                  : "Aucune donnee"}
              </p>
            </article>

            <article className="summary-card panel" data-testid="summary-coverage-card">
              <span className="summary-card__label">Vue courante</span>
              <strong>{formatCompact(journeys.length)} trajets - {formatCompact(visibleCountryCount)} pays</strong>
              <p>{split.nightShare}% nuit / {split.dayShare}% jour</p>
            </article>
          </section>

          {error ? (
            <section className="panel error-panel" role="alert">
              <p className="eyebrow">Erreur</p>
              <h2>Chargement impossible</h2>
              <p>{error}</p>
            </section>
          ) : null}

          <section className="comparison-module panel" data-testid="comparison-module">
            <div className="module-title">Comparatif Ferroviaire</div>
            <div className="comparison-grid">
              {comparisonBlocks.map((block) => {
                const maxValue = Math.max(block.dayValue, block.nightValue, 1);
                return (
                  <article key={block.label} className="comparison-card">
                    <div className="comparison-card__title">{block.label}</div>
                    <div className="comparison-bar">
                      <span
                        className="comparison-bar__fill comparison-bar__fill--day"
                        style={{ width: `${(block.dayValue / maxValue) * 100}%` }}
                      />
                    </div>
                    <div className="comparison-row">
                      <span>Jour</span>
                      <strong>{block.formatter(block.dayValue)}</strong>
                    </div>
                    <div className="comparison-bar">
                      <span
                        className="comparison-bar__fill comparison-bar__fill--night"
                        style={{ width: `${(block.nightValue / maxValue) * 100}%` }}
                      />
                    </div>
                    <div className="comparison-row">
                      <span>Nuit</span>
                      <strong>{block.formatter(block.nightValue)}</strong>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="map-module" data-testid="map-module">
            <div className="module-title">Carte Europeenne</div>
            <MapPanel
              journeys={mapJourneys}
              selectedTripId={selectedTripId}
              selectedJourney={selectedJourney}
              onSelectTrip={setSelectedTripId}
            />
          </section>

          <section className="table-module" data-testid="table-module">
            <div className="module-title">Detail des Offres</div>
            <JourneyTable
              journeys={journeys}
              selectedTripId={selectedTripId}
              onSelectTrip={setSelectedTripId}
            />
          </section>
        </div>
      </section>

      {loading ? <div className="loading-banner">Mise a jour des donnees en cours...</div> : null}
    </div>
  );
}
