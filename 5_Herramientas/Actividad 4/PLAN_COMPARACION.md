# Plan - Comparacion automatica de trazos contra la pauta

Pregunta: una vez rectificado el cuadro del alumno, como comparar su dibujo
contra el dibujo pauta y entregar algo mas util que una superposicion a ojo.

## Estado del arte, cuatro familias

1. **Comparacion por pixel.** IoU, Dice o F-score entre las dos mascaras de
   trazo, con una dilatacion de tolerancia. Trivial de implementar, corre en
   milisegundos. Castiga fuerte el desalineamiento y el grosor del lapiz, y no
   dice que estuvo mal, solo cuanto se parece.
2. **Distancia entre nubes de puntos.** Chamfer y Hausdorff sobre la
   transformada de distancia. Es la metrica estandar para dibujos de linea:
   tolera diferencias de grosor y desviaciones pequenas, y se puede reportar
   como error medio en milimetros de la hoja. Sigue sin explicar el error.
   Se acompana de un registro previo, rigido o afin, con ECC o ICP, para no
   penalizar un dibujo correcto pero corrido.
3. **Vectorizacion y comparacion estructural.** Esqueletizar el trazo, extraer
   segmentos rectos y arcos, y comparar el grafo resultante contra el de la
   pauta emparejando por angulo, largo y posicion. Es lo unico que permite
   decir "falta la arista oculta de la derecha" o "dibujaste continua una
   linea que va de trazos". Hay trabajo academico especifico de vectorizacion
   de dibujos tecnicos y sistemas de correccion automatica de laminas de tres
   vistas con RANSAC.
4. **Aprendizaje profundo.** Redes siamesas o embeddings de sketch entrenados
   para medir similitud entre dibujos a mano. Requiere datos etiquetados, no
   entrega explicacion, y es desproporcionado para seis ejercicios con pauta
   fija. Descartado para este caso.

## La ventaja que tiene este ramo

El dibujo va sobre reticula impresa. Eso convierte el problema difuso de
comparar trazos a mano alzada en un problema casi discreto: si se detecta el
paso de la cuadricula y se cuantizan los extremos de cada segmento a los nodos
de la reticula, el dibujo del alumno queda como una lista de segmentos en
coordenadas enteras. Comparar dos listas de segmentos enteros es exacto,
rapido y explicable. La misma logica sirve para la reticula isometrica, con
tres direcciones a 30, 90 y 150 grados en vez de dos.

Esto ademas conecta con el generador de vistas en DXF, que ya trabaja con
solidos de cubos en reticula: la pauta podria venir de ahi como geometria
vectorial exacta en vez de un escaneo.

## Plan por fases

**Fase 0. Metricas base.** Registro rigido por ECC entre el cuadro del alumno
y el de la pauta, mas IoU con tolerancia y distancia de Chamfer en ambos
sentidos. Entrega un semaforo de similitud y un mapa de diferencia coloreado.
Barato y sirve de inmediato para ordenar la revision de mayor a menor riesgo.

**Fase 1. Normalizacion a la reticula.** Detectar el paso y la fase de la
cuadricula por autocorrelacion o FFT, y expresar todo en coordenadas de
reticula. Deja alumno y pauta en el mismo sistema, independiente de la escala
de la foto.

**Fase 2. Vectorizacion.** Esqueleto del trazo, deteccion de segmentos con
transformada de Hough probabilistica o LSD, fusion de segmentos colineales,
simplificacion y cuantizacion de extremos a nodos de la reticula.
Clasificar cada segmento en linea llena, de trazos o de eje segun su
continuidad. Descartar la letra A y las marcas auxiliares.

**Fase 3. Emparejamiento y diagnostico.** Emparejar los segmentos del alumno
con los de la pauta por posicion, angulo y largo, resolviendo el emparejamiento
optimo. Clasificar cada resultado en coincide, falta, sobra, corrido, largo
equivocado o tipo de linea equivocado. Esa lista es el diagnostico.

**Fase 4. Agrupacion por vistas.** Agrupar los segmentos en alzado, planta y
perfil por componentes conexas y posicion relativa, para decir cual de las
tres vistas fallo, que es el error tipico del ramo, y verificar la
correspondencia entre vistas.

**Fase 5. Integracion en el visor.** Una quinta pestana de comparacion junto a
las cuatro actuales: sobre el cuadro se pintan los segmentos que faltan y los
que sobran, con una lista lateral clicable. La nota sigue siendo tuya, el
sistema solo propone y tu confirmas.

## Validacion

- La pauta contra si misma debe dar coincidencia perfecta.
- La pauta perturbada a proposito, con un segmento borrado, otro corrido dos
  cuadros y una linea llena convertida en trazos, debe detectar exactamente
  esas tres diferencias.
- Tres entregas reales corregidas a mano por el profesor, comparadas contra el
  diagnostico automatico. Sin ese contraste no hay forma de saber si sirve.

## Riesgos conocidos

Lapiz muy tenue y trazos repasados dos veces, que la vectorizacion ve como dos
segmentos. Lineas de construccion que el alumno dejo marcadas y no deberian
penalizar. Dibujos correctos pero ubicados en otro lugar del cuadro, que el
registro debe absorber sin premiar un dibujo mal posicionado cuando la posicion
relativa entre vistas si importa. La deteccion de reticula falla si la foto
esta muy desenfocada.

## Decision pendiente

Si la pauta se sigue tomando del escaneo a mano o se genera vectorial con el
generador de vistas en DXF. Lo segundo hace exacto todo el lado derecho de la
comparacion y elimina el ruido de la pauta escaneada.
