"""Tests del adaptador RONI. Nunca tocan la red: solo ``parse()``."""

from __future__ import annotations

from datetime import date

import pandas as pd

from proteo.data.roni import INDEX, SEASON_MONTH, parse
from proteo.schema import validate

VINTAGE = date(2026, 9, 3)

# Cabecera y tres filas de ejemplo tal como están en CLAUDE.md.
FIXTURE_INLINE = """\
SEAS   YR  ANOM
DJF  1950 -1.19
JFM  1950 -1.08
MJJ  2026  0.98
"""


def test_parse_fixture_inline():
    df = parse(FIXTURE_INLINE, VINTAGE)

    assert len(df) == 3
    assert df["date"].tolist() == [
        pd.Timestamp("1950-01-01"),
        pd.Timestamp("1950-02-01"),
        pd.Timestamp("2026-06-01"),
    ]
    assert df["value"].tolist() == [-1.19, -1.08, 0.98]
    assert (df["index"] == INDEX).all()


def test_parse_full_year_of_seasons():
    # Un año sintético con las 12 temporadas debe producir 12 meses
    # consecutivos del mismo año, en orden.
    lines = ["SEAS   YR  ANOM"]
    for season in SEASON_MONTH:
        lines.append(f"{season}  2000  0.10")
    df = parse("\n".join(lines), VINTAGE)

    assert len(df) == 12
    expected = pd.date_range("2000-01-01", periods=12, freq="MS")
    assert df["date"].tolist() == list(expected)


def test_fixture_passes_validate():
    df = parse(FIXTURE_INLINE, VINTAGE)
    validate(df)
