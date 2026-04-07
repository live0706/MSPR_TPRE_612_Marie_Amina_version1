import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="ObRail Dashboard", page_icon="🚄", layout="wide")

# Connexion BDD
DATABASE_URL = os.getenv('DATABASE_URL')

# --- FONCTION DE CHARGEMENT ---
# @st.cache_data permet de garder les données en mémoire pour que le site soit rapide
@st.cache_data(ttl=60) # Rafraîchit toutes les 60 secondes
def load_data():
    try:
        engine = create_engine(DATABASE_URL)
        query = """
            SELECT
                t.trip_id,
                o.name AS operator_name,
                so.name AS origin_city,
                sd.name AS destination_city,
                t.departure_time,
                t.arrival_time,
                t.service_type,
                t.train_type,
                r.distance_km,
                t.co2_emissions
            FROM trips t
            LEFT JOIN routes r ON t.route_id = r.route_id
            LEFT JOIN operators o ON r.operator_id = o.operator_id
            LEFT JOIN stations so ON r.origin_station_id = so.station_id
            LEFT JOIN stations sd ON r.destination_station_id = sd.station_id
        """
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return pd.DataFrame()

# --- INTERFACE UTILISATEUR ---

st.title("🚄 ObRail Europe - Observatoire Ferroviaire")
st.markdown("Ce tableau de bord permet de comparer l'offre de trains de **Jour** et de **Nuit** en Europe.")

# 1. Chargement des données
df = load_data()

if df.empty:
    st.warning("Aucune donnée disponible. Lancez l'ETL d'abord !")
else:
    # 2. Indicateurs Clés (KPIs)
    st.header("1. Indicateurs Globaux")
    col1, col2, col3, col4 = st.columns(4)
    
    total_trains = len(df)
    night_trains = len(df[df['service_type'] == 'Nuit'])
    avg_co2 = df['co2_emissions'].mean()
    nb_operators = df['operator_name'].nunique()

    col1.metric("Total Trajets", total_trains)
    col2.metric("Trains de Nuit", night_trains, delta=f"{night_trains/total_trains:.1%}")
    col3.metric("Émission Moyenne CO2", f"{avg_co2:.2f} kg")
    col4.metric("Opérateurs", nb_operators)

    st.divider()

    # 3. Graphiques (Plotly)
    st.header("2. Analyse Comparative")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Répartition Jour / Nuit")
        # Camembert simple
        fig_pie = px.pie(df, names='service_type', title='Part des trains de nuit', 
                         color='service_type', color_discrete_map={'Nuit':'#1E1E5A', 'Jour':'#FFC107'})
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Top Opérateurs (Volume)")
        # Bar chart horizontal
        top_ops = df['operator_name'].value_counts().head(10).reset_index()
        top_ops.columns = ['Opérateur', 'Nombre de Trajets']
        fig_bar = px.bar(top_ops, x='Nombre de Trajets', y='Opérateur', orientation='h', color='Nombre de Trajets')
        st.plotly_chart(fig_bar, use_container_width=True)

    # 4. Qualité des Données
    st.header("3. Contrôle Qualité des Données")
    
    # Calcul des taux de remplissage
    missing_co2 = df['co2_emissions'].isna().sum() + (df['co2_emissions'] == 0).sum()
    st.info(f"📊 **Qualité CO2 :** {missing_co2} trajets ont une émission nulle ou manquante (estimée par l'ETL).")

    # Explorateur de données
    with st.expander("🔎 Consulter les données brutes"):
        # Filtres simples
        operator_filter = st.selectbox("Filtrer par Opérateur", ["Tous"] + list(df['operator_name'].unique()))
        
        if operator_filter != "Tous":
            df_view = df[df['operator_name'] == operator_filter]
        else:
            df_view = df
            
        st.dataframe(df_view, use_container_width=True)
