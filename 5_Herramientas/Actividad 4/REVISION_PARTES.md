# Revision de integracion — mover_parte / tipo_hoja (Actividad 4)

Fecha: 2026-09-20. Revisor: agente de QA, sobre el trabajo en paralelo de
dos agentes (Python: `servidor.py` + `comparador/tipo_hoja.py`; front:
`visor/*`) contra el contrato descrito en `comparador/LEEME.md` y
`visor/LEEME.md`. Ambos lados se habian escrito sin probarse juntos.

## Como se probo

- `servidor.py` levantado de verdad (`python3 servidor.py 8099`) contra
  `salida/` real (19 alumnos), no contra `salida_demo/`.
- Las tres paginas del visor (`index.html`, `escaner.html`,
  `comparacion.html`) abiertas con Chromium headless via Playwright
  (`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`), con listeners de consola,
  `pageerror` y respuestas HTTP >=400 activos en todo momento.
- Lectura cruzada de los campos que emite cada endpoint nuevo
  (`servidor.py`) contra los que consume cada modulo del front
  (`servidorHojas.js`, `estadoPartes.js`, `partes.js`, `vistaTabla.js`,
  `app.js` de las tres paginas) antes de ejecutar nada, y despues
  verificado en vivo con `curl` y con las requests reales del navegador.
- Camino completo de `POST /api/hoja/mover_parte` con datos reales: alumno
  `iverdejo2026`, pagina `vistas_2` (que, revisando las miniaturas, en
  realidad es una hoja de isometricos mal etiquetada) movida a
  `isometricos` y de vuelta a `vistas_2`, disparado por click real en el
  boton "Mover esta hoja a la otra parte" + dialogo de confirmacion, no
  por llamada directa al API.
- Verificado con `md5sum` que los 12 PNG de celdas + la hoja rectificada
  quedaron **byte a byte identicos** antes/despues del ida y vuelta, y que
  `manifest.json` quedo identico al original (ignorando el timestamp
  `generado`) tras revertir un efecto secundario esperado de
  `tipo_confirmado` (ver abajo).
- Discrepancia de tipo con datos reales (no sinteticos): se buscaron con
  `tipo_hoja.detectar_tipo_hoja` los cuadros reales cuyo tipo detectado
  discrepa del tipo de su propia pagina con confianza alta (>=0.55); se
  encontraron 3, y se uso `fpaez2026 / vistas / cuadro 6` (confianza 1.0)
  para probar el flujo end-to-end en `comparacion.html`.
- Selector global de parte, atajo `F2` (en `index.html` Y en
  `escaner.html`, sincronizando ahi el campo "Pagina") y doble indicador de
  la lista (incluyendo el borde "sospechosa" cuando el tipo detectado no
  coincide con la parte), verificados leyendo clases/`title` reales del
  DOM, no solo capturas.
- Capturas de cada paso, revisadas con la tool `Read` (no solo generadas):
  selector+lista, contacto de un alumno normal, F2, dialogo de
  confirmacion, estado antes/despues de mover, escaner, y la tabla de
  comparacion con la discrepancia.
- Al terminar: servidor detenido, `salida/manifest.json` y
  `salida/comparacion/` restaurados **byte a byte** desde una copia tomada
  antes de la primera prueba (diff vacio confirmado); no quedaron alumnos,
  paginas ni cachés de prueba en `salida/`.

## Desajustes encontrados y arreglados

Los *nombres* de campo que declara `comparador/LEEME.md` y los que
consume `servidorHojas.js`/`estadoPartes.js`/`vistaTabla.js` ya coincidian
exactamente (`pagina_origen`, `pagina_destino`, `tipo_detectado`,
`confianza_tipo`, `tipo_confirmado`, `discrepancia_tipo`, `aviso_tipo`,
`partes.vistas/isometricos.estado`, etc.) — ahi no hubo que tocar nada.
Los problemas reales aparecieron al ejercitar el flujo completo:

