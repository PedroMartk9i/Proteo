"""Tests del registro de pronósticos. Usan tmp_path, sin red."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from proteo.forecasts import registry


def _forecast_df(start: str, h: int = 3, base: float = 100.0) -> pd.DataFrame:
    dates = pd.date_range(start, periods=h, freq="MS")
    means = base + np.arange(h, dtype=float)
    return pd.DataFrame(
        {
            "date": dates,
            "mean": means,
            "lower": means - 10,
            "upper": means + 10,
            "assumed_exog": [False, False, True][:h],
        }
    )


CONFIG = {"model": "sarimax", "order": [1, 1, 1], "exog": "roni", "lag": 2}


def test_issue_two_forecasts_and_verify_only_first(tmp_path):
    id1 = registry.issue(
        _forecast_df("2026-09-01"), CONFIG, date(2026, 9, 3),
        notes="primero", root=tmp_path,
    )
    id2 = registry.issue(
        _forecast_df("2026-12-01"), CONFIG, date(2026, 12, 1),
        notes="segundo", root=tmp_path,
    )
    assert id1 == "20260903-sarimax-01"
    assert id2 == "20261201-sarimax-01"
    assert (tmp_path / f"{id1}.json").exists()
    assert registry.load_config(id1, root=tmp_path)["notes"] == "primero"

    # La serie real solo cubre los meses del primer pronóstico.
    actual = pd.Series(
        [105.0, 90.0, 101.0],
        index=pd.date_range("2026-09-01", periods=3, freq="MS"),
    )
    verified = registry.verify(actual, date(2026, 12, 15), root=tmp_path)
    assert len(verified) == 3
    assert set(verified["forecast_id"]) == {id1}

    # El segundo sigue completamente pendiente.
    pend = registry.pending(root=tmp_path)
    assert set(pend["forecast_id"]) == {id2}
    assert len(pend) == 3


def test_verified_rows_are_immutable(tmp_path):
    registry.issue(_forecast_df("2026-09-01"), CONFIG, date(2026, 9, 3), root=tmp_path)
    actual_v1 = pd.Series(
        [105.0], index=pd.date_range("2026-09-01", periods=1, freq="MS")
    )
    first = registry.verify(actual_v1, date(2026, 10, 5), root=tmp_path)
    assert first["actual"].iloc[0] == 105.0

    # Un vintage posterior trae el valor REVISADO: la fila no cambia.
    actual_v2 = pd.Series(
        [999.0, 90.0], index=pd.date_range("2026-09-01", periods=2, freq="MS")
    )
    second = registry.verify(actual_v2, date(2026, 11, 5), root=tmp_path)
    # Solo se verificó la fila nueva (octubre), no la de septiembre.
    assert len(second) == 1
    assert second["target_date"].iloc[0] == pd.Timestamp("2026-10-01")

    full = registry.load(root=tmp_path)
    sept = full[full["target_date"] == "2026-09-01"]
    assert sept["actual"].iloc[0] == 105.0  # NO 999
    assert sept["verified_at"].iloc[0] == "2026-10-05"


def test_scorecard_by_hand(tmp_path):
    # Pronóstico: medias 100, 101, 102 con banda ±10.
    registry.issue(_forecast_df("2026-09-01"), CONFIG, date(2026, 9, 3), root=tmp_path)
    # Reales: 105 (dentro, error 5), 90 (fuera, error 11), 101 (dentro, error 1).
    actual = pd.Series(
        [105.0, 90.0, 101.0],
        index=pd.date_range("2026-09-01", periods=3, freq="MS"),
    )
    registry.verify(actual, date(2026, 12, 15), root=tmp_path)

    card = registry.scorecard(by=("model",), root=tmp_path)
    assert len(card) == 1
    row = card.iloc[0]
    assert row["n"] == 3
    assert row["mae"] == (5 + 11 + 1) / 3
    assert np.isclose(row["rmse"], np.sqrt((25 + 121 + 1) / 3))
    assert np.isclose(row["coverage_pct"], 200 / 3)

    # Por horizonte: una fila por paso con n=1.
    by_h = registry.scorecard(root=tmp_path)
    assert len(by_h) == 3
    assert (by_h["n"] == 1).all()


def test_empty_registry(tmp_path):
    assert registry.load(root=tmp_path).empty
    assert registry.pending(root=tmp_path).empty
    assert registry.scorecard(root=tmp_path).empty
    actual = pd.Series([1.0], index=pd.date_range("2026-09-01", periods=1, freq="MS"))
    assert registry.verify(actual, date(2026, 9, 3), root=tmp_path).empty
