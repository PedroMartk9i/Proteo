"""SARIMAX de statsmodels con exógena opcional.

Configuración de referencia del paper: SARIMAX(1,1,1)(1,0,0)12 sobre el
precio mensual, con RONI rezagado 2 meses como regresor exógeno (ver
``proteo/models/presets.py``).
"""

from __future__ import annotations

import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.statespace.sarimax import SARIMAX

from proteo.models.base import Model


class SARIMAXModel(Model):
    """SARIMAX(p,d,q)(P,D,Q)s con exógena opcional."""

    name = "sarimax"

    def __init__(
        self,
        order: tuple[int, int, int],
        seasonal_order: tuple[int, int, int, int] = (0, 0, 0, 0),
        trend: str | None = None,
    ) -> None:
        super().__init__()
        self.params = {
            "order": order,
            "seasonal_order": seasonal_order,
            "trend": trend,
        }
        self._result = None
        self._last_date = None

    def fit(self, y: pd.Series, X: pd.DataFrame | None = None) -> "SARIMAXModel":
        y = y.copy()
        try:
            # Índice con frecuencia explícita para que statsmodels no avise;
            # si hay huecos se queda como está (las fechas del pronóstico se
            # construyen a mano en forecast()).
            y.index = pd.DatetimeIndex(y.index, freq="MS")
        except ValueError:
            pass

        model = SARIMAX(
            y,
            exog=X,
            order=self.params["order"],
            seasonal_order=self.params["seasonal_order"],
            trend=self.params["trend"],
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        self._result = model.fit(disp=False)
        self._last_date = y.index[-1]
        return self

    def forecast(
        self,
        h: int,
        X_future: pd.DataFrame | None = None,
        alpha: float = 0.2,
    ) -> pd.DataFrame:
        fc = self._result.get_forecast(steps=h, exog=X_future)
        ci = fc.conf_int(alpha=alpha)
        return pd.DataFrame(
            {
                "date": self._future_dates(self._last_date, h),
                "mean": fc.predicted_mean.to_numpy(),
                "lower": ci.iloc[:, 0].to_numpy(),
                "upper": ci.iloc[:, 1].to_numpy(),
            }
        )

    def fitted(self) -> pd.Series:
        return self._result.fittedvalues

    def summary(self) -> dict:
        """Coeficientes (coef, std_err, pvalue), aic, bic, n_obs y
        ljung_box_p (Ljung-Box con 12 rezagos sobre los residuos; si es
        menor a 0.05 quedan autocorrelaciones sin modelar)."""
        res = self._result
        coefficients = {
            name: {
                "coef": float(res.params[name]),
                "std_err": float(res.bse[name]),
                "pvalue": float(res.pvalues[name]),
            }
            for name in res.params.index
        }
        lb = acorr_ljungbox(res.resid.dropna(), lags=[12])
        return {
            "coefficients": coefficients,
            "aic": float(res.aic),
            "bic": float(res.bic),
            "n_obs": int(res.nobs),
            "ljung_box_p": float(lb["lb_pvalue"].iloc[0]),
        }
