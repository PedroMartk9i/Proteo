# STATUS de Proteo — v1.0

Última sesión: 2026-09-03. Empaquetado v1.0: arranque con doble clic,
ventana propia opcional, README completo y limpieza final.

## Qué hace (v1.0)

- **Datos**: descarga con un clic de Niño 3.4 y RONI (NOAA/CPC) y del
  precio de bolsa nacional (XM vía pydataxm). Cada descarga es un
  vintage fechado que nunca se sobrescribe. Exportar CSV por índice.
- **Entrenar**: SARIMAX con exógena opcional (RONI o Niño 3.4), rezago
  configurable, término cuadrático, objetivo nivel/log, preset del
  paper, diagnósticos (AIC/BIC/Ljung-Box), configuración activa en JSON.
- **Backtest**: origen móvil contra naive y naive estacional, métricas
  por horizonte, mejora por incluir RONI, Diebold-Mariano con HLN,
  desglose por fase ENSO, cobertura, corridas guardadas y recargables.
  Benchmark de agosto 2026 reproducido (ver historial v0.4).
- **Pronósticos**: emisión por temporada CPC con registro inmutable
  (registry.parquet + JSON por emisión), verificación contra lo
  observado, scorecard y boletín markdown. Primer pronóstico real:
  20260903-sarimax-01, OND 2026.
- **Arranque**: `run.bat` (navegador) y `run_desktop.bat` (ventana
  nativa pywebview 1400×900 que al cerrarse mata el servidor). Tema y
  puerto fijos en `.streamlit/config.toml`. README con instalación en
  tres pasos, flujo de uso, cómo agregar fuentes, citas y créditos.
- Calidad: 46 tests en verde con `filterwarnings = error` (cero
  warnings), `compileall` limpio, requirements con versiones fijadas.

## Qué no hace todavía (límites conocidos)

- El RONI futuro NO se pronostica: persistencia del último valor
  observado a partir del paso `lag+1`. La interfaz y el boletín lo
  advierten.
- El backtest usa un solo vintage (el más reciente) para todas las
  fechas; el backtest "como si fuera esa fecha" llegará cuando la app
  acumule vintages históricos.
- La app es local (navegador o ventana propia); no hay despliegue web
  ni multiusuario.
- Créditos del README: falta completar grupo de investigación y
  coautores del trabajo de origen (marcados "por completar").
- Capturas del README: marcadores listos en docs/img/, las pone Pedro.

## Pendiente operativo

- Cuando XM publique septiembre 2026: Datos → descargar XM →
  Pronósticos → "Verificar pendientes". Primera verificación real.

## Después de v1.0 (ideas, en orden de valor)

1. RONI futuro con el pronóstico oficial de CPC en vez de persistencia.
2. Backtest "como si fuera esa fecha" con vintages históricos.
3. Segundo modelo con machine learning (segundo paper) bajo la misma
   interfaz Model, comparable en el mismo backtest.
4. Caudales o aportes hídricos de XM como exógena adicional.

## Decisiones tomadas (v1.0)

- Fases 1-5: ver historial de STATUS en git (v0.1-v0.5).
- pywebview agregado a requirements.txt (ventana nativa opcional).
- requirements.txt fijado a las versiones instaladas y probadas (pip
  freeze filtrado a dependencias directas).
- `pytest.ini` con `filterwarnings = error`: la suite está limpia hoy y
  cualquier warning futuro debe corregirse o justificarse por escrito.
- run.bat abre el navegador solo cuando el puerto 8765 responde (un
  vigilante PowerShell en segundo plano); el servidor corre en primer
  plano para que cerrar la ventana lo detenga y los errores se lean
  (pause al fallar).
- desktop.py mata el árbol completo del subproceso con taskkill /T /F:
  verificado que no queda nada escuchando el 8765 al cerrar la ventana.
- Tema de config.toml con la paleta de guia_diseno_figuras.md. El Niño
  conserva el cálido #d94a3d de la guía ("rojo para cálido... no se
  invierte por ningún motivo"), que cumple el rol del "naranja" pedido.
