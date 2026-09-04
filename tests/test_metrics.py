"""Tests de las métricas del backtest. Datos sintéticos, sin red."""

from __future__ import annotations

import numpy as np
import pandas as pd

from proteo.backtest.metrics import by_enso_phase, by_horizon, coverage, skill


def _results() -> pd.DataFrame:
    rng = np.random.default_rng(5)
    origins = pd.date_range("2021-01-01", periods=10, freq="MS")
    rows = []
    for model, bias in [("a", 1.0), ("b", 2.0)]:
        for origin in origins:
            for h in (1, 2):
                actual = 100.0 + rng.normal(0, 1)
                rows.append(
                    {
                        "origin": origin,
                        "horizon": h,
                        "target_date": origin + pd.DateOffset(months=h),
                        "actual": actual,
                        "forecast": actual + bias,
                        "lower": -np.inf,
                        "upper": np.inf,
                        "assumed_exog": False,
                        "model": model,
                    }
                )
    return pd.DataFrame(rows)


def test_by_horizon_shapes_and_values():
    table = by_horizon(_results())
    assert set(table["model"]) == {"a", "b"}
    assert set(table["horizon"]) == {1, 2}
    assert (table["n"] == 10).all()
    # Sesgo constante: MAE == RMSE == |bias|.
    a = table[table["model"] == "a"]
    assert np.allclose(a["mae"], 1.0) and np.allclose(a["rmse"], 1.0)


def test_skill_of_model_against_itself_is_zero():
    table = skill(_results(), "a", "a")
    assert np.allclose(table["improvement_pct"], 0.0)


def test_skill_sign():
    # 'a' (error 1) mejora a 'b' (error 2) en 50%.
    table = skill(_results(), "a", "b")
    assert np.allclose(table["improvement_pct"], 50.0)


def test_coverage_infinite_intervals_is_100():
    table = coverage(_results())
    assert (table["coverage_pct"] == 100.0).all()


def test_by_enso_phase_classification():
    results = _results()
    origins = sorted(results["origin"].unique())
    # RONI: primeros 4 orígenes en El Niño, luego 3 en La Niña, resto neutral.
    values = [1.0] * 4 + [-1.0] * 3 + [0.0] * 3
    roni = pd.DataFrame(
        {
            "date": origins,
            "value": np.array(values, dtype="float64"),
            "index": "roni",
            "source": "test",
            "vintage": pd.Timestamp("2026-09-03").date(),
        }
    )
    table = by_enso_phase(results, roni)
    counts = table.groupby("phase")["n"].sum()
    # 2 modelos × 2 horizontes por origen.
    assert counts["nino"] == 4 * 4
    assert counts["nina"] == 3 * 4
    assert counts["neutral"] == 3 * 4
