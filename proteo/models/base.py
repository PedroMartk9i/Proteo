"""Interfaz común de los modelos de Proteo.

Todo modelo hereda de :class:`Model`: ``fit(y, X)`` entrena y devuelve
``self``; ``forecast(h, X_future)`` devuelve un DataFrame con columnas
``date, mean, lower, upper``; ``fitted()`` la serie ajustada en la
muestra; ``summary()`` un dict de diagnósticos (vacío en los naive).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Model(ABC):
    """Modelo de pronóstico mensual con exógena opcional."""

    name: str = "modelo"

    def __init__(self) -> None:
        self.params: dict = {}

    @abstractmethod
    def fit(self, y: pd.Series, X: pd.DataFrame | None = None) -> "Model":
        """Entrena con ``y`` (índice mensual) y exógena opcional ``X``."""

    @abstractmethod
    def forecast(
        self,
        h: int,
        X_future: pd.DataFrame | None = None,
        alpha: float = 0.2,
    ) -> pd.DataFrame:
        """Pronostica ``h`` pasos. Devuelve DataFrame[date, mean, lower,
        upper] con intervalo de confianza ``1 - alpha``."""

    @abstractmethod
    def fitted(self) -> pd.Series:
        """Serie ajustada dentro de la muestra de entrenamiento."""

    def summary(self) -> dict:
        """Diagnósticos del ajuste. Los naive devuelven ``{}``."""
        return {}

    @staticmethod
    def _future_dates(last_date, h: int) -> pd.DatetimeIndex:
        """Fechas mensuales consecutivas después de ``last_date``."""
        return pd.date_range(
            pd.Timestamp(last_date) + pd.DateOffset(months=1),
            periods=h,
            freq="MS",
        )
