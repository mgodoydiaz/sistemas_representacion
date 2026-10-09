# Visor de entregas — Sistemas de Representación (Actividad 4)

Visor web local para revisar las 6 láminas (cuadros) de cada alumno contra
la pauta, cuadro por cuadro, y dejar un veredicto con comentario.

Funciona 100% offline: no usa CDN ni librerías externas, es HTML + CSS +
JavaScript (módulos ES) a mano, y no requiere instalar nada salvo Python
(para levantar un servidor local que sirva los archivos).

## Como abrirlo

1. Doble click en `Visor.bat` (carpeta raíz del proyecto, junto a `salida/`
   y `visor/`). Si Windows no tiene Python instalado, el script lo avisa
   con instrucciones para instalarlo.
2. Se abre el navegador en `http://localhost:8000/visor/index.html`,
   apuntando a la carpeta real `salida/` que genera el script de recortes.
3. No cierres la ventana de la consola mientras uses el visor: ahí corre
   el servidor. Para cerrar, simplemente cierra esa ventana.

El visor **no modifica ni escribe nada** en `salida/`: solo lee. Todas las
calificaciones se guardan en el navegador (localStorage) y se exportan a
CSV/JSON cuando quieras entregarlas o respaldarlas.

### Probar con datos de ejemplo

Si `salida/` todavía no existe (el proceso de recorte no ha corrido) se
puede abrir el visor igual con datos sintéticos de prueba agregando el
parámetro `?datos=` en la URL:

```
http://localhost:8000/visor/index.html?datos=../salida_demo
```

Esa carpeta (`salida_demo/`) trae 3 alumnos de ejemplo con el mismo
contrato de `salida/`, incluyendo casos "feos" (página con método
fallido, avisos de baja confianza, un cuadro vacío) para ver cómo se
comporta el visor en esos casos.

## Partes de la actividad y el selector global

La actividad tiene dos láminas, que en toda la interfaz (visor, escáner y
comparación) se llaman **"Parte 1 · Vistas"** y **"Parte 2 · Isométricos"**.
Por dentro (nombres de archivo, claves del manifest, parámetros que se le
mandan al servidor) siguen siendo `vistas` / `isometricos` tal cual, eso
nunca cambia: solo cambió la etiqueta que se muestra.

Arriba de las tres páginas hay un **selector de parte**, siempre visible,
que filtra todo lo que se ve debajo (pestañas de alumno, grilla, tabla de
comparación). La elección se guarda en el navegador y se recuerda entre
páginas y entre sesiones (así que si dejaste el visor en "Parte 2" y
mañana abres el escáner, arranca también en "Parte 2"). El atajo `F2`
alterna entre las dos partes sin necesidad del mouse (no funciona mientras
escribes en un campo de texto, para no interferir con lo que estás
tipeando).

**Por qué importa**: la grilla de un alumno debajo del selector solo
muestra las páginas cuyo tipo (según el nombre de archivo) coincida con la
parte elegida. Si una hoja quedó guardada con el nombre equivocado (por
ejemplo, una lámina de isométricos que se guardó como `vistas`), esto se
nota de inmediato: aparecerá bajo "Parte 1 · Vistas" en vez de "Parte 2 ·
Isométricos", con la grilla triangular de isométricos a la vista pese a
estar en la pestaña de vistas. Ahí sirve el botón que sigue.

### Corregir un etiquetado equivocado (sin volver a escanear)

Cuando estás viendo una hoja de un alumno, aparece el botón **"Mover esta
hoja a Parte X"** junto a sus pestañas (solo si el alumno realmente tiene
algo guardado en la parte activa; si no hay nada que mover, el botón no se
muestra). Al hacer click pide confirmación explícita (mover archivos en el
servidor no es reversible con un click) y, al confirmar, llama al
servidor para reetiquetar la hoja y refresca la vista sola. El mismo botón
existe en la página de comparación.

Este botón depende de un endpoint del servidor (`/api/hoja/mover_parte`)
que puede no estar disponible todavía en tu copia de `servidor.py`: si no
existe, el visor muestra un mensaje explicando que es una función
pendiente, en vez de fallar en silencio.

### Doble indicador en la lista de alumnos

Cada alumno de la lista muestra dos cuadritos, uno por parte (**1** y
**2**), con cuatro estados posibles: sin escanear (gris), escaneada
(azul), comparada (verde azulado) y con nota (verde). Pasa el mouse por
encima de un cuadrito para ver el detalle. Si el servidor detecta que el
tipo real de una hoja no coincide con la parte donde está guardada, el
cuadrito se resalta con un borde rojo.

Los estados "comparada" y "con nota" dependen de que el listado del
servidor (`/api/comparacion/listado`) incluya el detalle por parte; si tu
copia de `servidor.py` todavía no lo entrega, el indicador cae a un
cálculo aproximado (solo sin escanear / escaneada) y lo dice en el
tooltip, en vez de aparentar una precisión que no tiene.

## Flujo de trabajo

