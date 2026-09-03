"""Contrato de datos de Proteo.

Todo adaptador devuelve un ``pandas.DataFrame`` con exactamente las
columnas de ``COLUMNS``, en ese orden, y llama ``validate()`` antes de
devolver. ``validate()`` lanza ``ValueError`` con un mensaje que dice
exactamente qué falló.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

# Columnas del contrato, en este orden exacto.
COLUMNS = ["date", "value", "index", "source", "vintage"]

# Valores permitidos para la columna ``index``.
ALLOWED_INDEX = {"nino34", "roni", "xm_precio_bolsa"}


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Verifica el contrato de datos. Devuelve el mismo df si es válido.

    Comprueba, en orden: columnas y su orden, tipo de ``date`` (datetime
    sin zona), tipo ``float64`` y ausencia de NaN en ``value``, ``index``
    dentro del conjunto permitido, ``source`` de texto, ``vintage`` como
    ``datetime.date``, fechas sin duplicar y en orden ascendente.

    Lanza ``ValueError`` con un mensaje claro si algo falla.
    """
    cols = list(df.columns)
    if cols != COLUMNS:
        raise ValueError(
            f"Columnas inválidas: se esperaba {COLUMNS}, se obtuvo {cols}"
        )

    # date: datetime64[ns] sin zona horaria
    if not pd.api.types.is_datetime64_ns_dtype(df["date"]):
        raise ValueError(
            f"La columna 'date' debe ser datetime64[ns], es {df['date'].dtype}"
        )
    if getattr(df["date"].dt, "tz", None) is not None:
        raise ValueError("La columna 'date' no debe tener zona horaria")

    # value: float64 sin NaN
    if df["value"].dtype != "float64":
        raise ValueError(
            f"La columna 'value' debe ser float64, es {df['value'].dtype}"
        )
    if df["value"].isna().any():
        n = int(df["value"].isna().sum())
        raise ValueError(f"La columna 'value' tiene {n} NaN")

    # index: str dentro del conjunto permitido
    bad_index = set(df["index"].astype(object).unique()) - ALLOWED_INDEX
    if bad_index:
        raise ValueError(
            f"'index' fuera del conjunto permitido {sorted(ALLOWED_INDEX)}: "
            f"{sorted(bad_index)}"
        )

    # source: texto
    if not df["source"].map(lambda s: isinstance(s, str)).all():
        raise ValueError("La columna 'source' debe contener solo texto")

    # vintage: datetime.date (no datetime ni Timestamp)
    def _is_plain_date(v: object) -> bool:
        return isinstance(v, date) and not isinstance(v, datetime)

    if not df["vintage"].map(_is_plain_date).all():
        raise ValueError(
            "La columna 'vintage' debe contener objetos datetime.date"
        )

    # fechas sin duplicar
    if df["date"].duplicated().any():
        dups = df.loc[df["date"].duplicated(), "date"].dt.date.tolist()
        raise ValueError(f"Fechas duplicadas: {dups}")

    # orden ascendente por fecha
    if not df["date"].is_monotonic_increasing:
        raise ValueError("Las fechas no están en orden ascendente")

    return df
