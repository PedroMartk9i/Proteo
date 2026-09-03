# STATUS de Proteo

Última sesión: 2026-09-03. Fase 1 — descarga de Niño 3.4 con un clic.

## Funciona

- Estructura del núcleo `proteo/` (sin Streamlit) y de la interfaz `app/`.
- `proteo/schema.py`: `COLUMNS` y `validate(df)` con mensajes en español que
  dicen exactamente qué falló (columnas/orden, `date` datetime64[ns] sin tz,
  `value` float64 sin NaN, `index` permitido, `source` texto, `vintage` como
  `datetime.date`, fechas sin duplicar y ascendentes).
- `proteo/store/vintages.py`: `save_raw`, `save_processed`, `list_vintages`,
  `load` (con `None` carga el más reciente). Aceptan `root` para tests con
  `tmp_path`. Vintage roundtrip por parquet conserva `datetime.date`.
- `proteo/data/nino34.py`: adaptador de referencia. `URL`, `fetch_raw()` (red),
  `parse()` (pura, usa la última columna), `download()` (fetch → save_raw →
  parse → validate → save_processed).
- Tests en verde (`pytest -q`: 6 passed): fixture inline de CLAUDE.md, archivo
  crudo de `examples/` vs. formateado (tol. 1e-9), `validate` rechaza fechas
  duplicadas, y vintages (orden y carga del más reciente).
- App: `app/Home.py` (portada) y `app/pages/1_Datos.py` (botón de descarga,
  tabla de vintages, gráfica Plotly con umbrales ±0.5, fallback a último
  vintage si falla la red). RONI y XM visibles pero deshabilitados.
- Descarga real verificada 2026-09-03: 918 filas (1950-01 → 2026-06),
  último valor junio 2026 = 1.44. Vintage guardado en `data/raw/nino34/` y
  `data/processed/nino34/`.

## Falta

- Adaptador RONI (`proteo/data/roni.py`), mismo patrón que nino34.
- Adaptador XM (`proteo/data/xm.py`): `fetch_raw` por tramos anuales +
  `aggregate_monthly` (probar contra `examples/promedio_mensual.csv`, tol 1e-6).
- Modelos (`base`, `naive`, `sarimax`), backtest y registro de pronósticos.
- `statsmodels` y `pydataxm` NO están aún en `requirements.txt` (se agregan en
  las sesiones que los necesiten, avisando).

## Siguiente prompt

Adaptador RONI copiando el patrón de `nino34.py`: `URL` de `RONI.ascii.txt`,
`parse()` que mapea SEAS→mes central (DJF=01, JFM=02, …, NDJ=12) con el año de
la fila, `download()`, y `tests/test_roni.py` con fixture inline de CLAUDE.md +
comparación contra el crudo. Botón "Descargar RONI" activo en la página Datos.

## Decisiones tomadas

- Identificación de fixtures de Niño 3.4 en `examples/`: crudo =
  `sstoi.indices_20260804T125949Z.txt` (formato `YR MON … NINO3.4 ANOM`,
  última columna); formateado = `Data-8-28.csv` (columna `nino34_anom`).
- `parse()` fuerza `datetime64[ns]` porque pandas 2.x deriva `[s]` desde
  objetos `date`, y el contrato exige `[ns]`.
- `save_raw` escribe `.txt` para texto y `.csv` para DataFrame; `vintage` en
  disco como `YYYY-MM-DD`.
- Dos descargas el mismo día → mismo archivo (se reemplaza), como manda el
  contrato de vintages.
- `requirements.txt` incluye solo lo usado esta sesión: pandas, numpy,
  requests, pyarrow, plotly, streamlit, pytest.
