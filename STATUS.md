# STATUS de Proteo

Última sesión: 2026-09-03. Fase 3 — dataset de modelado, modelos base y
página Entrenar.

## Funciona

- Fases 1 y 2 completas (v0.1, v0.2): contrato de datos, vintages, los
  tres adaptadores y la página Datos con gráfica de dos ejes.
- `proteo/dataset.py` (funciones puras): `build_dataset` (series al
  calendario mensual "MS" completo, rezago POR CALENDARIO con shift sobre
  el índice, término cuadrático opcional, log opcional, recorte y dropna),
  `inverse_transform`, y `future_exog` con persistencia y columna
  `assumed` (con lag=2, pasos 1-2 observados y 3+ supuestos).
- `proteo/models/`: `base.Model` (fit/forecast/fitted/summary),
  `naive.Naive` y `naive.SeasonalNaive` con intervalos de camino
  aleatorio, `sarimax.SARIMAXModel` (statsmodels, enforce_* en False,
  summary con coeficientes/aic/bic/n_obs/ljung_box_p a 12 rezagos),
  `MODELS` en `__init__` y `presets.PAPER`.
- Tests en verde (`pytest -q`: 24 passed): rezago por calendario
  sobrevive a un mes borrado, cuadrático, log ida y vuelta 1e-9,
  future_exog 2+4, naives, AR(1) recupera phi (0.55-0.85), exógena
  sintética recupera beta=2 con p<0.01.
- Página Entrenar: barra lateral completa (vintages, rango, objetivo
  nivel/log, exógena con rezago 0-6 y cuadrático, órdenes, h, confianza),
  botón preset del paper, métricas AIC/BIC/Ljung-Box/n_obs, tabla de
  coeficientes con exógena resaltada, gráfica observado/ajustado/
  pronóstico con banda y línea de fin de entrenamiento, panel de la
  exógena con supuestos en naranja, advertencia de persistencia cuando
  h > lag, guardado de config/active_model.json y descarga CSV.
  st.cache_data: volver a parámetros ya calculados no reentrena
  (verificado: 0.5s primer entrenamiento, 0.1s cacheado).
- Verificación del paper con datos reales (vintage 2026-09-03, rango
  2000-01 → 2026-07, n=319): RONI rezago 2 positivo y significativo.
  En nivel: beta=85.71, p=1.1e-06. En log: beta=0.286, p=9.0e-06 (la
  referencia beta≈0.25 del paper corresponde a la escala log).
  Ljung-Box p=0.40 (sin autocorrelación residual).

## Falta

- Backtest de origen móvil, métricas por horizonte (MAE/RMSE/MAPE),
  Diebold-Mariano y página 3_Backtest.
- Registro de pronósticos (`forecasts/registry.py`), verificación contra
  lo observado y página 4_Pronosticos (leerá config/active_model.json).

## Siguiente prompt

Fase 4, backtest: `proteo/backtest/rolling_origin.py` (entrenar hasta t,
pronosticar t+1..t+h, avanzar un mes, repetir), `metrics.py` (MAE, RMSE,
MAPE por horizonte; sin MAPE si la serie cruza cero), `dm_test.py`
(Diebold-Mariano) y página 3_Backtest comparando SARIMAX contra los dos
naive con los vintages correctos por fecha de origen.

## Decisiones tomadas

- Fases 1-2: ver historial de STATUS en git (v0.1, v0.2).
- statsmodels y scipy agregados a requirements.txt (los exigen SARIMAX,
  Ljung-Box y los cuantiles normales de los naive).
- El rezago es siempre por calendario: la serie se reindexa al calendario
  mensual completo antes de shift, así un mes faltante queda NaN y no
  corre el rezago (test explícito con mes borrado).
- v1: el RONI futuro NO se pronostica; persistencia del último observado,
  documentado en future_exog y advertido en la interfaz.
- `future_exog` acepta `add_squared` (extra sobre el spec) para que
  X_future case con las columnas de build_dataset.
- La página Entrenar muestra todo en NIVEL aunque se entrene en log
  (inverse_transform antes de graficar).
- config/active_model.json está en .gitignore: es estado de ejecución,
  no código. La página Pronósticos debe tolerar que no exista.
- Controles con clave usan defaults vía session_state.setdefault y
  widgets sin valor propio (evita el warning default/estado de Streamlit
  y permite que el preset del paper escriba session_state).
- Paleta de guia_diseno_figuras.md aplicada a Plotly: observado #22303f,
  SARIMAX #1d4ed8, banda alfa 0.15, supuestos #c2410c, umbrales
  #d94a3d/#2f6fb0.
