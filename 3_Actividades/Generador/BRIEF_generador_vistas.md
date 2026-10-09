# BRIEF — Generador de ejercicios de vistas (imagen → modelo → DXF)

> **Instrucción para el agente:** este documento es el encargo. **No escribas código todavía.**
> Primero produce un plan de trabajo (arquitectura, fases, riesgos, decisiones abiertas) y
> preséntalo para aprobación. Recién aprobado el plan, implementa.
>
> Orquestación sugerida (skill `agentes-con-fable`): **Fable** planifica y revisa el diseño y
> los criterios de aceptación; **Opus** implementa los módulos de geometría y DXF;
> **Sonnet** ejecuta tareas mecánicas (fixtures, scaffolding, formateo, tests repetitivos).

---

## 1. Contexto

Ramo **Sistemas de Representación (PCI 1119)**, carrera de Arquitectura, Universidad Católica de
Temuco. El docente prepara material para el capítulo *Vistas de un objeto* y su repaso: sólidos
formados por cubos unitarios sobre una retícula, de los que el estudiante debe deducir alzado,
perfil y planta.

Hoy esas láminas se arman a mano o se reciclan de material ajeno. El objetivo es **producirlas por
código**: reproducibles, en lote, con solucionario correcto, y en formato editable en AutoCAD.

## 2. Objetivo

Una herramienta en Python que:

1. **Lea** un sólido desde una imagen (isométrica dibujada a mano o escaneada) o desde una
   definición textual.
2. **Modele** el sólido como una matriz de ocupación en retícula.
3. **Derive** por cálculo geométrico las seis vistas ortogonales, con aristas vistas y ocultas.
4. **Emita** la lámina de ejercicio y la hoja de solución en `.dxf`, más versiones `.svg`/`.png`
   para insertar en las presentaciones del ramo.
5. **Genere lotes** de ejercicios aleatorios con semilla reproducible.

## 3. Alcance por fases

**Fase 1 — núcleo determinista (prioritaria).**
Entrada: sólidos de cubos sobre retícula N×N×N (por defecto 3×3×3). La imagen de entrada es una
isométrica sobre malla regular, del tipo usado en el material del ramo. El reconocimiento se apoya
en que la proyección isométrica de una retícula es una teselación de rombos: se detecta la malla,
se clasifica cada rombo por su orientación (cara superior / cara izquierda / cara derecha) y su
tono, y se reconstruye la ocupación por consistencia. **Sin machine learning.**

**Fase 2 — croquis a mano alzada.**
Vectorización de bocetos libres: preprocesado, detección de segmentos, unión de líneas quebradas,
ajuste a las tres direcciones isométricas, cierre de polígonos. Se acepta que requiera confirmación
humana. El plan debe contemplarla pero **no se implementa hasta cerrar la Fase 1**.

Fase 1 y Fase 2 deben compartir el mismo modelo intermedio, de modo que el resto del pipeline
(vistas + DXF) sea idéntico para ambas.

## 4. Modelo de datos y convenciones geométricas

**Estas convenciones son obligatorias y ya están validadas contra el material del ramo. No las
reinterpretes.**

Retícula de cubos unitarios con índices `(i, j, k)`, cada uno en `0..N-1`:

- `i` — profundidad; **crece hacia el observador del alzado** (hacia adelante).
- `j` — horizontal; **crece hacia la derecha del observador del alzado**.
- `k` — vertical; crece hacia arriba.

Sistema de representación: **primer diedro (europeo)**, el que se usa en el ramo.

| Vista | Dirección de mirada | Ubicación en lámina | Columna de la retícula | Fila | Sentido |
|---|---|---|---|---|---|
| Alzado (frontal) | según `−i` | referencia | `j` | `k` | `j` a la derecha, `k` hacia arriba |
| Perfil izquierdo | según `+j` | a la **derecha** del alzado | `i` | `k` | `i` a la derecha |
| Perfil derecho | según `−j` | a la izquierda del alzado | `i` | `k` | espejo del anterior |
| Planta | según `−k` | **debajo** del alzado | `j` | `i` | `j` a la derecha, `i` hacia **abajo** (el frente queda abajo) |
| Alzado posterior | según `+i` | a la derecha del perfil izq. | `j` | `k` | espejo horizontal del alzado |
| Vista inferior | según `+k` | sobre el alzado | `j` | `i` | espejo vertical de la planta |

**Silueta:** una celda de la vista está llena si existe al menos un cubo en la fila de profundidad
correspondiente.

**Aristas vistas:** calcular un *mapa de profundidad* por vista (la superficie más cercana al
observador en cada celda). Se dibuja arista vista en el borde entre dos celdas contiguas cuando su
profundidad difiere, y en todo el contorno de la silueta.

**Aristas ocultas:** cambios de geometría que quedan tapados por material más cercano se dibujan en
trazo segmentado. No omitirlas: son parte de la corrección del ejercicio.

## 5. Fixtures de validación (verdad de terreno)

Dos sólidos ya verificados contra las láminas originales del capítulo 03. Sirven como golden tests:
si el pipeline no los reproduce exactamente, está mal.

