# Proteo

Estudio visual para ENSO y precio de bolsa en Colombia. Descarga con un clic
Niño 3.4 y RONI (NOAA/CPC) y el precio de bolsa nacional (XM), entrena modelos
SARIMAX con RONI como regresor exógeno, permite mover parámetros y ver el
resultado, hace backtest de origen móvil y registra cada pronóstico emitido
para verificarlo después contra el valor observado.

Autor: Pedro Martínez (UNAB, Bucaramanga). Idioma del proyecto: español en
docstrings, comentarios, textos de la interfaz, STATUS.md y mensajes de commit.
Nombres de variables, funciones y archivos en inglés.

## Reglas que no se negocian

1. `proteo/` (núcleo) no importa Streamlit nunca. `app/` solo llama funciones
   de `proteo/`. Si algo se necesita en la interfaz, primero existe en el núcleo.
2. Nunca sobrescribir datos descargados. Cada descarga es un *vintage*
   (copia fechada). Ver la sección Vintages.
3. Todo adaptador de datos devuelve el MISMO DataFrame. Ver Contrato de datos.
4. Descarga y parseo son funciones separadas: `fetch_raw()` toca la red,
   `parse()` es pura (texto de entrada, DataFrame de salida). Los tests solo
   prueban `parse()` y las funciones puras, con fixtures tomados de `examples/`.
   Los tests nunca tocan la red.
5. Cada módulo nuevo lleva su archivo de test en `tests/`.
6. Terminado significa: `pytest -q` en verde Y la funcionalidad visible al
   correr `streamlit run app/Home.py`. No declarar terminado antes de eso.
7. Una tarea por sesión. No adelantar módulos que no se pidieron en el prompt.
8. Al cerrar cada sesión, actualizar `STATUS.md`: qué funciona, qué falta,
   cuál es el siguiente prompt. Es lo primero que se lee al retomar.
9. Windows: rutas con `pathlib`, y todo `open()` con `encoding="utf-8"`.
10. No agregar dependencias fuera de `requirements.txt` sin avisar.

## Estructura

```
proteo/                 # núcleo, sin Streamlit
  schema.py             # contrato de datos: COLUMNS, validate(df)
  data/
    nino34.py           # adaptador Niño 3.4 (referencia para los demás)
    roni.py             # adaptador RONI, mismo patrón que nino34
    xm.py               # adaptador precio de bolsa XM vía pydataxm
  store/
    vintages.py         # guardar y cargar vintages
  models/
    base.py             # interfaz común: fit(y, X), forecast(h, X_future)
    naive.py            # naive y naive estacional (12)
    sarimax.py          # SARIMAX de statsmodels con exógena opcional
  backtest/
    rolling_origin.py   # origen móvil
    metrics.py          # MAE, RMSE, MAPE por horizonte
    dm_test.py          # prueba Diebold-Mariano
  forecasts/
    registry.py         # registro de pronósticos emitidos y su verificación
app/
  Home.py               # portada
  pages/
    1_Datos.py
    2_Entrenar.py
    3_Backtest.py
    4_Pronosticos.py
data/                   # ignorado por git salvo data/.gitkeep
  raw/<index>/<YYYY-MM-DD>.<ext>
  processed/<index>/<YYYY-MM-DD>.parquet
examples/               # fixtures reales: crudos y salidas esperadas (solo lectura)
tests/
STATUS.md
requirements.txt
```

## Contrato de datos

Todo adaptador devuelve un `pandas.DataFrame` con exactamente estas columnas,
en este orden:

| date       | value | index  | source                                                   | vintage    |
|------------|-------|--------|----------------------------------------------------------|------------|
| 2024-01-01 | 1.81  | nino34 | https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii | 2026-09-03 |
| 2024-02-01 | 1.52  | nino34 | https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii | 2026-09-03 |

- `date`: `datetime64[ns]`, primer día del mes, sin zona horaria.
- `value`: `float64`. Sin NaN.
- `index`: `str`, uno de `nino34`, `roni`, `xm_precio_bolsa`.
- `source`: `str`, la URL o `pydataxm:PrecBolsNaci`.
- `vintage`: `datetime.date` de la descarga (YYYY-MM-DD).
- Orden ascendente por `date`, sin fechas duplicadas.

`proteo/schema.py` expone `COLUMNS` y `validate(df)`, que lanza `ValueError`
con un mensaje claro si algo falla. Todo adaptador llama `validate()` antes de
devolver.

## Fuentes y formatos crudos (few-shot)

Estos son los formatos reales verificados el 2026-09-03. Los adaptadores deben
reproducir exactamente estas parejas entrada→salida.

### Niño 3.4 mensual (ERSSTv5, base 1991-2020)

URL: `https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii`

Texto plano, columnas separadas por espacios de ancho variable. Una cabecera y
una fila por mes. Se usa la ÚLTIMA columna (ANOM de NINO3.4). Las otras
regiones (1+2, 3, 4) se ignoran.

Entrada:
```
 YR   MON  NINO1+2  ANOM   NINO3    ANOM   NINO4    ANOM   NINO3.4  ANOM
1950   1   23.01   -1.55   23.56   -2.10   26.94   -1.38   24.55   -1.99
1950   2   24.32   -1.78   24.89   -1.52   26.67   -1.53   25.06   -1.69
2026   6   25.94    2.82   28.33    1.71   30.19    1.22   29.17    1.44
```

