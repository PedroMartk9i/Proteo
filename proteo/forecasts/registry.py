"""Registro inmutable de pronósticos emitidos y su verificación.

Almacenamiento en ``data/forecasts/``:

- ``registry.parquet``: una fila por pronóstico × paso.
- ``<forecast_id>.json``: configuración completa del pronóstico (modelo,
  parámetros, exógena, rezago, transformación, vintages usados, notas).
  ``forecast_id`` con formato ``YYYYMMDD-<modelo>-<secuencia>``.

Regla de inmutabilidad: una fila ya verificada no se toca nunca, aunque
un vintage nuevo traiga un valor revisado. El pronóstico se juzga contra
el primer valor observado, que es el que existía cuando se verificó.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from proteo.forecasts.seasons import next_season

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "forecasts"

REGISTRY_COLUMNS = [
    "forecast_id", "issued_at", "season_label", "model", "target_date",
    "horizon", "mean", "lower", "upper", "assumed_exog",
    "actual", "error", "abs_error", "inside_interval", "verified_at",
]


def _dir(root: Path | str | None) -> Path:
    return Path(root) if root is not None else DATA_ROOT


def _registry_path(root: Path | str | None) -> Path:
    return _dir(root) / "registry.parquet"


def load(root: Path | str | None = None) -> pd.DataFrame:
    """Registro completo; vacío (con columnas) si aún no existe."""
    path = _registry_path(root)
    if not path.exists():
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    return pd.read_parquet(path)


def _save(registry: pd.DataFrame, root: Path | str | None) -> None:
    directory = _dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    registry.to_parquet(_registry_path(root), index=False)


def issue(
    forecast_df: pd.DataFrame,
    config: dict,
    issued_at: date,
    notes: str = "",
    root: Path | str | None = None,
) -> str:
    """Registra un pronóstico emitido. Devuelve su ``forecast_id``.

    ``forecast_df`` trae columnas ``date, mean, lower, upper`` y
    opcionalmente ``assumed_exog``. La temporada objetivo se deriva del
    primer paso (el mes anterior es el último observado).
    """
    registry = load(root)
    model = str(config.get("model", "modelo"))

    prefix = f"{issued_at:%Y%m%d}-{model}-"
    existing = {
        fid for fid in registry["forecast_id"].unique()
        if str(fid).startswith(prefix)
    }
    forecast_id = f"{prefix}{len(existing) + 1:02d}"

    fc = forecast_df.sort_values("date").reset_index(drop=True)
    first_step = fc["date"].iloc[0]
    last_observed = (pd.Timestamp(first_step) - pd.DateOffset(months=1)).date()
    season, _ = next_season(last_observed)

    assumed = (
        fc["assumed_exog"].astype(bool)
        if "assumed_exog" in fc.columns
        else pd.Series(False, index=fc.index)
    )
    rows = pd.DataFrame(
        {
            "forecast_id": forecast_id,
            "issued_at": issued_at.isoformat(),
            "season_label": season,
            "model": model,
            "target_date": pd.to_datetime(fc["date"]).astype("datetime64[ns]"),
            "horizon": np.arange(1, len(fc) + 1),
            "mean": fc["mean"].astype("float64"),
            "lower": fc["lower"].astype("float64"),
            "upper": fc["upper"].astype("float64"),
            "assumed_exog": assumed.to_numpy(),
            "actual": np.nan,
            "error": np.nan,
            "abs_error": np.nan,
            "inside_interval": np.nan,
            "verified_at": None,
        }
    )
    _save(pd.concat([registry, rows], ignore_index=True), root)

    directory = _dir(root)
    payload = {
        **config,
        "forecast_id": forecast_id,
        "issued_at": issued_at.isoformat(),
        "season_label": season,
        "notes": notes,
    }
    with open(directory / f"{forecast_id}.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return forecast_id


def verify(
    actual: pd.Series,
    today: date,
    root: Path | str | None = None,
) -> pd.DataFrame:
    """Verifica las filas pendientes cuyo ``target_date`` ya está en
    ``actual``. Las filas ya verificadas NO se tocan nunca. Devuelve las
    filas recién verificadas."""
    registry = load(root)
    if registry.empty:
        return registry

    actual = actual.copy()
    actual.index = pd.to_datetime(actual.index)

    mask = registry["verified_at"].isna() & registry["target_date"].isin(
        actual.index
    )
    if not mask.any():
        return registry.iloc[0:0]

    observed = actual.reindex(registry.loc[mask, "target_date"]).to_numpy(
        dtype="float64"
    )
    registry.loc[mask, "actual"] = observed
    registry.loc[mask, "error"] = observed - registry.loc[mask, "mean"]
    registry.loc[mask, "abs_error"] = np.abs(registry.loc[mask, "error"])
    registry.loc[mask, "inside_interval"] = (
        (registry.loc[mask, "actual"] >= registry.loc[mask, "lower"])
        & (registry.loc[mask, "actual"] <= registry.loc[mask, "upper"])
    ).astype("float64")
    registry.loc[mask, "verified_at"] = today.isoformat()

    _save(registry, root)
    return registry.loc[mask]


def pending(root: Path | str | None = None) -> pd.DataFrame:
    """Filas emitidas y aún sin verificar."""
    registry = load(root)
    return registry[registry["verified_at"].isna()]


def scorecard(
    by=("model", "horizon"),
    root: Path | str | None = None,
) -> pd.DataFrame:
    """MAE, RMSE, cobertura y n sobre las filas YA verificadas."""
    registry = load(root)
    verified = registry[registry["verified_at"].notna()]
    if verified.empty:
        return pd.DataFrame(columns=list(by) + ["mae", "rmse", "coverage_pct", "n"])
    out = (
        verified.groupby(list(by))
        .apply(
            lambda g: pd.Series(
                {
                    "mae": float(g["abs_error"].mean()),
                    "rmse": float(np.sqrt((g["error"] ** 2).mean())),
                    "coverage_pct": float(g["inside_interval"].mean() * 100),
                    "n": int(len(g)),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    out["n"] = out["n"].astype(int)
    return out


def history(forecast_id: str, root: Path | str | None = None) -> pd.DataFrame:
    """Filas de un pronóstico, ordenadas por horizonte."""
    registry = load(root)
    return (
        registry[registry["forecast_id"] == forecast_id]
        .sort_values("horizon")
        .reset_index(drop=True)
    )


def load_config(forecast_id: str, root: Path | str | None = None) -> dict:
    """Configuración JSON guardada al emitir el pronóstico."""
    path = _dir(root) / f"{forecast_id}.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
