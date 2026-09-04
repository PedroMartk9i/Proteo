"""Adaptador del precio de bolsa nacional de XM (COP/kWh) vía pydataxm.

Sigue el patrón del adaptador de referencia ``nino34.py``, con la
diferencia de que el crudo es un DataFrame (una fila por día, 24 columnas
de hora) y no texto. ``fetch_raw()`` toca la red; ``aggregate_monthly()``
es pura y es lo único que se testea.

Agregación mensual: ``value`` = promedio simple de TODAS las horas de
todos los días del mes. Debe reproducir ``examples/promedio_mensual.csv``
con tolerancia 1e-6; ese archivo es la verdad.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from proteo.schema import COLUMNS, validate
from proteo.store import vintages

SOURCE = "pydataxm:PrecBolsNaci"
INDEX = "xm_precio_bolsa"
START_DEFAULT = date(2000, 1, 1)

HOUR_COLUMNS = [f"Values_Hour{h:02d}" for h in range(1, 25)]


def fetch_raw(start: date, end: date) -> pd.DataFrame:
    """Descarga el crudo diario por tramos anuales y concatena.

    Toca la red; no se testea. La API de XM limita el rango por llamada,
    por eso se pide año por año. Import perezoso de pydataxm para que el
    resto del módulo funcione sin el paquete instalado.
    """
    from pydataxm.pydataxm import ReadDB

    api = ReadDB()
    frames: list[pd.DataFrame] = []
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(date(chunk_start.year, 12, 31), end)
        chunk = api.request_data("PrecBolsNaci", "Sistema", chunk_start, chunk_end)
        if chunk is not None and not chunk.empty:
            frames.append(chunk)
        chunk_start = date(chunk_start.year + 1, 1, 1)

    if not frames:
        raise RuntimeError(
            f"pydataxm no devolvió datos entre {start} y {end}"
        )
    return pd.concat(frames, ignore_index=True)


def aggregate_monthly(df_raw: pd.DataFrame, vintage: date) -> pd.DataFrame:
    """Agrega el crudo diario a promedio mensual. Función pura.

    ``value`` = promedio simple de todas las horas de todos los días del
    mes (columnas ``Values_Hour01`` … ``Values_Hour24``). Las columnas de
    promedios precalculados que traiga el crudo se ignoran.
    """
    df = df_raw.copy()
    df["month"] = pd.to_datetime(df["Date"]).dt.to_period("M")
    for col in HOUR_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    long = df[["month"] + HOUR_COLUMNS].melt(id_vars="month", value_name="v")
    monthly = long.groupby("month")["v"].mean().sort_index()

    out = pd.DataFrame(
        {
            "date": monthly.index.to_timestamp().astype("datetime64[ns]"),
            "value": monthly.to_numpy(dtype="float64"),
        }
    )
    out["index"] = INDEX
    out["source"] = SOURCE
    out["vintage"] = vintage
    out = out[COLUMNS].sort_values("date").reset_index(drop=True)
    return out


def download(
    start: date = START_DEFAULT,
    end: date | None = None,
    vintage: date | None = None,
) -> pd.DataFrame:
    """Descarga completa: fetch_raw → save_raw → aggregate_monthly →
    validate → save_processed. Con ``end=None`` o ``vintage=None`` usa la
    fecha de hoy. Devuelve el DataFrame validado.
    """
    if end is None:
        end = date.today()
    if vintage is None:
        vintage = date.today()

    df_raw = fetch_raw(start, end)
    vintages.save_raw(INDEX, vintage, df_raw)
    df = aggregate_monthly(df_raw, vintage)
    validate(df)
    vintages.save_processed(INDEX, vintage, df)
    return df
