# Guía de diseño de figuras

Directrices de las figuras del proyecto ENSO y precio de bolsa. El objetivo no es que se
vean bonitas sino que se lean rápido y sin ambigüedad, incluso impresas en blanco y negro
o proyectadas en una sala con mala luz.

Acompaña al módulo `estilo.py`, que trae todos estos valores listos para importar.

---

## 1. Principio de fondo

**El color codifica significado, nunca decora.** Cada matiz de la paleta tiene un rol
asignado y solo uno. Si aparece un rojo en una figura, es porque hay algo cálido o algo que
requiere atención, jamás porque hacía falta variedad. Cuando un elemento no tiene rol
semántico se dibuja en gris azulado y se manda al fondo.

De ahí salen tres reglas operativas:

1. **Máximo dos colores saturados por panel.** Todo lo demás es neutro. Si necesitas un
   tercero, probablemente el panel debería ser dos paneles.
2. **Lo importante va adelante y grueso, el contexto va atrás y delgado.** El orden se
   controla con `zorder`, no con el orden de las llamadas.
3. **Lo que se puede decir con posición no se dice con color.** El color es el último
   recurso, después de posición, tamaño y grosor.

---

## 2. Paleta

### 2.1 Neutros y estructura

| Rol | Hex | Muestra | Dónde se usa |
|---|---|---|---|
| Tinta principal | `#22303f` | azul pizarra muy oscuro | serie observada, texto de anotaciones |
| Tinta fuerte | `#111111` | casi negro | solo marcadores de anclaje en el gráfico IRI |
| Texto secundario | `#4a5560` | gris azulado medio | notas al pie, aclaraciones |
| Texto sobre relleno claro | `#33393f` | gris carbón | etiquetas dentro de barras claras |
| Borde de ejes | `#8a949e` | gris medio | `axes.edgecolor`, líneas separadoras verticales |
| Línea de referencia | `#6b7680` | gris | el cero, líneas de base |
| Rejilla | `#d7dde3` | gris muy claro | rejilla sobre fondo blanco |
| Rejilla clara | `#e3e7ea` | casi blanco | paneles de barras, donde la rejilla estorba más |
| Elemento inactivo | `#9fb3c8` | gris azulado | barras no destacadas, series de contexto |

**Por qué la tinta no es negro puro.** `#22303f` es un azul pizarra que se lee como negro
pero no compite con los colores saturados ni produce el contraste duro del `#000000` en
pantalla. El negro puro se reserva para un único elemento por figura, cuando hace falta un
ancla visual inequívoca.

### 2.2 Modelos

| Rol | Hex | Nombre aproximado |
|---|---|---|
| ARIMA | `#c2410c` | naranja quemado |
| SARIMAX | `#1d4ed8` | azul cobalto |
| Miembros del ensamble | `#7f9dc4` | azul apagado, siempre con alfa 0,32 |

Esta pareja resiste tres pruebas. En escala de grises el naranja queda claramente más
oscuro que el azul, así que se distinguen impresos en blanco y negro. Se separan bajo
deuteranopia y protanopia, los dos daltonismos más frecuentes. Y ninguno de los dos es
rojo ni azul puro, así que no se confunden con la codificación de fases del ENSO.

**Asignación fija:** el naranja es siempre el modelo más simple y el azul siempre el más
completo. No se rota entre figuras. Quien vea tres gráficos seguidos debe poder leer el
cuarto sin mirar la leyenda.

### 2.3 Fases ENSO

| Rol | Hex primario | Hex de fondo |
|---|---|---|
| Fase cálida (El Niño) | `#d94a3d` | `#fbe3e0` |
| Neutral | `#8a949e` | `#f4f5f6` |
| Fase fría (La Niña) | `#2f6fb0` | `#e2ecf6` |

Rojo para cálido y azul para frío. Es la convención de toda la literatura climática y **no
se invierte por ningún motivo**, ni siquiera por coherencia con otra parte del documento.

El par primario/fondo funciona así: el primario para líneas de umbral y etiquetas, el fondo
para las bandas horizontales. El fondo tiene la saturación bajísima a propósito, porque
ocupa mucha superficie y a mayor área menor saturación tolerable.

### 2.4 Bloques de partición

| Rol | Hex |
|---|---|
| Entrenamiento | `#e8eef4` |
| Prueba | `#fde9d7` |
| Reserva | `#e3f0e6` |

Azul, naranja y verde muy desaturados. Van con `zorder=0`, siempre detrás de todo. La
intuición cromática es deliberada: azul frío para lo que el modelo ya conoce, naranja tibio
para lo que va a poner a prueba, verde para lo que nunca tocó.

