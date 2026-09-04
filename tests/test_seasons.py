"""Tests de las temporadas CPC. Puros, sin red."""

from __future__ import annotations

from datetime import date

from proteo.forecasts.seasons import next_season, season_label


def test_twelve_last_observed_months_give_correct_labels():
    # último observado → (etiqueta, primer mes de la temporada objetivo)
    expected = {
        1: ("MAM 2026", date(2026, 3, 1)),
        2: ("AMJ 2026", date(2026, 4, 1)),
        3: ("MJJ 2026", date(2026, 5, 1)),
        4: ("JJA 2026", date(2026, 6, 1)),
        5: ("JAS 2026", date(2026, 7, 1)),
        6: ("ASO 2026", date(2026, 8, 1)),
        7: ("SON 2026", date(2026, 9, 1)),
        8: ("OND 2026", date(2026, 10, 1)),
        9: ("NDJ 2026", date(2026, 11, 1)),
        10: ("DJF 2027", date(2026, 12, 1)),
        11: ("JFM 2027", date(2027, 1, 1)),
        12: ("FMA 2027", date(2027, 2, 1)),
    }
    for month, (label, start) in expected.items():
        got_label, got_months = next_season(date(2026, month, 1))
        assert got_label == label, f"mes {month}: {got_label} != {label}"
        assert got_months[0] == start
        assert len(got_months) == 3


def test_example_from_spec():
    # Último dato agosto 2026 → OND 2026 (septiembre es paso intermedio).
    label, months = next_season(date(2026, 8, 1))
    assert label == "OND 2026"
    assert months == [date(2026, 10, 1), date(2026, 11, 1), date(2026, 12, 1)]


def test_ndj_crosses_december_to_january():
    # NDJ 2026 cubre nov 2026, dic 2026 y ene 2027.
    label, months = next_season(date(2026, 9, 1))
    assert label == "NDJ 2026"
    assert months == [date(2026, 11, 1), date(2026, 12, 1), date(2027, 1, 1)]


def test_season_label_uses_central_month_year():
    assert season_label(date(2026, 12, 1)) == "NDJ 2026"
    assert season_label(date(2027, 1, 1)) == "DJF 2027"
    assert season_label(date(2026, 10, 1)) == "SON 2026"
