"""Baselines naive. Sin baseline no hay comparación válida.

- :class:`Naive`: repite el último valor observado. Intervalo con la
  desviación estándar de las diferencias históricas × sqrt(h) × cuantil
  normal (camino aleatorio).
- :class:`SeasonalNaive`: repite el valor del mismo mes del año anterior.
  Intervalo análogo con las diferencias estacionales.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from proteo.models.base import Model


class Naive(Model):
    """Pronóstico = último valor observado."""

    name = "naive"

    def __init__(self) -> None:
        super().__init__()
        self._y: pd.Series | None = None

    def fit(self, y: pd.Series, X: pd.DataFrame | None = None) -> "Naive":
        self._y = y.copy()
        return self

    def forecast(
        self,
        h: int,
        X_future: pd.DataFrame | None = None,
        alpha: float = 0.2,
    ) -> pd.DataFrame:
        y = self._y
        dates = self._future_dates(y.index[-1], h)
        last = float(y.iloc[-1])
        sigma = float(y.diff().dropna().std())
        z = norm.ppf(1 - alpha / 2)

        steps = np.arange(1, h + 1)
        half = z * sigma * np.sqrt(steps)
        return pd.DataFrame(
            {
                "date": dates,
                "mean": np.full(h, last),
                "lower": last - half,
                "upper": last + half,
            }
        )

    def fitted(self) -> pd.Series:
        return self._y.shift(1)


class SeasonalNaive(Model):
    """Pronóstico = valor del mismo mes del año anterior."""

    name = "naive_estacional"

    def __init__(self, period: int = 12) -> None:
        super().__init__()
        self.params = {"period": period}
        self.period = period
        self._y: pd.Series | None = None

    def fit(self, y: pd.Series, X: pd.DataFrame | None = None) -> "SeasonalNaive":
        if len(y) < self.period:
            raise ValueError(
                f"Se necesitan al menos {self.period} observaciones, hay {len(y)}"
            )
        self._y = y.copy()
        return self

    def forecast(
        self,
        h: int,
        X_future: pd.DataFrame | None = None,
        alpha: float = 0.2,
    ) -> pd.DataFrame:
        y = self._y
        p = self.period
        dates = self._future_dates(y.index[-1], h)
        # Paso j → observación de p meses atrás en el ciclo correspondiente.
        means = np.array(
            [float(y.iloc[len(y) - p + ((j - 1) % p)]) for j in range(1, h + 1)]
        )
        sigma = float(y.diff(p).dropna().std())
        z = norm.ppf(1 - alpha / 2)
        # El error crece con el número de ciclos estacionales cubiertos.
        cycles = np.array([np.ceil(j / p) for j in range(1, h + 1)])
        half = z * sigma * np.sqrt(cycles)
        return pd.DataFrame(
            {"date": dates, "mean": means, "lower": means - half, "upper": means + half}
        )

    def fitted(self) -> pd.Series:
        return self._y.shift(self.period)
