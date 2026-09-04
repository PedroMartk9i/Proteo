"""Temporadas de tres meses con la convención de CPC (funciones puras).

Cada temporada se nombra por sus tres iniciales (DJF, JFM, …, NDJ) y
lleva el año de su MES CENTRAL, igual que la serie RONI: NDJ 2026 cubre
noviembre 2026, diciembre 2026 y enero 2027 (central diciembre 2026);
DJF 2027 cubre diciembre 2026, enero 2027 y febrero 2027.
"""

from __future__ import annotations

from datetime import date

# Mes central → temporada (la misma tabla de CLAUDE.md, invertida).
SEASON_BY_CENTRAL = {
    1: "DJF", 2: "JFM", 3: "FMA", 4: "MAM", 5: "AMJ", 6: "MJJ",
    7: "JJA", 8: "JAS", 9: "ASO", 10: "SON", 11: "OND", 12: "NDJ",
}


def _add_months(d: date, k: int) -> date:
    """Primer día del mes k meses después de d."""
    m = d.month - 1 + k
    return date(d.year + m // 12, m % 12 + 1, 1)


def season_label(target) -> str:
    """Etiqueta de la temporada centrada en la fecha dada.

    Acepta ``datetime.date`` o ``pandas.Timestamp`` (usa .month y .year).
    Ejemplo: 2026-12-01 → "NDJ 2026".
    """
    return f"{SEASON_BY_CENTRAL[target.month]} {target.year}"


def next_season(last_observed: date) -> tuple[str, list[date]]:
    """Primera temporada completa a pronosticar tras el último dato.

    La temporada objetivo empieza dos meses después del último dato
    observado: el mes inmediatamente siguiente queda como paso
    intermedio (horizonte 1), no pertenece a la temporada objetivo pero
    sí se pronostica. Ejemplo: último dato agosto 2026 →
    ("OND 2026", [2026-10-01, 2026-11-01, 2026-12-01]).
    """
    start = _add_months(last_observed, 2)
    months = [start, _add_months(start, 1), _add_months(start, 2)]
    return season_label(months[1]), months