Salida (vintage 2026-09-03):
```
date        value  index   source                          vintage
1950-01-01  -1.99  nino34  https://www.cpc.ncep.noaa.gov/... 2026-09-03
1950-02-01  -1.69  nino34  https://www.cpc.ncep.noaa.gov/... 2026-09-03
2026-06-01   1.44  nino34  https://www.cpc.ncep.noaa.gov/... 2026-09-03
```

### RONI (Relative Oceanic Niño Index, media móvil de 3 meses, base 1991-2020)

URL: `https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt`

Texto plano con cabecera `SEAS YR ANOM`. Cada fila es una temporada de tres
meses. Se asigna al mes central de la temporada, con el año que trae la fila:

| SEAS | mes | SEAS | mes | SEAS | mes | SEAS | mes |
|------|-----|------|-----|------|-----|------|-----|
| DJF  | 01  | MAM  | 04  | JJA  | 07  | SON  | 10  |
| JFM  | 02  | AMJ  | 05  | JAS  | 08  | OND  | 11  |
| FMA  | 03  | MJJ  | 06  | ASO  | 09  | NDJ  | 12  |

Entrada:
```
SEAS   YR  ANOM
DJF  1950 -1.19
JFM  1950 -1.08
MJJ  2026  0.98
```

Salida (vintage 2026-09-03):
```
date        value  index  source                                          vintage
1950-01-01  -1.19  roni   https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt  2026-09-03
1950-02-01  -1.08  roni   https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt  2026-09-03
2026-06-01   0.98  roni   https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt  2026-09-03
```

Nota: la serie oficial de CPC empieza en 1950. El CSV de RONI desde 1850 que
existe en `examples/` es una reconstrucción externa y NO se descarga; si se
quiere usar, se carga como vintage estático con `source` = ruta del archivo.

### XM, precio de bolsa nacional (pydataxm)

Fuente: `pydataxm.ReadDB().request_data("PrecBolsNaci", "Sistema", fecha_inicio, fecha_fin)`.
Devuelve un DataFrame con una fila por día y 24 columnas de hora
(`Values_Hour01` ... `Values_Hour24`), en COP/kWh. El formato exacto está en
`examples/` (archivo crudo de la API). La API limita el rango por llamada:
descargar en tramos anuales desde 2000-01-01 hasta hoy y concatenar.

Agregación mensual: `value` = promedio simple de TODAS las horas de todos los
días del mes. Debe reproducir el archivo de promedio mensual que está en
`examples/` con tolerancia 1e-6. Ese archivo es la verdad; si no cuadra, el
error está en el adaptador, no en el archivo.

Separar en `xm.py`: `fetch_raw(start, end) -> DataFrame` (red),
`aggregate_monthly(df_raw, vintage) -> DataFrame` (pura, la que se testea).

## Vintages

- `data/raw/<index>/<YYYY-MM-DD>.<ext>`: copia cruda tal como llegó.
- `data/processed/<index>/<YYYY-MM-DD>.parquet`: salida del contrato.
- `proteo/store/vintages.py` expone:
  - `save_raw(index, vintage, text_or_df)`
  - `save_processed(index, vintage, df)`
  - `list_vintages(index) -> list[date]` ordenada ascendente
  - `load(index, vintage=None) -> DataFrame`; con `None` carga el más reciente
- Dos descargas el mismo día comparten vintage y la segunda reemplaza a la
  primera. Días distintos, archivos distintos, siempre.
- Por qué: NOAA revisa valores hacia atrás. Un backtest debe usar los datos
  que existían en la fecha del pronóstico, no los de hoy. Si no, hay sesgo de
  look-ahead (el modelo "ve" información que no estaba disponible).

## Modelos (a partir de la fase 3)

- Todo modelo hereda de `proteo/models/base.py` con `fit(y, X=None)` y
  `forecast(h, X_future=None) -> DataFrame[date, mean, lower, upper]`.
- SARIMAX de `statsmodels`. Configuración de referencia del paper:
  SARIMAX(1,1,1)(1,0,0)12 sobre el precio mensual, con RONI rezagado 2 meses
  como regresor exógeno.
- Baselines obligatorios: naive (último valor) y naive estacional (mismo mes
  del año anterior). Sin baseline no hay comparación válida.

## Comandos

```powershell
.\.venv\Scripts\activate
pytest -q
streamlit run app/Home.py
```

## Glosario (para retomar el hilo sin releer todo)

- Adaptador: módulo que sabe descargar y parsear UNA fuente y entregarla en el
  contrato de datos.
- Contrato de datos: esquema fijo de columnas que todo adaptador cumple, para
  que modelos y gráficas no dependan de la fuente.
- Vintage: copia de los datos tal como estaban en una fecha de descarga.
- Backtest de origen móvil: entrenar con datos hasta t, pronosticar t+1..t+h,
  avanzar t un mes, repetir. Mide qué tan bien habría funcionado el modelo
  en el pasado sin trampa.
- Diebold-Mariano: prueba estadística que dice si la diferencia de error entre
  dos modelos es significativa o puede ser azar.
- RONI: anomalía de Niño 3.4 menos la anomalía media de los trópicos. Índice
  oficial de NOAA para clasificar ENSO desde febrero de 2026.
- Regresor exógeno: variable externa (aquí RONI) que entra al modelo para
  explicar la serie objetivo (aquí el precio).
