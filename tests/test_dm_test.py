"""Tests de la prueba Diebold-Mariano. Sin red."""

from __future__ import annotations

import numpy as np

from proteo.backtest.dm_test import diebold_mariano


def test_identical_errors_give_zero_stat_pvalue_one():
    rng = np.random.default_rng(1)
    e = rng.normal(0, 1, 100)
    out = diebold_mariano(e, e.copy())
    assert out["stat"] == 0.0
    assert out["pvalue"] == 1.0
    assert out["n"] == 100


def test_large_constant_difference_is_significant():
    rng = np.random.default_rng(2)
    e2 = rng.normal(0, 0.1, 100)
    e1 = e2 + 5.0
    out = diebold_mariano(e1, e2)
    assert out["pvalue"] < 1e-6
    # e1 tiene MAYOR pérdida: stat > 0 según la convención de signo.
    assert out["stat"] > 0


def test_white_noise_difference_is_not_significant():
    # Con d_t ruido blanco, |stat| < 3 en cinco semillas fijas.
    for seed in (10, 11, 12, 13, 14):
        rng = np.random.default_rng(seed)
        e1 = rng.normal(0, 1, 200)
        e2 = rng.normal(0, 1, 200)
        out = diebold_mariano(e1, e2)
        assert abs(out["stat"]) < 3, f"semilla {seed}: stat={out['stat']:.2f}"


def test_absolute_loss_and_h_greater_than_one():
    rng = np.random.default_rng(3)
    e1 = rng.normal(0, 1, 150)
    e2 = rng.normal(0, 1, 150)
    out = diebold_mariano(e1, e2, h=6, loss="absolute")
    assert out["n"] == 150
    assert 0.0 <= out["pvalue"] <= 1.0
