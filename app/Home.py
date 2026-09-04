"""Portada de Proteo."""

import sys
from pathlib import Path

# Permite importar el paquete ``proteo`` al correr ``streamlit run app/Home.py``.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

st.set_page_config(page_title="Proteo", page_icon="🌊", layout="wide")

st.title("🌊 Proteo")

st.markdown(
    "Estudio visual de **ENSO** y el **precio de bolsa** en Colombia: descarga "
    "los índices del Niño y el precio nacional, entrena modelos SARIMAX con "
    "RONI como regresor exógeno y verifica cada pronóstico contra lo observado."
)

st.subheader("Páginas")
st.markdown(
    """
    - **Datos** — descargar índices y precio, guardar vintages y graficar.
    - **Entrenar** — ajustar SARIMAX, mover parámetros y ver el resultado.
    - **Backtest** — origen móvil, métricas por horizonte y Diebold-Mariano.
    - **Pronósticos** — emitir por temporada, registrar y verificar contra lo observado.
    """
)

st.caption("Autor: Pedro Martínez (UNAB, Bucaramanga).")
