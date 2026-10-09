# Clase 1 — Introducción a los Sistemas de Representación

**PCI 1119 · Sistemas de Representación** · Ingeniería Civil Industrial · UCT
Docente: Miguel Godoy Díaz · Semestre 2026-2 · Secciones 3 y 4

---

## 1. Objetivos del ramo

Tomados del programa oficial de la asignatura.

### 1.1 Resultados de aprendizaje

- **R1 —** Identifica los tipos de proyección gráfica y sus aplicaciones, mediante conceptos de geometría descriptiva, para representar objetos tridimensionales o la intersección entre cuerpos.
- **R2 —** Aplica distintos tipos de proyecciones gráficas, gestionando información y usando herramientas tecnológicas y técnicas de dibujo, para representar soluciones a problemas de ingeniería.

### 1.2 Contenidos conceptuales

1. Definición de lugares geométricos: punto, recta, plano y manejo de escalas.
2. Definición de sistemas de proyección: punto de vista, objeto proyectado, plano de proyección.
3. Tipos de representación gráfica: sistema cónico y cilíndrico.
4. Sistema cilíndrico: doble proyección ortogonal, proyección acotada y proyección axonométrica (isometría).
5. Intersección, paralelismo y perpendicularidad entre rectas y planos, para los distintos sistemas de proyección.
6. Problemas métricos.
7. Introducción al uso de herramientas tecnológicas para la representación gráfica.

### 1.3 Contenidos procedimentales

- Uso de herramientas básicas para los sistemas de representación.
- Análisis de procesos secuenciales para conseguir la solución de problemas métricos.
- Uso de software para la representación en isometría, doble proyección ortogonal, acotado y sólidos en tres dimensiones.

### 1.4 Contenidos actitudinales

- Fomento de la creatividad y de la noción espacial de los sistemas de representación gráfica.

### 1.5 Qué significa esto en la práctica

Al terminar el semestre, cada estudiante debería poder tomar un objeto tridimensional —una pieza, un montaje, un terreno— y producir un documento gráfico que otra persona pueda leer sin ambigüedad y usar para fabricar, cotizar o construir. Y, en el sentido inverso, leer un plano ajeno y reconstruir mentalmente el objeto que describe.

---

## 2. Dibujo técnico

El **dibujo técnico** es el lenguaje gráfico normalizado con que se describe de forma completa y sin ambigüedad la forma, las dimensiones y las características de un objeto, con el fin de fabricarlo, construirlo, verificarlo o comunicarlo.

Tres rasgos lo separan del dibujo artístico:

| | Dibujo artístico | Dibujo técnico |
|---|---|---|
| Finalidad | Expresiva, estética | Informativa, unívoca |
| Interpretación | Abierta, personal | Única: todos leen lo mismo |
| Reglas | Libres | Normalizadas (ISO, NCh, ASME) |

**Normalizado** es la palabra clave. Un plano funciona porque emisor y receptor comparten un mismo código: qué significa una línea de trazos, cómo se ordenan las vistas, cómo se escribe una cota. Ese código lo fijan las normas —a nivel internacional la serie **ISO 128** (principios generales de representación) e **ISO 5457** (formatos), y en Chile las **NCh** del INN, que en general son homólogas de las ISO.

**Escala.** El dibujo técnico casi nunca se hace a tamaño real, pero sí siempre en proporción exacta. La escala es la razón entre la medida del dibujo y la medida real:

- Escala natural: 1:1
- Escalas de reducción: 1:2, 1:5, 1:10, 1:20, 1:50, 1:100…
- Escalas de ampliación: 2:1, 5:1, 10:1…

La escala se declara en el cajetín. Una regla que nunca se rompe: **las cotas indican siempre la medida real del objeto**, no la medida medida sobre el papel.

---

## 3. Geometría descriptiva

La **geometría descriptiva** es la rama de la geometría que estudia cómo representar figuras del espacio tridimensional sobre un plano bidimensional, de modo que la representación sea **reversible**: a partir del dibujo plano se puede reconstruir la posición y las dimensiones del objeto en el espacio, y resolver gráficamente problemas de tres dimensiones.

