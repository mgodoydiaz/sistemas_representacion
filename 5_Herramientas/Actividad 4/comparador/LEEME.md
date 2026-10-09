# Motor de similitud (comparador/similitud.py)

Compara el trazo de un alumno contra su pauta y devuelve un porcentaje de
parecido de 0 a 100 mas las metricas que lo explican. Pensado para usarse
desde `servidor.py` (endpoints `/api/comparacion/...`) y tambien solo, desde
la consola.

## Que necesita

Dos PNG RGBA de 1000x1000: la capa de trazo de la pauta y la del alumno
(el mismo formato que ya generan `rectificador/nucleo.py` y el escaner
manual, `salida/celdas/<usuario>_<pagina>_c<n>_trazo.png` y
`salida/pautas/pauta_<pagina>_c<n>_trazo.png`: negro con alfa variable,
fondo transparente).

Dependencias: **numpy y Pillow (PIL), obligatorias**. `cv2` es opcional
(acelera la dilatacion y la transformada de distancia si esta instalado,
pero el modulo funciona igual sin el). No se usa `scipy` para nada: la
transformada de distancia esta implementada a mano.

## Uso desde consola

```bash
python3 comparador/similitud.py salida/pautas/pauta_vistas_c1_trazo.png \
    salida/celdas/acolinir2026_vistas_c1_trazo.png \
    --salida-diferencia /tmp/diferencia.png
```

Imprime un JSON con el porcentaje, las metricas y el registro (desplazamiento
detectado). `--umbral` cambia el umbral de binarizacion (por defecto 40).

## Uso como libreria

```python
from comparador import similitud as sim

resultado = sim.comparar_desde_paths(ruta_pauta_trazo, ruta_alumno_trazo)
print(resultado["porcentaje"], resultado["metricas"])
sim.guardar_mapa_diferencia("diferencia.png", resultado["mapa_diferencia"])
```

`comparar_mascaras(mascara_pauta, mascara_alumno)` hace lo mismo pero
recibe arreglos numpy 2D booleanos ya cargados (por si se quiere binarizar
distinto, o comparar mascaras generadas en memoria, como hacen las pruebas).

## El metodo, paso a paso

1. **Binarizar.** Cada PNG de trazo se reduce a una mascara booleana:
   `alfa >= UMBRAL_ALFA` (40 de 255 por defecto). `cargar_mascara_trazo()`.

2. **Registro** (`registrar()`): busca la traslacion, la escala (0.9-1.1) y
   la rotacion (unos pocos grados) del alumno que mejor coincide con la
   pauta, y devuelve esos parametros ademas de la mascara del alumno ya
   alineada. Es deliberadamente una busqueda gruesa a fina, no una
   optimizacion numerica, para que sea facil de leer y de confiar:
   - Se reducen ambas mascaras (`REGISTRO_FACTOR_DS`, 1000 -> 200 px) con
     pooling OR (si algun pixel del bloque tiene trazo, el bloque reducido
     tambien: un trazo fino no desaparece al reducir).
   - Para cada combinacion de `REGISTRO_ROTACIONES` x `REGISTRO_ESCALAS`
     (25 por defecto): se rota/escala el alumno reducido una sola vez, y se
     prueban todas las traslaciones de una grilla gruesa
     (`REGISTRO_RANGO_GRUESO_DS`, paso `REGISTRO_PASO_GRUESO_DS`), y despues
     una fina (paso 1) alrededor del mejor punto de esa grilla gruesa. El
     puntaje de cada traslacion es el coeficiente de Dice contra la pauta
     reducida.
   - Con la mejor (rotacion, escala) encontrada, se repite el registro de
     traslacion en la resolucion COMPLETA (paso 1 px, rango
     `REGISTRO_RANGO_FINAL_PX` alrededor de lo hallado en baja resolucion),
     para que el `dx`/`dy` que se reporta sea fiel a la imagen real: un
     dibujo muy corrido es informacion util para el profesor, no solo un
     dato interno para alinear.
   - Con este esquema, comparar un cuadro toma ~1 a 1.5 segundos en esta
     maquina (con `cv2` disponible); sin `cv2` es un poco mas lento por la
     transformada de distancia manual, pero sigue siendo del mismo orden.

