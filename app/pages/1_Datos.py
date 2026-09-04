"""Página Datos: descargar los tres índices, ver vintages y graficar."""

import sys
from pathlib import Path

# Permite importar ``proteo`` al correr la app desde la raíz del repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from proteo.data import nino34, roni, xm
from proteo.store import vintages

st.set_page_config(page_title="Datos · Proteo", page_icon="🌊", layout="wide")

st.title("Datos")
st.caption("Descarga con un clic, guardada como vintage (copia fechada).")

# Etiqueta → (nombre de índice, función download). XM tarda más: descarga
# año por año desde 2000.
ADAPTERS = {
    "Niño 3.4": (nino34.INDEX, nino34.download),
    "RONI": (roni.INDEX, roni.download),
    "XM": (xm.INDEX, xm.download),
}


def _download_one(label: str) -> bool:
    """Descarga un índice y reporta en pantalla. Devuelve True si funcionó."""
    index, download = ADAPTERS[label]
    try:
        with st.spinner(f"Descargando {label}…"):
            df = download()
        st.success(
            f"Descargado {label}: {len(df)} filas, "
            f"de {df['date'].min().date()} a {df['date'].max().date()}. "
            f"Vintage: {df['vintage'].iloc[0]}."
        )
        return True
    except Exception as exc:  # noqa: BLE001 — la red puede fallar de muchas formas
        disponibles = vintages.list_vintages(index)
        if disponibles:
            st.warning(
                f"No se pudo descargar {label} (posible fallo de red): {exc}. "
                f"Se muestra el último vintage disponible ({disponibles[-1]})."
            )
        else:
            st.error(
                f"No se pudo descargar {label} y no hay ningún vintage "
                f"guardado: {exc}"
            )
        return False


# --- Botones ----------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Descargar Niño 3.4", type="primary"):
        _download_one("Niño 3.4")
with col2:
    if st.button("Descargar RONI", type="primary"):
        _download_one("RONI")
with col3:
    if st.button("Descargar XM", type="primary",
                 help="Descarga año por año desde 2000; tarda un poco."):
        _download_one("XM")
with col4:
    if st.button("Descargar todo"):
        results = {label: _download_one(label) for label in ADAPTERS}
        ok = [l for l, r in results.items() if r]
        bad = [l for l, r in results.items() if not r]
        resumen = f"Resumen: {len(ok)}/{len(results)} descargas exitosas."
        if bad:
            st.warning(f"{resumen} Fallaron: {', '.join(bad)}.")
        else:
            st.success(resumen)

# --- Vintages por índice ----------------------------------------------------
st.subheader("Vintages disponibles")
vintage_cols = st.columns(len(ADAPTERS))
series: dict[str, pd.DataFrame] = {}
for col, (label, (index, _)) in zip(vintage_cols, ADAPTERS.items()):
    with col:
        st.markdown(f"**{label}** (`{index}`)")
        disponibles = vintages.list_vintages(index)
        if disponibles:
            st.dataframe(
                pd.DataFrame({"vintage": [v.isoformat() for v in disponibles]}),
                hide_index=True,
            )
            series[label] = vintages.load(index)
        else:
            st.info("Sin vintages aún.")

# --- Gráfica de dos ejes ----------------------------------------------------
if series:
    st.subheader("Series (vintage más reciente de cada índice)")

    min_date = min(df["date"].min() for df in series.values()).date()
    max_date = max(df["date"].max() for df in series.values()).date()
    rango = st.slider(
        "Rango de fechas",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM",
    )
    lo, hi = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])

    fig = go.Figure()
    axis_for = {"Niño 3.4": "y", "RONI": "y", "XM": "y2"}
    for label, df in series.items():
        view = df[(df["date"] >= lo) & (df["date"] <= hi)]
        fig.add_trace(
            go.Scatter(
                x=view["date"], y=view["value"], mode="lines",
                name=label, yaxis=axis_for[label],
            )
        )

    # Umbrales de El Niño (+0.5) y La Niña (-0.5), sobre el eje izquierdo.
    if "Niño 3.4" in series or "RONI" in series:
        fig.add_hline(y=0.5, line_dash="dash", line_color="red",
                      annotation_text="El Niño (+0.5)")
        fig.add_hline(y=-0.5, line_dash="dash", line_color="blue",
                      annotation_text="La Niña (-0.5)")

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis=dict(title="Anomalía ENSO (°C)"),
        yaxis2=dict(
            title="Precio de bolsa (COP/kWh)",
            overlaying="y", side="right", showgrid=False,
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30),
    )
    st.plotly_chart(fig, width="stretch")

    ultimos = " · ".join(
        f"{label}: {df['date'].iloc[-1].date()} = {df['value'].iloc[-1]:.2f}"
        for label, df in series.items()
    )
    st.caption(f"Últimos valores — {ultimos}")
else:
    st.info("Aún no hay datos. Usa los botones de descarga.")