Esa reversibilidad es lo esencial. Una fotografía representa un objeto, pero no permite recuperar sus medidas. Una doble proyección ortogonal sí.

Es la base teórica del dibujo técnico: mientras el dibujo técnico se ocupa de las convenciones y la normalización, la geometría descriptiva aporta los fundamentos —proyección, verdadera magnitud, intersección, paralelismo, perpendicularidad, distancias y ángulos.

**Los tres problemas que resuelve:**

1. **Representación.** Cómo llevar un punto, una recta, un plano o un sólido al plano del dibujo.
2. **Posición.** Determinar si dos elementos se cortan, son paralelos o perpendiculares, y dónde.
3. **Medida (problemas métricos).** Obtener la verdadera magnitud de segmentos, ángulos y superficies que en la proyección aparecen deformados.

---

## 4. Gaspard Monge

**Gaspard Monge** (Beaune, 1746 – París, 1818) es el fundador de la geometría descriptiva como disciplina sistemática.

Siendo joven profesor en la Escuela Real de Ingeniería Militar de Mézières, se le encargó calcular el trazado de una fortificación (el **desenfilado**: determinar la altura de los muros para que ningún punto interior quedara expuesto al fuego enemigo). El procedimiento habitual era un cálculo aritmético largo y tedioso. Monge lo resolvió gráficamente, con un método de doble proyección, en una fracción del tiempo. La solución fue tan eficaz que el ejército francés la clasificó como **secreto militar** durante unos quince años.

Recién en 1794-1795 pudo enseñarla públicamente en la recién creada **École Polytechnique**, y en 1799 publicó *Géométrie descriptive*, texto que fijó el método y desde el cual se difundió a toda la ingeniería occidental. Por eso el sistema de doble proyección ortogonal se llama también **sistema de Monge**.

Monge fue además fundador de la École Polytechnique, ministro de Marina durante la Revolución y acompañó a Napoleón en la campaña de Egipto.

> **La idea de Monge en una frase:** proyectar el objeto sobre dos planos perpendiculares entre sí y luego abatir uno sobre el otro, de modo que las dos vistas queden en la misma hoja y, juntas, definan el objeto sin ambigüedad.

---

## 5. Proyecciones

**Proyectar** es hacer corresponder cada punto del objeto con un punto del plano del dibujo, trazando rectas —**rayos proyectantes**— desde un centro o punto de vista hasta el plano de proyección.

Todo sistema de proyección tiene tres elementos:

1. **Punto de vista** (centro de proyección) — desde dónde se mira.
2. **Objeto proyectado** — qué se mira.
3. **Plano de proyección** — dónde se recoge la imagen.

### 5.1 Clasificación

Según dónde se ubique el punto de vista:

```
PROYECCIÓN
│
├── CÓNICA (central) — punto de vista propio, a distancia finita
│     Los rayos convergen. Es la perspectiva: realista, con puntos de fuga,
│     pero deforma las medidas. Uso: arquitectura, presentación, render.
│
└── CILÍNDRICA (paralela) — punto de vista impropio, en el infinito
      Los rayos son paralelos entre sí. Conserva proporciones.
      │
      ├── OBLICUA — rayos no perpendiculares al plano (caballera, militar)
      │
      └── ORTOGONAL — rayos perpendiculares al plano
            ├── Doble proyección ortogonal (sistema diédrico)
            ├── Proyección acotada (una vista + cota numérica)
            └── Proyección axonométrica (isométrica, dimétrica, trimétrica)
```

El dibujo técnico trabaja casi exclusivamente con **proyección cilíndrica ortogonal**, porque es la única que permite medir directamente sobre el dibujo.

### 5.2 Por qué no basta una sola proyección

Una proyección aislada pierde información: infinitos objetos distintos pueden dar la misma sombra. De ahí la necesidad de **dos o más proyecciones** relacionadas entre sí —el aporte de Monge— o de una proyección única acompañada de información adicional, como la cota numérica en la proyección acotada.

---

## 6. Vistas principales