### 2.5 Escala de intensidad

| Categoría | Hex |
|---|---|
| Neutral o La Niña | `#c8ced4` |
| Débil (0,5 a 1,0) | `#f6c6ba` |
| Moderado (1,0 a 1,5) | `#ee9179` |
| Fuerte (1,5 a 2,0) | `#dc5c42` |
| Muy fuerte (≥ 2,0) | `#a8271a` |

Es una escala **secuencial**, no categórica: las categorías están ordenadas y el color va
del claro al oscuro siguiendo ese orden. Usar colores distintos para categorías ordenadas
destruye la información de orden, que en este caso es justamente lo que se quiere mostrar.

---

## 3. Un conflicto conocido

El azul cumple dos papeles: SARIMAX (`#1d4ed8`) y fase fría (`#2f6fb0`). En la figura del
pronóstico ENSO ambos aparecen a la vez, la línea del modelo y el umbral de La Niña.

No es un descuido, es un compromiso aceptado. La regla para manejarlo:

- Los tonos son distintos, cobalto contra azul acero, y los grosores también.
- La fase siempre aparece como **línea punteada horizontal o banda de fondo**. El modelo
  siempre como **línea sólida con marcadores**. La forma desambigua donde el color no.
- Si un panel necesita que ambos roles sean prominentes, se separa en dos paneles.

Declararlo por escrito es preferible a fingir que la paleta es perfecta.

---

## 4. Tipografía

| Elemento | Tamaño | Peso | Alineación |
|---|---|---|---|
| Base | 9,5 | normal | |
| Título de figura | 12,5 | negrita | izquierda, `x=0.006` |
| Título de panel único | 11,5 a 13 | negrita | izquierda |
| Título de subpanel | 9,5 | negrita | izquierda |
| Leyenda | 8,0 a 8,5 | normal | |
| Anotación dentro del gráfico | 8,0 a 8,6 | normal o negrita si es la conclusión | |
| Nota al pie | 7,6 a 7,9 | normal | color `#4a5560` |

**Todos los títulos van alineados a la izquierda.** El ojo occidental empieza por la
esquina superior izquierda; un título centrado obliga a un salto innecesario. Se usa
`loc="left"` en paneles y `x=0.006, ha="left"` en el título de figura.

**Los subpaneles se numeran con letra y punto:** `A. Serie y partición`. La letra permite
referirse a ellos en el texto sin describirlos.

---

## 5. Grosores, alfas y capas

| Elemento | Grosor | Alfa |
|---|---|---|
| Serie observada larga (300+ puntos) | 0,9 | 1,0 |
| Serie observada en acercamiento | 1,4 a 1,5 | 1,0 |
| Modelo principal | 1,9 a 2,6 | 1,0 |
| Modelo secundario o backtesting | 1,2 a 1,4 | 1,0 |
| Miembro del ensamble | 0,55 | 0,32 |
| Umbral y línea del cero | 0,7 a 0,9 | 1,0 |
| Banda punteada (intervalo empírico) | 1,1 | 0,9 |
| Relleno del intervalo | sin borde | 0,15 |
| Sombreado de episodios ENSO | sin borde | 0,13 |
| Rejilla | 0,6 | 0,7 |

**Regla del grosor inverso a la longitud:** cuanto más larga la serie, más delgada la
línea. Una serie de 535 puntos a grosor 1,5 se convierte en una mancha. La misma serie
recortada a 60 puntos necesita 1,5 para no verse anémica.

**Regla del alfa para superposición:** un relleno que va debajo de una línea no pasa de
0,16. Si necesita más alfa para verse, el problema es el color, no la opacidad.

**Capas (`zorder`):**

```
0  bandas de fondo y sombreado de partición
1  líneas de umbral y del cero
2  miembros del ensamble
3  serie observada
4  modelos y pronósticos
5  banda del intervalo
6  modelo destacado
7  marcadores de anclaje
```

Siempre con `axes.axisbelow=True` para que la rejilla quede detrás de los datos. Es un
error frecuente y arruina cualquier gráfico denso.

---

## 6. Reglas de composición

**Sin marco.** Se eliminan los bordes superior y derecho (`axes.spines.top` y
`.right` en `False`) y el recuadro de la leyenda (`legend.frameon=False`). Menos tinta que
no aporta información.

**La conclusión va dentro del gráfico, no en el pie.** Si el hallazgo es que el intervalo
paramétrico subcubre, eso se escribe como anotación dentro del área de datos, en el color
del elemento al que se refiere. El lector no debería tener que buscar la explicación en
otro lado.

