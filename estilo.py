"""
estilo.py
Paleta y directrices de diseño para las figuras del proyecto ENSO - precio de bolsa.

Uso:
    from estilo import aplicar, C, FASE, INTENSIDAD, cop, titulo_figura
    aplicar()
"""
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ---------------------------------------------------------------- 1. Paleta

# Tinta y estructura
NEUTRO = {
    "tinta":        "#22303f",   # serie observada, texto principal
    "tinta_fuerte": "#111111",   # solo para marcadores de anclaje
    "texto_sec":    "#4a5560",   # notas al pie, anotaciones secundarias
    "texto_barra":  "#33393f",   # etiquetas sobre relleno claro
    "eje":          "#8a949e",   # borde de ejes, líneas separadoras
    "referencia":   "#6b7680",   # línea del cero
    "rejilla":      "#d7dde3",   # rejilla sobre fondo blanco
    "rejilla_clara":"#e3e7ea",   # rejilla en paneles de barras
    "inactivo":     "#9fb3c8",   # barras o series no destacadas
}

# Modelos: naranja quemado contra azul cobalto. Distinguibles en escala de grises
# (el naranja es más oscuro) y separables por la mayoría de daltonismos.
MODELO = {
    "arima":   "#c2410c",
    "sarimax": "#1d4ed8",
    "plume":   "#7f9dc4",        # miembros del ensamble, siempre con alfa bajo
}

# Fases ENSO: rojo cálido, azul frío. Nunca se invierten.
FASE = {
    "calida":       "#d94a3d",
    "fria":         "#2f6fb0",
    "neutral":      "#8a949e",
    "calida_fondo": "#fbe3e0",
    "neutral_fondo":"#f4f5f6",
    "fria_fondo":   "#e2ecf6",
}

# Bloques de partición: azul, naranja y verde muy desaturados. Van al fondo.
PARTICION = {
    "entrenamiento": "#e8eef4",
    "prueba":        "#fde9d7",
    "reserva":       "#e3f0e6",
}

# Escala secuencial de intensidad, del claro al oscuro. Ordinal, no categórica.
INTENSIDAD = [
    ("Neutral o La Niña",   "#c8ced4"),
    ("Débil (0,5 a 1,0)",   "#f6c6ba"),
    ("Moderado (1,0 a 1,5)", "#ee9179"),
    ("Fuerte (1,5 a 2,0)",  "#dc5c42"),
    ("Muy fuerte (≥ 2,0)",  "#a8271a"),
]

# Diccionario plano, compatible con el código existente
C = {
    "obs": NEUTRO["tinta"], "grid": NEUTRO["rejilla"],
    "arima": MODELO["arima"], "sarimax": MODELO["sarimax"],
    "band": MODELO["sarimax"], "band_a": MODELO["arima"],
    "warm": FASE["calida"], "cold": FASE["fria"],
    "train": PARTICION["entrenamiento"], "test": PARTICION["prueba"],
    "hold": PARTICION["reserva"],
}

# ---------------------------------------------------------------- 2. Grosores

LW = {
    "observado_largo": 0.9,   # series de 300+ puntos
    "observado_corto": 1.4,   # acercamientos
    "modelo":          1.9,   # línea de pronóstico principal
    "modelo_sec":      1.3,   # segundo modelo o backtesting
    "plume":           0.55,  # miembro del ensamble
    "referencia":      0.8,   # cero y umbrales
    "banda_punteada":  1.1,   # intervalo empírico
    "rejilla":         0.6,
}

ALFA = {
    "banda":     0.15,   # relleno del intervalo de confianza
    "episodio":  0.13,   # sombreado de fases ENSO sobre la serie
    "plume":     0.32,
    "rejilla":   0.7,
}

FS = {
    "base":       9.5,
    "titulo_fig": 12.5,
    "titulo_pan": 11.5,
    "subpanel":   9.5,
    "leyenda":    8.3,
    "anotacion":  8.4,
    "pie":        7.7,
}

# ---------------------------------------------------------------- 3. Aplicar

def aplicar(dpi=150):
    """Fija los parámetros globales de matplotlib."""
    plt.rcParams.update({
        "figure.dpi": dpi, "savefig.dpi": dpi,
        "figure.facecolor": "white",
        "font.size": FS["base"],
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": NEUTRO["eje"],
        "axes.grid": True, "axes.axisbelow": True,
        "grid.color": NEUTRO["rejilla"], "grid.linewidth": LW["rejilla"],
        "grid.alpha": ALFA["rejilla"],
        "legend.frameon": False,
    })


# ---------------------------------------------------------------- 4. Utilidades

# Miles con punto, convención colombiana
cop = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
miles = cop


def titulo_figura(fig, texto, x=0.006):
    """Título de figura alineado al margen izquierdo."""
    fig.suptitle(texto, x=x, ha="left", fontsize=FS["titulo_fig"], fontweight="bold")


def titulo_panel(ax, texto, grande=False):
    ax.set_title(texto, loc="left", fontweight="bold",
                 fontsize=FS["titulo_pan"] if grande else FS["subpanel"])


def pie(fig, texto, y=0.012, x=0.006):
    """Nota de procedencia al pie de la figura."""
    fig.text(x, y, texto, fontsize=FS["pie"], color=NEUTRO["texto_sec"])


def destacar(valores, indice_destacado, color=None):
    """Lista de colores para un gráfico de barras con un solo elemento resaltado."""
    color = color or MODELO["sarimax"]
    return [color if i == indice_destacado else NEUTRO["inactivo"]
            for i in range(len(valores))]


def ancla(ax, x, y, color=None, ms=8):
    """Marcador hueco: dato parcial, observado o punto de anclaje."""
    ax.scatter([x], [y], s=ms ** 2, facecolor="white",
               edgecolor=color or FASE["calida"], lw=2.0, zorder=8)


def bandas_enso(ax, y_min, y_max, umbral=0.5):
    """Fondo horizontal por fase, estilo IRI."""
    ax.axhspan(umbral, y_max, color=FASE["calida_fondo"], lw=0, zorder=0)
    ax.axhspan(-umbral, umbral, color=FASE["neutral_fondo"], lw=0, zorder=0)
    ax.axhspan(y_min, -umbral, color=FASE["fria_fondo"], lw=0, zorder=0)
    ax.axhline(umbral, color=FASE["calida"], lw=0.9, ls="--", zorder=1)
    ax.axhline(-umbral, color=FASE["fria"], lw=0.9, ls="--", zorder=1)
    ax.axhline(0.0, color="#b6bec6", lw=LW["referencia"], zorder=1)
    ax.grid(axis="y", color="#ffffff", lw=0.9, alpha=0.85)
    ax.set_axisbelow(True)
