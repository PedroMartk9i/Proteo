# STATUS de Proteo — v1.2

Última sesión: 2026-09-03. Sistema "caja beige" aplicado a las cuatro
páginas, con revisión de accesibilidad y consistencia.

## Qué hace (v1.2)

- Todo lo de v1.0-v1.1 (ver historial): datos con vintages, SARIMAX
  interactivo, backtest, pronósticos con registro inmutable, arranque
  con doble clic, sistema de diseño en Inicio y Datos.
- Entrenar rediseñada: barra lateral como panel de instrumento (grupos
  con borde, etiqueta mono arriba y valor actual a la derecha con
  `components.control_header`), Entrenar único primario, métricas con
  metric_card, fila de la exógena con fondo banda y p<0.05 en peso 500,
  gráfica con bandas ENSO al fondo (cuando la exógena es RONI),
  ajustado en tinta y pronóstico en nino discontinuo, panel de exógena
  con futuros observados por signo (nino/nina) y supuestos en tinta,
  advertencia de persistencia como st.info.
- Backtest rediseñada: progreso con tiempo en mono, métricas con
  NumberColumn a dos decimales, mejora % coloreada (positivo nino,
  negativo nina), Diebold-Mariano como heatmap papel→panel con celdas
  p<0.05 anotadas en linea, fases ENSO en tres columnas con metric_card
  y LED por fase (+ tabla completa en expander), error absoluto con el
  colorway del template.
- Pronósticos rediseñada: cabecera con data_header de la config activa
  (LED por frescura de saved_at), flujo en dos pasos con Confirmar y
  registrar como único primario, historial con LED de estado por
  pronóstico, gráfica con código de color (dentro=nina, fuera=nino,
  pendiente=tinta) explicado en la leyenda, boletín con el mismo
  vocabulario de la interfaz (observada / supuesta (persistencia),
  pendiente / verificado, intermedio / objetivo / extendido).
- Accesibilidad: tests/test_theme.py verifica 4.5:1 (AA) en los seis
  pares texto/fondo. Foco visible teal en botones y controles. Ningún
  color literal fuera de app/theme.py (grep en verde).
- Capturas reales de las cinco páginas en docs/img/ (backtest.png
  muestra una corrida completa nueva: 112 orígenes, mejora +0.8% a
  +3.8% por horizonte).
- 52 tests en verde; proteo/ intacto.

## Cambios de paleta por accesibilidad (avisar a Pedro)

- tinta: #7A736A → #625B53 (el original daba 3.3:1 sobre panel).
- nina: #2F8F8A → #22706D (papel sobre el original daba 3.2:1; además
  la lista de pares del spec exigía papel/nina ≥ 4.5:1).
- banda_nina y la grilla del template se derivan de los nuevos valores.
- docs/style_tile.html y .streamlit/config.toml actualizados con los
  mismos valores. PALETTE tiene un token derivado extra, banda_tinta
  (tinta al 15 %), para las bandas de pronósticos pendientes.

## Qué no hace todavía

- Límites de v1.0 sin cambio: RONI futuro por persistencia, backtest
  con un solo vintage, app local.
- README: completar grupo de investigación y coautores.

## Pendiente operativo

- Cuando XM publique septiembre 2026: Datos → Descargar XM →
  Pronósticos → Verificar pendientes. Hay 12 filas pendientes (dos
  pronósticos de OND 2026).

## Decisiones tomadas (v1.2)

- Grupos de la barra lateral con st.container(border=True) +
  control_header; los valores del encabezado salen de session_state
  (por eso h y confianza ahora tienen clave).
- El heatmap DM anota TODOS los p-valores (tinta) y los significativos
  en linea, sin barra de color; diagonal vacía.
- Las bandas de intervalo usan mode="none" en el trace de relleno: sin
  él, el template pinta marcadores en el borde de la banda.
- El desglose por fase muestra RMSE (media sobre horizontes) por modelo
  en metric_cards y conserva la tabla completa en un expander.
- Ojo al probar con la app abierta: un servidor viejo en el 8765
  mantiene módulos importados (theme/components) cacheados y mezcla
  código nuevo de páginas con módulos viejos; reiniciar el servidor
  tras cambiar app/theme.py o app/components.py.
