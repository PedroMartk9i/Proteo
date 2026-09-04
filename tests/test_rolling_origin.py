"""Tests del backtest de origen móvil. Series sintéticas, sin red."""

from __future__ import annotations

import numpy as np
import pandas as pd

from proteo.backtest.rolling_origin import run_backtest
from proteo.models.naive import Naive


def _y(n: int = 30) -> pd.Series:
    rng = np.random.default_rng(3)
    idx = pd.date_range("2020-01-01", periods=n, freq="MS")
    return pd.Series(100 + rng.normal(0, 5, n).cumsum(), index=idx, name="price")


def test_row_count_and_dates():
    n, initial_train, horizons = 30, 20, [1, 2, 3]
    y = _y(n)
    results = run_backtest(Naive, y, initial_train=initial_train, horizons=horizons)

    expected_rows = (n - max(horizons) - initial_train + 1) * len(horizons)
    assert len(results) == expected_rows

    # target_date == origin + horizon meses, en todas las filas.
    for _, row in results.iterrows():
        expected = row["origin"] + pd.DateOffset(months=row["horizon"])
        assert row["target_date"] == expected


def test_naive_forecast_is_last_train_value():
    y = _y(30)
    results = run_backtest(Naive, y, initial_train=20, horizons=[1, 2, 3])

    # El pronóstico de Naive en cada fila es el valor de y en el origen.
    for _, row in results.iterrows():
        assert row["forecast"] == y.loc[row["origin"]]
        assert row["actual"] == y.loc[row["target_date"]]
    assert (results["model"] == "naive").all()
    assert not results["assumed_exog"].any()


def test_assumed_exog_pattern_with_lag2():
    # Con lag=2: pasos 1 y 2 usan exógena observada, del 3 en adelante
    # supuesta por persistencia, en TODOS los orígenes.
    y = _y(30)
    X = pd.DataFrame(
        {"roni_lag2": np.arange(30, dtype=float)}, index=y.index
    )
    results = run_backtest(
        Naive, y, X=X, initial_train=20, horizons=[1, 2, 3, 4]
    )
    pattern = results.groupby("horizon")["assumed_exog"].unique()
    assert list(pattern.loc[1]) == [False]
    assert list(pattern.loc[2]) == [False]
    assert list(pattern.loc[3]) == [True]
    assert list(pattern.loc[4]) == [True]


def test_rolling_window_and_label():
    y = _y(30)
    results = run_backtest(
        Naive, y, initial_train=20, horizons=[1],
        window="rolling", label="naive_v2",
    )
    assert (results["model"] == "naive_v2").all()
    # Con ventana fija el naive sigue pronosticando el último valor.
    for _, row in results.iterrows():
        assert row["forecast"] == y.loc[row["origin"]]
