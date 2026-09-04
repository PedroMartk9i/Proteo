"""Construcción del dataset de modelado a partir de series en el
contrato de datos.

Funciones puras: reciben DataFrames del contrato (5 columnas) y
devuelven series y matrices listas para los modelos. El rezago de la
exógena es SIEMPRE por calendario (sobre el índice mensual completo),
nunca por posiciones de filas: un mes faltante queda como NaN y no
corre el rezago.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _to_monthly_series(df: pd.DataFrame) -> tuple[pd.Series, str]:
    """Convierte un DataFrame del contrato a una Serie mensual ("MS").

    Reindexa al calendario mensual completo entre la primera y la última
    fecha, de modo que un mes faltante queda como NaN explícito.
    Devuelve la serie y el nombre del índice (columna ``index``).
    """
    name = str(df["index"].iloc[0])
    s = df.set_index("date")["value"]
    calendar = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    s = s.reindex(calendar)
    s.index.name = "date"
    return s, name


def build_dataset(
    price: pd.DataFrame,
    exog: pd.DataFrame | None = None,
    lag: int = 0,
    start=None,
    end=None,
    log_target: bool = False,
    add_squared: bool = False,
) -> tuple[pd.Series, pd.DataFrame | None]:
    """Arma ``y`` (precio) y ``X`` (exógena rezagada) para modelar.

    - ``price`` y ``exog`` llegan en el contrato de datos (5 columnas).
    - Rezago por calendario: ``X_t = exog_{t-lag}``. Con ``lag=2`` la
      fila de marzo lleva el valor de enero, implementado con
      ``shift(lag)`` sobre el índice mensual completo.
    - ``add_squared=True`` agrega ``<exog>_lag<k>_sq = X_t**2`` (la
      relación cuadrática ENSO–precio encontrada en el proyecto).
    - ``log_target=True`` transforma ``y = log(price)``; deshacer con
      :func:`inverse_transform`.
    - Recorta a ``[start, end]`` y elimina filas con NaN en ``y`` o en
      ``X``.

    Devuelve ``(y, X)`` con ``y.name == "price"`` y columnas de ``X``
    como ``roni_lag2``, ``roni_lag2_sq``; ``X`` es None sin exógena.
    """
    y, _ = _to_monthly_series(price)
    if log_target:
        y = np.log(y)
    y.name = "price"

    X: pd.DataFrame | None = None
    if exog is not None:
        xs, exog_name = _to_monthly_series(exog)
        col = f"{exog_name}_lag{lag}"
        X = xs.shift(lag).to_frame(col)
        if add_squared:
            X[f"{col}_sq"] = X[col] ** 2

    combined = pd.concat([y, X], axis=1) if X is not None else y.to_frame()
    combined = combined.loc[slice(start, end)]
    combined = combined.dropna()

    y_out = combined["price"]
    X_out = combined.drop(columns="price") if X is not None else None
    return y_out, X_out


def inverse_transform(series: pd.Series, log_target: bool) -> pd.Series:
    """Devuelve la serie al nivel original (deshace el log si aplica)."""
    return np.exp(series) if log_target else series


def future_exog(
    exog: pd.DataFrame,
    last_date,
    h: int,
    lag: int,
    strategy: str = "persistence",
    add_squared: bool = False,
) -> pd.DataFrame:
    """Exógena futura para pronosticar ``h`` pasos después de ``last_date``.

    Para el paso ``j`` (mes ``last_date + j``) se necesita el valor de
    ``last_date + j - lag``: si ya está observado se usa el valor real;
    si no, se usa el último valor observado (persistencia). La columna
    booleana ``assumed`` marca cuáles filas son supuestas.

    Decisión de diseño explícita de la v1: el RONI futuro NO se
    pronostica, se supone constante, y la interfaz lo advierte. Con
    ``lag=2`` los pasos 1 y 2 son observados y del 3 en adelante son
    supuestos.

    ``add_squared=True`` agrega la columna cuadrática con los mismos
    nombres que :func:`build_dataset`, para que ``X_future`` case con
    ``X``.
    """
    if strategy != "persistence":
        raise ValueError(f"Estrategia desconocida: {strategy!r}")

    xs, exog_name = _to_monthly_series(exog)
    observed = xs.dropna()
    last_value = float(observed.iloc[-1])

    dates = pd.date_range(
        pd.Timestamp(last_date) + pd.DateOffset(months=1), periods=h, freq="MS"
    )
    values: list[float] = []
    assumed: list[bool] = []
    for d in dates:
        source_date = d - pd.DateOffset(months=lag)
        if source_date in observed.index:
            values.append(float(observed.loc[source_date]))
            assumed.append(False)
        else:
            values.append(last_value)
            assumed.append(True)

    col = f"{exog_name}_lag{lag}"
    out = pd.DataFrame({col: values}, index=dates)
    if add_squared:
        out[f"{col}_sq"] = out[col] ** 2
    out["assumed"] = assumed
    out.index.name = "date"
    return out
