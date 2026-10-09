# Revisión y propuesta de orden — PCI 1119

**Encargo:** ordenar dos clases (introducción, tipos de vistas, grosores, formatos de hoja) y proponer una secuencia de capítulos de lo simple a lo complejo.
**Material revisado:** `01_Introduccion_y_Proyeccion_Ortogonal.pptx` (18 diapos) · `02_Elementos_del_Dibujo.pptx` (9 diapos) · carpeta `Capítulos\` (11 archivos) · `TEMARIO_CURSO_SR.md` · planificación 2026-2.

---

## 1. Diagnóstico del material heredado

### 1.1 Hay una inversión pedagógica entre el capítulo 01 y el 02

El capítulo **01** pide a los estudiantes, en las diapositivas 9 y 10, *"desarrollar las vistas correspondientes"* y *"desarrollar vista 3D"*. Es un ejercicio de lámina. Pero las herramientas para hacer esa lámina —tipos de línea, grosores, escalas— recién aparecen en el capítulo **02**.

Se nota que el propio autor lo detectó: la diapositiva 17 del capítulo 01 dice, literalmente, **"ANTES DE AVANZAR — ¿CÓMO SE DIBUJA?"**. Esa diapositiva es la bisagra que reconoce el problema y empalma con el capítulo 02.

**Recomendación:** invertir el orden. Primero se aprende a trazar, después se aprende a proyectar. Es el orden clásico del dibujo técnico y el que sigue tu propio `TEMARIO_CURSO_SR.md` (Módulo 1 = trazado, Módulo 2 = proyección).

### 1.2 El capítulo 02 mezcla dos niveles distintos

Las diapositivas 3 a 7 son **geometría elemental y convenciones** (punto, recta, tipos de línea, escalas): material de semana 1.

Las diapositivas 8 y 9 introducen el **plano de proyección** —PH, PV, PP, línea de tierra, formas de definir un plano—. Eso ya es sistema diédrico: material de semana 3 en tu planificación. Si se dicta en la primera semana, se dicta en el vacío.

**Recomendación:** partir el capítulo 02. Diapos 3–7 se quedan en el módulo de fundamentos; diapos 8–9 migran al capítulo del sistema diédrico.

### 1.3 Faltan tres cosas que sí están en tu programa

| Falta | Dónde debería estar | Estado |
|---|---|---|
| **Formatos de hoja** (serie A: A4, A3, A2, A1, A0), márgenes, plegado | Fundamentos, junto a escalas | No aparece en ningún capítulo |
| **Serie de grosores normalizados ISO 128** (0,25 / 0,35 / 0,50 / 0,70 mm y relación 2:1) | Fundamentos, junto a tipos de línea | El cap. 02 lista los *tipos* de línea, pero no los *anchos* |
| **Cajetín y rotulación normalizada** | Fundamentos | No aparece |

Sin estos tres elementos, no se puede pedir una lámina entregable con criterio de corrección objetivo.

### 1.4 La brecha grande: no hay sistema diédrico

Este es el hallazgo más relevante de la revisión. La secuencia heredada es:

`Intro → Elementos → Vistas → Ejercicios de vistas → Cónico → CAD 2D → Isometría → Volúmenes 3D → Intersecciones → Proyecto`

Es una secuencia de **dibujo técnico**, no de **geometría descriptiva**. Nunca aparecen: el punto por cota y alejamiento, las trazas de la recta, las rectas notables del plano, la verdadera magnitud, los abatimientos, giros o cambios de plano.

Pero tu planificación destina a eso las **semanas 3 a 9** —el 45 % del semestre— y ahí se juegan la **Prueba 1** (semana 7) y el **Control 2** (semana 10).

**Consecuencia práctica:** los capítulos del colega cubren bien las semanas 1–2 y 10–14 (isometría, CAD, proyecto). Para las semanas 3–9 hay que construir material propio, y para eso ya tienes las fuentes mapeadas en el `TEMARIO_CURSO_SR.md` (caps. 7 a 17) y los tres PDF de la carpeta `Bibliografía\`.

---

## 2. Las dos clases de introducción

Dos sesiones de 2 h 20 cada una. La regla que las ordena: **Clase A entrega el instrumento, Clase B lo usa.**

### Clase A — El lenguaje del dibujo técnico

*"Antes de dibujar un objeto, hay que saber dibujar una línea."*

| Bloque | Tiempo | Contenido | Origen |
|---|---|---|---|
| 1. Presentación del curso | 15 min | Programa, R1 y R2, evaluaciones y fechas, materiales exigidos | Cap. 00 |
| 2. Dibujo técnico y geometría descriptiva | 25 min | Qué es cada uno y en qué se diferencian del dibujo artístico. Monge y el problema del desenfilado. Por qué el lenguaje es normalizado | Cap. 01, diapos 2–4 y 11 |
| 3. El soporte: formatos de hoja | 25 min | Serie A (ISO 216): A0 = 1 m², razón √2, plegado a A4. Márgenes y borde de archivado (ISO 5457). El cajetín: qué campos lleva y por qué | **Nuevo** |
| 4. Tipos de línea y grosores | 30 min | Los 8 tipos de línea de ISO 128 y su significado. Serie de anchos y relación grueso : fino = 2 : 1. Jerarquía cuando dos líneas coinciden | Cap. 02, diapo 4 (ampliada) |
| 5. Escalas | 25 min | Natural, reducción, ampliación. Escalas normalizadas. Escalímetro. **Regla de oro: la cota siempre indica la medida real** | Cap. 02, diapos 5–7 |
| 6. Taller de trazado | 30 min | Lámina A4: margen, cajetín rotulado y una tira con los 8 tipos de línea, correctamente diferenciados por grosor | **Nuevo** |

**Producto de la clase:** una lámina A4 con cajetín. Es también el formato en que se entregará todo el resto del semestre.

### Clase B — Proyección y vistas

*"Ahora sí: cómo se lleva un objeto de tres dimensiones a una hoja de dos."*

| Bloque | Tiempo | Contenido | Origen |
|---|---|---|---|
| 1. Del espacio al papel | 15 min | 1D, 2D, 3D. Por qué una sola imagen plana pierde información: infinitos objetos dan la misma sombra | Cap. 01, diapos 6–8 |
| 2. Qué es proyectar | 25 min | Los tres elementos: punto de vista, objeto, plano de proyección. Rayo proyectante. **Cónica** (rayos convergentes, deforma medidas) vs. **cilíndrica** (rayos paralelos, conserva proporciones). Por qué la técnica exige rayos a 90° | Cap. 01, diapo 12 |
| 3. La caja de cristal | 25 min | PH → planta · PV → alzado · PP → perfil. El abatimiento: cómo las tres vistas llegan a una misma hoja | Cap. 01, diapo 13 · Cap. 02, diapo 8 |
| 4. Las vistas principales | 30 min | Las seis vistas. Elección del alzado. **Primer diedro (Chile/ISO) vs. tercer diedro (EE.UU.)** y el símbolo del cono truncado. Correspondencia: anchos, altos, profundidades. Aristas ocultas. Número mínimo de vistas | Cap. 01, diapos 14–15 |
| 5. Isometría como lectura | 15 min | Ejes a 120°. Para qué sirve: la vista que *muestra la forma*, complemento de las vistas que *dan la medida*. Sin entrar en construcción todavía | Cap. 01, diapo 11 · Cap. 07 |
| 6. Taller doble | 40 min | **(a)** De la isometría a las tres vistas. **(b)** De las tres vistas a la isometría. En lámina A4 con cajetín, aplicando los grosores de la Clase A | Cap. 01, diapos 9–10 y 15 |

**Por qué el taller es doble:** el paso 3D → 2D y el paso 2D → 3D activan procesos mentales distintos. El segundo es el que realmente construye visión espacial, y es el que aparece en las evaluaciones.

**Criterio de corrección del taller (anúncialo antes):** correspondencia entre vistas · uso correcto de línea gruesa/fina/trazos · cajetín completo. Tres criterios, revisables en treinta segundos por lámina.

---

## 3. Orden propuesto de capítulos, de lo simple a lo complejo

### 3.1 Sobre el índice de Rowe y McFarland

No pude recuperar el índice exacto del ejemplar de biblioteca (516.6/R878g) — Internet Archive y Google Books no exponen su tabla de contenidos. Vale la pena revisarlo físicamente en San Juan Pablo II.

Lo que sí es característico de ese texto está en su subtítulo: ***the direct method***. El método directo de Rowe resuelve todo con **vistas auxiliares sucesivas** en lugar de abatimientos, giros y trazas al estilo europeo. Su progresión es: proyección ortográfica → punto → recta → plano → vista auxiliar primaria → vista auxiliar secundaria → perpendicularidad e intersecciones → sólidos y desarrollos.

**Recomendación derivada de esto:** en un curso de primer año sin prerrequisitos, elige **un solo método** para verdadera magnitud —el cambio de plano / vista auxiliar— y enséñalo bien, en vez de pasar abatimientos, giros y cambios de plano como tres técnicas paralelas. Los tres resuelven lo mismo; tres notaciones distintas en cinco semanas es la principal fuente de confusión en este ramo.

### 3.2 Secuencia propuesta

Cada peldaño usa solo lo anterior. Ese es el criterio.

| # | Capítulo | Semana | Estado del material |
|---|---|---|---|
| 00 | Portada y programa | 1 | ✅ Existe |
| 01 | **Fundamentos del trazado** — formatos, cajetín, líneas y grosores, escalas | 1 | 🔧 Cap. 02 diapos 3–7 + material nuevo (formatos, cajetín) |
| 02 | **Teoría de la proyección** — elementos, cónica vs. cilíndrica | 2 | ✅ Cap. 01 diapos 6–8, 11–12 |
| 03 | **Vistas de un objeto** — caja de cristal, seis vistas, diedros | 2 | ✅ Cap. 01 diapos 13–15 + Cap. 03 |
| 04 | **Ejercitación de vistas** — 3D ⇄ 2D | 2–3 | ✅ Cap. 04 |
| 05 | **Diédrico: el punto** — LT, cota, alejamiento, cuadrantes | 3 | 🔴 Por crear · Cap. 02 diapo 8 + Gordon |
| 06 | **Diédrico: la recta** — trazas, posiciones notables | 3–4 | 🔴 Por crear · Gordon + Taibo I |
| 07 | **Diédrico: el plano** — trazas, pertenencia, rectas notables | 4 | 🔴 Por crear · Cap. 02 diapo 9 + Taibo I |
| 08 | **Verdadera magnitud** — vistas auxiliares (método único) | 5 | 🔴 Por crear · Rowe + Gordon |
| 09 | **Intersecciones** — recta-plano y plano-plano, visibilidad | 8 | 🟡 Cap. 09 (parcial) |
| 10 | **Paralelismo y perpendicularidad** | 8 | 🟡 Cap. 09 (parcial) |
| 11 | **Problemas métricos** — distancias y ángulos | 9 | 🔴 Por crear · Gordon |
| 12 | **Sólidos, secciones y desarrollos** | 9 | 🟡 Cap. 08 (parcial) |
| 13 | **Proyección acotada** | 10 | 🔴 Por crear |
| 14 | **Axonometría e isometría** | 11 | ✅ Cap. 07 |
| 15 | **Sistema cónico** — perspectiva | 11 | ✅ Cap. 05 |
| 16 | **AutoCAD 2D** — entorno, dibujo, capas, acotación | 11–12 | ✅ Cap. 06 |
| 17 | **AutoCAD 3D y volúmenes** | 12–13 | ✅ Cap. 08 |
| 18 | **Proyecto integrador** | 13–14 | ✅ Cap. 10 |

**Leyenda:** ✅ material heredado utilizable · 🔧 requiere recorte y complemento · 🟡 existe parcialmente · 🔴 por crear

### 3.3 Cuatro decisiones de orden, con su fundamento

1. **Fundamentos antes que proyección.** No se puede evaluar una lámina cuyo lenguaje aún no se enseñó. Corrige la inversión de la sección 1.1.

2. **Vistas antes que diédrico.** Contraintuitivo si se mira solo el índice de un libro de geometría descriptiva, pero correcto para primer año: la caja de cristal es concreta —hay un objeto que se puede tocar— mientras que el punto por cota y alejamiento es abstracto. Se llega al diédrico habiendo visto ya, informalmente, en qué consiste proyectar sobre dos planos.

3. **El cónico al final, no en la semana 5.** En la presentación heredada el sistema cónico aparece antes que la isometría. Conceptualmente basta mencionarlo en el capítulo 02 —"existen dos familias de proyección"— y desarrollarlo después de la axonometría, cuando ya hay dominio de la proyección cilíndrica. Ir de lo que conserva medidas a lo que las deforma, y no al revés.

4. **CAD después del trazado a mano, no en paralelo.** El software ejecuta; no enseña a proyectar. AutoCAD entra en la semana 11, cuando el criterio gráfico ya está formado, y sirve al proyecto integrador.

---

## 4. Qué hacer ahora

1. **Inmediato:** armar las dos clases con el guion de la sección 2. Falta producir el bloque de formatos de hoja y cajetín (no existe en ningún archivo) y la tabla de grosores ISO 128 (existe a medias).
2. **Corto plazo:** recortar el `02_Elementos_del_Dibujo.pptx` — las diapositivas 8 y 9 se mueven al futuro capítulo de diédrico.
3. **Antes de la semana 3:** decidir el método de verdadera magnitud (recomendación: vista auxiliar / cambio de plano, único) y empezar a producir los capítulos 05 a 08, que son los que sostienen la Prueba 1.
4. **Cuando pases por biblioteca:** revisar el índice real de Rowe y McFarland (516.6/R878g) y el de Wellman (516.6/W452g) para contrastar esta secuencia.