Al proyectar el objeto ortogonalmente sobre las seis caras de un cubo imaginario que lo envuelve, se obtienen las **seis vistas principales** (ISO 128):

| Vista | También llamada | Dirección de observación |
|---|---|---|
| **Alzado** | Vista frontal, vista principal | De frente |
| **Planta** | Vista superior | Desde arriba |
| **Vista lateral izquierda** | Perfil izquierdo | Desde la izquierda |
| **Vista lateral derecha** | Perfil derecho | Desde la derecha |
| **Vista inferior** | — | Desde abajo |
| **Vista posterior** | Vista trasera | Desde atrás |

El **alzado** es la vista que mejor define el objeto —la que muestra más información y menos aristas ocultas— y se elige primero; las demás se ordenan respecto de ella.

### 6.1 Sistemas de disposición

Existen dos convenciones para ordenar las vistas en la hoja:

- **Primer diedro (europeo, ISO-E).** El objeto se sitúa entre el observador y el plano de proyección. La vista se dibuja **al lado opuesto** de donde se mira: la planta va debajo del alzado, la vista lateral izquierda va a la derecha. Es el sistema usado en Chile y Europa.
- **Tercer diedro (americano, ISO-A).** El plano se sitúa entre el observador y el objeto. La vista se dibuja **del mismo lado** desde el que se mira: la planta va arriba, la lateral izquierda a la izquierda. Se usa en EE.UU. y Canadá.

Ambos sistemas se distinguen mediante un **símbolo de cono truncado** en el cajetín. Confundirlos invierte el objeto: es una de las causas más habituales de error de fabricación.

### 6.2 Reglas de correspondencia

Las vistas no son dibujos independientes; están ligadas:

- **Alineación.** Alzado y planta comparten anchos (correspondencia vertical); alzado y perfil comparten alturas (correspondencia horizontal).
- **Igualdad.** La profundidad de la planta es igual a la anchura del perfil.
- **Economía.** Se dibuja **el mínimo número de vistas** que define el objeto sin ambigüedad —muchas piezas quedan definidas con dos o tres.

---

## 7. Sistema diédrico

El **sistema diédrico** o **sistema de Monge** es la doble proyección ortogonal sobre dos planos perpendiculares entre sí:

- **Plano horizontal de proyección (PH)** — sobre él se obtiene la **proyección horizontal** o **planta**.
- **Plano vertical de proyección (PV)** — sobre él se obtiene la **proyección vertical** o **alzado**.
- Su intersección es la **línea de tierra (LT)**.
- A veces se agrega un tercer plano, el **plano de perfil (PP)**, perpendicular a los dos anteriores.

Los dos planos dividen el espacio en cuatro regiones llamadas **diedros** o cuadrantes. En dibujo técnico normalizado el objeto se ubica en el **primer diedro** (sistema europeo).

### 7.1 El abatimiento

Para llevar ambas proyecciones a una misma hoja, el plano horizontal se **abate** —se gira 90° en torno a la línea de tierra— hasta hacerlo coincidir con el vertical. El resultado es el dibujo plano habitual: alzado arriba, planta abajo, alineados verticalmente.

### 7.2 El punto en diédrico

Un punto A del espacio queda definido por dos proyecciones, **A'** (horizontal) y **A''** (vertical), siempre alineadas en una perpendicular a la línea de tierra. Sus coordenadas reciben nombres propios:

- **Cota** — distancia del punto al plano horizontal (su "altura").
- **Alejamiento** — distancia del punto al plano vertical (su "profundidad").
- **Abscisa** — posición a lo largo de la línea de tierra.

Con estos tres datos, el sistema es completamente reversible: del dibujo se recupera el espacio. Sobre esta base se construye después todo lo demás —la recta y sus trazas, el plano, las intersecciones, la verdadera magnitud, los problemas métricos.

---

## 8. Isometría

La **proyección axonométrica** es una proyección cilíndrica ortogonal sobre un plano oblicuo respecto de los tres ejes coordenados, de modo que una sola vista muestra las tres dimensiones a la vez. Según los ángulos que el plano forme con los ejes se distinguen tres tipos:

