# Plan didáctico: cajetín ampliado, vistas auxiliares y vistas en corte

PCI 1119 Sistemas de Representación · UCT 2026-2 · Documento para el redactor del apunte (no es el apunte)

## 0. Decisiones de encuadre

| Contenido nuevo | Dónde va | Motivo |
|---|---|---|
| Cajetín ampliado (ISO 7200 / NCh14) | Cap. 2, reemplaza la sección 2 "El cajetín" | Ya existe una versión corta; se amplía en el mismo lugar para no duplicar. |
| Vistas auxiliares | Cap. 4 nuevo | Usa solo lo del Cap. 3 (caja de cristal, correspondencia). Es la semilla del cambio de plano del futuro capítulo de verdadera magnitud (método único recomendado en la Revisión de orden). |
| Vistas en corte, secciones, roturas, ejes | Cap. 5 nuevo | Requiere tipos de línea (Cap. 2) y vistas (Cap. 3). No depende del Cap. 4. |

**Advertencia de coherencia.** El Cap. 2 actual llama "campos obligatorios" a seis campos (título, autor, fecha, escala, n.º de lámina, símbolo de diedro). ISO 7200 declara obligatorios otros ocho, y escala y diedro no están entre ellos. El redactor debe renombrar la lista del curso como **"campos exigidos en este curso"** y mostrar la correspondencia con la norma (tabla de la subsección 2.3). No corregir en silencio: el estudiante ya vio la lista anterior.

**Principios que ordenan todo el plan** (con evidencia):