1. En la lista de la izquierda, busca o hace click en un alumno.
2. Se abre la **vista de contacto**: sus 6 cuadros en una grilla 2x3, con
   pestañas para cambiar entre las páginas que corresponden a la parte
   activa (ver selector global arriba). Si falta una página o vino con
   problemas, se muestra un aviso arriba.
3. Click en un cuadro abre el **comparador**, con 4 modos (teclas 1-4):
   - **1 Superposición**: pauta (azul) y alumno (rojo) superpuestos, con
     slider de opacidad para el trazo del alumno.
   - **2 Lado a lado**: pauta y alumno en paneles separados, con zoom
     (rueda del mouse) y desplazamiento (arrastrar) sincronizados entre
     ambos.
   - **3 Cortina**: una barra vertical arrastrable revela la pauta a un
     lado y el alumno al otro.
   - **4 Diferencia**: gris donde coinciden, un color donde solo dibujó
     el alumno y otro donde solo está en la pauta.
4. Ajusta grosor de trazo, umbral, rotación o el ajuste fino de posición
   si el recorte del alumno quedó corrido.
5. Califica con los botones o las teclas `a`/`s`/`d`. El visor avanza
   solo al cuadro siguiente para que puedas calificar rápido.
6. Exporta el trabajo con **Exportar CSV** o **Exportar JSON** cuando
   quieras. **Importar JSON** permite recuperar un respaldo anterior (por
   ejemplo si cambiaste de computador).

## Atajos de teclado

| Tecla | Acción |
|---|---|
| `1` – `4` | Cambiar modo de comparación (superposición / lado a lado / cortina / diferencia) |
| `a` | Veredicto: correcto |
| `s` | Veredicto: parcial |
| `d` | Veredicto: incorrecto |
| `n` o `→` | Cuadro siguiente |
| `p` o `←` | Cuadro anterior |
| `↑` / `↓` | Ajuste fino: mover el alumno verticalmente (2 px, 10 px con Shift) |
| `Alt` + `←`/`→` | Ajuste fino: mover el alumno horizontalmente |
| `+` / `-` | Ajuste fino: escalar el alumno |
| `0` | Reiniciar el ajuste fino del cuadro actual |
| `r` | Rotar el alumno 90 grados |
| `Esc` | Volver a la vista de contacto |
| Rueda del mouse | Zoom en el modo "lado a lado" (sincronizado) |
| Arrastrar | Mover la vista (modo 2) o la barra de la cortina (modo 3) |
| `F2` | Alternar entre Parte 1 · Vistas y Parte 2 · Isométricos (selector global, funciona en las tres páginas) |

Los atajos de calificación y navegación no se activan mientras escribes
en el buscador o en el comentario, para no interferir con lo que estás
tipeando.

## Notas sobre el contrato de datos

El visor lee `manifest.json` y las imágenes de `salida/` tal como las
genera el proceso de recorte (no se toca ni se asume nada sobre ese
proceso). Maneja explícitamente estos casos:

- Alumno que no entregó una de las dos páginas: la pestaña correspondiente
  aparece deshabilitada con "(sin entrega)".
- Página con `metodo: "fallido"`: aviso rojo, se puede seguir revisando
  igual pero queda claro que el recorte no es confiable.
- Página con `metodo: "fallback"` o confianza baja: aviso amarillo.
- Cuadro con `vacio: true`: se marca con un patrón rayado en la grilla y
  un aviso en el comparador.
- Falta la pauta de una página/cuadro: aviso en vez de romper la
  comparación.
- Carpeta `salida/` inexistente o `manifest.json` inválido: mensaje de
  error legible en vez de una pantalla en blanco.
- Endpoints del servidor todavía no implementados (`/api/hoja/mover_parte`,
  `/api/hoja/tipo`): se avisa que es una función pendiente en vez de
  romper la página (ver "Partes de la actividad" arriba).

## Estructura de archivos

```
visor/
  index.html
  escaner.html
  comparacion.html
  css/estilo.css        estilos comunes (incluye selector de parte, dialogo, indicadores)
  css/escaner.css
  css/comparacion.css
  js/
    datos.js            carga y acceso al manifest
    almacen.js          localStorage + export/import CSV/JSON
    imagenes.js         procesamiento de canvas (tinte, grosor, diferencia)
    vistaLista.js        panel lateral de alumnos (index.html)
    vistaContacto.js     grilla de 6 cuadros
    comparador.js        los 4 modos de comparación
    app.js               orquestación general y atajos de teclado (index.html)
    partes.js            selector global de parte (Parte 1/Parte 2), compartido por las 3 paginas
    dialogo.js           dialogo de confirmacion modal generico
    servidorHojas.js      llamadas a /api/hoja/mover_parte, /api/hoja/tipo y /api/comparacion/listado
    estadoPartes.js       calculo del doble indicador (sin_escanear/escaneada/comparada/con_nota)
    escaner/              modulos propios del escaner (ver LEEME_ESCANER.md)
    comparacion/           modulos propios de la pagina de comparacion
```
