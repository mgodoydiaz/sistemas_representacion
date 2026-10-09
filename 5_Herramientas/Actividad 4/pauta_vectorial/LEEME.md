# Pauta vectorial - Actividad 4 (Sistemas de Representacion)

Reemplaza el escaneo de la pauta del profesor por geometria vectorial exacta,
para poder comparar contra ella con precision en el visor (`a4/visor/`).

## 1. Que hay en esta carpeta

```
pauta_vectorial/
  pauta_vistas_c1.json ... pauta_vistas_c6.json          <- datos, lamina "vistas"
  pauta_isometricos_c1.json ... pauta_isometricos_c6.json <- datos, lamina "isometricos"
  generar_pauta.py                                        <- CLI que produce DXF y PNG
  dxf/                                                     <- DXF generado (por cuadro y por lamina)
  _qa/                                                     <- 12 imagenes de control (render vs pauta a mano)
  LEEME.md                                                 <- este archivo
```

Los PNG que consume el visor NO se generan aqui: se escriben directamente en
`a4/salida/pautas/` (el CLI recibe esa carpeta como `--salida`), que es donde
`manifest.json` y el visor ya los buscan (`pautas/pauta_<pagina>_c<N>.png` y
`..._trazo.png`). Esa carpeta ya tenia una version basada en el escaneo
(generada por el rectificador); esta pauta vectorial la reemplaza en el mismo
lugar y con el mismo nombre.

## 2. Formato de los datos (pauta_<pagina>_c<N>.json)

```jsonc
{
  "pagina": "vistas" | "isometricos",
  "cuadro": 1..6,
  "reticula": { ... },       // ver seccion 3
  "elementos": [
    {"clase": "segmento", "a": [x1,y1], "b": [x2,y2],
     "tipo": "llena" | "oculta" | "eje",
     "vista": "alzado" | "planta" | "perfil" | "isometrico"},
    {"clase": "circulo", "centro": [x,y], "radio": r,
     "tipo": "llena", "vista": "..."}
  ],
  "dudoso": true,            // opcional, ver seccion 5
  "nota": "..."              // opcional, explica el motivo de "dudoso"
}
```

- **Origen y ejes**: abajo a la izquierda del CUADRO COMPLETO (no de cada
  vista por separado), eje Y hacia arriba. Cada vista (alzado/planta/perfil)
  ocupa una region propia dentro de ese mismo sistema de coordenadas: las
  tres comparten un unico plano 2D, tal como se ven dibujadas en la hoja.
- **tipo** define la capa/estilo de linea: `llena` = arista vista (continua),
  `oculta` = arista oculta (trazos), `eje` = eje o linea de centro (trazo y
  punto). Esto se traduce 1 a 1 a las capas DXF `LLENA`/`OCULTA`/`EJE` y a los
  patrones punteados del PNG.
- **vista** es solo informativa (para poder filtrar/editar por vista); el
  renderizador no la usa para el dibujo, todas las coordenadas ya estan en el
  sistema unico del cuadro.

### Disposicion de las vistas (lamina "vistas")

Verificada contra `a4/pautas/pauta_p2_vistas.png` (la pauta a mano del
profesor, rotada a su orientacion correcta): el profesor NO dibuja el perfil
al lado del alzado (que seria lo esperable en un primer diedro "de libro"),
sino que usa:

- **Alzado**: arriba, ocupando todo el ancho del cuadro.
- **Planta**: abajo a la izquierda, debajo del alzado.
- **Perfil**: abajo a la derecha, AL LADO DE LA PLANTA (no del alzado).

Los 12 archivos de `_qa/` muestran que esta disposicion se respeto de forma
consistente en los 6 ejercicios. Si en algun momento se agrega un cuadro
nuevo, revisar esto antes de asumir la disposicion "de libro".

### Identificacion de cada ejercicio

