# Plan - Rectificador y visor de la Actividad 4 (PCI1119)

Objetivo: tomar la foto que sube el alumno (hoja de respuestas de la Actividad 4),
enderezar la perspectiva, cortar los 6 cuadros como cuadrados, resaltar el trazo a lapiz
y compararlo contra la pauta escaneada de Miguel desde una pagina HTML.

Decisiones tomadas (2026-09-20):
- Procesamiento pesado en Python (cv2); la pagina HTML solo revisa y compara.
- Se revisan las paginas 2 (vistas) y 3 (isometricos) del enunciado.
- Las pautas las escanea Miguel a mano y pasan por el mismo pipeline.
- La comparacion debe ofrecer los cuatro modos: superposicion, lado a lado, cortina y diferencia.
- Debe existir un detector de trazos con control de grosor (engrosar el dibujo del alumno).

## Estructura de carpetas

    Actividad 4/
      entradas/
        entregas/            fotos o PDF crudos, una carpeta por alumno
        pautas_escaneadas/   el desarrollo de Miguel, pagina 2 y 3
      rectificador/          scripts Python
      salida/
        rectificadas/        hoja completa enderezada, tamano canonico
        celdas/              <usuario>_p<2|3>_c<1..6>.png  (+ capa de trazo)
        pautas/              pauta_p<2|3>_c<1..6>.png      (+ capa de trazo)
        reportes/            PNG de comparacion y CSV de notas
      visor/                 index.html, css, js

Nomenclatura fija: `<usuario>_p<pagina>_c<cuadro>[_trazo].png`.
Todo lo que produzca el pipeline se describe en un `manifest.json` por alumno.

## Etapa 0 - Insumos (Miguel)

1. Escanear o fotografiar el desarrollo propio de las paginas 2 y 3. Escaner plano si
   se puede; si es foto, hoja completa con los cuatro bordes visibles.
2. Dejar 3 a 5 entregas reales de ejemplo en `entradas/entregas/` que cubran los casos
   dificiles: foto en angulo, sombra sobre la hoja, screenshot de celular, PDF.
3. Confirmar el formato de entrega (zip de Moodle, PDF, foto suelta).

Sin estos ejemplos el rectificador se calibra a ciegas.

## Etapa 1 - Rectificador de hoja (`rectificador/01_rectificar.py`)

1. Cargar la imagen (o rasterizar el PDF a 200 dpi).
2. Aplanar iluminacion: cierre morfologico con kernel grande y division por ese fondo.
   Elimina sombras y el degradado tipico de la foto de celular.
3. Detectar el marco exterior impreso de la lamina: gris, blur, umbral adaptativo,
   contornos, quedarse con el cuadrilatero convexo de mayor area y 4 vertices.
4. Ordenar esquinas (suma y diferencia de coordenadas) y `warpPerspective` a un lienzo
   canonico fijo: A4 apaisado a 200 dpi, 2339 x 1654 px.
5. Detectar orientacion: buscar la banda "Nombre / Rut / Fecha" al pie. Si aparece arriba,
   rotar 180 grados.
6. Si no se encuentra marco, marcar la hoja como `manual` en el manifest. El visor permite
   marcar las 4 esquinas a mano y rehacer la homografia en el navegador.

Salida: `salida/rectificadas/<usuario>_p<N>.png` + entrada en el manifest con el metodo
usado y la confianza.

## Etapa 2 - Corte de los 6 cuadros (`rectificador/02_celdas.py`)

1. Calibrar una plantilla maestra a partir del PDF del enunciado: coordenadas exactas de
   los 6 marcos en el lienzo canonico (`plantilla_p2.json`, `plantilla_p3.json`).
2. Sobre la hoja rectificada, afinar cada marco con proyeccion de perfiles (suma de pixeles
   oscuros por fila y columna) para absorber el error residual de la homografia.
3. Recortar cada cuadro, reescalar a un cuadrado canonico (por ejemplo 1000 x 1000) y guardar.
4. Verificar el numero impreso del cuadro (1..6) en la esquina superior izquierda con
   coincidencia de plantilla. Si no calza, avisar en vez de asumir el orden.

Salida: 6 PNG por pagina, ya cuadrados y en la misma escala que la pauta.

## Etapa 3 - Detector de trazos (`rectificador/03_trazo.py`)

El problema real: la hoja trae una reticula impresa muy tenue que no debe confundirse con
el lapiz del alumno.

