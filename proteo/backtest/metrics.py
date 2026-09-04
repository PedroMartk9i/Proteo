"""Métricas del backtest por modelo, horizonte y fase ENSO.

Todas reciben el DataFrame de resultados de ``run_backtest`` (una fila
por origen × horizonte). El MAPE se reporta pero no es fiable si la
serie cruza cero (regla del proyecto: no usarlo en ese caso).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_METRIC_COLUMNS = ["n", "mae", "rmse", "mape", "smape"]


def _error_metrics(group: pd.DataFrame) -> pd.Series:
    e = group["actual"] - group["forecast"]
    a = group["actual"]
    f = group["forecast"]
    with np.errstate(divide="ignore", invalid="ignore"):
        mape = float(np.mean(np.abs(e / a)) * 100)
        smape = float(np.mean(2 * np.abs(e) / (np.abs(a) + np.abs(f))) * 100)
    return pd.Series(
        {
            "n": int(len(group)),
            "mae": float(np.mean(np.abs(e))),
            "rmse": float(np.sqrt(np.mean(e**2))),
            "mape": mape,
            "smape": smape,
        }
    )


def by_horizon(results: pd.DataFrame) -> pd.DataFrame:
    """MAE, RMSE, MAPE y sMAPE por modelo y horizonte, con n."""
    out = (
        results.groupby(["model", "horizon"])
        .apply(_error_metrics, include_groups=False)
        .reset_index()
    )
    out["n"] = out["n"].astype(int)
    out["horizon"] = out["horizon"].astype(int)
    return out[["model", "horizon"] + _METRIC_COLUMNS]


def skill(
    results: pd.DataFrame,
    model: str,
    baseline: str,
    metric: str = "rmse",
) -> pd.DataFrame:
    """Mejora porcentual del modelo sobre el baseline por horizonte.

    ``improvement = 1 - metric_model / metric_baseline``: positivo
    significa que el modelo mejora al baseline.
    """
    table = by_horizon(results).set_index(["model", "horizon"])[metric]
    m = table.loc[model]
    b = table.loc[baseline]
    improvement = (1 - m / b) * 100
    return pd.DataFrame(
        {"horizon": improvement.index, "improvement_pct": improvement.to_numpy()}
    )


def by_enso_phase(
    results: pd.DataFrame,
    roni: pd.DataFrame,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Métricas por fase ENSO, modelo y horizonte, con n.

    Clasifica cada origen por el RONI observado en la fecha de origen:
    ``nino`` (≥ threshold), ``nina`` (≤ -threshold), ``neutral``.
    ``roni`` llega en el contrato de datos.
    """
    roni_series = roni.set_index("date")["value"]

    def _phase(origin) -> str:
        value = roni_series.get(origin, np.nan)
        if np.isnan(value):
            return "desconocida"
        if value >= threshold:
            return "nino"
        if value <= -threshold:
            return "nina"
        return "neutral"

    tagged = results.copy()
    tagged["phase"] = tagged["origin"].map(_phase)
    out = (
        tagged.groupby(["phase", "model", "horizon"])
        .apply(_error_metrics, include_groups=False)
        .reset_index()
    )
    out["n"] = out["n"].astype(int)
    out["horizon"] = out["horizon"].astype(int)
    return out[["phase", "model", "horizon"] + _METRIC_COLUMNS]


def coverage(results: pd.DataFrame) -> pd.DataFrame:
    """Porcentaje de veces que el real cayó dentro de [lower, upper]."""
    inside = (results["actual"] >= results["lower"]) & (
        results["actual"] <= results["upper"]
    )
    tagged = results.assign(inside=inside)
    out = (
        tagged.groupby(["model", "horizon"])["inside"]
        .mean()
        .mul(100)
        .rename("coverage_pct")
        .reset_index()
    )
    out["horizon"] = out["horizon"].astype(int)
    return out