| Tipo | Ángulos entre ejes | Coeficientes de reducción |
|---|---|---|
| **Isométrica** | 120° – 120° – 120° | Iguales en los tres ejes |
| **Dimétrica** | Dos iguales | Dos iguales, uno distinto |
| **Trimétrica** | Los tres distintos | Los tres distintos |

La **isometría** (del griego *isos métron*, "igual medida") es el caso en que los tres ejes forman ángulos iguales de **120°** entre sí. En el papel se dibujan habitualmente como un eje vertical y dos a **30°** respecto de la horizontal.

**Coeficiente de reducción.** En rigor, la proyección isométrica reduce todas las medidas por igual, en un factor de **√(2/3) ≈ 0,8165**. Trabajar con ese factor es incómodo, así que en la práctica se dibuja **dibujo isométrico**: las medidas se llevan a escala 1:1 sobre los ejes. El resultado es un objeto un 22,5 % más grande que la proyección isométrica estricta, pero geométricamente semejante —y por eso perfectamente válido.

**Propiedades útiles:**

- Las medidas paralelas a los ejes isométricos se llevan directamente a escala (líneas isométricas).
- Las medidas **no** paralelas a los ejes se deforman: no se pueden medir directamente, hay que construirlas por coordenadas.
- Las circunferencias se proyectan como **elipses**; en la práctica se aproximan con el método de los cuatro centros.

**Para qué sirve.** La isometría es el puente entre el plano y la comprensión espacial: complementa las vistas diédricas mostrando de un vistazo la forma del objeto. Es, además, la base de la representación en software CAD 3D.

---

## 9. Grosores de línea

En un plano, el **grosor** de la línea no es decorativo: es información. La norma **ISO 128** define un conjunto de tipos de línea, cada uno con un significado y un grosor asociado.

### 9.1 Serie de grosores normalizados

Los anchos se toman de una serie donde cada valor es aproximadamente √2 veces el anterior:

`0,13 — 0,18 — 0,25 — 0,35 — 0,50 — 0,70 — 1,00 — 1,40 — 2,00 mm`

En cada dibujo se elige un **grupo de líneas**: un ancho grueso y su correspondiente fino, en relación **2:1**. Los grupos más usados son:

| Grupo | Línea gruesa | Línea fina |
|---|---|---|
| Dibujos pequeños / A4 | 0,50 mm | 0,25 mm |
| Uso general | 0,70 mm | 0,35 mm |
| Formatos grandes | 1,00 mm | 0,50 mm |

Dentro de un mismo plano se mantiene **un solo grupo**.

### 9.2 Tipos de línea y su uso

| Tipo de línea | Grosor | Se usa para |
|---|---|---|
| Continua **gruesa** | grueso | Aristas y contornos **visibles** |
| Continua **fina** | fino | Líneas de cota, líneas auxiliares de cota, rayado de cortes, líneas de referencia |
| Continua fina a **mano alzada** o en **zigzag** | fino | Límites de vistas o cortes parciales (rotura) |
| **Trazos** (discontinua) | fino (o grueso según norma) | Aristas y contornos **ocultos** |
| **Trazo y punto** fina | fino | Ejes de simetría, ejes de revolución, circunferencias primitivas |
| Trazo y punto fina, **gruesa en los extremos y cambios** | mixto | Trazas de **planos de corte** |
| Trazo y punto **gruesa** | grueso | Superficies con requisitos especiales (tratamientos) |
| Trazo y **doble punto** fina | fino | Contornos de piezas adyacentes, posiciones extremas de piezas móviles, contornos primitivos antes del conformado |

### 9.3 Reglas de trazado

- Cuando dos líneas de distinto tipo coinciden, **prevalece la de mayor jerarquía**: arista visible → arista oculta → eje.
- Las líneas de trazos deben **empezar y terminar con trazo**, no con espacio.
- Los ejes sobresalen ligeramente (3 a 5 mm) del contorno de la pieza.
- La longitud de trazos y espacios se mantiene **uniforme** en todo el dibujo.

