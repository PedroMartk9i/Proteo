"""Revisión de los archivos de marca: existen, son monocolor en tinta
de línea, vectoriales de verdad y con los tamaños de favicon correctos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PIL import Image

from app.theme import PALETTE

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"

ASSETS = [
    STATIC / "logo.svg",
    STATIC / "favicon.svg",
    STATIC / "favicon_32.png",
    STATIC / "favicon_64.png",
    STATIC / "logo_512.png",
    ROOT / "docs" / "img" / "logo_papel.svg",
]


@pytest.mark.parametrize("path", ASSETS, ids=lambda p: p.name)
def test_asset_exists(path: Path):
    assert path.exists(), f"Falta {path.relative_to(ROOT)}"


@pytest.mark.parametrize("name", ["logo.svg", "favicon.svg"])
def test_svg_is_monochrome_linea(name: str):
    text = (STATIC / name).read_text(encoding="utf-8")
    assert "viewBox" in text, f"{name} no declara viewBox"
    fills = set(re.findall(r'fill="(#[0-9A-Fa-f]{6})"', text))
    assert fills == {PALETTE["linea"]}, (
        f"{name} debe tener un solo color de relleno, el de línea "
        f"({PALETTE['linea']}); tiene {sorted(fills)}"
    )
    assert "<text" not in text, f"{name} contiene <text>"
    assert "<image" not in text, f"{name} contiene <image>"


@pytest.mark.parametrize(
    "name,size", [("favicon_32.png", 32), ("favicon_64.png", 64)]
)
def test_favicon_png_sizes(name: str, size: int):
    with Image.open(STATIC / name) as image:
        assert image.size == (size, size), (
            f"{name} mide {image.size}, se esperaba {(size, size)}"
        )
