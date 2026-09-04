"""Bloques de interfaz compartidos por todas las páginas.

Requisito: la página debe llamar ``theme.inject_css()`` antes de usar
estos componentes (las clases ``pt-*`` viven en ese CSS).
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from app.theme import PALETTE


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


def appbar(subtitle: str | None = None, vintage: date | None = None) -> None:
    """Barra superior: wordmark Proteo en mono, LED y sello del vintage."""
    extra = f'<span class="pt-stamp">{subtitle}</span>' if subtitle else ""
    stamp = vintage_stamp("más reciente", vintage) if vintage else extra
    st.markdown(
        f'<div class="pt-appbar"><span class="pt-wordmark">Proteo</span>'
        f"{led(vintage)}{stamp}</div>",
        unsafe_allow_html=True,
    )


def section(title: str, help: str | None = None) -> None:
    """Título de sección en sans 600, sentence case."""
    st.markdown(f'<div class="pt-section">{title}</div>', unsafe_allow_html=True)
    if help:
        st.markdown(f'<p class="pt-help">{help}</p>', unsafe_allow_html=True)
