# Corrector Actividad 1 por portapapeles

PCI1119 Sistemas de Representacion - Seccion 3

## Como se usa

1. Doble clic en `Corregir.bat`. Se abre la ventana.
2. Dejala donde quieras. Puede quedar detras de otras ventanas, no molesta.
3. Abre la entrega del alumno en pantalla (PDF, foto, lo que sea).
4. Presiona `Win + Shift + S` y recorta **solo las cuatro piezas** de la lamina.
5. Listo. La ventana vigila el portapapeles y corrige sola cada recorte nuevo.
   No tienes que volver a ella para pegar.

No necesitas recortar preciso: puede sobrar margen, y si te queda el panel
derecho con la leyenda tambien lo descarta solo.

El resultado queda ademas en el **titulo de la ventana** (`L3  41/43  95 pts`),
asi que lo lees desde la barra de tareas sin cambiar de ventana.

### Si prefieres pegar a mano

Apaga la casilla "Corregir solo al recortar" y usa `Ctrl+V` o el boton azul.
Tambien puedes copiar un archivo de imagen desde el Explorador y pegarlo.

### Opciones de ventana

- **Siempre encima**: apagado por defecto. Si lo enciendes, la ventana se queda
  sobre todas las demas y la unica forma de ver lo que hay detras es minimizarla.
- **Compacta** (o la tecla `F2`): deja solo la barra del puntaje. Ocupa poca
  pantalla y sirve para tenerla en una esquina mientras revisas los PDF.

## Lo que muestra la ventana

- **Puntaje**: porcentaje de caras correctas. Verde sobre 85, ambar entre 60 y 85, rojo bajo 60.
- **Confianza de lectura**: que tan nitido quedo el color de las caras. Sobre 90 por ciento
  puedes anotar la nota sin mirar. Bajo 80 por ciento conviene revisar la imagen de la derecha.
- **Caras erradas**: una linea por cara, con el color que esperaba la pauta y el que pinto el alumno.

## Si detecta mal la lamina

El selector `Lamina` esta en `Auto`. Si se equivoca (pasa cuando el recorte quedo muy
apretado o muy suelto), eligela a mano en el desplegable y vuelve a pegar.

## Que tan confiable es

Probado con verdad-terreno sintetica: se repintaron caras al azar en las cinco laminas,
se simulo una captura con cambio de escala y margen, y el corrector identifico
**exactamente** las caras erradas en 10 de 10 casos.

Con entregas reales funciono bien con las imagenes exportadas del applet, con screenshots
de celular y con capturas de PDF. Con fotos tomadas a la pantalla en angulo la confianza
baja, y ahi el programa te avisa para que revises a ojo.

## Numeracion de las caras

Los identificadores tipo `P2-C05` significan pieza 2, cara 5. Las piezas se numeran
1 arriba-izquierda, 2 arriba-derecha, 3 abajo-izquierda, 4 abajo-derecha. Las caras van de
arriba a abajo y de izquierda a derecha dentro de cada pieza.

Para ver la numeracion completa de cada lamina, abre `salida/pauta/lamina1_anotada.png`
hasta `lamina5_anotada.png`. Esas imagenes te sirven tambien como pauta de correccion a mano.

## Codigo de colores por lamina

- Lamina 1: rojo = Alzado, amarillo = Planta, cyan = Perfil
- Lamina 2: agrega naranjo = Alzado + Planta
- Lamina 3: agrega verde = Perfil + Planta
- Lamina 4: agrega azul = Alzado + Perfil
- Lamina 5: agrega cafe = Alzado + Planta + Perfil

Total de caras: 30, 44, 43, 48 y 47 respectivamente. 212 caras en total.

## Corregir una entrega desde la consola

Si prefieres la linea de comandos a la ventana, o quieres corregir un archivo que
todavia no pasa por la extraccion:

    python corregir_entrega.py "C:\ruta\entrega.pdf"
    python corregir_entrega.py "C:\ruta\carpeta_del_alumno"
    python corregir_entrega.py captura.png --lamina 3

Acepta una imagen, un PDF, un .docx o una carpeta completa. Del PDF saca las
imagenes embebidas y, si una pagina no trae ninguna util, la rasteriza a 200 dpi.
Despues decide sola cual imagen es cual lamina y entrega la tabla con las cinco,
el total sobre 212 caras y la lista de caras erradas.

Opciones utiles:

- `--lamina N` fuerza la lamina, por si se equivoca al adivinar
- `--reportes` guarda los PNG de comparacion en `salida\reportes\`
- `--csv notas.csv` va acumulando una linea por entrega, lista para pegar al Excel
- `--detalle` lista las 212 caras, no solo las erradas

Si ninguna imagen calza con las cinco laminas, te avisa que probablemente la
entrega sea de otro ejercicio del mismo sitio.

## Atajo: los que ya estan corregidos

Antes de ponerte a pegar capturas, corre una vez:

    python corregir_lote.py

Corrige de una sola pasada a los alumnos cuya entrega se pudo recortar sola (los que
entregaron PDF limpios o los JPG del applet). Deja `salida/lote_resumen.csv` con el
puntaje de cada uno y `salida/reportes/<alumno>_L<N>.png` con la comparacion visual.

Al dia de hoy eso resuelve 9 de los 18 alumnos que entregaron. Para los otros 9
(fotos a la pantalla, screenshots de celular, PDF con varias imagenes por pagina)
usa la ventana y pega captura por captura.

El puntaje del lote se calcula sobre las 212 caras de las cinco laminas, asi que un
alumno al que le falta una lamina queda automaticamente penalizado.

## Archivos

- `Corregir.bat` : lanzador de la ventana, doble clic
- `PegarYCorregir.pyw` : la ventana
- `nucleo_correccion.py` : el motor, se puede usar desde otro script
- `corregir_entrega.py` : corrige UNA entrega (archivo, PDF, docx o carpeta) desde la consola
- `corregir_lote.py` : corrige de una pasada lo que ya esta normalizado
- `06_pendientes.py` : resuelve por alumno los casos que la normalizacion automatica no pudo
- `05_excel.py` : regenera la planilla de notas
- `03_normalizar.py` : recorta entregas automaticamente (parcial: resuelve 10 de 18)
- `02_pauta.py` : regenera las pautas si cambian las imagenes de `Pauta/`
- `01_extraer.py` : extrae el zip de Moodle sin el error de ruta larga
- `NOTA_ERROR_ZIP.md` : explicacion del error 0x80010135
