# Revision de integracion — Actividad 4 (rectificador + visor)

Fecha: 2026-09-20. Revisor: agente de QA, sobre el trabajo de los dos agentes anteriores.

## Que se probo

- Contrato del `manifest.json` real (`salida/manifest.json`, 19 alumnos, 2 pautas) contra lo que el visor espera: campos, valores de `pagina`, `metodo` (`contornos`/`fallback`/`fallido`/`cuadro_suelto`), `hoja: null`, celdas con `n=0` y `vacio`.
- Integridad de archivos: los 622 `img`/`trazo`/`hoja` que el manifest referencia existen, no estan vacios, y las 576 celdas (`img`+`trazo`) miden exactamente 1000x1000 con el `trazo` en RGBA.
- El visor completo, servido con `python -m http.server` desde `a4/` y recorrido con Chromium headless (Playwright, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`) **contra `salida/` real**, no contra `salida_demo/`:
  - Lista de 19 alumnos.
  - Casos pedidos explicitamente: `slara2026` (bueno), `mstubing2026` (dos hojas en una foto -> 4 paginas), `maximiliano.vasquez2026` (una pagina `fallido` + una `desconocida`), una pagina de isometricos (`adelafuente2026`).
  - Recorrido automatizado de **los 19 alumnos y las 32 paginas** que aparecen en el manifest real, entrando a cada tab, abriendo un cuadro y pasando por los 4 modos (superposicion, lado a lado, cortina, diferencia).
  - Slider de grosor de trazo, calificacion con teclado (`a`/`s`/`d`), export CSV.
  - Consola del navegador y requests de red (404/5xx) en todo el recorrido anterior.
  - Casos sinteticos que **no existen en los datos reales** pero que el rectificador puede producir: `cuadro_suelto` (celda `n=0`) y celda `vacio: true`, montados en una carpeta de datos aparte para no tocar `salida/`.
  - Lectura de `Visor.bat` (no se pudo ejecutar en este entorno Linux).

## Bugs encontrados y arreglados

1. **[Alto] Paginas fuera de "vistas"/"isometricos" invisibles e imposibles de calificar.** `vistaContacto.js` tenia los tabs fijos a `["vistas","isometricos"]` y `app.js` elegia la primera pagina activa igual. El rectificador nombra `vistas_2`, `isometricos_2`, `vistas_3`, `desconocida_N` cuando hay mas de una hoja por foto o la hoja no se pudo clasificar (ver `rectificar.siguiente_nombre_pagina`). Esto afecta a **9 de los 19 alumnos reales** (incluye ambos casos pedidos: `mstubing2026` con 4 paginas y `maximiliano.vasquez2026` con 2 `desconocida_N`). Antes del arreglo esas paginas no tenian tab, no se podian abrir ni calificar desde la interfaz (aunque el CSV si las contaba, porque `almacen.js` si itera sobre todas las paginas del manifest — quedaba una inconsistencia entre lo que se exporta y lo que se puede calificar a mano).
   - Arreglo: `datos.js` agrega `paginasDeAlumno()` (lista real de paginas del alumno, ordenada) y `etiquetaPagina()`; `vistaContacto.js` y `app.js` ahora generan los tabs y la pagina inicial a partir de esa lista en vez de una lista fija.
2. **[Alto] La pauta no se encontraba para paginas con sufijo.** `celdaPauta`/`celdasPauta` buscaban `manifest.pautas["vistas_2"]`, que no existe (el manifest solo tiene pautas para `vistas` e `isometricos`), asi que al abrir `vistas_2`/`isometricos_2` la comparacion contra la pauta quedaba vacia aunque la pagina si se pudiera abrir.
   - Arreglo: `tipoBasePagina()` en `datos.js` extrae el tipo base (`vistas`/`isometricos`) del nombre con sufijo, y `celdasPauta` cae a esa pauta cuando no hay una entrada exacta. Verificado con Playwright que al abrir `mstubing2026 / Vistas 2` el navegador efectivamente pide `pauta_vistas_c1.png` (antes no pedia ninguna pauta).
3. **[Medio] `cuadro_suelto` (celda con `n=0`) no se mostraba en ningun lado.** La grilla de contacto y el comparador solo buscan celdas `n=1..6`; una pagina `cuadro_suelto` (una unica celda `n=0`) quedaba invisible aunque la pagina existiera y tuviera datos. No ocurre en los 19 alumnos reales, pero es un metodo documentado del rectificador (`nucleo.detectar_cuadro_suelto`) y puede aparecer en una futura corrida.
   - Arreglo: `esPaginaCuadroSuelto()` + logica en `celdaAlumno()` que mapea esa unica celda al casillero #1; aviso explicito en la vista de contacto y en el comparador explicando que no se sabe a que ejercicio corresponde. Probado con datos sinteticos: no revienta, se ve, se puede calificar.
4. **[Bajo, cosmetico-pero-confuso] Chip "X/2 paginas" mostraba numeros sin sentido para hojas dobles.** Con `mstubing2026` (4 paginas) el chip decia literalmente "4/2 paginas", que parece un bug a simple vista. `psalazar2025` llega a 3 "vistas".
   - Arreglo: se separo en dos chips — "`N/2 tipos`" (cuantos de los 2 tipos de lamina entrego, vistas/isometricos) y, solo si difiere, "`M hojas`" (cantidad real de fotos/paginas). Confirmado visualmente en `salida/_qa/visor_contacto_mstubing2026.png`.
5. **[Bajo] `contacto-tabs` sin `flex-wrap`.** Con 3-4 tabs (hojas dobles + desconocidas) el contenedor podia desbordar en pantallas angostas. Se agrego `flex-wrap: wrap` en `estilo.css`.
6. **[Cosmetico, sin impacto funcional] `etiquetaPagina` duplicada e import muerto en `app.js`.** Habia una funcion local `etiquetaPagina` que colisionaba en nombre con la que se necesitaba importar de `datos.js`, y `paginaAlumno` quedaba importado sin usarse tras el punto 1. Se limpio al mismo tiempo que el arreglo del punto 1 (no es un refactor aparte, fue necesario para que el fix compilara sin duplicados).

Todos los archivos JS se validaron con `node --check` (como `.mjs`, para que efectivamente valide sintaxis de modulos ES — con extension `.js` sin `package.json` de por medio Node no siempre detecta errores de sintaxis dentro de imports, ver Correction en el propio proceso de revision) y con un recorrido real en Chromium.

## Verificacion final (post-arreglos)

- Recorrido automatizado de los 19 alumnos x todas sus paginas (32 combinaciones alumno-pagina reales) x apertura de comparador x los 4 modos: **0 errores de consola, 0 requests fallidos (4xx/5xx)**.
- Export CSV: 277 filas (cabecera + 276 celdas, coincide con la suma de celdas de todas las paginas del manifest, incluidas las que antes eran invisibles).
- Calificacion con teclado verificada contra `localStorage` (`visor_calificaciones_v1`), incluyendo el avance automatico al siguiente cuadro.
- Casos sinteticos `cuadro_suelto` y `vacio: true` no producen errores ni pantallas rotas.

## Visor.bat (revision estatica, no se pudo ejecutar en Linux)

- Usa `%~dp0` + `cd /d` para pararse siempre en la raiz del proyecto (correcto, es independiente de desde donde se hace doble click).
- Detecta Python probando `where python` y luego `where py`; si no encuentra ninguno, avisa con un mensaje claro y un link de descarga, y sale con `pause` en vez de cerrarse solo. Correcto.
- Sirve con `%PY_CMD% -m http.server %PUERTO%` desde la raiz (`a4/`), y abre `http://localhost:8000/visor/index.html`, que es la ruta correcta dado que `visor/` cuelga de esa raiz y `datos.js` resuelve `../salida` en forma relativa a esa URL.
- Avisa si no encuentra `salida\manifest.json` y sugiere la URL con `?datos=../salida_demo` como alternativa. Buen detalle.
- **Pendiente/riesgo menor (no arreglado):** el `start` que abre el navegador se dispara *antes* de que `http.server` este realmente escuchando; en la practica el navegador reintenta o el usuario recarga, pero es una condicion de carrera. Tambien, si el puerto 8000 ya esta ocupado, `python -m http.server` va a fallar con una traza fea en la consola en vez de un mensaje amigable o de probar otro puerto. Ninguno de los dos es una falla real reportada por un usuario, y arreglarlos bien (verificar puerto libre, esperar a que el server responda antes de abrir el navegador) es mas cambio de lo que amerita esta revision — quedan anotados para una iteracion futura si se vuelve un problema real.

## Que NO se pudo verificar

- No se pudo ejecutar `Visor.bat` de verdad (requiere Windows); la revision fue solo de lectura del script.
- No se reviso `nucleo.py`/`rectificar.py` linea por linea (1500+ y 380 lineas respectivamente): se hizo una revision dirigida (manejo de excepciones, casos fallido/fallback/cuadro_suelto, generacion de manifest) y se validaron sus *salidas* exhaustivamente (todas las imagenes referenciadas existen, tienen el tamano y modo de color esperados), pero no se auditó cada funcion de vision por computador (deteccion de contornos, homografias, clasificacion de reticula) buscando bugs sutiles de precision geometrica — esos solo se notarian comparando el recorte contra la hoja fisica original, que esta fuera del alcance de esta revision.
- No se probo el visor en un navegador real con mouse (pan/zoom con rueda, arrastre de la barra de cortina): se ejercitaron via clicks y sliders con Playwright, pero no se simulo `wheel`/`mousedown+mousemove` para el pan-zoom del modo "lado a lado" ni el arrastre de la cortina; el codigo se leyo y no tiene nada evidentemente roto, pero no quedo verificado en un navegador real interactuando con el mouse.
- No se corrio el rectificador de nuevo (la salida real ya estaba generada); no se genero adrede un caso `cuadro_suelto` ni `vacio: true` reales con el pipeline completo, se simularon a mano en el manifest para probar el visor.

## Archivos tocados

- `visor/js/datos.js` — nuevas funciones `tipoBasePagina`, `etiquetaPagina`, `esPaginaCuadroSuelto`, `paginasDeAlumno`, `metodoEsCuadroSuelto`; `celdasPauta`/`celdaAlumno` con los fallbacks descritos arriba.
- `visor/js/vistaContacto.js` — tabs dinamicos, aviso de `cuadro_suelto`, uso de `celdaAlumno` en la grilla.
- `visor/js/app.js` — pagina inicial dinamica, uso de `etiquetaPagina` importado (se elimino la version local duplicada).
- `visor/js/comparador.js` — aviso de `cuadro_suelto` en el comparador.
- `visor/js/vistaLista.js` — chip de progreso separado en "tipos" vs "hojas".
- `visor/css/estilo.css` — `flex-wrap` en los tabs de la vista de contacto.

## Capturas

En `salida/_qa/`:
- `visor_lista.png` — panel de alumnos con los chips corregidos (tipos/hojas).
- `visor_contacto_mstubing2026.png` — el caso de las 2 hojas en una foto, con los 4 tabs (Vistas, Vistas 2, Isometricos, Isometricos 2) ya visibles y funcionando.
- `visor_contacto_maximiliano.png` — el alumno con una pagina `fallido`, tabs "Desconocida 1"/"Desconocida 2" visibles.
- `visor_comparador_slara2026.png` — comparador en modo diferencia sobre un alumno normal.
