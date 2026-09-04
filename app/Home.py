"""Portada de Proteo."""

import sys
from pathlib import Path

# Permite importar ``proteo`` y ``app`` al correr desde la raíz del repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from app import components, theme
from proteo.store import vintages

theme.page_setup("Inicio")

components.brand_lockup(height=96)
st.markdown(
    '<p style="max-width:60ch">Estudio visual de la relación entre el ENSO '
    "y el precio de bolsa de la energía en Colombia: datos con vintages, "
    "SARIMAX con RONI como exógena, backtest honesto y pronósticos "
    "verificados contra lo observado.</p>",
    unsafe_allow_html=True,
)

INDICES = [
    ("Niño 3.4", "nino34"),
    ("RONI", "roni"),
    ("Precio de bolsa", "xm_precio_bolsa"),
]

components.section("Datos disponibles")
cols = st.columns(len(INDICES))
for col, (name, index) in zip(cols, INDICES):
    with col:
        available = vintages.list_vintages(index)
        components.data_header(name, index, available[-1] if available else None)