1. **[Alto, backend] La discrepancia de tipo de un cuadro se perdia al
   comparar la pagina completa.** `verificar_tipo_antes_de_comparar()` arma
   el diccionario `{"discrepancia_tipo": true, "tipo_alumno", "tipo_pauta",
   "confianza", "mensaje"}` sin los campos `usuario`/`pagina`/`n`, y
   `comparar_cuadro()` lo devolvia tal cual en ese caso. `POST
   /api/comparacion/comparar` (un cuadro suelto) no tenia problema porque
   el front indexa por el `n` que **el mismo pidio**, pero
   `comparar_pagina()` (los 6 cuadros de una vez, que es lo que se dispara
   solo al abrir un alumno) devuelve un arreglo, y
   `visor/js/comparacion/app.js` hace `nuevos[r.n] = r` para cada resultado:
   sin `r.n`, la discrepancia del cuadro 6 quedaba guardada bajo la clave
   `undefined` en vez de bajo `6`. Efecto visible: el aviso grande de
   arriba y el panel de nota SI se veian bien (escanean por valor, no por
   `n`), pero la fila del cuadro 6 en la tabla se quedaba en "sin
   comparar" en vez de mostrar el chip "tipo distinto" — es decir, no se
   veia un porcentaje (eso ya andaba), pero tampoco se veia el mensaje de
   discrepancia donde correspondia verlo primero.
   **Arreglo** (`servidor.py`, dentro de `comparar_cuadro`): cuando
   `verificar_tipo_antes_de_comparar` devuelve una discrepancia, se le
   agregan `usuario`/`pagina`/`n` antes de devolverla, para que tenga la
   misma forma que un resultado normal. Verificado en vivo: la fila del
   cuadro 6 de `fpaez2026/vistas` ahora muestra el chip rojo "tipo
   distinto" (con el mensaje completo en el `title`) en vez de "sin
   comparar", sin tocar `comparador/tipo_hoja.py` ni el contrato de
   `verificar_tipo_antes_de_comparar` en si (los tests directos de esa
   funcion en `comparador/pruebas_tipo.py` no la llaman a traves de
   `comparar_cuadro`, asi que siguen intactos).

2. **[Alto, front] Tras mover una hoja, la vista quedaba incoherente.**
   En `visor/js/app.js`, `moverHojaActivaAOtraParte()` cambiaba
   `estado.paginaActiva` a la pagina destino pero **no** cambiaba
   `estado.parteActiva` (el selector global). Resultado, reproducido con
   Playwright sobre datos reales: despues de mover
   `iverdejo2026/vistas_2` a `isometricos`, el selector se quedaba en
   "Parte 1 · Vistas", ninguna pestaña quedaba marcada activa, y la
   grilla seguia mostrando la hoja recien movida (ya matriculada como
   `isometricos`) colgando de la parte equivocada — la misma ambigüedad
   de etiquetado que esta funcion existe para resolver, ahora causada por
   la propia interfaz. Ademas, el bloque `finally` restauraba
   incondicionalmente el texto del boton al que tenia ANTES de mover
   (`refs.btnMoverParte.textContent = original`), pisando el texto
   correcto que `actualizarBotonMoverParte()` ya habia calculado para el
   nuevo estado: el boton seguia ofreciendo "Mover a Parte 2 ·
   Isometricos" (dataset `destino=isometricos`) cuando en realidad
   `dataset.destino` interno ya decia `vistas` (la version comparacion.html
   de esta funcion tenia el mismo bug de `finally`, pero no el de la parte,
   porque ya usaba su propio `irAParte()` para eso).
   **Arreglo**: `visor/js/app.js` ahora, tras un `mover_parte` exitoso,
   tambien fija `estado.parteActiva = destino` y llama
   `selectorParte.fijar(destino)` (se elevo la referencia al selector, antes
   local a `iniciar()`, a variable de modulo); y en ambos archivos
   (`visor/js/app.js` y `visor/js/comparacion/app.js`) el texto "original"
   del boton solo se restaura en el `catch` (si la operacion fallo), nunca
   en el `finally`. Verificado en vivo, dos veces (antes/despues del
   arreglo, mismo alumno real): ahora el selector salta solo a "Parte 2 ·
   Isometricos", la pestaña "Isometricos" queda marcada activa, y el boton
   dice correctamente "Mover esta hoja a Parte 1 · Vistas".

