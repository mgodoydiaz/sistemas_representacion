# Capítulo 2 — Elementos del dibujo

PCI 1119 — Sistemas de Representación · Ingeniería Civil Industrial, UCT
Docente: Miguel Godoy Díaz

Un plano se construye con cuatro elementos: la hoja donde se dibuja, el cajetín que lo identifica, los entes geométricos que se representan y las líneas con que se representan. Este capítulo fija esos cuatro elementos en su forma normalizada.

---

## 1. El soporte: formatos serie A (ISO 216)

La serie A parte del **A0**, cuya superficie es de **1 m²** y cuyos lados guardan la razón **√2 : 1**. Al dividir el formato por la mitad del lado mayor se obtiene el siguiente, que conserva la misma proporción. Por eso un dibujo pasa de un formato a otro sin deformarse.

| Formato | Medidas (mm) |
|---|---|
| A0 | 841 × 1189 |
| A1 | 594 × 841 |
| A2 | 420 × 594 |
| A3 | 297 × 420 |
| A4 | 210 × 297 |

**Plegado.** Todo formato mayor se pliega hasta el tamaño **A4 (210 × 297)**, dejando el cajetín visible en la cara superior y el borde de archivado libre para la perforación.

**Márgenes (ISO 5457).** Se traza un recuadro interior a **10 mm** del borde en los cuatro lados, salvo el borde izquierdo —el de archivado—, donde el margen es de **20 mm**. Nada se dibuja fuera de ese recuadro.

## 2. El cajetín

El **cajetín** (o rótulo) es el bloque de identificación del plano. Va siempre en la **esquina inferior derecha**, apoyado en el recuadro. Es lo primero que lee quien recibe el plano y sin él la lámina no es un documento técnico.

Campos obligatorios:

- **Título** del dibujo o de la pieza
- **Autor** (nombre y curso)
- **Fecha**
- **Escala** empleada
- **Número de lámina** (y total de láminas)
- **Símbolo del método de proyección** (primer o tercer diedro)

## 3. Punto, recta y plano

Son los entes geométricos elementales; todo lo demás se construye con ellos.

- **Punto:** posición sin dimensión. Se nombra con **letra mayúscula**: A, B, C.
- **Recta:** sucesión infinita de puntos en una sola dirección; se nombra con **minúscula**: r, s.
- **Plano:** superficie infinita determinada por tres puntos no alineados; se nombra con **letra griega**: α, β.

Notación de proyecciones: la proyección horizontal lleva **una prima** (A', r', α') y la vertical **dos primas** (A'', r'', α''). Esta convención se usará en todo el sistema diédrico.

## 4. Tipos de línea (ISO 128)

El tipo de línea es información, no decoración.

| Tipo de línea | Grosor | Uso |
|---|---|---|
| Continua gruesa | grueso | Aristas y contornos **visibles** |
| Continua fina | fino | Cotas, líneas auxiliares, rayado de cortes, referencias |
| Trazos | fino | Aristas y contornos **ocultos** |
| Trazo y punto fina | fino | Ejes de simetría y de revolución |
| Trazo y punto fina, gruesa en extremos | mixto | Trazas de planos de corte |
| Zigzag o mano alzada fina | fino | Roturas y vistas parciales |

## 5. Grosores

Serie normalizada de uso corriente: **0,25 — 0,35 — 0,50 — 0,70 — 1,00 mm**.

En cada lámina se elige un **grupo de líneas**: un grueso y su fino en relación **2:1**, y no se mezcla con otro grupo.

| Formato | Gruesa | Fina |
|---|---|---|
| A4 | 0,50 mm | 0,25 mm |
| Uso general | 0,70 mm | 0,35 mm |

## 6. Jerarquía y reglas de trazado

Cuando dos líneas coinciden en la misma posición, se dibuja solo la de mayor jerarquía:

**arista visible > arista oculta > eje**

Reglas de ejecución:

- Las líneas de trazos **empiezan y terminan en trazo**, nunca en espacio.
- Los ejes **sobresalen 3 a 5 mm** del contorno de la pieza.
- La longitud de trazos y espacios se mantiene uniforme en toda la lámina.

## 7. Escalas

La escala es la razón entre la medida del dibujo y la medida real.

- **Natural:** 1:1
- **Reducción:** 1:2, 1:5, 1:10, 1:20, 1:50, 1:100
- **Ampliación:** 2:1, 5:1, 10:1

Solo se usan escalas normalizadas: series de 1, 2 y 5 multiplicadas por potencias de 10. La escala se declara en el cajetín; si una vista va en escala distinta, se indica junto a ella.

El **escalímetro** es una regla de sección triangular con seis graduaciones, cada una calculada para una escala. Se lee directamente sobre la cara correspondiente: no se mide y luego se divide.

**Regla de oro:** la cota indica siempre la **medida real** del objeto, nunca la medida tomada sobre el papel.

## 8. Taller de la clase

**Encargo.** Una lámina A4 en formato vertical con:

1. Margen ISO 5457 (10 mm; 20 mm a la izquierda).
2. Cajetín en la esquina inferior derecha, rotulado a mano con los seis campos obligatorios.
3. Una tira horizontal con muestras de los tipos de línea de la sección 4, de 60 mm cada una, rotuladas con su nombre y grosor. Grupo obligatorio: **0,50 / 0,25 mm**.

**Criterios de corrección.**

| Criterio | Qué se evalúa |
|---|---|
| Cajetín completo | Los seis campos presentes y legibles |
| Grosores distinguibles | Se diferencia grueso de fino a un metro de distancia |
| Limpieza del trazado | Trazos uniformes, sin repasos ni manchas, recuadro cerrado |
