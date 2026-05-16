import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from utils import build_trajet_params, normalize_status_label

st.set_page_config(page_title="ObRail Control Center", page_icon="🚆", layout="wide")

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")


@st.cache_data(ttl=60)
def api_get(endpoint, params=None):
    response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def safe_api_get(endpoint, params=None, default=None):
    try:
        return api_get(endpoint, params=params)
    except Exception as exc:
        st.error(f"Erreur API sur {endpoint}: {exc}")
        return default


def render_theme():
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top right, rgba(25, 91, 255, 0.08), transparent 35%),
                    linear-gradient(180deg, #F8FAFC 0%, #EDF2F7 100%);
            }
            .block-container {
                max-width: 1400px;
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }
            .hero-card, .panel-card {
                background: white;
                border: 1px solid #D7E2F0;
                border-radius: 18px;
                padding: 1.2rem 1.25rem;
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
            }
            .hero-title {
                font-size: 2rem;
                font-weight: 700;
                color: #0F172A;
                margin-bottom: 0.35rem;
            }
            .hero-subtitle {
                color: #334155;
                font-size: 1rem;
                line-height: 1.5;
                margin-bottom: 0;
            }
            .status-chip {
                display: inline-block;
                border-radius: 999px;
                padding: 0.35rem 0.75rem;
                font-weight: 600;
                font-size: 0.9rem;
                margin-bottom: 0.75rem;
            }
            .status-ok {
                background: #DCFCE7;
                color: #166534;
            }
            .status-degraded {
                background: #FEF3C7;
                color: #92400E;
            }
            .status-error {
                background: #FEE2E2;
                color: #991B1B;
            }
            .quick-links a {
                text-decoration: none;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(health_payload):
    status = (health_payload or {}).get("status", "error")
    status_class = {
        "ok": "status-ok",
        "degraded": "status-degraded",
        "error": "status-error",
    }.get(status, "status-error")
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="status-chip {status_class}">Etat API: {normalize_status_label(status)}</div>
            <div class="hero-title">ObRail Control Center</div>
            <p class="hero-subtitle">
                Interface d'exploitation pour consulter les trajets ferroviaires europeens,
                suivre les volumes, verifier la sante de l'API et acceder a la supervision.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(kpis, health_payload, monitoring_payload):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Trajets references", int(kpis.get("total_trains", 0)))
    col2.metric("Pays couverts", int(kpis.get("total_countries", 0)))
    col3.metric("Operateurs", int(kpis.get("total_operators", 0)))
    col4.metric("Periode", kpis.get("years_covered", "N/A"))

    detail_col1, detail_col2 = st.columns([1.2, 1])
    with detail_col1:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.subheader("Etat de la plateforme")
        st.write(
            {
                "api_status": health_payload.get("status", "unknown"),
                "database": health_payload.get("database", {}),
                "quality_report": health_payload.get("quality_report", {}),
                "model_metrics": health_payload.get("model_metrics", {}),
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with detail_col2:
        st.markdown('<div class="panel-card quick-links">', unsafe_allow_html=True)
        st.subheader("Acces rapides")
        st.markdown(
            f"""
            - [Swagger API]({API_BASE_URL}/api/docs)
            - [Prometheus]({PROMETHEUS_URL})
            - [Grafana]({GRAFANA_URL})
            - [Healthcheck API]({API_BASE_URL}/health)
            - [Resume monitoring]({API_BASE_URL}/api/monitoring/summary)
            """
        )
        st.caption(
            f"Derniere ingestion connue : {monitoring_payload.get('latest_ingestion_at', 'Aucune donnee')}"
        )
        st.markdown("</div>", unsafe_allow_html=True)


def render_catalogue(trajets_df):
    st.subheader("Catalogue des trajets")
    if trajets_df.empty:
        st.warning("Aucun trajet ne correspond aux filtres courants.")
        return

    st.metric("Resultats", len(trajets_df))
    display_columns = [
        "trip_id",
        "operator_name",
        "origin_city",
        "destination_city",
        "country_code",
        "service_type",
        "departure_time",
        "distance_km",
        "co2_emissions",
    ]
    st.dataframe(trajets_df[display_columns], use_container_width=True, hide_index=True)

    selected_trip_id = st.selectbox("Detail d'un trajet", trajets_df["trip_id"].tolist())
    trip_detail = safe_api_get(f"/trajets/{selected_trip_id}", default={}) or {}
    if trip_detail:
        st.json(trip_detail)


def render_statistics(timeline, volumes_df):
    st.subheader("Statistiques et volumes")
    stat_col1, stat_col2 = st.columns(2)

    if timeline:
        timeline_df = pd.DataFrame(timeline)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timeline_df["year"], y=timeline_df["train_count"], name="Trajets"))
        fig.add_trace(go.Scatter(x=timeline_df["year"], y=timeline_df["co2_emissions"], name="CO2", yaxis="y2"))
        fig.update_layout(
            title="Evolution des volumes et emissions",
            xaxis_title="Annee",
            yaxis_title="Trajets",
            yaxis2=dict(title="CO2", overlaying="y", side="right"),
            hovermode="x unified",
        )
        stat_col1.plotly_chart(fig, use_container_width=True)
    else:
        stat_col1.info("Aucune serie temporelle disponible.")

    if not volumes_df.empty:
        fig = px.bar(
            volumes_df,
            x="country_code",
            y="total_trajets",
            color="year",
            title="Volumes de trajets par pays",
            barmode="group",
        )
        stat_col2.plotly_chart(fig, use_container_width=True)
    else:
        stat_col2.info("Aucun volume agrege disponible.")

    if not volumes_df.empty:
        st.dataframe(volumes_df, use_container_width=True, hide_index=True)


def render_monitoring(health_payload, monitoring_payload, sources_payload):
    st.subheader("Monitoring et supervision")
    left_col, right_col = st.columns([1.1, 1])

    with left_col:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.write(health_payload)
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.write(monitoring_payload)
        st.markdown("</div>", unsafe_allow_html=True)

    sources = sources_payload.get("sources", []) if isinstance(sources_payload, dict) else []
    if sources:
        st.subheader("Sources de donnees")
        sources_df = pd.DataFrame(sources)
        st.dataframe(sources_df, use_container_width=True, hide_index=True)


def main():
    render_theme()

    health_payload = safe_api_get("/health", default={}) or {}
    monitoring_payload = safe_api_get("/api/monitoring/summary", default={}) or {}
    kpis = safe_api_get("/api/dashboard/kpis", default={}) or {}
    countries = safe_api_get("/api/countries", default=[]) or []
    operators = safe_api_get("/api/operators", default=[]) or []
    timeline = safe_api_get("/api/statistics/timeline", default=[]) or []
    sources_payload = safe_api_get("/api/metadata/sources", default={"sources": []}) or {"sources": []}

    render_header(health_payload)

    country_options = {"Tous": None}
    for country in countries:
        country_options[f"{country['country_name']} ({country['country_code']})"] = country["country_code"]

    operator_options = {"Tous": None}
    for operator in operators:
        operator_options[operator["operator_name"]] = operator["operator_name"]

    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Vue", ["Vue d'ensemble", "Catalogue", "Statistiques", "Monitoring"])
        st.header("Filtres")
        selected_country_label = st.selectbox("Pays", list(country_options.keys()))
        selected_operator_label = st.selectbox("Operateur", list(operator_options.keys()))
        selected_service_type = st.selectbox("Service", ["Tous", "Nuit", "Jour"])
        selected_year = st.text_input("Annee", value="")
        search_text = st.text_input("Recherche libre", placeholder="Ville, operateur, identifiant...")

    year_value = selected_year.strip() if selected_year else None
    if year_value and not year_value.isdigit():
        st.sidebar.warning("Le filtre annee doit etre numerique.")
        year_value = None

    trajets_params = build_trajet_params(
        country_code=country_options[selected_country_label],
        operator_name=operator_options[selected_operator_label],
        year=year_value or None,
        service_type=selected_service_type,
        search=search_text,
        limit=250,
    )
    trajets = safe_api_get("/trajets", params=trajets_params, default=[]) or []
    volumes = safe_api_get(
        "/stats/volumes",
        params={
            key: value
            for key, value in {
                "country_code": country_options[selected_country_label],
                "year": int(year_value) if year_value else None,
                "limit": 100,
            }.items()
            if value is not None
        },
        default=[],
    ) or []

    trajets_df = pd.DataFrame(trajets)
    volumes_df = pd.DataFrame(volumes)

    if page == "Vue d'ensemble":
        render_overview(kpis, health_payload, monitoring_payload)
    elif page == "Catalogue":
        render_catalogue(trajets_df)
    elif page == "Statistiques":
        render_statistics(timeline, volumes_df)
    else:
        render_monitoring(health_payload, monitoring_payload, sources_payload)


if __name__ == "__main__":
    main()