3. **Metricas** (sobre las mascaras ya alineadas por el registro):
   - **IoU con tolerancia**: se dilatan AMBAS mascaras `TOLERANCIA_PX`
     pixeles (6 por defecto) y se calcula IoU entre esas dos versiones
     dilatadas. Sin esto, un trazo desplazado 3 px del original (perfectamente
     aceptable a mano alzada) daria IoU ~0 pixel a pixel.
   - **Precision**: que fraccion de lo que el alumno dibujo cae dentro de
     la pauta dilatada (no se "sale de la raya"). **Cobertura** (recall):
     que fraccion de la pauta quedo cubierta por el alumno dilatado (no le
     "falto dibujar" nada). **F-score**: media armonica de ambas.
   - **Distancia de Chamfer**, en ambos sentidos (alumno->pauta y
     pauta->alumno), en pixeles y en "casillas de reticula" (`CASILLA_PX`,
     asumiendo una reticula de 10x10 en cada cuadro de 1000x1000). Sin
     `scipy` ni `cv2`, se calcula con una transformada de distancia
     euclidiana exacta implementada a mano (Felzenszwalt & Huttenlocher
     2004, separable por filas/columnas, funcion `_edt_manual`); si `cv2`
     esta disponible se usa `cv2.distanceTransform` (mas rapida, resultado
     casi identico: en las pruebas la diferencia maxima medida fue de
     ~0.5 px, por la aproximacion interna de OpenCV con mascara 5x5).

4. **Porcentaje final**: combinacion ponderada de las tres metricas de
   arriba (cada una ya normalizada a un score en `[0,1]`), con los pesos en
   el diccionario `PESOS` **al principio del archivo**:

   ```python
   PESOS = {
       "iou_tolerante": 0.40,
       "f_score": 0.35,
       "chamfer": 0.25,
   }
   ```

   `score_chamfer` es `max(0, 1 - chamfer_promedio_px / CHAMFER_PX_MALO)`
   (0 cuando la distancia promedio es >= `CHAMFER_PX_MALO`, 120 px por
   defecto). El porcentaje es el promedio ponderado de los tres scores,
   normalizado por la suma de los pesos (no hace falta que sumen 1)
   multiplicado por 100.

5. **Mapa de diferencia** (`_mapa_diferencia()`): PNG RGBA donde, sobre las
   mascaras ya alineadas, se pinta:
   - gris `(120,120,120)`: coincide (ambos tienen trazo).
   - rojo `(205,60,55)`: el alumno dibujo esto y la pauta no.
   - azul `(60,110,210)`: la pauta lo pide y al alumno le falta.
   - casi blanco `(250,250,250)`: ninguno tiene trazo ahi.

   Los colores rojo/azul son los MISMOS que usa el visor principal
   (`visor/css/estilo.css`, variables `--alumno-color`/`--pauta-color`, y
   `visor/js/imagenes.js:calcularDiferencia`), para que ambas pantallas se
   lean igual.

## Como ajustar el comportamiento

Todo lo que se puede querer tocar esta en la seccion "PARAMETROS AJUSTABLES"
al principio de `similitud.py`, con un comentario explicando cada uno.
En particular:

- **El alumno queda "duro" con lo que dibujo de mas / de menos**: subir
  `PESOS["f_score"]` (o bajar `PESOS["iou_tolerante"]`).
- **El porcentaje cae muy rapido cuando el trazo esta apenas corrido**:
  subir `TOLERANCIA_PX` (dilata mas antes de comparar) o revisar que
  `registrar()` este encontrando un buen `dx/dy` (el campo `registro` del
  resultado lo muestra).
- **Trazos muy incompletos siguen dando un porcentaje alto**: bajar
  `CHAMFER_PX_MALO` (la distancia de Chamfer castiga mas fuerte) o subir
  `PESOS["chamfer"]`.
- **El umbral de binarizacion no calza con el trazo real** (demasiado
  ruido, o se pierde trazo fino): ajustar `UMBRAL_ALFA`.
