# STATUS de Proteo — v1.1

Última sesión: 2026-09-03. Sistema de diseño "caja beige" (variante B)
aplicado a Inicio y Datos.

## Qué hace (v1.1)

- Todo lo de v1.0 (ver historial): datos con vintages, SARIMAX
  interactivo, backtest con benchmark reproducido, pronósticos con
  registro inmutable, arranque con doble clic.
- Sistema de diseño "caja beige" como código reutilizable:
  - `app/theme.py`: PALETTE (papel, panel, linea, tinta, nino, nina,
    bandas), IBM Plex Sans/Mono con fallback del sistema,
    `BRUTAL_ACCENT = True` (variante B: sombras duras 4px 4px 0 en
    tinta, radio 4 px, primario que se hunde), `inject_css()`,
    template Plotly "proteo" como default, `PLOTLY_CONFIG`,
    `add_enso_bands()` (agrupa meses consecutivos en un rectángulo)
    y `add_threshold_lines()`.
  - `app/components.py`: `led` (naranja hoy / teal < 7 días / tinta),
    `vintage_stamp`, `metric_card`, `data_header`, `appbar`, `section`.
  - `.streamlit/config.toml`: theming nativo completo de Streamlit 1.63
    (colores, borderColor, radios 4px, fuentes Plex, dataframe, charts).
- Inicio: appbar con wordmark mono + LED + sello, frase, tres
  data_header y enlace a Datos. Sin emojis.
- Datos: "Descargar todo" único primario; gráfica con template proteo,
  precio (linea) a la izquierda, Niño 3.4 (nino) y RONI (nina) a la
  derecha con umbrales y bandas ENSO; tabla de vintages con DateColumn;
  estados vacíos con la voz del tile ("No hay vintage de RONI todavía.
  Pulsa Descargar RONI.").
- Capturas reales de Inicio y Datos en docs/img/ (home.png, datos.png),
  tomadas de la app corriendo.
- CLAUDE.md: sección "## Diseño" con las reglas del sistema.
- 46 tests en verde (el diseño no toca proteo/).

## Qué no hace todavía

- Entrenar, Backtest y Pronósticos siguen con el estilo anterior: se
  migran al sistema en la siguiente sesión (usar theme + components,
  quitar sus diccionarios COLOR locales y emojis).
- Límites de v1.0 sin cambio: RONI futuro por persistencia, backtest
  con un solo vintage, app local.
- README: faltan capturas de las otras tres páginas (los marcadores ya
  existen) y completar grupo de investigación y coautores.

## Siguiente prompt

Aplicar el sistema "caja beige" a 2_Entrenar, 3_Backtest y
4_Pronosticos: reemplazar sus diccionarios COLOR por PALETTE, activar
el template proteo y PLOTLY_CONFIG en todas las gráficas, usar
add_enso_bands/add_threshold_lines en el panel de exógena, metric_card
para las métricas, data_header/section/appbar donde aplique, quitar
emojis de set_page_config, y capturar entrenar.png, backtest.png y
pronosticos.png para el README.

## Decisiones tomadas (v1.1)

- Variante elegida por Pedro: B (acento brutalista).
- `inject_css()` se inyecta en CADA ejecución del script, no una vez
  por sesión como decía el spec: Streamlit vacía el DOM en cada rerun y
  con la bandera en session_state la página quedaría sin estilo tras el
  primer clic. La regla de uso es "una llamada por página, en la
  cabecera". Documentado en el docstring.
- El eje de índices ENSO pasó al lado derecho (y2) y el precio al
  izquierdo, como pide la firma de add_threshold_lines(yref="y2").
- `data_header(name, index, vintage)` lleva nombre visible e índice
  separados (el índice va en el title del sello).
- Capturas con Chrome headless vía CDP (scratchpad/shot.py) porque
  --screenshot con virtual-time-budget no espera el websocket de
  Streamlit y salía la página vacía.
- style_tile.html movido de la raíz a docs/style_tile.html (la ruta que
  usa CLAUDE.md).
