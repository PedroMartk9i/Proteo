# Fuentes de datos (verificadas 2026-09-03)

| Índice | URL / API | Formato | Inicio | Último valor visto |
|--------|-----------|---------|--------|--------------------|
| Niño 3.4 mensual, ERSSTv5, base 1991-2020 | https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii | texto, cabecera + `YR MON NINO1+2 ANOM NINO3 ANOM NINO4 ANOM NINO3.4 ANOM`; usar la última columna | 1950-01 | 2026-06 = 1.44 |
| RONI, media móvil 3 meses, base 1991-2020 | https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt | texto, `SEAS YR ANOM`; temporada → mes central | DJF 1950 | MJJ 2026 = 0.98 |
| Precio de bolsa nacional (XM) | `pydataxm.ReadDB().request_data("PrecBolsNaci", "Sistema", inicio, fin)` | DataFrame diario con 24 columnas de hora, COP/kWh; agregar a promedio mensual | 2000-01 | ver `promedio_mensual` en esta carpeta |

Cadencia de actualización de NOAA: mensual, normalmente en los primeros días
del mes siguiente. Por eso cada descarga se guarda como vintage.

Nota sobre el CSV de RONI desde 1850 que está en esta carpeta: no proviene de
CPC (la serie oficial arranca en 1950); es una reconstrucción externa y se
trata como archivo estático, no como fuente descargable.