> **Regla práctica:** si un plano se lee a un metro de distancia y se distingue de inmediato el contorno del objeto de sus detalles internos, los grosores están bien elegidos.

---

## 10. Bibliografía recomendada

### 10.1 Disponible en biblioteca UCT

Resultados de la búsqueda "geometría descriptiva" en el catálogo del Sistema de Bibliotecas UCT:

| # | Título | Autores | Año | Disponibilidad |
|---|---|---|---|---|
| 1 | *Geometría descriptiva* | Rowe, Charles E.; McFarland, James D. | 1970 | San Juan Pablo II — General · **516.6/R878g** |
| 2 | *Geometría descriptiva* | Morales Urbina, Esther María; Salazar, Aura | 2018 | En línea |
| 3 | *Geometría descriptiva: compendio de geometría descriptiva para técnicos* | Wellman, B. Leighton (Bernard Leighton), 1908– | 1987 | San Juan Pablo II — Básica Obligatoria · **516.6/W452g** |
| 4 | *Nueva gama de ejercicios: geometría descriptiva* | Trujillo Peláez, Carlos Hernando, 1960–; Parra Lara, Hernando, 1967– | 2022 | En línea |
| 5 | *Geometría descriptiva: sistema diédric i acotat: problemes* | Gómez Jiménez, Francisco; Fernández González, Mario | 2007 | En línea |
| 6 | *Geometría descriptiva y sus aplicaciones. Tomo I, punto, recta y plano* | Taibo Fernández, Ángel | 2009 | En línea |
| 7 | *Geometría descriptiva y sus aplicaciones. Tomo II, curvas y superficies* | Taibo Fernández, Ángel | 2009 | En línea |

**Cómo usarlos en este curso:**

- **Wellman (3)** — texto principal de referencia. Está en Básica Obligatoria y cubre el sistema diédrico con enfoque técnico. Es el más cercano al enfoque del ramo.
- **Taibo, Tomo I (6)** — el mejor apoyo para las unidades de punto, recta y plano (semanas 3 a 5). Disponible en línea, sin límite de ejemplares.
- **Taibo, Tomo II (7)** — para intersecciones, superficies y desarrollos (semanas 8 y 9).
- **Trujillo y Parra (4)** y **Gómez y Fernández (5)** — colecciones de problemas resueltos, útiles para preparar controles y pruebas. El (5) está en catalán, pero los enunciados gráficos se siguen sin dificultad.
- **Rowe y McFarland (1)** — clásico de ingeniería, buen complemento para axonometría.
- **Morales y Salazar (2)** — texto breve y accesible, adecuado como primera lectura.

### 10.2 Material adicional del curso

- **Osers, Harry.** *Estudio de Geometría Descriptiva.* Editorial Torino. — Bibliografía declarada en el programa oficial de la asignatura.
- **Gordon, V. O.; Sementsov-Oguievski, M. A.** *Curso de Geometría Descriptiva.* Editorial Mir, Moscú.
- **Gordon, V.; Ivanov, Y.; Solntseva, T.** *Problemas de Geometría Descriptiva.* Editorial Mir, Moscú, 1974. — Problemario complementario del anterior.

### 10.3 Normas de referencia

- **ISO 128** — Dibujos técnicos: principios generales de representación (tipos de línea, vistas, cortes).
- **ISO 5457** — Formatos y disposición de los elementos gráficos de la hoja.
- **ISO 129** — Acotación.
- **NCh** (INN, Chile) — Serie de normas chilenas de dibujo técnico, homólogas de las ISO.

---

## 11. Cierre de la clase

Tres ideas para retener:

1. El dibujo técnico es un **lenguaje con reglas**, y su valor está en que no admita dos lecturas.
2. Toda representación plana de un objeto 3D es una **proyección**; elegir el sistema de proyección es elegir qué información se conserva y cuál se pierde.
3. El sistema diédrico conserva las **medidas**; la isometría conserva la **forma**. En un plano técnico completo aparecen los dos, porque se complementan.

**Para la próxima sesión:** lugares geométricos —punto, recta y plano— y manejo de escalas.