1. Separar reticula de trazo: la reticula es clara, de grosor constante y perfectamente
   horizontal/vertical. Se elimina con umbral por intensidad mas apertura con kernels
   orientados (1 x k y k x 1) y se resta del binario.
2. Binarizar con Sauvola o umbral adaptativo gaussiano; limpiar puntos sueltos con
   apertura pequena y filtro por area de componentes conexas.
3. Generar tres capas por cuadro:
   - `_gris.png`  recorte rectificado tal cual
   - `_trazo.png` binario del lapiz, fondo transparente
   - grosor ajustable: el engrosado se hace en el visor por dilatacion en canvas, para que
     Miguel lo mueva con un slider sin reprocesar nada.
4. Metricas opcionales por cuadro: densidad de tinta, numero de componentes, segmentos
   detectados con HoughLinesP (largo y angulo). Sirven para ordenar la revision y para
   detectar cuadros en blanco.

## Etapa 4 - Pautas

1. La pauta escaneada pasa por las etapas 1 a 3 sin cambios; solo cambia la carpeta de salida.
2. Registro fino opcional: alineacion ECC o por ORB entre el cuadro del alumno y el de la
   pauta, limitada a traslacion y escala, para que la superposicion calce pese a diferencias
   de mano. Si la correlacion queda baja, se avisa en vez de forzar.
3. La capa de trazo de la pauta se tine de azul y la del alumno de rojo, para que la
   superposicion se lea sola.

## Etapa 5 - Visor HTML (`visor/index.html`)

Pagina offline, sin dependencias externas. Se abre con doble clic.

- Carga: seleccionar la carpeta de salida (input webkitdirectory) o arrastrar imagenes.
  Lee el `manifest.json` para saber que alumno y que cuadro es cada archivo.
- Vista de contacto: los 6 cuadros del alumno en grilla 2 x 3; clic para ampliar.
- Panel de comparacion con los cuatro modos, conmutables con teclas 1-4:
  1. Superposicion con slider de opacidad y colores por capa.
  2. Lado a lado con zoom y desplazamiento sincronizados.
  3. Cortina vertical arrastrable.
  4. Diferencia: pauta menos alumno, resaltando lo que sobra y lo que falta.
- Controles de trazo: grosor (dilatacion), umbral, mostrar u ocultar reticula, invertir,
  rotar 90 grados.
- Editor de esquinas: si el recorte salio mal, marcar 4 puntos sobre la foto original y
  rehacer la homografia en el navegador, sin volver a Python.
- Rubrica lateral: por cuadro y por vista (alzado, planta, perfil) marcar correcto,
  parcial o error, mas comentario libre. Atajos de teclado. Exporta CSV y JSON.

## Etapa 6 - Integracion con `corrector/`

Reutilizar lo que ya existe en vez de duplicarlo:
- `01_extraer.py` para el zip de Moodle (ya resuelve el error de ruta larga).
- Mismas convenciones del `CONTRATO.md`: una fila por item en `resultados.csv`, una fila por
  estudiante en `resumen.csv`, y un script de Excel para las notas.
- Sin emojis en los scripts, comentarios en espanol, Python 3.10, solo cv2, numpy, PIL,
  pandas, openpyxl.

## Etapa 7 - Validacion

- Probar con las entregas de ejemplo de la etapa 0 y medir: porcentaje de hojas rectificadas
  sin intervencion manual y error de alineacion en pixeles contra la pauta.
- Caso de prueba sintetico: tomar la pauta, deformarla con una homografia conocida, agregar
  ruido y sombra, y verificar que el rectificador recupera las esquinas dentro de pocos pixeles.
- Meta razonable: 80 por ciento de las hojas sin tocar, el resto resuelto con el editor de
  esquinas del visor en menos de 15 segundos cada una.

## Orden de trabajo sugerido

1. Etapa 0, que depende de Miguel.
2. Etapas 1 y 2 juntas, con la plantilla maestra calibrada desde el PDF.
3. Etapa 3.
4. Etapa 5, primero el visor con los cuatro modos sobre archivos ya generados.
5. Etapa 4 fina (registro) y etapa 6.
6. Etapa 7 al cierre de cada bloque.

## Pendientes por confirmar

- Formato real de entrega de los alumnos.
- Si la nota se pone por cuadro (6 puntos por pagina) o por vista (18 por pagina).
- Si conviene generar tambien las pautas digitales con el generador de vistas en DXF,
  para tener una referencia vectorial ademas del escaneo.
