"""Tests de ``proteo.dataset``. Series sintéticas, sin red."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from proteo.dataset import build_dataset, inverse_transform

VINTAGE = date(2026, 9, 3)


def _contract_df(dates, values, index_name) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates).astype("datetime64[ns]"),
            "value": np.asarray(values, dtype="float64"),
            "index": index_name,
            "source": "test",
            "vintage": VINTAGE,
        }
    )


@pytest.fixture
def price():
    dates = pd.date_range("2020-01-01", periods=24, freq="MS")
    return _contract_df(dates, np.arange(24, dtype=float) + 100.0, "xm_precio_bolsa")


@pytest.fixture
def exog():
    # Exógena sintética: el valor es el número de mes (1..12, 1..12).
    dates = pd.date_range("2020-01-01", periods=24, freq="MS")
    return _contract_df(dates, [d.month for d in dates], "roni")


def test_lag_is_by_calendar(price, exog):
    y, X = build_dataset(price, exog, lag=2)
    # X en 2020-03-01 vale el exog de 2020-01-01 (mes 1).
    assert X.loc["2020-03-01", "roni_lag2"] == 1.0
    assert X.loc["2020-07-01", "roni_lag2"] == 5.0
    assert list(X.columns) == ["roni_lag2"]
    assert y.name == "price"


def test_lag_survives_missing_month(price, exog):
    # Se borra un mes en medio: el rezago sigue siendo por calendario,
    # no por posiciones de filas.
    exog_holed = exog[exog["date"] != "2020-04-01"].reset_index(drop=True)
    y, X = build_dataset(price, exog_holed, lag=2)

    # 2020-06 necesitaba el exog de 2020-04 (borrado): la fila cae.
    assert pd.Timestamp("2020-06-01") not in X.index
    # Las demás no se corren: 2020-07 sigue llevando el mes 5.
    assert X.loc["2020-07-01", "roni_lag2"] == 5.0
    assert X.loc["2020-03-01", "roni_lag2"] == 1.0


def test_add_squared(price, exog):
    _, X = build_dataset(price, exog, lag=2, add_squared=True)
    assert list(X.columns) == ["roni_lag2", "roni_lag2_sq"]
    assert (X["roni_lag2_sq"] == X["roni_lag2"] ** 2).all()


def test_log_target_roundtrip(price):
    y_level, _ = build_dataset(price)
    y_log, _ = build_dataset(price, log_target=True)
    recovered = inverse_transform(y_log, log_target=True)
    assert np.allclose(recovered.to_numpy(), y_level.to_numpy(), atol=1e-9)
    # Sin log, inverse_transform es identidad.
    assert inverse_transform(y_level, log_target=False).equals(y_level)


def test_crop_and_no_exog(price):
    y, X = build_dataset(price, start="2020-06-01", end="2020-09-01")
    assert X is None
    assert y.index[0] == pd.Timestamp("2020-06-01")
    assert y.index[-1] == pd.Timestamp("2020-09-01")
    assert len(y) == 4
