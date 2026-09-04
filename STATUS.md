# STATUS de Proteo

Última sesión: 2026-09-03. Fase 2 — adaptadores RONI y XM, página Datos completa.

## Funciona

- Fase 1 completa (ver commit v0.1): schema, vintages, adaptador nino34,
  portada y página Datos con Niño 3.4.
- `proteo/data/roni.py`: mismo patrón que nino34. `parse()` mapea cada
  temporada a su mes central (DJF→01 … NDJ→12) con el año de la fila.
- `proteo/data/xm.py`: `fetch_raw(start, end)` descarga PrecBolsNaci por
  tramos anuales con pydataxm (import perezoso dentro de la función);
  `aggregate_monthly()` (pura) = promedio simple de todas las horas del mes.
  Reproduce `examples/promedio_mensual.csv`: 320/320 meses, diff máx 2.3e-13.
- Tests en verde (`pytest -q`: 11 passed). Sin red: fixtures inline de
  CLAUDE.md, año sintético de 12 temporadas para RONI, y el par
  crudo→promedio de examples/ para XM (tol 1e-6).
- Página Datos: tres botones activos + "Descargar todo" con resumen,
  tabla de vintages por índice, gráfica de dos ejes (Niño 3.4 y RONI a la
  izquierda con umbrales ±0.5, precio XM a la derecha) y slider de rango
  de fechas.
- Descargas reales verificadas 2026-09-03, vintages guardados en
  `data/raw/` y `data/processed/` para los tres índices:
  - nino34: 918 filas, último junio 2026 = 1.44.
  - roni: 919 filas, último julio 2026 (JJA) = 1.36; junio (MJJ) = 0.97.
  - xm_precio_bolsa: 320 filas, último agosto 2026 = 945.00; enero 2000
    reproduce la verdad de examples/ exacto.

## Falta

- Modelos: `base.py`, `naive.py` (naive y estacional 12), `sarimax.py`
  (statsmodels, aún no está en requirements.txt — avisar al agregarlo).
- Backtest de origen móvil, métricas por horizonte, Diebold-Mariano.
- Registro de pronósticos (`forecasts/registry.py`) y páginas 2, 3 y 4.

## Siguiente prompt

Fase 3, modelos: `proteo/models/base.py` (interfaz `fit(y, X)` /
`forecast(h, X_future)` → DataFrame[date, mean, lower, upper]),
`naive.py` con los dos baselines, `sarimax.py` con statsmodels
(agregar statsmodels a requirements.txt) y la configuración de referencia
SARIMAX(1,1,1)(1,0,0)12 con RONI rezagado 2 meses como exógena. Tests con
series sintéticas. Página 2_Entrenar con selectores de parámetros.

## Decisiones tomadas

- Fase 1: crudo Niño 3.4 = `sstoi.indices_…txt` (última columna), formateado =
  `Data-8-28.csv` (`nino34_anom`). `parse()` fuerza `datetime64[ns]`.
  `.gitignore` ancla `/data/*` a la raíz para no ignorar `proteo/data/`.
- pydataxm agregado a requirements.txt (lo exige el adaptador XM). `ReadDB`
  se importa de `pydataxm.pydataxm` (no del paquete raíz), y solo dentro de
  `fetch_raw` para que los tests no dependan del paquete.
- El crudo de XM en examples/ trae columnas `Daily Average` y
  `Monthly Average` precalculadas que pydataxm NO devuelve; el adaptador
  las ignora y calcula solo desde `Values_Hour01…24`.
- `promedio_mensual.csv` usa fechas MM/DD/YYYY; agosto 2026 difiere de la
  descarga de hoy (933.07 vs 945.00) porque el archivo se cortó el 28 de
  agosto con el mes incompleto. No es un error del adaptador.
- NOAA revisó RONI hacia atrás: CLAUDE.md documenta MJJ 2026 = 0.98
  (verificado 2026-09-03 en la redacción) pero el archivo de hoy trae 0.97.
  Confirmación práctica del porqué de los vintages. El fixture inline de
  los tests sigue usando 0.98 de CLAUDE.md (parse es puro, no importa).
- Deprecación de Streamlit: `st.plotly_chart(..., width="stretch")` en vez
  de `use_container_width=True`.
