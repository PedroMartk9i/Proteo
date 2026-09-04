"""Bloques de interfaz compartidos por todas las páginas.

Requisito: la página debe llamar ``theme.inject_css()`` antes de usar
estos componentes (las clases ``pt-*`` viven en ese CSS).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import streamlit as st

from app.theme import PALETTE, STACK_MONO

STATIC = Path(__file__).resolve().parent / "static"


def brand_lockup(height: int = 40, wordmark: bool = True) -> None:
    """Marca de Proteo inline (SVG nítido a cualquier zoom) con el
    wordmark en mono a la derecha, alineado a la línea base.

    El SVG se inserta inline y no con st.image para que escale nítido y
    lleve siempre el color de tinta del sistema: cualquier fill que
    traiga el archivo se reemplaza por PALETTE["linea"] AL LEERLO (el
    archivo no se edita). El bloque <metadata> se descarta para no
    inflar el HTML.
    """
    svg = (STATIC / "logo.svg").read_text(encoding="utf-8")
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
    svg = re.sub(r'fill="#[0-9A-Fa-f]{3,8}"', f'fill="{PALETTE["linea"]}"', svg)
    svg = svg.replace("<svg ", f'<svg height="{height}" ', 1)

    gap = round(height * 0.3)
    font_size = round(height * 0.45)
    wordmark_html = (
        f'<span style="font-family:{STACK_MONO};font-weight:500;'
        f'font-size:{font_size}px;line-height:1;'
        f'color:{PALETTE["linea"]}">Proteo</span>'
        if wordmark else ""
    )
    st.markdown(
        f'<div style="display:flex;align-items:flex-end;gap:{gap}px">'
        f"{svg}{wordmark_html}</div>",
        unsafe_allow_html=True,
    )


def dot(color_key: str) -> str:
    """Punto de 10 px (HTML) en un color de la paleta, por nombre."""
    return f'<span class="pt-led" style="background:{PALETTE[color_key]}"></span>'


def phase_led(phase: str) -> str:
    """LED por fase ENSO: nino (naranja), nina (teal), neutral (tinta)."""
    return dot({"nino": "nino", "nina": "nina"}.get(phase, "tinta"))


def status_led(verified: bool) -> str:
    """LED de estado de un pronóstico: teal verificado, tinta pendiente."""
    return dot("nina" if verified else "tinta")


def control_header(label: str, value: str) -> None:
    """Cabecera de grupo de controles: etiqueta mono arriba a la
    izquierda y valor actual en mono a la derecha."""
    st.markdown(
        f'<div class="pt-ctrl"><span class="pt-l">{label}</span>'
        f'<span class="pt-v">{value}</span></div>',
        unsafe_allow_html=True,
    )


def led(vintage: date | None) -> str:
    """Punto de estado de 10 px (HTML). Naranja si el vintage es de hoy,
    teal si tiene menos de 7 días, tinta si es más viejo o no existe."""
    if vintage is None:
        color = PALETTE["tinta"]
    elif vintage == date.today():
        color = PALETTE["nino"]
    elif (date.today() - vintage).days < 7:
        color = PALETTE["nina"]
    else:
        color = PALETTE["tinta"]
    return f'<span class="pt-led" style="background:{color}"></span>'


def vintage_stamp(index: str, fecha: date | None) -> str:
    """Sello ``vintage 2026-09-03`` en mono (HTML)."""
    text = f"vintage {fecha.isoformat()}" if fecha else "sin vintage"
    return f'<span class="pt-stamp" title="{index}">{text}</span>'


def metric_card(label: str, value: str, hint: str | None = None) -> None:
    """Tarjeta con borde de 2 px, valor en mono de 19 px, hint en tinta."""
    hint_html = f" <small>{hint}</small>" if hint else ""
    st.markdown(
        f'<div class="pt-card"><div class="pt-k">{label}</div>'
        f'<div class="pt-v">{value}{hint_html}</div></div>',
        unsafe_allow_html=True,
    )


def data_header(name: str, index: str, vintage: date | None) -> None:
    """Fila con el nombre del índice, el LED de frescura y el sello del
    vintage. Se reutiliza en todas las páginas."""
    st.markdown(
        f'<div class="pt-datahead"><span class="pt-name">{name}</span>'
        f"{led(vintage)}{vintage_stamp(index, vintage)}</div>",
        unsafe_allow_html=True,
    )


def section(title: str, help: str | None = None) -> None:
    """Título de sección en sans 600, sentence case."""
    st.markdown(f'<div class="pt-section">{title}</div>', unsafe_allow_html=True)
    if help:
        st.markdown(f'<p class="pt-help">{help}</p>', unsafe_allow_html=True)
