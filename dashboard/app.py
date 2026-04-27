import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="ObRail Dashboard", page_icon="🚆", layout="wide")

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=120)
def api_get(endpoint, params=None):
    url = f"{API_BASE_URL}{endpoint}"
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()


def safe_api_get(endpoint, params=None, default=None):
    try:
        return api_get(endpoint, params=params)
    except Exception as exc:
        st.error(f"Erreur API sur {endpoint}: {exc}")
        return default


def build_filter_params(country_code, operator_name, year):
    params = {}
    if country_code and country_code != "Tous":
        params["country_code"] = country_code
    if operator_name and operator_name != "Tous":
        params["operator_name"] = operator_name
    if year and year != "Tous":
        params["year"] = int(year)
    return params


st.title("ObRail Europe")
st.caption("Dashboard analytique connecte a l'API ObRail.")

countries = safe_api_get("/api/countries", default=[]) or []
operators = safe_api_get("/api/operators", default=[]) or []
kpis = safe_api_get("/api/dashboard/kpis", default={}) or {}

country_map = {"Tous": None}
for country in countries:
    country_map[country["country_name"]] = country["country_code"]

operator_map = {"Tous": None}
for operator in operators:
    operator_map[operator["operator_name"]] = operator["operator_name"]

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Page",
        ["Accueil", "Dashboard", "Trains", "Operateurs", "Sources et qualite"],
    )

    st.header("Filtres")
    selected_country_name = st.selectbox("Pays", list(country_map.keys()))
    selected_operator_name = st.selectbox("Operateur", list(operator_map.keys()))
    train_type = st.selectbox("Type de train", ["Tous", "Nuit", "Jour"])

    years_covered = kpis.get("years_covered", "")
    years = ["Tous"]
    if "-" in years_covered:
        start_year, end_year = years_covered.split("-", 1)
        if start_year.isdigit() and end_year.isdigit():
            years.extend([str(year) for year in range(int(start_year), int(end_year) + 1)])
    selected_year = st.selectbox("Annee", years)

filter_params = build_filter_params(
    country_map[selected_country_name],
    operator_map[selected_operator_name],
    selected_year,
)