Notación: una capa por valor de `k` (de abajo hacia arriba); dentro de cada capa, una fila por `j`
(de `j=0` a `j=N-1`) y una columna por `i` (de `i=0` a `i=N-1`). `X` = cubo, `O` = vacío.

### Figura A — muro frontal + losa
```
k=0:  XXX / XXX / XXX
k=1:  XXX / OOO / OOO
k=2:  XXX / OOO / OOO
```
Vistas esperadas (█ lleno):
```
Alzado          Perfil izq.     Planta
█ · ·           █ █ █           █ █ █
█ · ·           █ █ █           █ █ █
█ █ █           █ █ █           █ █ █
```
Detalles que el solucionario debe incluir: el perfil izquierdo no tiene aristas vistas interiores,
pero sí una **arista oculta horizontal** a la altura `k=1`; la planta lleva una **arista vista
vertical** a un tercio desde la izquierda (cambio de cota 3 → 1).

### Figura B — muro lateral + losa escotada + cubo suelto
```
k=0:  XXX / XXX / XXO
k=1:  XOO / XXO / XOO
k=2:  XOO / XOO / XOO
```
Vistas esperadas:
```
Alzado          Perfil izq.     Planta
█ █ █           █ · ·           █ █ █
█ █ █           █ █ ·           █ █ █
█ █ █           █ █ █           █ █ ·
```
El alzado es una silueta llena **pero no es un rectángulo liso**: lleva aristas vistas por los
cambios de profundidad (horizontal completa a la altura `k=1`, verticales en la fila central y en la
fila inferior). Un solucionario que entregue el cuadrado vacío está incorrecto.

## 6. Salidas requeridas

1. **`ejercicio.dxf`** — isométrica del sólido + tres retículas vacías rotuladas *Alzado*, *Perfil*,
   *Planta*, dispuestas según primer diedro, con la flecha que indica la dirección del alzado.
2. **`solucion.dxf`** — la misma lámina con las vistas resueltas: aristas vistas, aristas ocultas en
   trazo segmentado y relleno o achurado de las caras.
3. **`*.svg` y `*.png`** — mismas láminas en vectorial y raster, con márgenes ajustados, para
   insertar en los `.pptx` del ramo.
4. **Lote**: `generar_lote(n, semilla)` produce N sólidos distintos con sus soluciones,
   reproducible a partir de la semilla, con control de dificultad (número de cubos, cantidad de
   escalones, presencia de aristas ocultas).

### Convenciones DXF

- Unidades en milímetros, formato de lámina parametrizable (A4 y A3 apaisado como mínimo).
- Capas separadas y nombradas: `ARISTA_VISTA`, `ARISTA_OCULTA`, `EJES`, `RETICULA`, `TEXTO`,
  `COTAS`, `ISOMETRICA`.
- Tipos de línea reales en el archivo (`CONTINUOUS`, `HIDDEN`), no simulados con segmentos sueltos.
- Espesores por capa según norma de dibujo técnico: contorno visible grueso, oculta y retícula finas.
- El archivo debe abrir limpio en AutoCAD y ser editable: geometría como `LINE`/`LWPOLYLINE`,
  textos como `MTEXT`, nada de bloques anidados innecesarios.

## 7. Restricciones

- Python 3.11+, Windows como entorno principal del docente.
- Dependencias: `ezdxf` para DXF, `numpy`, `opencv-python` y `Pillow` para la lectura de imagen,
  `svgwrite` o generación SVG propia. Evitar dependencias pesadas o que requieran compilación.
- Sin servicios en la nube ni llamadas a API para el reconocimiento: todo debe correr offline.
- Interfaz de línea de comandos clara; una API de Python igualmente utilizable desde un notebook.
- Código y comentarios en español.

## 8. Criterios de aceptación

- Las dos figuras del §5 se reproducen exactamente, incluidas aristas vistas y ocultas.
- Round-trip: `matriz → isométrica renderizada → lectura de esa imagen → matriz` devuelve la matriz
  original para al menos 50 sólidos aleatorios de 3×3×3.
- El DXF abre sin advertencias en AutoCAD y respeta capas y tipos de línea.
- Un lote de 20 ejercicios se genera en menos de 30 segundos.
- Tests automatizados que cubran la derivación de las seis vistas, no solo tres.

## 9. Fuera de alcance

- Sólidos con caras oblicuas, curvas o no alineadas a la retícula.
- Perspectiva cónica.
- Interfaz gráfica. La CLI es suficiente.
- Corrección automática de respuestas de estudiantes (posible fase 3, no ahora).

## 10. Preguntas que el plan debe responder

- ¿Cómo se detecta la malla isométrica en una imagen con inclinación, sombra o fotografía de papel?
- ¿Qué hacer ante ambigüedad real? Un sólido de cubos **no siempre** queda determinado por su
  isométrica: puede haber huecos internos invisibles. ¿Se asume el sólido mínimo, el máximo, o se
  pide confirmación?
- ¿Cómo se resuelve el reconocimiento cuando la retícula no es 3×3×3?
- ¿Qué estructura de proyecto conviene: paquete instalable, o carpeta de scripts junto al material
  del ramo?
