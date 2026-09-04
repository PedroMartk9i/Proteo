# STATUS de Proteo — v1.3

Última sesión: 2026-09-03. Marca de Proteo integrada en la app, el
README y el boletín.

## Qué hace (v1.3)

- Todo lo de v1.0-v1.2 (ver historial): datos con vintages, SARIMAX
  interactivo, backtest, pronósticos inmutables, arranque con doble
  clic, sistema "caja beige" en las cuatro páginas con AA verificado.
- Marca (SVG de Pedro, silueta en negativo sobre cuadro de línea):
  - `app/static/`: logo.svg, favicon.svg, favicon_32.png,
    favicon_64.png, logo_512.png. `docs/img/logo_papel.svg` (variante
    sobre papel para fondos claros de GitHub).
  - `theme.page_setup(title)`: única cabecera de página — set_page_config
    con `{title} | Proteo` y favicon, inject_css, plotly_template y
    marca en la barra lateral (st.logo con icon_image; fallback a
    brand_lockup(32) si la versión no tiene st.logo, comprobado con
    hasattr). Las cinco páginas la usan.
  - `components.brand_lockup(height, wordmark)`: SVG inline (nítido a
    cualquier zoom), fill forzado a PALETTE["linea"] al leerlo (el
    archivo no se toca), metadata C2PA descartada para no inflar el
    HTML, wordmark mono a 0.45·height con separación 0.3·height.
  - Inicio: lockup a 96 px + frase a máximo 60ch + los tres
    data_header. El appbar anterior se eliminó (lo reemplaza la marca).
  - README: logo_papel.svg centrado a 220 px con subtítulo; la captura
    de portada ahora es docs/img/inicio.png (home.png eliminada).
  - Boletín: primera línea con la marca (ruta relativa desde
    data/forecasts/); el boletín OND 2026 quedó regenerado con ella.
- `tests/test_assets.py`: los seis archivos existen; logo.svg y
  favicon.svg tienen viewBox, un único fill igual a PALETTE["linea"] y
  ni <text> ni <image>; favicons PNG de 32×32 y 64×64 (Pillow).
- 62 tests en verde; proteo/ intacto.

## Qué no hace todavía

- Límites de v1.0 sin cambio: RONI futuro por persistencia, backtest
  con un solo vintage, app local.
- README: completar grupo de investigación y coautores.

## Pendiente operativo

- Cuando XM publique septiembre 2026: Datos → Descargar XM →
  Pronósticos → Verificar pendientes (12 filas pendientes de OND 2026).

## Decisiones tomadas (v1.3)

- Los assets llegaron a la raíz del repo y se movieron con git mv a
  las rutas del spec (app/static/ y docs/img/); las pruebas de
  legibilidad (legibilidad*.png) quedaron en docs/. Mover no es
  modificar: el contenido de los archivos está intacto.
- La plantilla del boletín vive en app/pages/4_Pronosticos.py, no en
  proteo/forecasts/registry.py como decía el prompt (registry guarda y
  verifica datos; la página redacta). El cambio se hizo en la página.
- brand_lockup alinea el wordmark con align-items:flex-end (los SVG no
  exponen línea base tipográfica).
- page_setup importa components de forma perezosa solo en el fallback
  sin st.logo, para evitar el import circular theme ↔ components.