**Cada figura declara su procedencia al pie**, en 7,7 puntos y color `#4a5560`: fecha de
emisión, corte de datos, tamaño de muestra. Una figura que circula sin fecha se vuelve
peligrosa a los tres meses.

**Un solo destacado por gráfico de barras.** Cuando se muestra una selección, el ganador va
en color saturado y el resto en `#9fb3c8`. La función `destacar()` del módulo lo resuelve.

**Marcador hueco para lo especial.** Relleno blanco, borde de color y grosor 2,0. Se usa
para datos parciales (agosto con 25 de 31 días) y para el punto de anclaje del pronóstico.
Comunica "esto es distinto" sin necesidad de leyenda.

**Sólido contra punteado tiene significado fijo:** relleno sólido es el intervalo
paramétrico, línea punteada es el intervalo empírico. Nunca al revés.

---

## 7. Tamaños de figura

| Composición | `figsize` |
|---|---|
| Un panel ancho (serie temporal larga) | `(11, 4.4)` a `(11, 4.8)` |
| Dos paneles lado a lado | `(11, 4.1)` |
| Tres paneles lado a lado | `(13.4, 4.0)` |
| Cuatro paneles de diagnóstico | `(13, 3.2)` |
| Dos paneles apilados | `(11, 6.4)` |
| Apilado con panel principal dominante | `(10.5, 8.6)` con `height_ratios=[2.15, 1]` |

Todas a 150 dpi. Es suficiente para proyección e impresión en informe, y mantiene los
archivos por debajo de 500 KB.

Para series temporales la relación de aspecto ronda 2,5:1. Más cuadrado comprime el eje
temporal y esconde la dinámica; más alargado obliga a barrer la cabeza.

---

## 8. Detalles locales

**Miles con punto.** Convención colombiana: `1.529` y no `1,529`. El formateador `cop` del
módulo lo resuelve. Los decimales van con coma en todo el texto.

**Escala logarítmica cuando el rango cruza un orden de magnitud.** El precio va de 27 a
1.529 COP/kWh. En escala lineal los primeros diez años quedan aplastados contra el eje. Se
declara explícitamente en la etiqueta del eje para que nadie lea mal las pendientes.

**Sin el MAPE cuando la serie cruza cero.** No es un tema de diseño sino de honestidad,
pero se aplica en las tablas de las figuras igual que en el texto.

---

## 9. Uso del módulo

```python
from estilo import (aplicar, C, FASE, MODELO, NEUTRO, INTENSIDAD, PARTICION,
                    LW, ALFA, cop, titulo_figura, titulo_panel, pie,
                    destacar, ancla, bandas_enso)

aplicar()                      # fija los rcParams globales

fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(s.index, s.values, color=C["obs"], lw=LW["observado_largo"])
ax.plot(f.index, f.media,  color=MODELO["sarimax"], lw=LW["modelo"], marker="o", ms=4)
ax.fill_between(f.index, f.lo95, f.hi95,
                color=MODELO["sarimax"], alpha=ALFA["banda"], lw=0)
ax.yaxis.set_major_formatter(cop)
titulo_panel(ax, "Pronóstico a seis meses", grande=True)
pie(fig, "Emitido el 28-08-2026 con datos hasta julio de 2026.")
```

Funciones disponibles:

- `aplicar(dpi=150)` fija todos los parámetros globales.
- `bandas_enso(ax, y_min, y_max)` monta el fondo de tres franjas estilo IRI con sus
  umbrales y la rejilla blanca encima.
- `destacar(valores, indice)` devuelve la lista de colores para barras con un resaltado.
- `ancla(ax, x, y)` dibuja el marcador hueco.
- `titulo_figura`, `titulo_panel`, `pie` aplican tipografía y alineación correctas.
- `cop` formatea miles con punto.

---

## 10. Lista de verificación antes de exportar

- [ ] Ningún texto se solapa con datos ni con otro texto
- [ ] Todos los ejes tienen etiqueta con unidades
- [ ] La leyenda no tapa datos
- [ ] La rejilla está detrás de los datos
- [ ] Los límites del eje x llegan exactamente al rango de los datos, sin margen vacío
- [ ] La figura tiene nota de procedencia con fecha y corte de datos
- [ ] La conclusión principal está escrita dentro del área de datos
- [ ] El color de cada modelo coincide con el de las demás figuras
- [ ] Se ve bien convertida a escala de grises
- [ ] Se lee al 50% de zoom, que es como se verá proyectada