- **El semaforo de colores en la pagina de comparacion** (verde/ambar/rojo)
  se ajusta aparte, en `visor/js/comparacion/vistaTabla.js`
  (`UMBRAL_ALTO`/`UMBRAL_MEDIO`): es solo una guia visual sobre el
  porcentaje ya calculado, no cambia el porcentaje en si.

---

# Deteccion de tipo de hoja (comparador/tipo_hoja.py)

## El problema que resuelve

Cada alumno entrega dos laminas: Parte 1, VISTAS ortogonales sobre
reticula cuadrada; Parte 2, ISOMETRICOS sobre reticula triangular (30, 90 y
150 grados). El escaner (`visor/escaner.html`) guarda cada hoja bajo una
"pagina" que dice `vistas` o `isometricos`, pero esa etiqueta la elige
quien escanea, y nada impedia que quedara mal puesta. Le paso a un alumno
real: una hoja de isometricos quedo guardada como pagina "vistas", se
comparo contra la pauta de vistas y dio entre 10% y 30%. El numero estaba
bien calculado, pero comparando dos cosas que no correspondian: un
porcentaje bajo por una hoja mal etiquetada se ve identico a un dibujo
malo. Este modulo hace posible distinguir un caso del otro.

## Que mide (`comparador/tipo_hoja.py`)

`detectar_tipo_hoja(ruta_gris, ruta_trazo=None)` recibe UN cuadro ya
rectificado de 1000x1000 (el mismo contrato que usa `similitud.py`: la
imagen en gris del cuadro, y opcionalmente su capa de trazo RGBA) y
devuelve:

```python
{"tipo": "vistas" | "isometricos" | "indeterminado",
 "confianza": 0.0-1.0,
 "senales": {"reticula": {...}, "trazo": {...}}}
```

Dos señales independientes, cada una con su propio histograma de angulos
(180 bins, uno por grado) y dos criterios de clasificacion sobre ese mismo
histograma:

- **Por ventanas fijas** (`_clasificar_por_ventanas`): mide cuanta energia
  cae cerca de 0/90 grados (vistas) contra 30/90/150 (isometricos). Directo,
  pero asume que la reticula quedo alineada con los ejes de la imagen.
- **Por plegado rotacional** (`_clasificar_por_plegado`): "pliega" el
  histograma cada 90 grados (dos familias de lineas perpendiculares: si es
  cuadrada, sus dos picos caen en el mismo bin plegado) y cada 60 grados
  (tres familias a 60 grados: si es triangular, sus tres picos caen en el
  mismo bin). Es **invariante a una rotacion global** de la reticula, algo
  que se observo de verdad: una hoja rectificada con poca confianza (ver el
  campo `avisos` del manifest) puede terminar con la reticula girada unos
  grados de mas, y ahi el criterio de ventanas fijas se equivoca.

`_clasificar_histograma` corre ambos sobre el mismo histograma: si
coinciden, se refuerza la confianza; si discrepan, se prefiere el que dio
mas confianza pero se castiga fuerte el resultado (mismo principio que la
combinacion de señales, mas abajo).

**Señal (a), reticula** (`detectar_por_reticula`): angulos de la imagen en
gris. Si se entrega la capa de trazo, se usa SOLO para "tapar" (rellenar al
gris de fondo) el dibujo antes de buscar la reticula — un trazo mucho mas
oscuro/grueso que la reticula, con lados oblicuos validos (una cara
inclinada en una vista, por ejemplo), si no se tapa le gana en peso a la
reticula y confunde la señal. Usa `cv2.Canny` + `cv2.HoughLinesP` si `cv2`
esta disponible (segmentos de recta, ponderados por su largo); si no, la
orientacion dominante del espectro de Fourier de la imagen (numpy puro:
una familia de lineas paralelas concentra energia en el espectro en una
direccion perpendicular a su orientacion real). Si el resultado de
`cv2.HoughLinesP` tiene muy pocos segmentos o muy poca energia total
(`MIN_SEGMENTOS_RETICULA`/`MIN_ENERGIA_RETICULA`), se descarta esa lectura
(es probable que sea ruido: una sombra, un borde de la foto) y se usa el
respaldo de FFT en su lugar, en vez de mezclarlos.

