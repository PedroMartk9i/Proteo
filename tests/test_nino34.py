"""Tests del adaptador Niño 3.4. Nunca tocan la red: solo prueban
``parse()`` y ``validate()`` con fixtures inline y de ``examples/``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from proteo.data.nino34 import INDEX, parse
from proteo.schema import validate

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
RAW_FILE = EXAMPLES / "sstoi.indices_20260804T125949Z.txt"
FORMATTED_FILE = EXAMPLES / "Data-8-28.csv"

VINTAGE = date(2026, 9, 3)

# Cabecera y tres filas de ejemplo tal como están en CLAUDE.md.
FIXTURE_INLINE = """\
 YR   MON  NINO1+2  ANOM   NINO3    ANOM   NINO4    ANOM   NINO3.4  ANOM
1950   1   23.01   -1.55   23.56   -2.10   26.94   -1.38   24.55   -1.99
1950   2   24.32   -1.78   24.89   -1.52   26.67   -1.53   25.06   -1.69
2026   6   25.94    2.82   28.33    1.71   30.19    1.22   29.17    1.44
"""


def test_parse_fixture_inline():
    df = parse(FIXTURE_INLINE, VINTAGE)

    assert len(df) == 3
    assert df["date"].tolist() == [
        pd.Timestamp("1950-01-01"),
        pd.Timestamp("1950-02-01"),
        pd.Timestamp("2026-06-01"),
    ]
    assert df["value"].tolist() == [-1.99, -1.69, 1.44]
    assert (df["index"] == INDEX).all()
    # Pasa el contrato de datos.
    validate(df)


def test_parse_raw_file_matches_formatted():
    text = RAW_FILE.read_text(encoding="utf-8")
    df = parse(text, VINTAGE)

    # El parseo completo cumple el contrato.
    validate(df)

    # El archivo formateado de examples/ es la verdad de referencia.
    formatted = pd.read_csv(FORMATTED_FILE)
    formatted["date"] = pd.to_datetime(formatted["date"])
    expected = formatted.set_index("date")["nino34_anom"]

    parsed = df.set_index("date")["value"]
    common = parsed.index.intersection(expected.index)
    assert len(common) > 0
    for d in common:
        assert parsed.loc[d] == pytest.approx(expected.loc[d], abs=1e-9)


def test_validate_rejects_duplicate_dates():
    df = parse(FIXTURE_INLINE, VINTAGE)
    broken = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    broken = broken.sort_values("date").reset_index(drop=True)

    with pytest.raises(ValueError, match="duplicad"):
        validate(broken)
