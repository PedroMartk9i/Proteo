# STATUS de Proteo

Última sesión: 2026-09-03. Fase 5 — emisión por temporada, registro
inmutable, verificación y boletín. LAS CINCO PÁGINAS ESTÁN COMPLETAS.

## Funciona

- Fases 1-4 completas (v0.1-v0.4): datos + vintages, dataset, modelos,
  página Entrenar, backtest con benchmark reproducido.
- `proteo/forecasts/seasons.py`: temporadas CPC con año del mes central
  (NDJ 2026 = nov'26-ene'27). `next_season`: la temporada objetivo
  empieza 2 meses después del último dato (el mes siguiente es paso
  intermedio). Último dato agosto 2026 → OND 2026, como el spec.
- `proteo/forecasts/registry.py`: `issue` (registry.parquet + JSON por
  forecast_id YYYYMMDD-modelo-NN), `verify` (INMUTABLE: una fila
  verificada no se toca aunque llegue un valor revisado), `pending`,
  `scorecard`, `load`, `history`, `load_config`. Todo con `root` para
  tests con tmp_path.
- Página Pronósticos: cabecera con config activa (remite a Entrenar si
  falta), preparar → tabla y gráfica con pasos supuestos marcados →
  notas → confirmar y registrar; verificación contra el vintage más
  reciente de XM con mensaje claro cuando no hay nada que verificar;
  historial con gráfica de segmentos coloreados por resultado;
  scorecard; boletín markdown por temporada.
- Página Datos: botón "Exportar CSV" por índice (utf-8-sig para Excel).
- Tests en verde (`pytest -q`: 46 passed; 9 nuevos de seasons/registry
  + 1 de regresión del bug de rezago).
- PRIMER PRONÓSTICO REAL EMITIDO: 20260903-sarimax-01, temporada
  OND 2026, 6 pasos (sep'26-feb'27), vintages 2026-09-03, notas, con
  boletín en data/forecasts/boletin_OND_2026.md. "Verificar pendientes"
  responde correctamente que sep'26 aún no existe en XM.

## Falta

- Verificar el pronóstico emitido cuando XM publique septiembre 2026
  (descargar XM en Datos → Pronósticos → "Verificar pendientes").
- Ideas de mejora, no comprometidas: selector de métrica (MAE/RMSE) en
  la tabla de mejora del backtest, backtest con vintages históricos
  cuando se acumulen, pronóstico del RONI en vez de persistencia (v2).

## Siguiente prompt

Mantenimiento mensual: descargar los tres índices (vintage nuevo),
verificar pendientes, emitir el pronóstico de la siguiente temporada y
exportar el boletín. O bien: mejoras de la lista de arriba.

## Decisiones tomadas

- Fases 1-4: ver historial de STATUS en git (v0.1-v0.4).
- BUG CORREGIDO en dataset.py (detectado y avisado en esta sesión):
  shift(lag) posicional recortaba la cobertura de X al calendario propio
  de la exógena, perdiendo los últimos `lag` meses del precio cuyo valor
  rezagado SÍ estaba observado (entrenaba hasta julio en vez de agosto y
  la temporada salía SON en vez de OND). Ahora shift(lag, freq="MS")
  desplaza el índice por calendario. Test de regresión incluido. El
  coeficiente del paper apenas se mueve: 75.68 (p=2.7e-05) con n=320.
- Convención de temporada: etiqueta con el año del MES CENTRAL (igual
  que RONI en CLAUDE.md). El boletín marca cada paso como intermedio /
  objetivo / extendido.
- Inmutabilidad del registro: verify solo toca filas con verified_at
  NaN; el pronóstico se juzga contra el PRIMER valor observado, no
  contra revisiones posteriores.
- inside_interval se guarda como float (0/1/NaN) por compatibilidad de
  parquet; issued_at/verified_at como texto ISO.
- El registro real (data/forecasts/) queda fuera de git por el
  gitignore de /data/. El respaldo es responsabilidad del entorno
  (OneDrive lo cubre en esta máquina).
