# Plan - Separar Parte 1 (vistas) y Parte 2 (isometricos)

Problema detectado el 2026-09-20 con acolinir2026: se escaneo una hoja de
isometricos y quedo guardada como pagina "vistas". La comparacion la midio
contra la pauta de vistas y entrego entre 10 y 30 por ciento. El numero no
estaba mal calculado, estaba comparando dos cosas distintas.

Lo peligroso es que un porcentaje bajo por hoja mal etiquetada se ve
exactamente igual que un dibujo malo. Eso hay que hacerlo imposible.

## Plan A - Diferenciar vistas de isometricos

1. **Nomenclatura estable.** Se mantienen los identificadores internos
   `vistas` e `isometricos`, que ya estan en el manifest y en los nombres de
   archivo. Lo que cambia es la etiqueta visible: "Parte 1 · Vistas" y
   "Parte 2 · Isometricos". Nada de renombrar archivos.

2. **Deteccion automatica del tipo de hoja al rectificar.** Sobre el cuadro ya
   rectificado se mide la distribucion de angulos de la reticula impresa. En
   la hoja de vistas dominan 0 y 90 grados; en la de isometricos dominan 30,
   90 y 150. Se calcula con la transformada de Hough o con la FFT y entrega un
   tipo mas una confianza.

3. **Segunda senal, el dibujo del alumno.** Si la reticula esta muy tenue o la
   foto salio velada, se mide la direccion de los trazos del propio alumno.
   Un isometrico tiene la mayoria de sus aristas a 30 y 150 grados; unas vistas
   ortogonales son casi todas horizontales y verticales. Dos senales que
   coinciden bastan; si discrepan, se avisa en vez de decidir.

4. **Verificacion cruzada al comparar.** Antes de calcular el parecido, se
   compara el tipo del cuadro del alumno con el tipo de la pauta. Si no
   calzan, el sistema NO entrega un porcentaje: muestra "esta hoja parece ser
   de la otra parte" y ofrece corregir el etiquetado. Esto es lo que habria
   evitado el caso de hoy.

5. **Registro en el manifest.** Cada pagina guarda `tipo_detectado`,
   `confianza_tipo` y `tipo_confirmado`. Lo que el profesor confirma manda
   sobre lo que detecto el programa, pero queda la traza de ambos.

## Plan B - UX de Parte 1 y Parte 2

1. **Selector global de parte**, arriba y siempre visible, en el visor, el
   escaner y la pagina de comparacion. Filtra todo lo que se muestra abajo.
   Con atajo de teclado para cambiar de parte.

2. **En el escaner.** El selector define como se guarda la hoja. Llega
   preseleccionado con el tipo detectado y su confianza. Si el profesor elige
   una parte distinta de la detectada, se pide confirmacion con una frase
   clara, no un aviso que se pueda pasar por alto.

3. **En comparacion.** Dos pestanas, Parte 1 y Parte 2, cada una con su tabla
   de 6 cuadros. El panel de nota muestra el aporte de cada parte al total y
   deja claro si una de las dos todavia no se ha escaneado, en vez de
   promediar sobre datos incompletos.

4. **Lista de alumnos con doble indicador**, uno por parte, con tres estados:
   sin escanear, escaneada y comparada, nota registrada. Asi se ve de una
   mirada a quien le falta que, que es la pregunta real cuando se corrige un
   curso completo.

5. **Reetiquetado en un clic.** Boton "mover esta hoja a la otra parte": mueve
   los archivos de celdas, actualiza el manifest y borra la comparacion
   cacheada. Sin volver a escanear la foto. Resuelve de inmediato el caso de
   acolinir2026 y cualquier otro que aparezca.

6. **Excel.** Las columnas ya contemplan las dos partes. Se agrega el estado de
   cada una, para que la planilla diga si un promedio esta calculado sobre las
   doce comparaciones o solo sobre seis.

## Orden sugerido

Primero el punto 5 del plan B, que desatasca el trabajo de hoy. Despues la
verificacion cruzada del plan A punto 4, que es la red de seguridad. Luego la
deteccion automatica y por ultimo el resto de la UX.
