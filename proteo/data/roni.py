"""Adaptador del índice RONI (Relative Oceanic Niño Index, media móvil
de 3 meses, base 1991-2020).

Sigue el patrón del adaptador de referencia ``nino34.py``: ``fetch_raw()``
toca la red, ``parse()`` es pura y es lo único que se testea.

Formato crudo (texto plano)::

    SEAS   YR  ANOM
    DJF  1950 -1.19

Cada fila es una temporada de tres meses. Se asigna al mes CENTRAL de la
temporada, con el año que trae la fila (DJF→01, JFM→02, …, NDJ→12).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from proteo.schema import COLUMNS, validate
from proteo.store import vintages

URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"
INDEX = "roni"

# Temporada → mes central, según la tabla de CLAUDE.md.
SEASON_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def fetch_raw(url: str = URL, timeout: int = 30) -> str:
    """Descarga el texto crudo. Toca la red; no se testea."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse(text: str, vintage: date, source: str = URL) -> pd.DataFrame:
    """Parsea el texto crudo al contrato de datos. Función pura.

    Ignora la cabecera (``SEAS`` no está en la tabla de temporadas) y las
    líneas vacías. Asigna cada temporada a su mes central con el año de
    la fila.
    """
    records: list[tuple[date, float]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        month = SEASON_MONTH.get(parts[0])
        if month is None:
            # Cabecera u otra línea sin temporada válida: se ignora.
            continue
        try:
            year = int(parts[1])
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
