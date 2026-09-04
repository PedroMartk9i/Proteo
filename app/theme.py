"""Sistema de diseño "caja beige" de Proteo.

Fuente de verdad visual: docs/style_tile.html (los tokens de :root usan
estos mismos nombres). Variante B activada con BRUTAL_ACCENT = True:
sombras duras 4px 4px 0 en color tinta, radio 4 px y botón primario que
se hunde al pulsar. Con False queda la variante A (plana, radio 6 px).
Ningún color literal vive fuera de este módulo.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --- Tokens (mismos nombres que en docs/style_tile.html) --------------------
PALETTE = {
    "papel": "#EFE7D5",   # fondo general: plástico crema de la caja beige
    "panel": "#E1D8C3",   # paneles, barra lateral, cabeceras
    "linea": "#2B2925",   # texto, bordes, serie de precio
    "tinta": "#7A736A",   # etiquetas, ejes, grilla, sombras (variante B)
    "nino": "#E8792B",    # acción primaria, RONI positivo, fase El Niño
    "nina": "#2F8F8A",    # RONI negativo, fase La Niña, foco de teclado
    "banda": "rgba(232,121,43,.18)",
    "banda_nina": "rgba(47,143,138,.16)",
}

FONT_UI = "IBM Plex Sans"
FONT_MONO = "IBM Plex Mono"

# Único interruptor entre variantes: True = B (sombras duras, radio 4),
# False = A (plana, radio 6). Todo lo demás es idéntico.
BRUTAL_ACCENT: bool = True

# Pilas con fallback del sistema para cuando no haya red.
STACK_UI = f'"{FONT_UI}", system-ui, -apple-system, "Segoe UI", sans-serif'
STACK_MONO = f'"{FONT_MONO}", ui-monospace, "Cascadia Mono", Consolas, monospace'

_RADIUS = "4px" if BRUTAL_ACCENT else "6px"
_GRID = "rgba(122,115,106,.25)"  # tinta al 25 %

PLOTLY_CONFIG = {"displayModeBar": False}


def inject_css() -> None:
    """Inyecta el CSS del sistema. Llamar UNA vez al inicio de cada página.

    Nota: el spec pedía una bandera en st.session_state para inyectar una
    sola vez por sesión, pero Streamlit vacía el DOM en cada rerun: con
    esa bandera la página quedaría sin estilo tras el primer clic. Por
    eso se inyecta en cada ejecución del script (es barato) y la regla
    de uso es "una llamada por página, en la cabecera".
    """
    shadow_css = ""
    if BRUTAL_ACCENT:
        shadow_css = f"""
        /* Variante B: sombras duras en tinta; solo el primario en línea. */
        .stButton button, .stDownloadButton button,
        [data-testid="stMetric"], .pt-card, .pt-appbar, .pt-datahead {{
            box-shadow: 4px 4px 0 {PALETTE['tinta']};
        }}
        button[kind="primary"], [data-testid="stBaseButton-primary"] {{
            box-shadow: 4px 4px 0 {PALETTE['linea']} !important;
        }}
        .stButton button:active, .stDownloadButton button:active {{
            transform: translate(2px, 2px);
            box-shadow: 2px 2px 0 {PALETTE['tinta']};
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .stButton button, .stDownloadButton button {{
                transition: transform .08s, box-shadow .08s;
            }}
        }}
        """

    st.markdown(
        f"""<style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

        html, body, [data-testid="stAppViewContainer"] {{
            font-family: {STACK_UI};
        }}

        /* Botones: borde 2 px, texto oscuro SIEMPRE (nunca blanco sobre
           naranja: no cumple contraste). */
        .stButton button, .stDownloadButton button {{
            font-family: {STACK_UI};
            font-weight: 600;
            font-size: 14px;
            border: 2px solid {PALETTE['linea']} !important;
            border-radius: {_RADIUS} !important;
            background: {PALETTE['papel']};
            color: {PALETTE['linea']} !important;
        }}
        button[kind="primary"], [data-testid="stBaseButton-primary"] {{
            background: {PALETTE['nino']} !important;
            color: {PALETTE['linea']} !important;
        }}
        .stButton button:disabled, .stDownloadButton button:disabled {{
            color: {PALETTE['tinta']} !important;
            border-color: {PALETTE['tinta']} !important;
            box-shadow: none;
        }}
        .stButton button:focus-visible, .stDownloadButton button:focus-visible,
        a:focus-visible, [data-testid="stSelectbox"] *:focus-visible {{
            outline: 3px solid {PALETTE['nina']} !important;
            outline-offset: 2px;
        }}

        /* Métricas: tarjeta con borde 2 px, valor en mono. */
        [data-testid="stMetric"] {{
            border: 2px solid {PALETTE['linea']};
            border-radius: {_RADIUS};
            background: {PALETTE['papel']};
            padding: 10px 12px;
        }}
        [data-testid="stMetricValue"] {{
            font-family: {STACK_MONO};
            font-size: 19px;
            font-weight: 500;
        }}
        [data-testid="stMetricLabel"] p {{
            font-family: {STACK_MONO};
            font-size: 11px;
            letter-spacing: .06em;
            text-transform: uppercase;
            color: {PALETTE['tinta']};
        }}

        /* Etiquetas de controles: mono, mayúsculas, 11 px. */
        [data-testid="stWidgetLabel"] p {{
            font-family: {STACK_MONO};
            font-size: 11px;
            letter-spacing: .06em;
            text-transform: uppercase;
            color: {PALETTE['tinta']};
        }}

        /* Tablas y números en mono. */
        [data-testid="stDataFrame"] {{
            font-family: {STACK_MONO};
        }}

        /* Componentes propios (app/components.py). */
        .pt-appbar {{
            display: flex; align-items: center; gap: 10px;
            padding: 10px 12px;
            border: 2px solid {PALETTE['linea']};
            border-radius: {_RADIUS};
            background: {PALETTE['panel']};
            margin-bottom: 16px;
        }}
        .pt-wordmark {{
            font-family: {STACK_MONO};
            font-weight: 500; font-size: 18px;
            color: {PALETTE['linea']};
        }}
        .pt-led {{
            width: 10px; height: 10px; border-radius: 50%;
            box-shadow: inset 0 0 0 2px rgba(43,41,37,.18);
            flex: none; display: inline-block;
        }}
        .pt-stamp {{
            margin-left: auto;
            font-family: {STACK_MONO};
            font-size: 12px; color: {PALETTE['tinta']};
        }}
        .pt-card {{
            border: 2px solid {PALETTE['linea']};
            border-radius: {_RADIUS};
            padding: 10px 12px;
            background: {PALETTE['papel']};
            min-width: 0;
        }}
        .pt-card .pt-k {{ font-size: 12px; color: {PALETTE['tinta']}; }}
        .pt-card .pt-v {{
            font-family: {STACK_MONO};
            font-size: 19px; font-weight: 500; margin-top: 2px;
            white-space: nowrap; color: {PALETTE['linea']};
        }}
        .pt-card .pt-v small {{
            font-size: 12px; color: {PALETTE['tinta']}; font-weight: 400;
        }}
        .pt-datahead {{
            display: flex; align-items: center; gap: 10px;
            padding: 10px 12px;
            border: 2px solid {PALETTE['linea']};
            border-radius: {_RADIUS};
            background: {PALETTE['panel']};
            margin-bottom: 8px;
        }}
        .pt-datahead .pt-name {{
            font-weight: 600; font-size: 14px; color: {PALETTE['linea']};
        }}
        .pt-section {{
            font-family: {STACK_UI};
            font-weight: 600; font-size: 18px;
            margin: 18px 0 4px; color: {PALETTE['linea']};
        }}
        .pt-help {{
            font-size: 13px; color: {PALETTE['tinta']}; margin: 0 0 8px;
        }}
        {shadow_css}
        </style>""",
        unsafe_allow_html=True,
    )


def plotly_template() -> None:
    """Registra el template "proteo" y lo fija como default de Plotly."""
    template = go.layout.Template()
    template.layout = dict(
        paper_bgcolor=PALETTE["papel"],
        plot_bgcolor=PALETTE["papel"],
        font=dict(family=STACK_MONO, color=PALETTE["linea"], size=12),
        colorway=[PALETTE["linea"], PALETTE["nino"], PALETTE["nina"], PALETTE["tinta"]],
        xaxis=dict(
            gridcolor=_GRID, linecolor=PALETTE["linea"],
            tickfont=dict(family=STACK_MONO, size=11, color=PALETTE["tinta"]),
            title=dict(font=dict(family=STACK_MONO, size=11, color=PALETTE["tinta"])),
        ),
        yaxis=dict(
            gridcolor=_GRID, linecolor=PALETTE["linea"],
            tickfont=dict(family=STACK_MONO, size=11, color=PALETTE["tinta"]),
            title=dict(font=dict(family=STACK_MONO, size=11, color=PALETTE["tinta"])),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            font=dict(family=STACK_MONO, size=11, color=PALETTE["tinta"]),
        ),
        margin=dict(t=40, r=10, b=40, l=50),
        hovermode="x unified",
    )
    template.data.scatter = [go.Scatter(line=dict(width=2))]
    pio.templates["proteo"] = template
    pio.templates.default = "proteo"


def add_enso_bands(fig: go.Figure, roni: pd.Series, threshold: float = 0.5) -> go.Figure:
    """Sombreado de fases ENSO: naranja donde RONI ≥ threshold, teal
    donde RONI ≤ -threshold, agrupando meses consecutivos en un solo
    rectángulo. ``roni`` es una serie indexada por fecha mensual."""
    s = roni.dropna().sort_index()
    for condition, color in (
        (s >= threshold, PALETTE["banda"]),
        (s <= -threshold, PALETTE["banda_nina"]),
    ):
        groups = (condition != condition.shift()).cumsum()
        for _, block in s[condition].groupby(groups[condition]):
            fig.add_vrect(
                x0=block.index[0],
                x1=block.index[-1] + pd.DateOffset(months=1),
                fillcolor=color,
                line_width=0,
                layer="below",
            )
    return fig


def add_threshold_lines(fig: go.Figure, y=(0.5, -0.5), yref: str = "y2") -> go.Figure:
    """Líneas discontinuas en tinta sobre los umbrales ENSO del eje de
    índices (``yref="y2"`` cuando los índices van al eje derecho)."""
    for value in y:
        fig.add_shape(
            type="line",
            xref="paper", x0=0, x1=1,
            yref=yref, y0=value, y1=value,
            line=dict(color=PALETTE["tinta"], width=1, dash="dash"),
        )
    return fig
