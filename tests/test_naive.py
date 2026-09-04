"""Tests de los baselines naive. Series sintéticas, sin red."""

from __future__ import annotations

import numpy as np
import pandas as pd

from proteo.models.naive import Naive, SeasonalNaive


def _y(n: int = 36) -> pd.Series:
    rng = np.random.default_rng(42)
    idx = pd.date_range("2020-01-01", periods=n, freq="MS")
    return pd.Series(100 + rng.normal(0, 5, n).cumsum(), index=idx, name="price")


def test_naive_repeats_last_value():
    y = _y()
    fc = Naive().fit(y).forecast(6)

    assert len(fc) == 6
    assert (fc["mean"] == y.iloc[-1]).all()
    assert list(fc["date"]) == list(
        pd.date_range(y.index[-1] + pd.DateOffset(months=1), periods=6, freq="MS")
    )
    # Intervalo: crece con el horizonte y encierra la media.
    assert (fc["lower"] < fc["mean"]).all() and (fc["mean"] < fc["upper"]).all()
    widths = (fc["upper"] - fc["lower"]).to_numpy()
    assert (np.diff(widths) > 0).all()


def test_seasonal_naive_repeats_last_season():
    y = _y(36)
    fc = SeasonalNaive(period=12).fit(y).forecast(12)

    # Cada paso devuelve el valor de 12 meses atrás.
    expected = y.iloc[-12:].to_numpy()
    assert np.allclose(fc["mean"].to_numpy(), expected)
    assert (fc["lower"] < fc["mean"]).all() and (fc["mean"] < fc["upper"]).all()


def test_seasonal_naive_wraps_beyond_one_period():
    y = _y(36)
    fc = SeasonalNaive(period=12).fit(y).forecast(15)
    # Los pasos 13..15 repiten el mismo ciclo estacional.
    assert np.allclose(fc["mean"].iloc[12:].to_numpy(), fc["mean"].iloc[:3].to_numpy())
