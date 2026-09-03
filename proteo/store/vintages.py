"""Guardar y cargar vintages.

Un *vintage* es la copia de los datos tal como estaban en la fecha de
descarga. Nunca se sobrescribe entre días distintos: dos descargas el
mismo día comparten vintage y la segunda reemplaza a la primera; días
distintos, archivos distintos, siempre.

Estructura en disco::

    data/raw/<index>/<YYYY-MM-DD>.<ext>          copia cruda
    data/processed/<index>/<YYYY-MM-DD>.parquet  salida del contrato

Todas las funciones aceptan ``root`` para poder apuntar a un directorio
temporal en los tests. Por defecto usan ``data/`` en la raíz del repo.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

# Raíz por defecto: <repo>/data. Este archivo está en proteo/store/.
DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def _root(root: Path | str | None) -> Path:
    return Path(root) if root is not None else DATA_ROOT


def _vintage_str(vintage: date | str) -> str:
    """Normaliza el vintage a texto ``YYYY-MM-DD``."""
    if isinstance(vintage, str):
        return vintage
    return vintage.isoformat()


def save_raw(
    index: str,
    vintage: date | str,
    text_or_df: str | pd.DataFrame,
    ext: str | None = None,
    root: Path | str | None = None,
) -> Path:
    """Guarda la copia cruda tal como llegó.

    Si ``text_or_df`` es texto se escribe como ``.txt`` (UTF-8); si es un
    DataFrame se escribe como ``.csv``. ``ext`` permite forzar la
    extensión. Devuelve la ruta escrita.
    """
    directory = _root(root) / "raw" / index
    directory.mkdir(parents=True, exist_ok=True)
    stem = _vintage_str(vintage)

    if isinstance(text_or_df, pd.DataFrame):
        path = directory / f"{stem}.{ext or 'csv'}"
        text_or_df.to_csv(path, index=False, encoding="utf-8")
    else:
        path = directory / f"{stem}.{ext or 'txt'}"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text_or_df)
    return path


def save_processed(
    index: str,
    vintage: date | str,
    df: pd.DataFrame,
    root: Path | str | None = None,
) -> Path:
    """Guarda la salida del contrato como parquet. Devuelve la ruta."""
    directory = _root(root) / "processed" / index
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_vintage_str(vintage)}.parquet"
    df.to_parquet(path, index=False)
    return path


def list_vintages(index: str, root: Path | str | None = None) -> list[date]:
    """Lista los vintages procesados de ``index``, ascendente por fecha."""
    directory = _root(root) / "processed" / index
    if not directory.exists():
        return []
    out: list[date] = []
    for path in directory.glob("*.parquet"):
        try:
            out.append(date.fromisoformat(path.stem))
        except ValueError:
            continue
    return sorted(out)


def load(
    index: str,
    vintage: date | str | None = None,
    root: Path | str | None = None,
) -> pd.DataFrame:
    """Carga un vintage procesado. Con ``vintage=None`` carga el más reciente."""
    if vintage is None:
        available = list_vintages(index, root=root)
        if not available:
            raise FileNotFoundError(f"No hay vintages para '{index}'")
        vintage = available[-1]

    path = _root(root) / "processed" / index / f"{_vintage_str(vintage)}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No existe el vintage {vintage} para '{index}'")
    return pd.read_parquet(path)
