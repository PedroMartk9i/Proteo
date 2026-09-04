# STATUS de Proteo

Última sesión: 2026-09-03. Fase 4 — backtest de origen móvil, métricas,
Diebold-Mariano y página Backtest.

## Funciona

- Fases 1-3 completas (v0.1-v0.3): datos + vintages, dataset de
  modelado, modelos (naive, naive estacional, SARIMAX) y página Entrenar.
- `proteo/backtest/rolling_origin.py`: `run_backtest` con ventana
  expanding/rolling, `refit_every` (los orígenes intermedios extienden la
  muestra con `append` de statsmodels sin reoptimizar), exógena futura
  por origen construida con `future_exog` usando SOLO datos hasta t
  (reconstruye la exógena sin rezago desde las columnas de X y la corta
  en el origen), callback de progreso y `label` para variantes.
- `proteo/backtest/metrics.py`: `by_horizon` (n, mae, rmse, mape, smape),
  `skill` (1 - m/b, positivo = mejora), `by_enso_phase` (nino/nina/
  neutral por RONI en el origen, con n) y `coverage`.
- `proteo/backtest/dm_test.py`: Diebold-Mariano con pérdida cuadrática o
  absoluta, varianza de largo plazo con autocovarianzas hasta h-1,
  corrección HLN de muestra pequeña, t de Student n-1. stat < 0 = el
  modelo 1 pierde menos. Empate exacto → stat 0, p 1.
- Tests en verde (`pytest -q`: 37 passed; 13 nuevos).
- Página Backtest: multiselect de 4 modelos (naive, naive estacional,
  SARIMAX sin/con exógena, estos dos con la config activa o el preset),
  controles (initial_train 203, horizontes 1-6, ventana, refit_every,
  rango, vintages), barra de progreso con tiempo, métricas por modelo y
  horizonte, mejora % por incluir RONI, matriz DM por pestañas con
  p<0.05 resaltado, desglose por fase ENSO, error absoluto en el tiempo,
  cobertura de intervalos, y cada corrida guardada en
  data/backtests/<fecha_hora>.parquet + .json con selector de recarga.

## Benchmark de agosto 2026: reproducido

Con initial_train=203, horizontes 1-6, expanding, preset del paper
(datos reales, vintage 2026-09-03, n=319):

- Mejora por incluir RONI, TODOS los horizontes positivos. En MAE crece
  monótona: +0.4% (h=1) → +4.9% (h=6), consistente con la referencia
  (≈+1% → ≈+5.7%). En RMSE: +0.8% → +3.8% (pico h=3-4).
  LA REFERENCIA DEL BENCHMARK PARECE SER MAE, no RMSE.
- Fase El Niño: n=15 orígenes (igual que la referencia), mejora MAE
  +14.5% en h=3 (+5 a +10% en h=1-4), referencia ≈+10%.
- Diebold-Mariano RONI vs sin-RONI: stat negativo en los 6 horizontes
  (RONI pierde menos) y ningún p < 0.05 (mínimo p=0.19 en h=3), igual
  que la referencia.
- Truncar a abril 2026 no cambia el perfil: no hay bug de alineación.

## Falta

- Registro de pronósticos (`forecasts/registry.py`): guardar cada
  pronóstico emitido y verificarlo contra el valor observado después.
- Página 4_Pronosticos (lee config/active_model.json, que ya existe).

## Siguiente prompt

Fase 5, registro de pronósticos: `proteo/forecasts/registry.py` con
emitir (modelo activo + vintages del día, guardar DataFrame de
pronóstico con fecha de emisión), listar, y verificar (cruzar cada
pronóstico emitido con el valor observado cuando llegue). Página
4_Pronosticos: botón "Emitir pronóstico", tabla de pronósticos vivos y
verificados con su error, y gráfica pronóstico vs observado.

## Decisiones tomadas

- Fases 1-3: ver historial de STATUS en git (v0.1-v0.3).
- El backtest usa un solo vintage (el más reciente) para todas las
  fechas; la advertencia está en el docstring y el parámetro `vintage`
  queda expuesto para cuando existan vintages históricos acumulados.
- `run_backtest` recibe X ya rezagada (como sale de build_dataset) y
  reconstruye la exógena sin rezago parseando el nombre de columna
  (`roni_lag2`), para cortarla en cada origen sin mirar el futuro.
  Extensiones sobre el spec: `label` (distinguir variantes en la columna
  model) y `vintage` (futuro).
- `refit_every>1`: con ventana rolling siempre reentrena (append no
  aplica si la ventana pierde observaciones por el inicio); los naive
  reentrenan siempre (son gratis).
- Los intervalos del backtest usan el alpha por defecto de los modelos
  (0.2), por eso la tabla de cobertura dice "nominal 80%".
- data/backtests/ cae bajo el gitignore de /data/: las corridas son
  locales, reproducibles con el JSON de configuración adjunto.
- La tabla de mejora de la página usa RMSE (skill por defecto); el
  hallazgo de que la referencia parece MAE quedó documentado arriba.