**Señal (b), trazo** (`detectar_por_trazo`): mismo analisis pero sobre la
capa de trazo del alumno (sus aristas dibujadas). Sirve de respaldo cuando
la reticula impresa sale muy tenue en el escaneo. Si el cuadro tiene muy
poca tinta (`MIN_PIXELES_TRAZO`), se reporta "indeterminado" en vez de
opinar con casi nada de trazo.

**Combinacion** (`_combinar_senales`): la reticula es la señal PRINCIPAL
(mide el papel impreso, no el dibujo) y manda cuando se leyo con confianza
razonable (`UMBRAL_RETICULA_CONFIABLE`); el trazo es el RESPALDO. Si ambas
coinciden, se refuerza la confianza; si discrepan, NO se elige a la fuerza:
se devuelve el tipo de la señal mas seria pero con la confianza fuertemente
castigada (o "indeterminado" si queda muy baja).

Sin `cv2`, todo el modulo funciona igual (solo numpy + PIL), un poco mas
lento por la transformada de Fourier en vez de Hough; ver la tabla de
`pruebas_tipo.py` mas abajo con los 12 resultados por ambos caminos.

## Verificacion cruzada al comparar (servidor.py)

`verificar_tipo_antes_de_comparar` corre DENTRO de `comparar_cuadro` antes
de tocar la cache o calcular nada:

1. Si el profesor ya confirmo el tipo de esa pagina (`tipo_confirmado`),
   eso manda: si coincide con la pauta, se sigue de largo; si no, se
   bloquea igual (aunque la deteccion automatica ya no se ejecuta).
2. Si no hay confirmacion, se detecta el tipo del cuadro (`tipo_hoja.py`).
   Si discrepa del tipo de la pauta con confianza alta
   (`UMBRAL_DISCREPANCIA_BLOQUEA`, 0.55), se devuelve
   `{"discrepancia_tipo": true, "tipo_alumno", "tipo_pauta", "mensaje"}` y
   **no se calcula ningun porcentaje**.
3. Si la confianza es media (`UMBRAL_DISCREPANCIA_AVISA`, 0.30), se calcula
   el porcentaje normalmente pero se le agrega un campo `"aviso_tipo"` con
   el texto de la duda (no bloquea).
4. Si la confianza es baja o el tipo coincide, no se agrega nada.

El aviso/discrepancia se recalcula siempre (es barato comparado con el
registro geometrico de `similitud.py`), incluso si el porcentaje sale de la
cache: asi, si el profesor confirma el tipo despues, el aviso desaparece
sin tener que invalidar el porcentaje ya calculado.

## Registro en el manifest (item 4)

Al guardar desde el escaner (`POST /api/guardar`), `servidor.py` calcula el
tipo de la PAGINA completa (agrega la deteccion de cada uno de sus cuadros:
`_detectar_tipo_pagina`, voto ponderado por confianza, exige ademas que
varios cuadros esten de acuerdo) y escribe en esa pagina del manifest:

- `tipo_detectado`: "vistas" / "isometricos" / "indeterminado".
- `confianza_tipo`: 0.0-1.0.
- `tipo_confirmado`: lo que el profesor confirmo (por ahora, se fija solo
  al reetiquetar con `/api/hoja/mover_parte`: mover una pagina ES la
  confirmacion explicita de su tipo). `null` mientras no se haya
  confirmado nada.

`tipo_confirmado` manda sobre `tipo_detectado` (ver verificacion cruzada
arriba), pero los dos campos se conservan siempre.

`GET /api/hoja/tipo?usuario=&pagina=` devuelve esos tres campos. Si la
pagina es de antes de este cambio (no los tiene todavia), los calcula al
vuelo y los deja guardados en el manifest para no recalcularlos la proxima
vez.

## Reetiquetado de una hoja (item 1): POST /api/hoja/mover_parte

```json
{"usuario": "...", "pagina_origen": "vistas", "pagina_destino": "isometricos"}
```

