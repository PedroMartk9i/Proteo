"""Página Datos: descargar Niño 3.4, ver vintages y graficar la serie."""

import sys
from pathlib import Path

# Permite importar ``proteo`` al correr la app desde la raíz del repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from proteo.data import nino34
from proteo.store import vintages

st.set_page_config(page_title="Datos · Proteo", page_icon="🌊", layout="wide")

st.title("Datos")
st.caption("Descarga con un clic, guardada como vintage (copia fechada).")

col1, col2, col3 = st.columns(3)

with col1:
    descargar = st.button("Descargar Niño 3.4", type="primary")
with col2:
    st.button("Descargar RONI", disabled=True, help="próxima sesión")
with col3:
    st.button("Descargar XM", disabled=True, help="próxima sesión")

# --- Descarga ---------------------------------------------------------------
if descargar:
    try:
        df = nino34.download()
        st.success(
            f"Descargado Niño 3.4: {len(df)} filas, "
            f"de {df['date'].min().date()} a {df['date'].max().date()}. "
            f"Vintage: {df['vintage'].iloc[0]}."
        )
    except Exception as exc:  # noqa: BLE001 — la red puede fallar de muchas formas
        disponibles = vintages.list_vintages(nino34.INDEX)
        if disponibles:
            st.warning(
                "No se pudo descargar (posible fallo de red): "
                f"{exc}. Se muestra el último vintage disponible "
                f"({disponibles[-1]})."
            )
        else:
            st.error(
                f"No se pudo descargar y no hay ningún vintage guardado: {exc}"
            )

# --- Vintages disponibles ---------------------------------------------------
disponibles = vintages.list_vintages(nino34.INDEX)

st.subheader("Vintages de nino34")
if disponibles:
    st.dataframe(
        pd.DataFrame({"vintage": [v.isoformat() for v in disponibles]}),
        hide_index=True,
        use_container_width=False,
    )
else:
    st.info("Aún no hay vintages. Pulsa **Descargar Niño 3.4**.")

# --- Gráfica del vintage más reciente ---------------------------------------
if disponibles:
    serie = vintages.load(nino34.INDEX)
    st.subheader(f"Niño 3.4 · vintage {disponibles[-1]}")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=serie["date"],
            y=serie["value"],
            mode="lines",
            name="Niño 3.4 (anomalía)",
        )
    )
    # Umbrales de El Niño (+0.5) y La Niña (-0.5).
    fig.add_hline(y=0.5, line_dash="dash", line_color="red",
                  annotation_text="El Niño (+0.5)")
    fig.add_hline(y=-0.5, line_dash="dash", line_color="blue",
                  annotation_text="La Niña (-0.5)")
    fig.add_hline(y=0.0, line_width=1, line_color="gray")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Anomalía (°C)",
        hovermode="x unified",
        margin=dict(t=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    ultimo = serie.iloc[-1]
    st.caption(
        f"Último valor: {ultimo['date'].date()} = {ultimo['value']:.2f}"
    )
