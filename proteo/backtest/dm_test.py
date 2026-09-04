"""Prueba de Diebold-Mariano: ¿la diferencia de error entre dos modelos
es significativa o puede ser azar?

Convención de signo: ``stat < 0`` significa que el modelo 1 tiene menor
pérdida que el modelo 2 (d_t = L(e1) - L(e2) con media negativa).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import t as student_t


def diebold_mariano(e1, e2, h: int = 1, loss: str = "squared") -> dict:
    """Diebold-Mariano con corrección de muestra pequeña de Harvey,
    Leybourne y Newbold (1997).

    - ``d_t = L(e1_t) - L(e2_t)`` con pérdida cuadrática o absoluta.
    - Varianza de largo plazo con autocovarianzas hasta el rezago h-1
      (HAC: estimador robusto a heterocedasticidad y autocorrelación;
      para pronósticos a h pasos los errores están autocorrelacionados
      hasta h-1).
    - p-valor bilateral con t de Student de n-1 grados de libertad.

    Convención de signo: ``stat < 0`` significa que el modelo 1 tiene
    menor pérdida que el 2. Devuelve ``dict(stat, pvalue, n)``.
    """
    e1 = np.asarray(e1, dtype="float64")
    e2 = np.asarray(e2, dtype="float64")
    if e1.shape != e2.shape:
        raise ValueError(f"Longitudes distintas: {e1.shape} vs {e2.shape}")

    if loss == "squared":
        d = e1**2 - e2**2
    elif loss == "absolute":
        d = np.abs(e1) - np.abs(e2)
    else:
        raise ValueError(f"Pérdida desconocida: {loss!r}")

    n = len(d)
    d_bar = float(d.mean())
    centered = d - d_bar

    # Varianza de largo plazo: gamma_0 + 2 * sum_{k=1}^{h-1} gamma_k.
    gamma0 = float(centered @ centered) / n
    long_run = gamma0
    for k in range(1, min(h, n)):
        gamma_k = float(centered[k:] @ centered[:-k]) / n
        long_run += 2 * gamma_k

    if long_run <= 0:
        # Sin varianza: o las pérdidas son idénticas (empate exacto) o la
        # suma de autocovarianzas colapsó; se resuelve por la media.
        if d_bar == 0:
            return {"stat": 0.0, "pvalue": 1.0, "n": n}
        return {"stat": float(np.sign(d_bar) * np.inf), "pvalue": 0.0, "n": n}

    stat = d_bar / np.sqrt(long_run / n)

    # Corrección HLN de muestra pequeña.
    correction = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat *= correction

    pvalue = float(2 * student_t.sf(abs(stat), df=n - 1))
    return {"stat": float(stat), "pvalue": pvalue, "n": n}