def render_overview():
    timeline = safe_api_get("/api/statistics/timeline", default=[]) or []
    comparison = safe_api_get("/api/analysis/train-types-comparison", default=[]) or []

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pays couverts", int(kpis.get("total_countries", 0)))
    col2.metric("Trains references", int(kpis.get("total_trains", 0)))
    col3.metric("Operateurs", int(kpis.get("total_operators", 0)))
    col4.metric("CO2 moyen / passager", f"{float(kpis.get('avg_co2_per_passenger', 0.0)):.3f}")

    st.subheader("Synthese")
    summary_col1, summary_col2 = st.columns(2)
    summary_col1.info(
        f"Periode couverte : {kpis.get('years_covered', 'N/A')}\n\n"
        f"Volume agrege : {float(kpis.get('total_passengers', 0.0)):.0f}\n\n"
        f"CO2 total agrege : {float(kpis.get('total_co2_emissions', 0.0)):.2f}"
    )

    if comparison:
        comparison_df = pd.DataFrame(comparison)
        fig = px.bar(
            comparison_df,
            x="train_type",
            y="train_count",
            color="train_type",
            title="Volume de trains jour / nuit",
            color_discrete_map={"night": "#1D4ED8", "day": "#F59E0B"},
        )
        fig.update_xaxes(ticktext=["Jour", "Nuit"], tickvals=["day", "night"])
        summary_col2.plotly_chart(fig, use_container_width=True)
    else:
        summary_col2.warning("Aucune comparaison disponible.")

    if timeline:
        timeline_df = pd.DataFrame(timeline)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timeline_df["year"], y=timeline_df["passengers"], name="Volume agrege"))
        fig.add_trace(go.Scatter(x=timeline_df["year"], y=timeline_df["co2_emissions"], name="CO2", yaxis="y2"))
        fig.update_layout(
            title="Evolution temporelle",
            xaxis_title="Annee",
            yaxis_title="Volume agrege",
            yaxis2=dict(title="CO2", overlaying="y", side="right"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_dashboard():
    metrics = safe_api_get("/api/dashboard/metrics", default=[]) or []
    ranking = safe_api_get("/api/statistics/co2-ranking", params={"limit": 15}, default=[]) or []
    coverage = safe_api_get("/api/geographic/coverage", default={}) or {}

    if metrics:
        metrics_df = pd.DataFrame(metrics)
        fig = px.scatter(
            metrics_df,
            x="avg_passengers",
            y="avg_co2_per_passenger",
            size="avg_co2_emissions",
            color="country_name",
            hover_name="country_name",
            title="Relation volume / CO2 par pays",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune metrique disponible.")

    col1, col2 = st.columns(2)
    if ranking:
        ranking_df = pd.DataFrame(ranking)
        fig = px.bar(
            ranking_df,
            x="country_name",
            y="avg_co2_per_passenger",
            color="performance",
            title="Classement CO2",
            color_discrete_map={"good": "#10B981", "medium": "#F59E0B", "bad": "#EF4444"},
        )
        col1.plotly_chart(fig, use_container_width=True)
        col2.dataframe(ranking_df, use_container_width=True, hide_index=True)

    if coverage.get("coverage_by_country"):
        st.subheader("Couverture geographique")
        coverage_df = pd.DataFrame(coverage["coverage_by_country"])
        fig = px.bar(
            coverage_df,
            x="country_name",
            y="train_count",
            title="Trains references par pays",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_trains():
    if train_type == "Nuit":
        endpoint = "/api/night-trains/night"
    elif train_type == "Jour":
        endpoint = "/api/night-trains/day"
    else:
        endpoint = "/api/night-trains"

    trains = safe_api_get(endpoint, params={"limit": 500, **filter_params}, default=[]) or []
    if not trains:
        st.warning("Aucun train trouve pour les filtres courants.")
        return

    trains_df = pd.DataFrame(trains)
    trains_df["type"] = trains_df["is_night"].map({True: "Nuit", False: "Jour"})

    st.metric("Trains trouves", len(trains_df))
    st.dataframe(
        trains_df[
            ["night_train", "country_name", "operator_name", "year", "type", "distance_km", "co2_emissions"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    grouped = trains_df.groupby(["country_name", "type"], as_index=False).size()
    grouped = grouped.rename(columns={"size": "count"})
    fig = px.bar(
        grouped,
        x="country_name",
        y="count",
        color="type",
        title="Repartition des trains par pays",
        barmode="group",
        color_discrete_map={"Jour": "#F59E0B", "Nuit": "#1D4ED8"},
    )
    st.plotly_chart(fig, use_container_width=True)


def render_operators():
    operators_list = safe_api_get("/api/operators", params={"limit": 500}, default=[]) or []
    if not operators_list:
        st.warning("Aucun operateur disponible.")
        return

    operators_df = pd.DataFrame(operators_list)
    st.dataframe(operators_df, use_container_width=True, hide_index=True)

    if selected_operator_name != "Tous":
        operator_id = operators_df.loc[
            operators_df["operator_name"] == selected_operator_name, "operator_id"
        ]
        if not operator_id.empty:
            stats = safe_api_get(f"/api/operators/{int(operator_id.iloc[0])}/stats", default={}) or {}
            col1, col2, col3 = st.columns(3)
            col1.metric("Trains operes", int(stats.get("total_trains", 0)))
            col2.metric("Pays desservis", int(stats.get("countries_count", 0)))
            col3.metric("Operateur", stats.get("operator_name", "N/A"))
            if stats.get("countries_served"):
                st.write("Pays desservis :", ", ".join(stats["countries_served"]))


def render_quality():
    quality_payload = safe_api_get("/api/metadata/quality", default={}) or {}
    sources_payload = safe_api_get("/api/metadata/sources", default={"sources": []}) or {"sources": []}

    quality_report = quality_payload.get("quality_report", {})
    model_metrics = quality_payload.get("model_metrics", {})

    source_rows = sources_payload.get("sources", [])
    if source_rows:
        st.subheader("Sources chargees")
        st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Rapport qualite")
        if quality_report:
            st.json(quality_report)
        else:
            st.info("Aucun rapport qualite disponible.")

    with col2:
        st.subheader("Metriques modele")
        if model_metrics:
            st.json(model_metrics)
        else:
            st.info("Aucune metrique modele disponible.")


if page == "Accueil":
    render_overview()
elif page == "Dashboard":
    render_dashboard()
elif page == "Trains":
    render_trains()
elif page == "Operateurs":
    render_operators()
else:
    render_quality()
