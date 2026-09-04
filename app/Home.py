"""Portada de Proteo."""

import sys
from pathlib import Path

# Permite importar ``proteo`` y ``app`` al correr desde la raíz del repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from app import components, theme
from proteo.store import vintages

st.set_page_config(page_title="Proteo", layout="wide")
theme.inject_css()

INDICES = [
    ("Niño 3.4", "nino34"),
    ("RONI", "roni"),
    ("Precio de bolsa", "xm_precio_bolsa"),
]

# Barra superior con el vintage más reciente de cualquier índice.
all_vintages = [
    v for _, index in INDICES for v in vintages.list_vintages(index)
]
latest = max(all_vintages) if all_vintages else None
components.appbar(vintage=latest)

st.markdown(
    "Estudio visual de la relación entre el ENSO y el precio de bolsa de la "
    "energía en Colombia: datos con vintages, SARIMAX con RONI como exógena, "
    "backtest honesto y pronósticos verificados contra lo observado."
)

components.section("Datos disponibles")
cols = st.columns(len(INDICES))
for col, (name, index) in zip(cols, INDICES):
    with col:
        available = vintages.list_vintages(index)
        components.data_header(name, index, available[-1] if available else None)

st.page_link("pages/1_Datos.py", label="Abrir la página Datos")

st.markdown(
    '<p class="pt-help">Pedro Martínez, UNAB, Bucaramanga.</p>',
    unsafe_allow_html=True,
)
