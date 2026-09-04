"""Configuraciones de referencia.

``PAPER``: SARIMAX(1,1,1)(1,0,0)12 sobre el precio mensual con RONI
rezagado 2 meses como exógena, tal como en el paper del proyecto.
"""

PAPER = dict(
    order=(1, 1, 1),
    seasonal_order=(1, 0, 0, 12),
    exog="roni",
    lag=2,
    log_target=False,
    add_squared=False,
)
