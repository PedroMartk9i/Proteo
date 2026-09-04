"""Backtest de origen móvil.

Entrenar con datos hasta t, pronosticar t+1..t+h, avanzar t un mes,
repetir. Mide qué tan bien habría funcionado el modelo en el pasado sin
trampa: la exógena futura de cada origen se construye con
:func:`proteo.dataset.future_exog` usando SOLO datos disponibles hasta t.

ADVERTENCIA: Este backtest usa un solo vintage (el más reciente) para
todas las fechas. Un backtest verdaderamente 'como si fuera esa fecha'
requiere vintages históricos, que solo existirán a medida que la app los
acumule. El parámetro vintage queda expuesto para ese uso futuro.
"""

from __future__ import annotations

import re
from typing import Callable

import pandas as pd

from proteo.dataset import future_exog

# Nombre de columna de exógena rezagada, p. ej. "roni_lag2".
_LAG_COLUMN = re.compile(r"^(?P<name>.+)_lag(?P<lag>\d+)$")


def _parse_exog_column(X: pd.DataFrame) -> tuple[str, str, int, bool]:
    """Extrae (columna, nombre, rezago, tiene_cuadrado) de las columnas
    de ``X`` tal como las nombra ``build_dataset``."""
    base_cols = [c for c in X.columns if not c.endswith("_sq")]
    if len(base_cols) != 1:
        raise ValueError(
            f"Se esperaba una sola columna de exógena rezagada, hay {base_cols}"
        )
    col = base_cols[0]
    match = _LAG_COLUMN.match(col)
    if match is None:
        raise ValueError(
            f"La columna {col!r} no sigue el patrón '<exog>_lag<k>' de build_dataset"
        )
    has_squared = f"{col}_sq" in X.columns
    return col, match["name"], int(match["lag"]), has_squared


def _exog_observed_until(
    X: pd.DataFrame, col: str, name: str, lag: int, until
) -> pd.DataFrame:
    """Reconstruye la exógena SIN rezago a partir de ``X`` y la corta en
    ``until`` (la fecha del origen), para que future_exog solo vea datos
    disponibles en ese momento. La fila de X fechada en d contiene el
    valor de la exógena en d - lag."""
    dates = X.index - pd.DateOffset(months=lag)
    observed = pd.DataFrame(
        {"date": dates, "value": X[col].to_numpy(), "index": name}
    )
    return observed[observed["date"] <= pd.Timestamp(until)]


def run_backtest(
    model_factory: Callable,
    y: pd.Series,
    X: pd.DataFrame | None = None,
    initial_train: int = 203,
    horizons=range(1, 7),
    step: int = 1,
    window: str = "expanding",
    refit_every: int = 1,
    exog_strategy: str = "persistence",
    progress: Callable[[int, int], None] | None = None,
    label: str | None = None,
    vintage=None,
) -> pd.DataFrame:
    """Corre el backtest de origen móvil para un modelo.

    - ``model_factory``: función sin argumentos que devuelve un ``Model``
      nuevo, para no reutilizar estado entre orígenes.
    - Para cada origen t desde ``initial_train`` hasta ``n - max(horizons)``,
      de ``step`` en ``step``: entrena con ``y[:t]`` (``window="expanding"``)
      o con ``y[t-initial_train:t]`` (``window="rolling"``), construye la
      exógena futura con ``future_exog`` usando SOLO datos hasta t,
      pronostica ``max(horizons)`` pasos y compara con el valor real.
    - ``refit_every=k`` reentrena cada k orígenes; en los intermedios
      reutiliza los parámetros ya estimados extendiendo la muestra
      (``append`` de statsmodels) si el modelo lo permite, o reentrena si
      no. Solo para acelerar; por defecto 1 = siempre reentrena.
    - ``progress(i, total)`` es un callback opcional para la barra de
      Streamlit. ``label`` permite distinguir variantes del mismo modelo
      en la columna ``model`` (por defecto ``model.name``).

    Salida: una fila por origen × horizonte con columnas ``origin``,
    ``horizon``, ``target_date``, ``actual``, ``forecast``, ``lower``,
    ``upper``, ``assumed_exog``, ``model``.

    ADVERTENCIA: Este backtest usa un solo vintage (el más reciente) para
    todas las fechas. Un backtest verdaderamente 'como si fuera esa fecha'
    requiere vintages históricos, que solo existirán a medida que la app
    los acumule. El parámetro vintage queda expuesto para ese uso futuro.
    """
    if window not in ("expanding", "rolling"):
        raise ValueError(f"window debe ser 'expanding' o 'rolling': {window!r}")

    horizons = list(horizons)
    max_h = max(horizons)
    n = len(y)
    origins = list(range(initial_train, n - max_h + 1, step))
    total = len(origins)

    exog_info = _parse_exog_column(X) if X is not None else None

    rows: list[dict] = []
    model = None
    prev_len = 0
    for i, t in enumerate(origins):
        lo = 0 if window == "expanding" else t - initial_train
        y_train = y.iloc[lo:t]
        X_train = X.iloc[lo:t] if X is not None else None
        origin_date = y_train.index[-1]

        must_refit = (i % refit_every == 0) or model is None or window == "rolling"
        if must_refit:
            model = model_factory()
            model.fit(y_train, X_train)
        else:
            try:
                # Extiende la muestra con los parámetros ya estimados.
                new_y = y_train.iloc[prev_len:]
                new_X = X_train.iloc[prev_len:] if X_train is not None else None
                model._result = model._result.append(
                    new_y, exog=new_X, refit=False
                )
                model._last_date = origin_date
            except AttributeError:
                # El modelo no expone resultados de statsmodels: reentrenar
                # (los naive son baratos de todas formas).
                model = model_factory()
                model.fit(y_train, X_train)
        prev_len = len(y_train)

        X_future = None
        assumed = pd.Series(False, index=range(1, max_h + 1))
        if X is not None:
            col, name, lag, has_squared = exog_info
            observed = _exog_observed_until(X, col, name, lag, origin_date)
            ef = future_exog(
                observed, origin_date, max_h, lag,
                strategy=exog_strategy, add_squared=has_squared,
            )
            X_future = ef.drop(columns="assumed")
            assumed = pd.Series(ef["assumed"].to_numpy(), index=range(1, max_h + 1))

        fc = model.forecast(max_h, X_future=X_future)

        model_label = label or model.name
        for h in horizons:
            row = fc.iloc[h - 1]
            rows.append(
                {
                    "origin": origin_date,
                    "horizon": h,
                    "target_date": row["date"],
                    "actual": float(y.iloc[t + h - 1]),
                    "forecast": float(row["mean"]),
                    "lower": float(row["lower"]),
                    "upper": float(row["upper"]),
                    "assumed_exog": bool(assumed.loc[h]),
                    "model": model_label,
                }
            )

        if progress is not None:
            progress(i + 1, total)

    return pd.DataFrame(rows)