La numeracion de la pauta escaneada NO coincide con su posicion fisica en la
hoja (la hoja esta escaneada en retrato, rotada 90 grados, y ademas los
numeros de casillero quedan en una diagonal que no es la lectura habitual).
Cada ejercicio de esta carpeta fue identificado por su CONTENIDO, comparando
la figura de la pauta a mano contra el isometrico/vistas dado en
`enunciado_actividad4.pdf`, no por la posicion del numero en el escaneo. El
resultado (confirmado con las 12 imagenes de `_qa/`) es que, una vez rotada
correctamente la hoja, el cuadro rotulado "N" SI corresponde al ejercicio N
del enunciado, tanto en "vistas" como en "isometricos" (no hubo que
reasignar numeros; lo que hacia falta era la rotacion correcta de la
imagen antes de leerla).

## 3. Reticula y calibracion

### 3.1 Reticula cuadrada (lamina "vistas")

Medida directamente sobre `enunciado_actividad4.pdf`, pagina 2 (hoja de
respuesta en blanco, reticula cuadrada), rasterizada a 200 dpi con
`pdftoppm`. Se detectaron los bordes de cuadro (lineas gruesas) y el paso de
la reticula fina (picos de oscurecimiento cada ~35.5 px a 200 dpi) con
`scipy.signal.find_peaks` sobre franjas verticales/horizontales limpias.
Resultado: **17 casillas de ancho x 20 casillas de alto** por cuadro (esto
es lo que va en `reticula.casillas_ancho` / `casillas_alto`). Es el mismo
valor para los 6 cuadros de la lamina.

Si se vuelve a medir y da un numero distinto, hay que actualizar
`casillas_ancho`/`casillas_alto` en los 6 JSON de "vistas" (y ajustar las
coordenadas si el cambio es grande), porque el renderizador mapea
`[0, casillas_ancho] x [0, casillas_alto]` linealmente al lienzo de
1000x1000 - si el numero no calza con el de la hoja real, el recorte
rectificado del alumno y la pauta vectorial quedan a distinta escala.

### 3.2 Reticula isometrica (lamina "isometricos")

Medida de forma analoga sobre la pagina 4 del enunciado (hoja de respuesta
en blanco con reticula isometrica): pitch horizontal (lineas a 90 grados)
~40 px y pitch vertical (a lo largo de una linea de 90 grados, entre cruces
sucesivos con las diagonales) ~46.2 px a 200 dpi, consistentes con una
arista de reticula `u = 46.2 px` (ya que `pitch_horizontal = u * cos(30°)`).
Con el tamano de cuadro medido (~606 x 705 px), eso da del orden de 15 x 15
unidades de arista por cuadro. Para simplificar la autoria de los datos se
uso un marco de trabajo de **14 x 16 unidades utiles** (`casillas_ancho` /
`casillas_alto` de la lamina "isometricos"), ligeramente menor para dejar
margen, con la MISMA relacion de aspecto aproximada que el cuadro real.

**Conversion pasos de reticula -> cartesianas** (ver `P()` en el script de
generacion de datos, y `_dibujar_reticula_fondo()` en `generar_pauta.py`):
se definen tres direcciones a 30, 90 y 150 grados. Un punto dado por
`a` pasos en la direccion de 30 grados, `b` pasos en la direccion de 150
grados y `c` pasos verticales, se convierte a coordenadas cartesianas
(en unidades de arista) con:

```
x = (a - b) * cos(30°)
y = (a + b) * sin(30°) + c
```

Los JSON de "isometricos" ya guardan las coordenadas cartesianas resultantes
(no los pasos `a,b,c`), para que el esquema sea el mismo que el de "vistas"
(lista de segmentos/circulos con `a`,`b` o `centro`,`radio`). Si se necesita
editar un vertice en "pasos de reticula" en lugar de en cartesianas, conviene
usar la formula de arriba (o reabrir `build_datos.py` en el historial de este
proyecto, que tiene la funcion `P()` ya escrita).

