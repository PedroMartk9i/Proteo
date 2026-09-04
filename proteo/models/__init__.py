"""Modelos de pronóstico. Todos heredan de ``base.Model``."""

from proteo.models.naive import Naive, SeasonalNaive
from proteo.models.sarimax import SARIMAXModel

MODELS = {
    "naive": Naive,
    "naive_estacional": SeasonalNaive,
    "sarimax": SARIMAXModel,
}
