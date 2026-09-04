"""Tests del adaptador XM. Nunca tocan la red: solo ``aggregate_monthly()``
con el crudo de ``examples/`` como entrada y el promedio mensual de
``examples/`` como verdad de referencia.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from proteo.data.xm import INDEX, SOURCE, aggregate_monthly
from proteo.schema import validate

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
RAW_FILE = EXAMPLES / "precios_bolsa_nacional.csv"
TRUTH_FILE = EXAMPLES / "promedio_mensual.csv"

VINTAGE = date(2026, 9, 3)


@pytest.fixture(scope="module")
def df_monthly() -> pd.DataFrame:
    raw = pd.read_csv(RAW_FILE, encoding="utf-8-sig")
    return aggregate_monthly(raw, VINTAGE)


def test_aggregate_monthly_reproduces_truth_file(df_monthly):
    truth = pd.read_csv(TRUTH_FILE, encoding="utf-8-sig")
    # El archivo de la verdad trae fechas MM/DD/YYYY, primer día del mes.
    truth["date"] = pd.to_datetime(truth["Date"], format="%m/%d/%Y")
    expected = truth.set_index("date")["Monthly Average"]

    computed = df_monthly.set_index("date")["value"]
    common = computed.index.intersection(expected.index)
    assert len(common) > 0
    for d in common:
        assert computed.loc[d] == pytest.approx(expected.loc[d], abs=1e-6)


def test_output_passes_validate(df_monthly):
    validate(df_monthly)
    assert (df_monthly["index"] == INDEX).all()
    assert (df_monthly["source"] == SOURCE).all()
