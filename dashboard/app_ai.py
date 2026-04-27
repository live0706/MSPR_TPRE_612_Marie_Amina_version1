import json
import os
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(page_title="ObRail IA", page_icon="🤖", layout="wide")

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
QUALITY_REPORT_PATH = os.getenv("QUALITY_REPORT_PATH", "/app/data/processed/quality_report.json")
MODEL_METRICS_PATH = os.getenv("MODEL_METRICS_PATH", "/app/data/processed/model_metrics.json")


def load_local_json(path):
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_remote_payload():
    try:
        response = requests.get(f"{API_BASE_URL}/api/metadata/quality", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


remote_payload = load_remote_payload()
quality_report = remote_payload.get("quality_report") or load_local_json(QUALITY_REPORT_PATH)
model_metrics = remote_payload.get("model_metrics") or load_local_json(MODEL_METRICS_PATH)

st.title("ObRail IA")
st.caption("Vue de controle des rapports qualite et des metriques du modele CO2.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Qualite des donnees")
    if quality_report:
        st.json(quality_report)
    else:
        st.info("Aucun rapport qualite trouve.")

with col2:
    st.subheader("Metriques du modele")
    if model_metrics:
        st.json(model_metrics)
    else:
        st.info("Aucune metrique modele trouvee.")
