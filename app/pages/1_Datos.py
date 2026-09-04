"""Página Datos: descargar los tres índices, ver vintages y graficar."""

import sys
from pathlib import Path

# Permite importar ``proteo`` y ``app`` al correr desde la raíz del repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import components, theme
from app.theme import PALETTE, PLOTLY_CONFIG
from proteo.data import nino34, roni, xm
from proteo.store import vintages

theme.page_setup("Datos")

st.title("Datos")
st.markdown(
    '<p class="pt-help">Descarga con un clic, guardada como vintage '
    "(copia fechada que nunca se sobrescribe).</p>",
    unsafe_allow_html=True,
)

# Etiqueta → (nombre de índice, función download). XM tarda más: descarga
# año por año desde 2000.
ADAPTERS = {
    "Niño 3.4": (nino34.INDEX, nino34.download),
    "RONI": (roni.INDEX, roni.download),
    "Precio de bolsa": (xm.INDEX, xm.download),
}
DOWNLOAD_LABEL = {
    "Niño 3.4": "Descargar Niño 3.4",
    "RONI": "Descargar RONI",
    "Precio de bolsa": "Descargar XM",
}


def _download_one(label: str) -> bool:
    """Descarga un índice y reporta en pantalla. Devuelve True si funcionó."""
    index, download = ADAPTERS[label]
    try:
        with st.spinner(f"Descargando {label}…"):
            df = download()
        st.success(
            f"{label}: {len(df)} filas, de {df['date'].min().date()} a "
            f"{df['date'].max().date()}. Vintage {df['vintage'].iloc[0]}."
        )
        return True
    except Exception as exc:  # noqa: BLE001 — la red puede fallar de muchas formas
        disponibles = vintages.list_vintages(index)
        if disponibles:
            st.warning(
                f"No se pudo descargar {label}: {exc}. Se muestra el último "
                f"vintage disponible ({disponibles[-1]})."
            )
        else:
            st.error(
                f"No se pudo descargar {label} y no hay ningún vintage "
                f"guardado: {exc}. Revisa la conexión y vuelve a intentarlo."
            )
        return False


# --- Botones: un solo primario por página -----------------------------------
col_all, col1, col2, col3 = st.columns(4)
with col_all:
    if st.button("Descargar todo", type="primary"):
        results = {label: _download_one(label) for label in ADAPTERS}
        ok = [l for l, r in results.items() if r]
        bad = [l for l, r in results.items() if not r]
        resumen = f"{len(ok)}/{len(results)} descargas exitosas."
        if bad:
            st.warning(f"{resumen} Fallaron: {', '.join(bad)}.")
        else:
            st.success(resumen)
with col1:
    if st.button(DOWNLOAD_LABEL["Niño 3.4"]):
        _download_one("Niño 3.4")
with col2:
    if st.button(DOWNLOAD_LABEL["RONI"]):
        _download_one("RONI")
with col3:
    if st.button(DOWNLOAD_LABEL["Precio de bolsa"],
                 help="Descarga año por año desde 2000; tarda un poco."):
        _download_one("Precio de bolsa")

# --- Vintages por índice ----------------------------------------------------
components.section("Vintages disponibles")
vintage_cols = st.columns(len(ADAPTERS))
series: dict[str, pd.DataFrame] = {}
for col, (label, (index, _)) in zip(vintage_cols, ADAPTERS.items()):
    with col:
        disponibles = vintages.list_vintages(index)
        components.data_header(
            label, index, disponibles[-1] if disponibles else None
        )
        if disponibles:
            st.dataframe(
                pd.DataFrame({"vintage": pd.to_datetime(disponibles)}),
                hide_index=True,
                column_config={
                    "vintage": st.column_config.DateColumn(
                        "vintage", format="YYYY-MM-DD"
                    ),
                },
            )
            series[label] = vintages.load(index)
            # CSV con las cinco columnas del contrato; utf-8-sig para que
            # Excel lo abra bien con tildes.
            st.download_button(
                "Exportar CSV",
                series[label].to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{index}_{disponibles[-1].isoformat()}.csv",
                mime="text/csv",
                key=f"csv_{index}",
            )
        else:
            st.info(
                f"No hay vintage de {label} todavía. "
                f"Pulsa {DOWNLOAD_LABEL[label]}."
            )

# --- Gráfica: precio a la izquierda, índices ENSO a la derecha --------------
if series:
    components.section(
        "Series",
        help="Vintage más reciente de cada índice. Bandas: fases ENSO según RONI.",
    )

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

    def _view(label: str) -> pd.DataFrame:
        df = series[label]
        return df[(df["date"] >= lo) & (df["date"] <= hi)]

    fig = go.Figure()
    if "Precio de bolsa" in series:
        v = _view("Precio de bolsa")
        fig.add_trace(go.Scatter(
            x=v["date"], y=v["value"], mode="lines", name="Precio de bolsa",
            line=dict(color=PALETTE["linea"], width=2), yaxis="y",
        ))
    if "Niño 3.4" in series:
        v = _view("Niño 3.4")
        fig.add_trace(go.Scatter(
            x=v["date"], y=v["value"], mode="lines", name="Niño 3.4",
            line=dict(color=PALETTE["nino"], width=1.4), yaxis="y2",
        ))
    if "RONI" in series:
        v = _view("RONI")
        fig.add_trace(go.Scatter(
            x=v["date"], y=v["value"], mode="lines", name="RONI",
            line=dict(color=PALETTE["nina"], width=1.4), yaxis="y2",
        ))
        theme.add_enso_bands(fig, _view("RONI").set_index("date")["value"])

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis=dict(title="Precio de bolsa (COP/kWh)"),
        yaxis2=dict(
            title="Anomalía ENSO (°C)",
            overlaying="y", side="right", showgrid=False,
        ),
        height=430,
    )
    if "Niño 3.4" in series or "RONI" in series:
        theme.add_threshold_lines(fig)

    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    ultimos = " · ".join(
        f"{label}: {df['date'].iloc[-1].date()} = {df['value'].iloc[-1]:.2f}"
        for label, df in series.items()
    )
    st.markdown(
        f'<p class="pt-help">Últimos valores. {ultimos}</p>',
        unsafe_allow_html=True,
    )
else:
    st.info("No hay datos todavía. Pulsa Descargar todo.")
