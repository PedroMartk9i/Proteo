"""Tests del modelo SARIMAX. Series simuladas con semilla fija, sin red."""

from __future__ import annotations

import numpy as np
import pandas as pd

from proteo.models.sarimax import SARIMAXModel


def _ar1(n: int = 300, phi: float = 0.7, seed: int = 7) -> pd.Series:
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, 1, n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + eps[t]
    idx = pd.date_range("2000-01-01", periods=n, freq="MS")
    return pd.Series(y, index=idx, name="price")


def test_ar1_recovers_phi():
    y = _ar1()
    model = SARIMAXModel(order=(1, 0, 0)).fit(y)
    summary = model.summary()

    phi_hat = summary["coefficients"]["ar.L1"]["coef"]
    assert 0.55 <= phi_hat <= 0.85
    assert summary["n_obs"] == 300
    assert summary["aic"] < summary["bic"]


def test_forecast_shape_and_dates():
    y = _ar1()
    fc = SARIMAXModel(order=(1, 0, 0)).fit(y).forecast(6)

    assert len(fc) == 6
    assert list(fc.columns) == ["date", "mean", "lower", "upper"]
    assert (fc["lower"] < fc["mean"]).all() and (fc["mean"] < fc["upper"]).all()
    assert list(fc["date"]) == list(
        pd.date_range(y.index[-1] + pd.DateOffset(months=1), periods=6, freq="MS")
    )


def test_exog_coefficient_recovered():
    rng = np.random.default_rng(11)
    n = 300
    idx = pd.date_range("2000-01-01", periods=n, freq="MS")
    x = pd.Series(rng.normal(0, 1, n), index=idx)
    y = pd.Series(2.0 * x + rng.normal(0, 0.5, n), index=idx, name="price")
    X = x.to_frame("roni_lag2")

    model = SARIMAXModel(order=(1, 0, 0)).fit(y, X)
    coef = model.summary()["coefficients"]["roni_lag2"]
    assert 1.8 <= coef["coef"] <= 2.2
    assert coef["pvalue"] < 0.01
