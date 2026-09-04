"""Revisión de accesibilidad del sistema de diseño: todos los pares
texto/fondo en uso cumplen 4.5:1, el mínimo WCAG AA para texto normal.
"""

from __future__ import annotations

import pytest

from app.theme import PALETTE

# Pares (texto, fondo) en uso en la interfaz.
PAIRS = [
    ("linea", "papel"),   # texto principal sobre el fondo
    ("linea", "panel"),   # texto sobre paneles y cabeceras
    ("linea", "nino"),    # texto oscuro sobre el botón primario
    ("tinta", "papel"),   # etiquetas y ayudas sobre el fondo
    ("tinta", "panel"),   # etiquetas sobre paneles
    ("papel", "nina"),    # texto claro sobre teal (foco, chips)
]


def relative_luminance(hex_color: str) -> float:
    """Luminancia relativa sRGB según WCAG 2.x."""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))

    def linearize(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(color_a: str, color_b: str) -> float:
    """Relación de contraste WCAG entre dos colores hex."""
    lighter, darker = sorted(
        (relative_luminance(color_a), relative_luminance(color_b)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("text,background", PAIRS)
def test_pair_meets_aa(text: str, background: str):
    ratio = contrast_ratio(PALETTE[text], PALETTE[background])
    assert ratio >= 4.5, (
        f"{text}/{background} da {ratio:.2f}:1; el mínimo AA es 4.5:1"
    )
