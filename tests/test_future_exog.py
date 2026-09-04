"""Tests de ``future_exog``. Series sintéticas, sin red."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from proteo.dataset import future_exog

VINTAGE = date(2026, 9, 3)


def _exog_df() -> pd.DataFrame:
    # Observada hasta 2020-12; el valor es el número de mes.
    dates = pd.date_range("2020-01-01", periods=12, freq="MS")
    return pd.DataFrame(
        {
            "date": dates.astype("datetime64[ns]"),
            "value": np.array([d.month for d in dates], dtype="float64"),
            "index": "roni",
            "source": "test",
            "vintage": VINTAGE,
        }
    )


def test_lag2_h6_two_observed_four_assumed():
    exog = _exog_df()
    out = future_exog(exog, last_date="2020-12-01", h=6, lag=2)

    assert len(out) == 6
    assert list(out.index) == list(
        pd.date_range("2021-01-01", periods=6, freq="MS")
    )

    # Pasos 1 y 2: el exog de t-2 ya está observado (nov y dic de 2020).
    assert out["assumed"].tolist() == [False, False, True, True, True, True]
    assert out["roni_lag2"].iloc[0] == 11.0
    assert out["roni_lag2"].iloc[1] == 12.0
    # Del paso 3 en adelante: persistencia del último observado (12).
    assert (out["roni_lag2"].iloc[2:] == 12.0).all()


def test_add_squared_matches_build_dataset_columns():
    out = future_exog(_exog_df(), "2020-12-01", h=3, lag=2, add_squared=True)
    assert list(out.columns) == ["roni_lag2", "roni_lag2_sq", "assumed"]
    assert (out["roni_lag2_sq"] == out["roni_lag2"] ** 2).all()