**Importante sobre la deformacion**: el rectificador de los alumnos
(`a4/rectificador/nucleo.py`) mapea el cuadro real (que no es necesariamente
cuadrado en la foto) a un lienzo CUADRADO de 1000x1000 con una homografia.
Para que la pauta vectorial calce con esas fotos rectificadas, el PNG de esta
pauta hace lo mismo: mapea `[0,casillas_ancho]x[0,casillas_alto]` al lienzo
de 1000x1000 de forma NO uniforme (una escala en X y otra en Y). Esto es
intencional y esperable: si se mira el PNG de "isometricos" aislado, los
angulos de 30/90/150 grados se ven ligeramente distintos a los "ideales"
porque el cuadro real no es perfectamente cuadrado; asi es como tambien se
ven las fotos rectificadas de los alumnos, por lo que la comparacion sigue
siendo valida. Los archivos DXF, en cambio, SI guardan la geometria
isometrica ideal (sin esa deformacion), porque un DXF no tiene "lienzo".

## 4. Como regenerar DXF y PNG

Requiere Python 3.10+, `numpy`, `Pillow`, `ezdxf` (`pip install ezdxf` si
falta).

```bash
cd a4/pauta_vectorial
python3 generar_pauta.py --datos . --salida ../salida/pautas --dxf ./dxf
```

Esto:
- Lee todos los `pauta_<pagina>_c<N>.json` presentes en `--datos`.
- Escribe `pauta_<pagina>_c<N>.png` y `pauta_<pagina>_c<N>_trazo.png` (1000x1000)
  en `--salida` (por defecto `../salida/pautas`, que es donde el visor los
  busca).
- Escribe `pauta_<pagina>_c<N>.dxf` por cuadro y `pauta_<pagina>_lamina.dxf`
  (los 6 cuadros en grilla 2x3, con su marco) en `--dxf`.

Para regenerar un solo cuadro (por ejemplo tras corregirlo a mano):

```bash
python3 generar_pauta.py --datos . --salida ../salida/pautas --dxf ./dxf --cuadro vistas:3
```

(Con un solo cuadro no se regenera el DXF de lamina completa, porque ese
archivo junta los 6 cuadros de la pagina.)

## 5. Como corregir un cuadro a mano

1. Abrir el `pauta_<pagina>_c<N>.json` correspondiente en un editor de texto.
2. Editar/agregar/quitar elementos de la lista `elementos`. Cada elemento es
   un segmento (`a`,`b`) o un circulo (`centro`,`radio`), con su `tipo`
   (`llena`/`oculta`/`eje`) y `vista` (solo informativa).
3. Las coordenadas son numeros en "casillas de reticula" (pueden llevar
   decimales si hace falta media casilla), dentro del rango
   `[0, casillas_ancho] x [0, casillas_alto]` de la seccion `reticula`.
4. Volver a correr `generar_pauta.py` (ver seccion 4) para regenerar el DXF
   y los dos PNG de ese cuadro.
5. Si se quiere volver a validar visualmente, regenerar la imagen de control
   correspondiente en `_qa/` (ver seccion 6) y mirarla.
6. Si un cuadro estaba marcado `"dudoso": true` y ya se corrigio con
   confianza, borrar esa clave (y la `nota` asociada, o dejarla como
   historial de que fue revisada).

No hace falta tocar `generar_pauta.py` para corregir geometria: ese script
solo lee los JSON y dibuja: toda la "verdad" esta en los JSON.

## 6. Validacion (`_qa/`)

`_qa/qa_<pagina>_c<N>.png` pone lado a lado el render vectorial (izquierda)
y el recorte correspondiente de la pauta escaneada del profesor (derecha),
para verificar a simple vista que representan la misma figura, con las
mismas vistas, en la misma disposicion y a escala aproximada. Se generaron
con un script ad-hoc (no forma parte del entregable, pero el patron es
simple: recortar el cuadro N de la pauta escaneada -ya rotada a su
orientacion correcta- y pegarlo junto al PNG de `a4/salida/pautas/`); si se
quiere regenerar esta validacion tras corregir datos, se puede recrear ese
mismo patron apoyandose en las imagenes ya rotadas que se dejaron en
`/tmp/a4work/pauta_vistas_full_ccw.png` y `pauta_iso_full_ccw.png` durante
este trabajo (si ya no existen por ser una carpeta temporal, hay que volver
a rotar `a4/pautas/pauta_p2_vistas.png` y `pauta_p3_isometricos.png` en 90
grados antihorario con Pillow: `Image.open(...).rotate(-90, expand=True)`).