1. **Problema antes que regla.** Cada capítulo abre con una figura que muestra por qué la herramienta hace falta (cara deformada, vista llena de ocultas).
2. **Ejemplo resuelto y luego desvanecimiento.** Un ejemplo completo paso a paso, luego el mismo procedimiento con los últimos pasos en blanco, luego el taller. Retirar pasos resueltos de forma gradual mejora la transferencia frente a pasar directo de ejemplo a problema ([Renkl y Atkinson 2004, Instructional Science](https://link.springer.com/article/10.1023/B:TRUC.0000021815.74806.f6); [Atkinson, Renkl y Merrill 2003](https://www.researchgate.net/publication/200772684_Transitioning_From_Studying_Examples_to_Solving_Problems_Effects_of_Self-Explanation_Prompts_and_Fading_Worked-Out_Steps)).
3. **Contraste correcto / incorrecto lado a lado.** Comparar un ejemplo correcto con uno erróneo ayuda a corregir concepciones erróneas más que ver solo ejemplos correctos ([Durkin y Rittle-Johnson 2012](https://www.researchgate.net/publication/257408490_The_effectiveness_of_using_incorrect_examples_to_support_learning_about_decimal_magnitude); revisión sobre ejemplos erróneos: [ResearchGate 2025](https://www.researchgate.net/publication/395723857_Conditions_for_Effective_Learning_from_Erroneous_Examples_A_Systematic_Review)). Se usa en rayado y en indicación de cortes.
4. **Ir y volver entre 3D y 2D.** El entrenamiento de visualización espacial de Sorby (croquis, rotación, cortes de sólidos) elevó la graduación de estudiantes con bajo puntaje inicial (mujeres: 89 % con entrenamiento vs 68 % sin él) ([ENGAGE Engineering](https://www.engageengineering.org/spatial/whyitworks/learnmore); meta-análisis de efectos en STEM: [Stieff y Uttal 2015](https://link.springer.com/article/10.1007/s10648-015-9304-8)). Por eso cada vista cortada se acompaña, al menos una vez, de la isometría de la pieza cortada.
5. **Una pieza guía por capítulo.** La misma pieza reaparece en definición, ejemplo y errores. Cambiar de pieza a cada figura agrega carga cognitiva sin aprendizaje ([Sweller, guidance fading](https://cogscisci.wordpress.com/wp-content/uploads/2019/08/sweller-guidance-fading.pdf)).
6. **Rótulos dentro de la figura** (no en un pie largo) y anotaciones didácticas en azul (#2E5E8C), dibujo técnico en negro: el estudiante distingue qué es norma y qué es explicación.

## 1. Secuencias recomendadas y extensión

Extensión en palabras de texto corrido (sin contar tablas ni pies de figura). Estilo del apunte: frases cortas, definición en recuadro azul, una tabla donde se pueda, "Regla de oro" al cierre.

### Cap. 2, sección "El cajetín" ampliada (máx. 1,5 páginas, ~350 palabras)

| # | Sección | Máx. | Por qué en este orden |
|---|---|---|---|
| 2.1 | Qué es y para qué (definición azul) | 50 | Recupera lo ya visto; no parte de cero. |
| 2.2 | Dónde va: esquina inferior derecha, apoyado en el recuadro, se lee en la dirección del dibujo, ancho 180 mm (Fig. 2) | 60 | Lo espacial antes que lo textual: primero la lámina completa. |
| 2.3 | Norma: ISO 7200 y su homóloga NCh14 (Fig. 1 + tabla de campos) | 120 | Tabla de tres columnas: campo ISO · obligatorio sí/no · cómo se llena en PCI 1119. |
| 2.4 | Datos indicativos: escala, símbolo de diedro, unidades (mm) | 40 | Enlaza con escalas (sección 7 del cap.) y diedro (Cap. 3). |
| 2.5 | Recuadro "Adelanto AutoCAD" | 80 | Al final y en recuadro: se usa en semana 11, no se evalúa ahora. |

Datos de norma para la tabla 2.3 (verificados):
- ISO 7200:2004, campos obligatorios: propietario legal, número de identificación, fecha de emisión, número de hoja, título, persona que aprueba, autor (creador), tipo de documento. Opcionales usuales: índice de revisión, título complementario, idioma. Ancho recomendado 180 mm, igual para todos los formatos ([ISO](https://www.iso.org/standard/35446.html); [resumen de campos](https://github.com/pzfreo/draftwright/issues/1589)).
- NCh14.Of93 "Dibujos técnicos. Cuadro de rotulación" es homologación de ISO 7200:1984: **zona de identificación** (número, título, propietario) de máx. 170 mm, y **zonas de información suplementaria** (datos indicativos: método de proyección, escala, unidades; datos técnicos; datos administrativos) ([NCh14.Of93, PDF](https://www.arqydom.cl/wp-content/uploads/NCh0014-1993.pdf); formatos en [NCh13.Of93](http://www.arqydom.cl/wp-content/uploads/dlm_uploads/NCh0013-1993.pdf)). El redactor debe decir que la NCh sigue la versión 1984 y que el curso adopta la versión 2004 con los datos indicativos de la NCh.
- Llenado sugerido para el curso: propietario = "Universidad Católica de Temuco · PCI 1119"; n.º de identificación = "PCI1119-G3-L05" (grupo y lámina); aprobado por = docente; tipo de documento = "Lámina de ejercicio" o "Plano de pieza"; altura de letra 3,5 mm (título 5 mm).

Recuadro AutoCAD (máximo 6 pasos, sin capturas): (1) pestaña **Presentación**; (2) `PAGESETUP`: impresora "DWG To PDF", papel ISO A4; (3) `INSERT` del bloque cajetín en el **espacio papel** en 0,0 y **escala 1** (el cajetín mide lo mismo en todas las láminas); (4) llenar campos con doble clic sobre los **atributos** (`EATTEDIT`); (5) `MVIEW` para la ventana y fijar su escala normalizada (1:2, 1:5); (6) `PLOT` a PDF. Idea clave en una línea: **la pieza se dibuja a 1:1 en el modelo; el cajetín vive en la presentación; la escala se fija en la ventana**. Fuentes: [CAD Training Online](https://www.cadtrainingonline.com/ultimate-guide-to-title-blocks-in-autocad/), [myCADsite, atributos](https://www.mycadsite.com/tutorials/level_2/title-block-with-attributes-in-autocad-tutorial.html). Sugerencia al docente: entregar una plantilla `.dwt` con el cajetín ya hecho, para que en semana 11 el esfuerzo vaya al dibujo.

### Cap. 4 Vistas auxiliares (máx. 2 páginas, ~450 palabras)

| # | Sección | Máx. | Por qué en este orden |
|---|---|---|---|
| 4.1 | El problema: la cara inclinada se deforma en planta y perfil; el agujero se ve elíptico (Fig. 3) | 60 | Motiva: sin problema visible, el procedimiento parece capricho. |
| 4.2 | Definición azul: la vista auxiliar proyecta sobre un plano **paralelo a la cara inclinada**; esa cara debe verse **de canto** (como una línea) en una vista principal | 50 | Condición de uso antes que procedimiento. |
| 4.3 | Procedimiento en 4 pasos, ejemplo resuelto (Fig. 4, tabla paso / qué se hace / qué se mide) | 150 | Núcleo. Pasos numerados coinciden con paneles de la figura. |
| 4.4 | Vista auxiliar parcial y su rotulado (flecha + letra si se desplaza) | 60 | Lo práctico viene después de entender la vista completa. |
| 4.5 | Mismo ejemplo con pasos 3 y 4 en blanco (desvanecimiento) | 30 | Puente entre ejemplo y taller. |
| 4.6 | Errores frecuentes, Regla de oro, taller | tablas | Cierre estándar. |
| 4.7 | Una línea puente: "este mismo procedimiento, aplicado a rectas y planos, es el cambio de plano que se usará para hallar verdaderas magnitudes" | 30 | Anticipa el capítulo de VM sin enseñarlo. |

Nota: no introducir vistas auxiliares secundarias (cara oblicua). Fuera de alcance del apunte; van con verdadera magnitud.

### Cap. 5 Vistas en corte (máx. 3 páginas, ~700 palabras)

| # | Sección | Máx. | Por qué en este orden |
|---|---|---|---|
| 5.1 | Por qué cortar: una vista llena de ocultas es ilegible (Fig. 5, isometría con mitad retirada) | 60 | Problema antes que regla; ancla 3D. |
| 5.2 | Definiciones azules: **corte** (lo que toca el plano + lo que se ve detrás) vs **sección** (solo lo que toca el plano) | 60 | La diferencia se usa en todo lo que sigue. |
| 5.3 | Cómo se indica: traza del plano, flechas, letras A-A, rotulado de la vista (Fig. 6) | 100 | Todos los tipos de corte reutilizan esta notación: va antes que los tipos. |
| 5.4 | Rayado: 5 reglas en lista + contraste correcto/incorrecto (Fig. 11) | 100 | Justo después de la primera vista cortada, antes de que el error se fije. |
| 5.5 | Tipos: total, semicorte, parcial. Tabla "cuándo usar" (Fig. 7 y 8a) | 120 | De lo simple a lo compuesto: el semicorte es medio corte total + media vista. |
| 5.6 | Secciones abatida y desplazada (Fig. 8b) | 80 | Variación de 5.2 aplicada a piezas alargadas; prepara los ejes. |
| 5.7 | Lo que no se corta longitudinalmente: ejes, chavetas, pernos, pasadores, nervios, radios (Fig. 9) | 80 | Excepción a la regla: se enseña solo después de dominar la regla. |
| 5.8 | Ejes largos y piezas simétricas: rotura y símbolo de simetría (Fig. 10) | 80 | Economía de espacio; cierra con ejes, que son el caso de 5.6 y 5.7. |
| 5.9 | Errores frecuentes (Fig. 12), Regla de oro, taller | tablas | Cierre estándar. |

Omitir en el apunte (mencionar solo en una línea, si acaso): corte por planos paralelos (quebrado) y corte girado. Aparecen en el temario, pero no son necesarios para el proyecto y agregan notación.

## 2. Figuras (12, en orden de prioridad)

**Convenciones para todas (matplotlib):** unidades en mm, `ax.set_aspect('equal')`, sin ejes (`ax.axis('off')`). Gruesa `lw=1.4` (0,5 mm); fina `lw=0.7` (0,25 mm). Oculta: fina, `linestyle=(0,(4,1.5))`. Eje: fina, `linestyle=(0,(10,1.5,1.5,1.5))`, sobresale 4 mm. Traza de plano de corte: eje fino con tramos gruesos de 6 mm en extremos y quiebres, flechas de 6 mm perpendiculares al plano apuntando en la **dirección de observación**, letra mayúscula de 5 mm junto a cada flecha. Rayado: líneas finas a 45°, separación 2,5 mm, recortadas al contorno (usar `Polygon(..., hatch='///', fill=False)` solo si la densidad es controlable; si no, generar las líneas y recortar con `set_clip_path`). Texto de norma en negro; anotaciones didácticas (cotas explicativas, números de paso, "Correcto/Incorrecto") en azul #2E5E8C; marca "Incorrecto" con una X roja pequeña (#B03A2E) solo en figuras de contraste. Letras DejaVu Sans o la del apunte.

**Piezas guía** (reusar en varias figuras):
- **P1 (Cap. 4) Bloque con chaflán y agujero.** Bloque 80 (ancho X) × 40 (profundidad Y) × 50 (alto Z). Chaflán a 45°: en el alzado, la esquina superior derecha se corta desde (50, 50) hasta (80, 20). Agujero pasante Ø12 perpendicular a la cara inclinada, centrado en ella (cara inclinada en VM: 42,4 × 40).
- **P2 (Cap. 5) Buje con brida.** Brida Ø80 × 15 de alto; cubo Ø40 sobre la brida, alto total 50; agujero central pasante Ø20; 4 agujeros Ø10 en la brida sobre circunferencia Ø60 (a 0°, 90°, 180°, 270°). Simétrico: sirve para corte total y semicorte.
- **P3 (Cap. 5) Árbol escalonado.** Tramos Ø30 × 60, Ø40 × 80, Ø30 × 60 (largo 200), chaflanes 1×45° en extremos, chavetero 12 × 5 de profundidad y 40 de largo centrado en el tramo Ø40.

| # | Prioridad | Figura | Qué dibujar exactamente |
|---|---|---|---|
| 1 | A | **Cajetín ISO 7200 esquemático** (180 × 36 mm) | Rectángulo exterior grueso 180 × 36. Tres filas de 12 mm (divisiones finas). Fila inferior (zona de identificación, contorno grueso propio, 180 × 12): "Propietario legal" 60 · "Título" 80 · "N.º identificación" 40. Fila media: "Tipo de documento" 50 · "Autor" 50 · "Aprobado por" 40 · "Fecha" 40. Fila superior (datos indicativos): "Escala 1:2" 30 · símbolo de primer diedro 30 (dos vistas de un tronco de cono: a la izquierda el trapecio, a la derecha dos circunferencias concéntricas, según Cap. 3) · "Unidades: mm" 30 · "Hoja 1/1" 30 · "Formato A4" 60. Cada celda: nombre del campo en letra de 2 mm arriba a la izquierda (gris) y un ejemplo de llenado de 3,5 mm (negro). Llaves azules a la derecha: "zona de identificación (obligatoria)", "información suplementaria". |
| 2 | A | **Lámina A4 vertical con marco y cajetín** | Rectángulo 210 × 297 fino (borde del papel). Recuadro grueso con márgenes 20 mm izquierda, 10 mm en los demás lados (queda 180 × 277). Cajetín de la Fig. 1 simplificado (solo celdas) apoyado en la esquina inferior derecha del recuadro: ocupa los 180 mm de ancho útil. Cotas azules de 20, 10, 180, 36. Marcas de centrado cortas en el punto medio de cada lado. Rótulo azul: "zona de dibujo". Mensaje de la figura: en A4 vertical el cajetín ocupa todo el ancho. |
| 3 | A | **Por qué hace falta una vista auxiliar** (P1) | Tres paneles en primer diedro: alzado arriba a la izquierda (la cara inclinada es una línea a 45°; el agujero como dos ocultas paralelas perpendiculares a esa línea más su eje), planta debajo (la cara inclinada es un rectángulo 30 × 40; el agujero es una elipse de ejes 8,5 × 12, visible), perfil izquierdo a la derecha (elipse 8,5 × 12 aprox. en la cara 30 × 40 escorzada). A la derecha, isometría pequeña de P1. Anotación azul en la planta: "cara deformada: 30 mm en vez de 42,4 mm; círculo visto como elipse". |
| 4 | A | **Vista auxiliar en 4 pasos** (P1) | Cuatro paneles iguales (2 × 2) con alzado y planta de P1 ya dibujados en gris claro; lo nuevo de cada paso en negro y el número del paso en círculo azul. Paso 1: resaltar en azul la arista de canto (línea a 45° del alzado). Paso 2: línea de referencia fina paralela a esa arista, a 25 mm, rotulada "LR" (y "LR" también en la planta, horizontal, sobre la arista trasera). Paso 3: proyectantes finas perpendiculares a la línea de 45° desde cada vértice de la cara y desde el centro del agujero. Paso 4: transferir la profundidad 40 desde la planta (cota azul "40" en planta y en la auxiliar, flecha curva azul entre ambas) y dibujar la vista auxiliar **parcial**: rectángulo 42,4 × 40 grueso con circunferencia Ø12 y sus dos ejes, cerrada del lado del bloque por una línea fina a mano alzada (rotura). |
| 5 | A | **Qué es cortar** (P2) | Tres paneles en fila: (a) isometría de P2 con un plano de corte semitransparente azul por el eje; (b) isometría con la mitad delantera retirada y las caras cortadas rayadas a 45°; (c) alzado cortado de P2: contorno grueso, zonas macizas rayadas (brida y cubo a ambos lados del agujero central y los agujeros Ø10 cortados como huecos sin rayado), sin ocultas. Flechas azules de (a) a (b) a (c). |
| 6 | A | **Indicación del plano A-A** (P2) | Planta de P2 (circunferencias Ø80, Ø40, Ø20, 4 × Ø10, ejes) con traza de corte horizontal por el centro, tramos gruesos en los extremos, flechas apuntando hacia arriba en el papel (hacia el observador que mira el alzado) y letras "A". Arriba, alineado verticalmente, el alzado cortado de la Fig. 5c con rótulo "A-A" encima. Llamadas azules: "traza del plano", "flecha = dirección en que se mira", "rótulo de la vista", "no hay ocultas". |
| 7 | A | **Corte total vs semicorte** (P2) | Dos alzados lado a lado, mismo tamaño. Izquierda "Corte total": igual a Fig. 5c. Derecha "Semicorte": mitad izquierda como vista exterior (contorno grueso, sin ocultas), mitad derecha cortada y rayada; la línea que separa las mitades es **eje** (trazo y punto fino), no línea gruesa. Debajo de cada una, su planta con la traza: completa en el total; en L (desde el borde hasta el eje y luego a lo largo del eje) en el semicorte, con una sola flecha. Pie azul: "semicorte: solo en piezas simétricas; muestra interior y exterior en una vista". |
| 8 | A | **Corte parcial y secciones** (P3) | Árbol P3 en vista longitudinal, sin rayar (no se corta longitudinalmente). (a) **Corte parcial** en el chavetero: zona limitada por línea fina a mano alzada, rayado solo dentro, mostrando la profundidad 5. (b) **Sección abatida**: sobre el tramo Ø40, dibujada en el mismo lugar, circunferencia Ø40 en línea **fina** con el chavetero, rayada, con el contorno del árbol continuo a través de ella. (c) **Sección desplazada**: traza B-B en el chavetero y, fuera de la vista, la sección Ø40 con chavetero en contorno **grueso**, rayada, con rótulo "B-B". Rótulos azules comparan: "abatida: contorno fino, en el lugar" / "desplazada: contorno grueso, fuera, rotulada". |
| 9 | A | **Eje macizo en un conjunto cortado** | Conjunto en corte longitudinal: árbol Ø40 horizontal (tramo de 100 mm) con una polea/buje Ø100 exterior, Ø40 interior, 40 de ancho, montado al centro con chaveta 12 × 8. Corte por el eje del árbol: la polea se raya (45°); el árbol **y** la chaveta quedan sin rayar, con contorno grueso y eje. Si hay dos piezas rayadas en contacto (agregar un casquillo Ø50/Ø40 de 10 mm de ancho a un lado), rayar en dirección opuesta (135°). Llamada azul: "ejes, chavetas, pernos y nervios no se rayan si el plano pasa a lo largo de ellos". |
| 10 | A | **Rotura de eje y símbolo de simetría** | (a) Eje macizo Ø30 × 600 dibujado a 1:5 y acortado: dos tramos con la rotura central. Variante 1: línea fina a mano alzada (ISO 128). Variante 2: rotura convencional en "S" (lazo) para macizo cilíndrico, con la mitad del lazo rayada. Cota "600" azul sobre el total, mostrando que se acota la medida real, no la dibujada. (b) Tubo Ø40/Ø30 con rotura en doble "S". (c) Placa simétrica (rectángulo 80 × 40 con 2 agujeros Ø10) dibujada solo hasta su eje, con el **símbolo de simetría**: dos trazos finos cortos paralelos, perpendiculares al eje, en cada extremo del eje. |
| 11 | A | **Rayado correcto vs incorrecto** (4 pares) | Cuatro filas, cada una con "Correcto" (izquierda) e "Incorrecto" (derecha, X roja) de una misma sección rectangular hueca 40 × 20 con agujero Ø10: (1) 45° uniforme vs rayado paralelo a un borde; (2) separación constante vs separaciones irregulares; (3) mismo rayado en las dos zonas cortadas de la misma pieza vs direcciones distintas en la misma pieza; (4) contorno grueso y rayado que termina en él vs rayado que cruza el contorno o invade el hueco. |
| 12 | B | **Errores de indicación de corte** (P2) | Tres pares correcto/incorrecto en miniatura: (1) flechas en la dirección de observación vs flechas invertidas (la vista queda del lado opuesto); (2) vista cortada sin ocultas vs con ocultas dentro y fuera del rayado; (3) semicorte con separación por eje vs separación por línea gruesa. |

Si hay que recortar a 10, se eliminan la 12 (sus casos pasan a la tabla de errores) y la 3 (se describe en 4.1 con una frase y se reemplaza por el panel 1 de la Fig. 4).

## 3. Errores frecuentes a anticipar

Códigos (E#) usados después en los distractores. Fuentes generales: [McGill, Sectioning Technique](https://www.mcgill.ca/engineeringdesign/step-step-design-process/basics-graphics-communication/sectioning-technique); [UW Pressbooks, Auxiliary Views](https://uw.pressbooks.pub/enggraphics/chapter/auxiliary-views/); [EngineeringTechnology.org, hatch patterns](https://engineeringtechnology.org/engineering-graphics/section-views/standard-hatch-patterns/).

**Cajetín**

| Código | Error | Cómo se ve | Cómo evitarlo |
|---|---|---|---|
| E1 | Cajetín fuera de lugar | En la esquina superior o flotando, separado del recuadro | Fig. 2 como plantilla; criterio de taller explícito. |
| E2 | Campos incompletos o genéricos | "Título: Lámina", sin número ni aprobación | Tabla 2.3 con ejemplo de llenado para cada campo. |
| E3 | Escala mal escrita o falsa | "1/2", "escala 50 %", o 1:1 en un dibujo reducido | Recordar que se escribe con dos puntos y se verifica con el escalímetro. |
| E4 | Símbolo de diedro invertido | Símbolo de tercer diedro en una lámina de primer diedro | Dibujar el símbolo una vez, bien, y copiarlo siempre igual. |
| E5 | (CAD) Cajetín escalado | Cajetín dibujado en el modelo y agrandado para "que calce" | Regla: cajetín en presentación a escala 1; la escala va en la ventana. |

**Vistas auxiliares**

| Código | Error | Cómo se ve | Cómo evitarlo |
|---|---|---|---|
| E6 | Línea de referencia no paralela a la arista de canto | La cara sale deformada otra vez | Paso 1 obligatorio: marcar primero la arista de canto. |
| E7 | Proyectantes no perpendiculares | Vista auxiliar "corrida" o torcida | Usar escuadra apoyada en la arista de canto; mostrarlo en la Fig. 4. |
| E8 | Transferir la medida equivocada | Se lleva el ancho o el alto en vez de la profundidad | Tabla del paso 4: "la medida que no se ve en la vista de canto". |
| E9 | Proyectar desde una vista donde la cara no está de canto | Se proyecta desde la planta y no se obtiene VM | Definición azul con la condición "de canto". |
| E10 | Dibujar la auxiliar completa | Resto de la pieza deformado, lámina saturada | Enseñar la vista parcial como la forma normal. |

**Cortes, secciones y ejes**

| Código | Error | Cómo se ve | Cómo evitarlo |
|---|---|---|---|
| E11 | Dibujar solo la superficie cortada en un "corte" | Faltan aristas visibles detrás del plano | Definición corte vs sección con Fig. 5. |
| E12 | Ocultas en la vista cortada | Trazos dentro o fuera del rayado | Regla: en la vista cortada no hay ocultas (salvo que sin ellas quede ambigua). |
| E13 | Rayar huecos | Rayado dentro de agujeros | Isometría cortada (Fig. 5b): "se raya solo donde había material". |
| E14 | Rayado irregular o paralelo a un borde | Separación variable; líneas horizontales en pieza rectangular | Fig. 11, pares 1 y 2. |
| E15 | Misma pieza con rayados distintos / piezas vecinas con el mismo | Se lee como dos piezas o como una sola | Fig. 11 par 3 y Fig. 9. |
| E16 | Flechas invertidas o sin letras | Vista A-A ubicada al lado equivocado | Frase fija: "la flecha dice hacia dónde se mira"; Fig. 12. |
| E17 | Línea gruesa entre mitades del semicorte | Parece una arista real | Fig. 7 y Fig. 12 par 3. |
| E18 | Rayar ejes, chavetas o nervios cortados a lo largo | Eje macizo lleno de rayado en un conjunto | Fig. 9 y lista cerrada de elementos que no se cortan. |
| E19 | Confundir sección abatida y desplazada | Sección abatida con contorno grueso, o desplazada sin rótulo | Fig. 8 con comparación en rótulos azules. |
| E20 | Acotar la longitud dibujada en un eje con rotura | Cota "120" en un eje de 600 | Cota real en la Fig. 10; conectar con la Regla de oro del Cap. 2. |

## 4. Reglas de oro y destacados

| Capítulo | Regla de oro | Destacados en azul (definiciones) | Recuadros |
|---|---|---|---|
| Cap. 2, cajetín | **El cajetín tiene el mismo tamaño en todas las láminas; lo que cambia es la escala declarada en él.** | Cajetín; zona de identificación | "Adelanto AutoCAD" |
| Cap. 4 | **Una cara solo se ve en verdadera magnitud cuando se mira perpendicularmente a ella: primero búsquela de canto.** | Vista auxiliar; línea de referencia | "Truco": la profundidad se mide siempre desde la línea de referencia, en las dos vistas. |
| Cap. 5 | **Se raya solo el material que toca el plano de corte; la flecha indica hacia dónde se mira.** | Corte; sección; semicorte | Lista cerrada "No se cortan a lo largo: ejes, chavetas, pernos, pasadores, nervios, radios". |

## 5. Talleres (formato de los capítulos existentes)

**Cap. 2, cajetín ampliado.** Encargo: sobre la lámina del taller anterior, rehacer el cajetín en formato ISO 7200 de 180 mm (Fig. 1), llenado con los datos del curso; agregar escala y símbolo de primer diedro.

| Criterio | Qué se evalúa |
|---|---|
| Ubicación y tamaño | Esquina inferior derecha, apoyado en el recuadro, 180 mm de ancho |
| Campos obligatorios | Los ocho campos ISO presentes y llenados con datos reales, no genéricos |
| Datos indicativos | Escala escrita con ":" y símbolo de primer diedro correcto |

**Cap. 4, vistas auxiliares.** Encargo: dada una pieza en isometría con una cara inclinada y un agujero (variante de P1 con chaflán de 30° y ranura), dibujar alzado, planta y vista auxiliar parcial de la cara inclinada, en A4 con cajetín.

| Criterio | Qué se evalúa |
|---|---|
| Construcción | Línea de referencia paralela a la arista de canto y proyectantes perpendiculares |
| Verdadera magnitud | Medidas de la cara y circunferencia sin deformar en la vista auxiliar |
| Vista parcial | Solo la cara inclinada, limitada por línea de rotura fina |

**Cap. 5, vistas en corte.** Encargo: (a) dibujar P2 en semicorte con la traza indicada en la planta; (b) dibujar P3 con una sección desplazada B-B en el chavetero y el eje acortado con rotura.

| Criterio | Qué se evalúa |
|---|---|
| Indicación | Traza con tramos gruesos, flechas en la dirección correcta, letras y rótulo de la vista |
| Rayado | Fino, 45°, uniforme, solo en material cortado; eje sin rayar |
| Limpieza de la vista cortada | Sin ocultas; separación del semicorte por eje; cota real en el eje con rotura |

## 6. Preguntas de alternativas (Caps. 1 a 5)

**Formato:** 4 alternativas, una correcta, sin "todas/ninguna de las anteriores", enunciado en positivo. En Caps. 3 a 5 al menos la mitad de las preguntas lleva figura: "¿cuál de las cuatro vistas es correcta?" es la forma más directa de evaluar lectura de planos. **Cada distractor debe corresponder a un error de la sección 3 (E#)**; se anota el código en la pauta para saber qué concepción errónea tiene cada estudiante que lo marca.

| Cap. | N.º | Objetivos a evaluar | Bloom (aprox.) | Distractores tipo |
|---|---|---|---|---|
| 1 Introducción | 8 | Distinguir dibujo técnico de artístico; reversibilidad de la GD; elementos de un sistema de proyección; cónica vs cilíndrica; por qué hacen falta dos o más vistas | 4 recordar, 4 comprender | Atribuir a la cónica la conservación de medidas; confundir punto de vista con plano de proyección; "una vista basta si es precisa" |
| 2 Elementos (con cajetín) | 10 | Medidas y relación de formatos A; márgenes; ubicación y campos del cajetín; qué es obligatorio en ISO 7200; tipo de línea según uso; relación 2:1; calcular medida en el dibujo dada una escala; jerarquía de líneas | 3 recordar, 3 comprender, 4 aplicar | E1 a E4; escala invertida (1:2 leída como ampliación); trazos para ejes; ancho de margen izquierdo = 10 |
| 3 Vistas | 10 | Ubicar vistas en primer diedro; identificar el alzado óptimo; completar vista faltante; reconocer correspondencia de anchos/altos/profundidades; interpretar el símbolo del cono | 2 comprender, 5 aplicar, 3 analizar | Disposición en tercer diedro; perfil derecho en lugar del izquierdo; oculta dibujada como visible; profundidad transferida como altura |
| 4 Vistas auxiliares | 8 | Decidir cuándo se necesita; identificar la vista donde la cara está de canto; orientación de la línea de referencia; qué medida se transfiere; reconocer la vista auxiliar correcta entre cuatro | 2 comprender, 4 aplicar, 2 analizar | E6 a E10 dibujados como alternativas |
| 5 Cortes | 10 | Diferenciar corte y sección; leer la traza A-A y la dirección de observación; elegir corte total, semicorte o parcial para una pieza dada; reconocer rayado correcto; elementos que no se cortan; abatida vs desplazada; rotura y cota real | 2 comprender, 4 aplicar, 4 analizar | E11 a E20; en especial E12, E16, E17 y E18 como figuras casi idénticas a la correcta |

Total: ~46 preguntas. Sugerencias:
- **Nivel Bloom.** Subir la proporción de "aplicar/analizar" a medida que avanzan los capítulos; en Caps. 4 y 5 evitar preguntas de pura definición salvo corte vs sección.
- **Distractores gráficos** construidos a partir de la figura correcta cambiando **un solo** elemento (una flecha, una línea, un rayado). Así la pregunta mide el concepto y no la atención a detalles irrelevantes.
- **Pregunta de decisión** en cada capítulo técnico (Caps. 3 a 5): "¿qué vista/corte conviene para esta pieza?" con justificación implícita en las alternativas. Es la habilidad que exige el ABP del proyecto.
- **Ejemplos de enunciado** (para calibrar, no para copiar): Cap. 2: "En un plano a escala 1:5, un eje de 600 mm mide en el papel: a) 120 mm b) 3000 mm c) 600 mm d) 60 mm" (distractores: escala invertida, cota dibujada = real, error de coma). Cap. 5: "En la planta se indica el corte A-A con flechas hacia arriba. ¿Qué afirmación es correcta?" con alternativas sobre qué mitad se retira y dónde se ubica la vista.

Todas las fuentes se citan con enlace en el lugar donde se usan.
