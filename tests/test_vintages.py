"""Tests del almacén de vintages. Usan tmp_path, no tocan disco real."""

from __future__ import annotations

from datetime import date

import pandas as pd

from proteo.store import vintages


def _sample_df(vintage: date) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "value": [1.0, 2.0],
            "index": ["nino34", "nino34"],
            "source": ["http://x", "http://x"],
            "vintage": [vintage, vintage],
        }
    )


def test_two_vintages_listed_ascending_and_load_latest(tmp_path):
    old = date(2026, 9, 1)
    new = date(2026, 9, 3)

    # Se guardan en desorden a propósito.
    vintages.save_processed("nino34", new, _sample_df(new), root=tmp_path)
    vintages.save_processed("nino34", old, _sample_df(old), root=tmp_path)

    listed = vintages.list_vintages("nino34", root=tmp_path)
    assert listed == [old, new]

    # load() sin argumento devuelve el más reciente.
    latest = vintages.load("nino34", root=tmp_path)
    assert latest["vintage"].iloc[0] == new

    # load() con vintage explícito devuelve ese.
    older = vintages.load("nino34", vintage=old, root=tmp_path)
    assert older["vintage"].iloc[0] == old


def test_list_vintages_empty(tmp_path):
    assert vintages.list_vintages("nino34", root=tmp_path) == []


def test_save_raw_writes_text(tmp_path):
    path = vintages.save_raw("nino34", date(2026, 9, 3), "hola mundo", root=tmp_path)
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "hola mundo"
    assert path.suffix == ".txt"