Ninguno de los dos arreglos toco `comparador/similitud.py`,
`comparador/tipo_hoja.py`, ni reprocesó imagenes de alumnos: son cambios
puntuales (un enriquecimiento de diccionario en `servidor.py`, y una
correccion de manejo de estado en dos funciones de `app.js`).

## Verificado y funcionando sin cambios

- `GET /api/hoja/tipo`, `GET /api/comparacion/listado` (campo `partes` por
  alumno) y `POST /api/hoja/mover_parte` (caso exitoso, caso "ya existe
  destino" con 400 antes de tocar un archivo, caso "pagina origen no
  existe"): probados por `curl` y por la UI real.
- Doble indicador de la lista: confirmado con `rquintana2026` (Parte 2
  aparece "comparada" + clase `indicador-parte-sospechosa` con el tooltip
  exacto que arma `servidor.py`: *"el servidor detecta tipo 'vistas':
  revisar etiquetado"*, coincidiendo con `tipo_detectado=vistas,
  confianza_tipo=0.447` que trae el manifest para esa pagina).
- Selector global + atajo `F2`: probado en `index.html` (cambia tabs y
  contenido) y en `escaner.html` (sincroniza el campo "Pagina" de
  `vistas` a `isometricos`).
- `escaner.html` y `comparacion.html` cargan sin errores de consola ni
  requests fallidos, con el selector de parte integrado.
- **Cero errores de consola y cero requests con status >=400** (incluidos
  los endpoints nuevos) en todas las corridas, antes y despues de los
  arreglos.

## Que quedo dudoso / fuera de alcance

- El caso real que motiva `comparador/tipo_hoja.py`
  (`acolinir2026/vistas`, reticula rotada, confianza de rectificacion
  0.35) sigue sin disparar deteccion automatica por diseño documentado
  (confianza insuficiente): no se intento "arreglar" la deteccion en si,
  solo se confirmo que el remedio manual (`mover_parte`) sigue disponible
  y funcionando para ese caso.
- No se probo el dialogo de confirmacion de tipo del **escaner**
  (`revisarTipoDetectadoTrasGuardar` en `visor/js/escaner/app.js`, que
  aparece recien al guardar una hoja nueva) contra un guardado real de
  principio a fin (marcar esquinas + rectificar + guardar): habria
  requerido fotografiar/objetivo una hoja nueva o reprocesar una entrega
  existente, fuera del alcance acotado pedido. Se leyo el codigo y el
  contrato (`obtenerTipoHoja`/`moverParte`) esta bien enganchado, pero
  esta ruta especifica no se ejercito con Playwright.
- No se revisaron a fondo pan/zoom con mouse real (rueda, arrastre) en el
  comparador ni en el escaner: se uso Playwright con clicks y evaluacion
  de estado del DOM, no eventos de mouse nativos.
- El único efecto colateral notado en el propio `mover_parte` (esperado,
  no un bug): mover una hoja dos veces seguidas dejo `tipo_confirmado` en
  el manifest aunque antes no existiera esa clave (mover ES la
  confirmacion explicita del tipo, segun el diseño documentado). Para
  dejar `salida/` exactamente como estaba se restauro `manifest.json`
  completo desde una copia tomada antes de la primera prueba, en vez de
  confiar en que un segundo `mover_parte` inverso lo dejara bit a bit
  igual.

## Archivos tocados

- `servidor.py` — `comparar_cuadro()`: la discrepancia de tipo ahora
  incluye `usuario`/`pagina`/`n`.
- `visor/js/app.js` — `moverHojaActivaAOtraParte()` ahora tambien cambia
  la parte activa del selector global al mover una hoja; el texto
  original del boton ya no se restaura cuando el movimiento tuvo exito
  (se elevo `selectorParte` a variable de modulo para poder llamarlo
  desde ahi).
- `visor/js/comparacion/app.js` — mismo ajuste del texto del boton
  (`moverHojaActivaAOtraParte()`); esta version ya cambiaba la parte
  activa correctamente via `irAParte()`.
