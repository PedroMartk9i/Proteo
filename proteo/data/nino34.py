"""Adaptador del índice Niño 3.4 mensual (ERSSTv5, base 1991-2020).

Adaptador de REFERENCIA: los demás (RONI, XM) se construyen copiando
este patrón. Descarga y parseo van separados: ``fetch_raw()`` toca la
red, ``parse()`` es pura y es lo único que se testea.

Formato crudo (texto plano, columnas de ancho variable)::

     YR   MON  NINO1+2  ANOM   NINO3    ANOM   NINO4    ANOM   NINO3.4  ANOM
    1950   1   23.01   -1.55   23.56   -2.10   26.94   -1.38   24.55   -1.99

Se usa la ÚLTIMA columna de cada fila (ANOM de NINO3.4). Las demás
regiones se ignoran.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from proteo.schema import COLUMNS, validate
from proteo.store import vintages

URL = "https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii"
INDEX = "nino34"


def fetch_raw(url: str = URL, timeout: int = 30) -> str:
    """Descarga el texto crudo. Toca la red; no se testea."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse(text: str, vintage: date, source: str = URL) -> pd.DataFrame:
    """Parsea el texto crudo al contrato de datos. Función pura.

    Ignora la cabecera (primera columna no numérica) y las líneas vacías.
    Usa la última columna de cada fila como ``value`` y asigna la fecha al
    primer día del mes ``YR-MON``.
    """
    records: list[tuple[date, float]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            year = int(parts[0])
            month = int(parts[1])
        except ValueError:
            # Cabecera u otra línea no numérica: se ignora.
            continue
        try:
            value = float(parts[-1])
        except ValueError:
            continue
        records.append((date(year, month, 1), value))

    df = pd.DataFrame(records, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    df["value"] = df["value"].astype("float64")
    df["index"] = INDEX
    df["source"] = source
    df["vintage"] = vintage
    df = df[COLUMNS].sort_values("date").reset_index(drop=True)
    return df


def download(vintage: date | None = None) -> pd.DataFrame:
    """Descarga completa: fetch_raw → save_raw → parse → validate →
    save_processed. Con ``vintage=None`` usa la fecha de hoy. Devuelve el
    DataFrame validado.
    """
    if vintage is None:
        vintage = date.today()

    text = fetch_raw()
    vintages.save_raw(INDEX, vintage, text)
    df = parse(text, vintage)
    validate(df)
    vintages.save_processed(INDEX, vintage, df)
    return df
