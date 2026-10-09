# Capítulo 1 — Introducción a los sistemas de representación

**PCI 1119 · Sistemas de Representación** · Ingeniería Civil Industrial, UCT · Miguel Godoy Díaz

---

## 1. Presentación de la asignatura

Los dos resultados de aprendizaje del programa oficial son:

- **R1 —** Identifica los tipos de proyección gráfica y sus aplicaciones, mediante conceptos de geometría descriptiva, para representar objetos tridimensionales o la intersección entre cuerpos.
- **R2 —** Aplica distintos tipos de proyecciones gráficas, gestionando información y usando herramientas tecnológicas y técnicas de dibujo, para representar soluciones a problemas de ingeniería.

En la práctica: al terminar el semestre usted debería poder representar un objeto tridimensional en un documento gráfico que otra persona lea sin ambigüedad y, a la inversa, leer un plano ajeno y reconstruir el objeto.

**Evaluaciones**

| Instancia | Momento |
|---|---|
| Control 1 | Semana 4 |
| Prueba 1 | Semana 7 |
| Control 2 | Semana 10 |
| Prueba 2 | Semana 12 |
| Proyecto AutoCAD | 30 % de la nota final |

**Materiales exigidos:** lápiz grafito HB y 2H, escuadras, compás, escalímetro y croquera. Se usan desde la primera sesión práctica.

---

## 2. Dibujo técnico

El **dibujo técnico** es el lenguaje gráfico normalizado con que se describe de forma completa y sin ambigüedad la forma, las dimensiones y las características de un objeto, con el fin de fabricarlo, construirlo, verificarlo o comunicarlo.

| | Dibujo artístico | Dibujo técnico |
|---|---|---|
| Finalidad | Expresiva, estética | Informativa, unívoca |
| Interpretación | Abierta, personal | Única: todos leen lo mismo |
| Reglas | Libres | Normalizadas (ISO, NCh, ASME) |

La palabra clave es **normalizado**. Un plano funciona porque emisor y receptor comparten un mismo código: qué significa una línea de trazos, cómo se ordenan las vistas, cómo se escribe una cota. Ese código lo fijan las normas **ISO 128** e **ISO 5457**, y en Chile las **NCh** del INN, homólogas de las ISO.

---

## 3. Geometría descriptiva

La **geometría descriptiva** estudia cómo representar figuras del espacio tridimensional sobre un plano bidimensional de modo que la representación sea **reversible**: a partir del dibujo plano se puede reconstruir la posición y las dimensiones del objeto.

Esa reversibilidad es lo esencial: una fotografía representa un objeto, pero no permite recuperar sus medidas; una doble proyección ortogonal sí. Si el dibujo técnico aporta las convenciones, la geometría descriptiva aporta los fundamentos.

**Los tres problemas que resuelve:**

1. **Representación.** Cómo llevar un punto, una recta, un plano o un sólido a la hoja.
2. **Posición.** Determinar si dos elementos se cortan, son paralelos o perpendiculares, y dónde.
3. **Medida (problemas métricos).** Obtener la verdadera magnitud de segmentos, ángulos y superficies deformados en la proyección.

---

## 4. Gaspard Monge

**Gaspard Monge** (1746–1818), joven profesor en la Escuela Real de Ingeniería Militar de Mézières, recibió el encargo de calcular el **desenfilado** de una fortificación: determinar la altura de los muros para que ningún punto interior quedara expuesto al fuego enemigo. El procedimiento habitual era un cálculo aritmético largo; Monge lo resolvió gráficamente, mediante doble proyección, en una fracción del tiempo. La solución fue tan eficaz que el ejército francés la clasificó como **secreto militar** unos quince años, hasta que pudo enseñarla en la École Polytechnique y publicarla en 1799. Por eso el sistema de doble proyección ortogonal se llama también **sistema de Monge**.

> **La idea de Monge en una frase:** proyectar el objeto sobre dos planos perpendiculares entre sí y luego abatir uno sobre el otro, de modo que las dos vistas queden en la misma hoja y, juntas, definan el objeto sin ambigüedad.

---

## 5. Las dimensiones del espacio

En una dimensión (1D), la recta, basta un dato para ubicar un punto. En dos (2D), el plano —la hoja de papel—, hacen falta dos. En tres (3D), el espacio donde existen los objetos de ingeniería, se requieren tres. El problema de fondo del curso es que dibujamos en 2D objetos que viven en 3D: siempre hay una dimensión que debe codificarse de algún modo.

---

## 6. Qué es proyectar

**Proyectar** es hacer corresponder cada punto del objeto con un punto del plano del dibujo, trazando rectas desde un centro. Todo sistema de proyección tiene cuatro elementos:

- **Punto de vista** (centro de proyección): desde dónde se mira.
- **Objeto proyectado**: qué se mira.
- **Plano de proyección**: dónde se recoge la imagen.
- **Rayo proyectante**: la recta que une cada punto del objeto con su imagen.

---

## 7. Proyección cónica y proyección cilíndrica

- **Cónica (central).** Punto de vista a distancia finita; los rayos convergen. Es la perspectiva: conserva el realismo y la sensación de profundidad, pero deforma las medidas —lo lejano se ve menor. Uso: arquitectura, presentación, renderizado.
- **Cilíndrica (paralela).** Punto de vista en el infinito; los rayos son paralelos. Conserva proporciones y paralelismos; pierde el efecto de profundidad.

La cilíndrica se subdivide en **oblicua** (rayos inclinados) y **ortogonal** (rayos perpendiculares al plano). El dibujo técnico usa casi exclusivamente la **cilíndrica ortogonal**, porque es la única que permite medir directamente sobre el dibujo. Con todo, una proyección aislada pierde información: infinitos objetos distintos pueden dar la misma sombra. De ahí la necesidad de dos o más proyecciones relacionadas entre sí.

---

## 8. Mapa del curso

- **Sistema diédrico.** Doble proyección ortogonal sobre dos planos perpendiculares: base para resolver posición, verdadera magnitud y problemas métricos.
- **Proyección acotada.** Una vista más la cota numérica de cada punto; propia de topografía y obras de tierra.
- **Proyección axonométrica.** Una vista única que muestra las tres dimensiones a la vez; la isometría es el caso más usado.
- **Sistema cónico.** La perspectiva de punto de vista propio, para representación realista.

---

## 9. Cierre: ¿y cómo se dibuja esto?

Ya sabemos qué es proyectar y qué sistemas existen. Falta lo concreto: los elementos con que se construye cualquier dibujo —punto, recta y plano— y el manejo de escalas. Ese es el **Capítulo 2**.