Renombra en `salida/celdas/` todos los archivos
`<usuario>_<pagina_origen>_c*.png` y sus `_trazo.png` (y la hoja completa en
`salida/rectificadas/`, si existe) a los nombres de `pagina_destino`;
actualiza esa pagina en el manifest (nombre + rutas de cada celda) y deja
`tipo_confirmado` en el tipo base de la pagina destino; invalida en
`salida/comparacion/resultados.json` lo que quedo cacheado de la pagina de
origen (y borra sus mapas de diferencia, que quedaron comparando contra la
pauta que ya no corresponde).

Es una operacion de dos fases: primero se recolectan TODOS los renombres a
hacer y se valida que ningun archivo destino exista ya (incluida la pagina
destino completa contra el manifest); solo si nada choca se renombra de
verdad. Si la pagina destino ya existe para ese alumno, se corta con un
error claro ANTES de tocar un solo archivo ("no pisa nada"). Los renombres
en si usan `os.replace()` (atomico por archivo, mismo filesystem); el
manifest y la cache de comparaciones se siguen escribiendo con el patron
temp+`os.replace()` de siempre.

Respuesta: `{"ok": true, "movidos": [{"de": "...", "a": "..."}, ...], "pagina_destino": "..."}`.

## Listado enriquecido (item 5): GET /api/comparacion/listado

Cada pagina, ademas de lo que ya traia (metodo, confianza, cuadros,
tiene_pauta), ahora incluye `tipo_detectado`, `confianza_tipo` y
`tipo_confirmado`. Cada alumno ademas trae:

```json
"partes": {
  "vistas":       {"estado": "...", "tipo_detectado": "...", "confianza_tipo": 0.0},
  "isometricos":  {"estado": "...", "tipo_detectado": "...", "confianza_tipo": 0.0}
}
```

`estado` es `"sin_escanear"` (no hay ninguna pagina de esa parte),
`"escaneada"` (hay pagina pero ningun cuadro se comparo todavia),
`"comparada"` (al menos un cuadro de esa parte esta en la cache de
comparaciones) o `"con_nota"` (el alumno ya tiene una fila con
`nota_final` registrada en el Excel/CSV de notas). `tipo_detectado`/
`confianza_tipo` de la parte son los de su pagina "principal" (la que no
tiene sufijo `_2`, `_3`... si existe; si no, la primera que haya).

## Limitaciones conocidas (honestidad ante datos reales)

La deteccion funciona muy bien sobre las pautas (12/12, con y sin `cv2`) y
sobre fotos reales con buena reticula visible. Sobre fotos reales de mala
calidad puede fallar: se probo informalmente (fuera de la validacion
obligatoria) contra varios alumnos reales del curso y aparecieron dos
modos de falla:

- **Reticula demasiado tenue** (se ve casi blanca en el escaneo): las dos
  señales quedan con poca evidencia y el resultado suele salir
  "indeterminado" (no bloquea nada, pero tampoco ayuda). Es el
  comportamiento deseado: mejor no opinar que opinar casi al azar.
- **Reticula rotada varios grados de mas** por una rectificacion de baja
  confianza (`metodo` distinto de "contornos" en el manifest, o
  `confianza` baja): el criterio de plegado rotacional ayuda, pero si
  ademas hay un artefacto de la foto (una sombra, un doblez) con mucha
  energia en una direccion, puede seguir votando mal. Es el caso del
  propio alumno que motiva este modulo (`acolinir2026`, pagina "vistas"):
  su hoja se rectifico con confianza 0.35 y quedo con la reticula
  girada, y la deteccion automatica no la corrige con confianza alta.
  **Para ESE caso puntual, el remedio siempre disponible es el mismo
  reetiquetado manual** (`POST /api/hoja/mover_parte`), que no depende de
  que la deteccion automatica acierte.

En ningun caso la deteccion imprecisa hace que el porcentaje de un cuadro
salga mal: como mucho, dispara un `aviso_tipo` que el profesor puede
ignorar, o (con confianza alta y siempre en la direccion de la pauta
"contraria" a la del alumno, nunca al reves) bloquea con `discrepancia_tipo`
un calculo que de todos modos no iba a servir de nada.

## Pruebas (comparador/pruebas.py)

`python3 comparador/pruebas.py` corre 4 casos construidos a mano (usa las
pautas reales de `salida/pautas/` si existen; si no, genera un par de
figuras sinteticas) y una prueba extra de la transformada de distancia
manual contra `cv2`. Numeros reales obtenidos en esta maquina (ver el
mensaje de la tarea para el detalle completo):