### Resultado de la validacion (ver informe entregado con esta tarea)

- **Lamina "vistas"**: los 6 cuadros quedaron verificados contra la pauta a
  mano y calzan bien en disposicion, vistas y proporcion general. El cuadro
  2 (bloque escalonado) quedo marcado `"dudoso": true`: la pauta a mano tiene
  varios trazos finos superpuestos dificiles de leer con certeza vertice a
  vertice; se preservo el caracter escalonado y la disposicion, pero el
  detalle fino de esa pieza conviene revisarlo a mano contra el escaneo
  original antes de exigir una comparacion muy estricta. El cuadro 4 tiene
  el redondeo de esquina aproximado como una pequena escalera de peldanos
  (igual que lo dibujo el profesor a mano), en vez de un arco real.

- **Lamina "isometricos"**: los 6 cuadros estan marcados `"dudoso": true`.
  A diferencia de "vistas", esta geometria se reconstruyo a partir de las
  vistas dadas en el enunciado (pagina 3) con una interpretacion propia de
  la forma 3D, y solo se confirmo a grandes rasgos contra la pauta a mano
  del profesor (silueta general, aristas principales, ocultas vs vistas).
  El cuadro 1 (piramide) quedo con muy buen calce. Los cuadros 2, 4 y 6
  (cunas/prismas con corte diagonal) son los de menor fidelidad: la
  topologia general (una caja con un corte plano) esta representada, pero
  la posicion exacta de las aristas del corte no fue verificada vertice a
  vertice contra el trazo a mano. Antes de usar la lamina "isometricos" para
  calificar con exigencia, conviene revisarla a mano contra
  `a4/pautas/pauta_p3_isometricos.png`.

## 7. Parametros de dibujo

- Lienzo: 1000x1000 px, renderizado internamente a 4000x4000 (supersample
  x4) y reducido con filtro LANCZOS, para que las lineas queden con un
  antialiasing parecido al trazo de lapiz sobre papel (no un antialiasing
  duro tipo vector puro).
- Grosor de trazo: ~5 px sobre el lienzo de 1000 (parametro `GROSOR_PX` en
  `generar_pauta.py`, ajustable entre 4 y 6 segun se pida).
- Color de trazo: gris muy oscuro (35,35,35), no negro puro, para imitar
  lapiz. En la version `_trazo.png` lleva ademas canal alfa (~235/255).
- La version `pauta_<pagina>_c<N>.png` (fondo gris/blanco) incluye una
  reticula tenue de fondo (cuadrada o isometrica segun corresponda) para que
  se vea similar a la hoja rectificada real; la version `_trazo.png` NO
  lleva reticula (fondo transparente, solo el trazo), que es lo que espera
  el comparador del visor (`visor/js/comparador.js`, capa "trazo" separada
  del "fondo").

## 8. Limitaciones conocidas / honestidad de la calibracion

- La calibracion de 17x20 casillas para "vistas" se midio sobre la hoja
  generada por `pdftoppm` a 200 dpi a partir del PDF del enunciado, no sobre
  un escaneo fisico de una hoja impresa y fotocopiada; si la hoja que
  reciben los alumnos en papel tiene un margen de impresora distinto, puede
  haber un pequeno corrimiento. Se dejo como parametro explicito
  (`reticula.casillas_ancho/alto`) precisamente para poder corregirlo sin
  tocar el resto del pipeline.
- La calibracion isometrica (14x16) es una aproximacion mas gruesa que la de
  "vistas" (ver seccion 3.2); se prioriza que la RELACION de aspecto sea
  parecida a la real, mas que el numero exacto de unidades.
- No se implemento deteccion automatica de lineas ocultas a partir de un
  modelo 3D (CSG) para las piezas de "isometricos"; las lineas ocultas de
  esa lamina se asignaron a mano, con la convencion habitual (arista trasera
  de una caja = oculta, resto = vista), y pueden no ser exactas en las
  piezas con cortes diagonales (cuadros 2, 4 y 6).
