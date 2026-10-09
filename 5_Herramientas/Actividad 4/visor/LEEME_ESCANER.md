# Escaner manual de laminas

Herramienta para corregir a mano las entregas que el pipeline automatico
(`rectificador/rectificar.py`) no pudo procesar bien: fotos en angulo,
hojas curvadas, lapiz muy tenue, dos hojas en una misma foto, escaneos
girados 90 grados, etc. Vive en `visor/escaner.html` (boton **Escanear**
en la barra superior del visor) y guarda directamente en `salida/`, con el
mismo formato de archivos que usa el pipeline automatico.

## Antes de empezar

Hace falta el servidor propio del proyecto, `servidor.py` (reemplaza a
`python -m http.server`). Se levanta con `Visor.bat`, o a mano con:

```
python servidor.py [puerto]     (puerto por defecto: 8000)
```

El escaner NO funciona abriendo `escaner.html` directamente como archivo
desde el disco (necesita el servidor para listar/leer imagenes y para
guardar).

Si el equipo no tiene OpenCV (`cv2`) instalado, el escaner sigue
funcionando igual: se guarda la imagen del cuadro en escala de grises
(que es lo que se ve y se compara en el visor), pero no se genera la capa
de trazo separado ni las metricas de tinta para esos cuadros. El servidor
avisa esto por consola al arrancar y el escaner lo muestra en su Registro
despues de cada guardado.

## Flujo de uso

1. **Cargar la imagen**: arrastrela sobre el recuadro de la izquierda,
   use "Elegir archivo..." para buscarla en su computador, o eligala del
   desplegable "...o elegir una imagen ya presente en el servidor" (lista
   `entregas/<usuario>/...` y `pautas/...`).

2. **Cargar los datos**: usuario (el mismo nombre de carpeta que tiene en
   `entregas/`) y pagina. El campo "Pagina" esta sincronizado con el
   **selector de Parte 1 · Vistas / Parte 2 · Isometricos** de arriba (el
   mismo selector global de las tres paginas, atajo `F2`): cambiar de
   parte actualiza el campo, y escribir a mano un prefijo reconocible
   ("vistas"/"isometricos") sincroniza el selector de vuelta. Se puede
   seguir editando a mano para variantes como "vistas_2" (segunda hoja del
   mismo tipo) o "desconocida_1" (tipo no reconocible). Justo debajo del
   campo, y de nuevo arriba del boton **Guardar**, un aviso dice sin
   ambiguedad con que parte y para que usuario se va a guardar la hoja
   antes de apretar el boton.

3. **Elegir el modo**:
   - **Hoja completa**: se marcan las 4 esquinas del MARCO EXTERIOR de la
     hoja completa y el programa la divide en la grilla 2x3 (numeros
     1,2,3 arriba y 4,5,6 abajo). Los sliders "Margen interior" y
     "Separacion entre cuadros" ajustan la division en vivo.
   - **Cuadro suelto**: se marcan las 4 esquinas de UN SOLO cuadro
     (cuando la foto es el recorte de un solo ejercicio) y se elige a que
     numero del 1 al 6 corresponde con el desplegable.