| Caso                                        | Porcentaje |
|----------------------------------------------|-----------:|
| Pauta contra si misma                        |     100.0% |
| Pauta desplazada 20 px (registro la recupera) |    100.0% |
| Pauta con 35% del alto borrado                |      71.6% |
| Dos figuras distintas (vistas vs isometricos) |      31.2% |

El registro detecto correctamente `dx=-20, dy=-20` para compensar el
corrimiento de `(+20,+20)` aplicado en la prueba 2 (el signo compensa: es
el desplazamiento que hay que aplicarle al alumno para que quede sobre la
pauta).

## Pruebas (comparador/pruebas_tipo.py)

`python3 comparador/pruebas_tipo.py` valida tanto `tipo_hoja.py` como la
integracion en `servidor.py` (verificacion cruzada + reetiquetado). Corre
tres bloques y termina con un resumen; sale con codigo distinto de 0 si
algo fallo. No deja datos de prueba: el bloque de reetiquetado crea un
alumno `zzz_prueba_tipo_hoja_borrar` sintetico y lo borra al final (celdas,
hoja rectificada, entrada en el manifest y cache de comparaciones).

Numeros reales obtenidos en esta maquina, las 12 pautas, corridas COMPLETAS
por los dos caminos (`cv2` instalado, y forzando el respaldo sin `cv2`):

| Cuadro                | Tipo real   | Con cv2 (Hough)      | Sin cv2 (FFT)        |
|------------------------|-------------|----------------------|------------------------|
| pauta_vistas_c1        | vistas      | vistas (0.985)        | vistas (0.872)         |
| pauta_vistas_c2        | vistas      | vistas (0.987)        | vistas (0.898)         |
| pauta_vistas_c3        | vistas      | vistas (0.966)        | vistas (0.788)         |
| pauta_vistas_c4        | vistas      | vistas (0.983)        | vistas (0.876)         |
| pauta_vistas_c5        | vistas      | vistas (0.987)        | vistas (0.908)         |
| pauta_vistas_c6        | vistas      | vistas (0.465)        | vistas (0.815)         |
| pauta_isometricos_c1   | isometricos | isometricos (0.836)   | isometricos (0.993)    |
| pauta_isometricos_c2   | isometricos | isometricos (1.000)   | isometricos (0.988)    |
| pauta_isometricos_c3   | isometricos | isometricos (0.811)   | isometricos (0.953)    |
| pauta_isometricos_c4   | isometricos | isometricos (0.841)   | isometricos (0.995)    |
| pauta_isometricos_c5   | isometricos | isometricos (1.000)   | isometricos (0.977)    |
| pauta_isometricos_c6   | isometricos | isometricos (0.836)   | isometricos (0.988)    |

12/12 correctas en ambos caminos. `pauta_vistas_c6` da menos confianza con
`cv2` (0.465) porque su trazo de referencia es un triangulo con una
hipotenusa que cae cerca de la ventana de 30 grados (ver
`_clasificar_por_ventanas`); la reticula igual se lee bien (0.846) y define
el resultado.

Tambien valida, con datos reales (no sinteticos): un cuadro de isometricos
de un alumno real (`rquintana2026`, cuadro 6, detectado con confianza 0.75)
comparado a proposito contra la pauta de vistas devuelve
`discrepancia_tipo: true` (no un porcentaje).

## Notas sobre `salida/pautas/`

Otro agente esta generando en paralelo la pauta vectorial exacta en
`pauta_vectorial/`, que debera dejar sus PNG con el mismo contrato en
`salida/pautas/` (`pauta_<pagina>_c<n>.png` + `_trazo.png`, RGBA,
1000x1000). Este motor no depende de como se generaron esas pautas: solo
les pide el contrato de tamaño/formato. Si esos PNG cambian (mejor pauta
vectorial), los porcentajes cambiaran en consecuencia la proxima vez que se
compare cada cuadro (el cache en `salida/comparacion/resultados.json` se
invalida solo, comparando la fecha de modificacion del archivo de trazo
contra la que quedo guardada quando se calculo).