4. **Marcar las esquinas**: clic dentro de la imagen para poner cada
   punto, EN ESTE ORDEN: superior-izquierda, superior-derecha,
   inferior-derecha, inferior-izquierda **del resultado final que se
   quiere obtener** (no necesariamente como se ve la foto: si el
   escaneo esta girado, elija como primer punto el que va a terminar
   siendo la esquina superior-izquierda una vez corregido; el orden en
   que se hace clic alrededor del cuadrilatero, en sentido horario desde
   ese punto, es lo que fija la orientacion final -- ver "Escaneos
   girados 90 grados" mas abajo).
   - Al poner o arrastrar un punto aparece una **lupa** con el zoom de la
     imagen alrededor del cursor, para afinar al pixel.
   - Los 4 puntos tambien se pueden escribir/corregir a mano en la tabla
     de coordenadas bajo la imagen (columnas X / Y).
   - **Deshacer punto** quita el ultimo punto puesto; **Reiniciar
     puntos** borra los 4.
   - Rueda del mouse: zoom de la imagen de trabajo. Boton derecho
     (arrastrar): desplazar la vista. Botones **-**, **+**, **Ajustar**:
     lo mismo sin mouse.

5. **Refinar bordes** (opcional pero recomendado): ajusta las 4 rectas
   del cuadrilatero a los bordes reales de la imagen (busca, a lo largo
   de cada arista, el maximo del gradiente de intensidad en
   perpendiculares muestreadas, descarta los puntos de bajo contraste,
   ajusta cada recta por minimos cuadrados robustos e intersecta las 4
   rectas para las nuevas esquinas). El cuadrilatero anterior queda
   dibujado punteado en naranja para comparar; **Deshacer refinar**
   vuelve a el.

6. **Rectificar**: calcula la homografia (resuelta a mano, sistema de 8
   incognitas) y muestra la vista previa del recorte ya "enderezado".

7. **Revisar la orientacion**: con el resultado rectificado a la vista,
   use **-90 / +90** y **Voltear** (horizontal/vertical) hasta que el
   recuadro celeste marcado con **1** quede sobre el cuadro que
   realmente tiene el numero "1" impreso en la hoja.

8. **Guardar en el servidor**: recalcula cada cuadro a maxima resolucion
   directamente desde la imagen original (no desde la vista previa, que
   solo es para revisar) y lo manda al servidor. Escribe:
   - `salida/celdas/<usuario>_<pagina>_c<N>.png` (gris) y
     `..._c<N>_trazo.png` (capa de trazo, si hay OpenCV disponible).
   - `salida/rectificadas/<usuario>_<pagina>.png` (solo en modo "hoja
     completa": una vista de referencia en color de la hoja entera).
   - Actualiza `salida/manifest.json`: crea al alumno/pagina si hace
     falta, reemplaza SOLO los cuadros que se acaban de guardar (los
     demas quedan intactos) y marca la pagina con `metodo: "manual"` y
     `confianza: 1.0`.

9. En el visor (`index.html`), use el boton **Recargar datos** para que
   tome sin recargar la pagina lo que el escaner acaba de guardar (o
   simplemente recargue la pagina del navegador).

### Si el servidor detecta un tipo de lamina distinto al elegido

Justo despues de guardar, el escaner le pregunta al servidor
(`GET /api/hoja/tipo`) que tipo de lamina detecta para la hoja recien
guardada. Si el servidor detecta un tipo **distinto** al que se eligio
(por ejemplo, la hoja parece tener la reticula triangular de isometricos
pero se guardo como Parte 1 · Vistas), aparece un dialogo de confirmacion
explicito, con una frase clara ("esta hoja parece ser de la Parte 2, la
estas guardando como Parte 1") y dos botones: uno para moverla de
inmediato a la parte correcta y otro para dejarla como esta. No es un
aviso que se pueda pasar por alto sin decidir.

Esta deteccion depende de que el servidor tenga implementado el endpoint
`/api/hoja/tipo`; si tu copia de `servidor.py` todavia no lo tiene, el
guardado funciona exactamente igual, solo que sin este chequeo extra (no
aparece ningun dialogo ni error).

### Corregir una hoja que ya quedo mal etiquetada

Si una hoja ya se guardo con el nombre de pagina equivocado (por ejemplo,
isometricos guardado como "vistas") y no lo notaste al guardar, no hace
falta volver a escanearla: en el visor (`index.html`) o en la pagina de
**Comparacion con pauta**, abre esa hoja y usa el boton **"Mover esta hoja
a la otra parte"** (junto a las pestañas de la lamina). Pide confirmacion
porque mueve archivos en el servidor, y al confirmar la interfaz se
refresca sola. Tambien depende de un endpoint del servidor
(`/api/hoja/mover_parte`); si no esta disponible todavia, se muestra un
mensaje explicandolo en vez de fallar en silencio.

## Escaneos girados 90 grados

Un caso tipico: se escaneo la hoja apaisada pero el escaner la giro y
quedo el archivo en vertical (por ejemplo `pautas/pauta_p2_vistas.png`).
No hace falta enderezarla antes: se marcan las 4 esquinas del marco tal
como se ven en la foto, pero **empezando por la esquina que va a ser la
superior-izquierda una vez corregida** (por ejemplo, si en la foto vertical
la hoja quedo con el cuadro "1" abajo a la izquierda, ese es el primer
punto que hay que marcar) y siguiendo en sentido horario. El programa
arma la hoja ya "derecha" directamente, sin necesidad de rotarla despues.
Si igual queda al reves, los botones de rotar/voltear del paso 7 lo
arreglan sobre el resultado ya rectificado, sin tener que volver a marcar
los puntos.

## Atajos y controles

| Control | Efecto |
|---|---|
| Clic en la imagen | Pone el siguiente punto (hasta 4) |
| Arrastrar un punto puesto | Lo mueve (con lupa) |
| Rueda del mouse sobre la imagen | Zoom centrado en el cursor |
| Arrastrar con boton derecho | Desplazar la vista |
| Tabla de coordenadas (X/Y) | Ajuste fino de cada esquina a mano |
| Deshacer punto / Reiniciar puntos | Deshacer el ultimo punto / borrar los 4 |
| Refinar bordes / Deshacer refinar | Ajuste automatico de bordes / volver atras |
| -90 / +90 / Voltear | Corrige la orientacion del resultado ya rectificado |
| `F2` | Alterna el selector de Parte 1 · Vistas / Parte 2 · Isometricos (y el campo "Pagina" con el) |

## Que hacer si algo sale mal

- El Registro (panel izquierdo) deja un historial de cada accion, con
  avisos y errores en colores.
- Si el guardado falla, no se escribe nada a medias: el servidor valida
  todo el pedido antes de tocar el disco.
- Guardar de nuevo el mismo `usuario`+`pagina`+cuadro simplemente
  reemplaza esa entrada (sirve para corregir un error sin tener que
  tocar los demas cuadros de la misma hoja).
