# Capítulo 3 — Vistas de un objeto

**PCI 1119 · Sistemas de Representación** · Ingeniería Civil Industrial · UCT
Docente: Miguel Godoy Díaz

---

## 1. La caja de cristal

Imagine la pieza suspendida dentro de un cubo transparente. Cada cara del cubo es un **plano de proyección**: se mira la pieza perpendicularmente a esa cara y se dibuja sobre ella el contorno que se ve, como si se calcara. No hay perspectiva ni fuga; los rayos proyectantes son paralelos, así que las medidas se conservan.

Tres planos bastan para empezar:

- **PH**, plano horizontal → sobre él se obtiene la **planta** (mirando desde arriba).
- **PV**, plano vertical → sobre él se obtiene el **alzado** (mirando de frente).
- **PP**, plano de perfil → sobre él se obtiene el **perfil** o vista lateral.

Los tres son perpendiculares entre sí. La intersección de PH con PV es la **línea de tierra (LT)**.

## 2. El abatimiento

Las tres imágenes están en planos distintos del espacio; la hoja es una sola. El **abatimiento** resuelve el problema: se deja fijo el plano vertical y los demás se giran 90° hasta hacerlos coincidir con él, como si se desplegara la caja de cristal.

Resultado, en primer diedro:

- El **alzado** queda arriba, en el centro.
- La **planta** cae **debajo** del alzado, alineada verticalmente.
- El **perfil izquierdo** queda **a la derecha** del alzado, alineado horizontalmente.

Las vistas no se distribuyen "donde quepan": su posición es información normalizada.

## 3. Las seis vistas principales

Desplegando las seis caras del cubo se obtienen las seis vistas de ISO 128.

| Vista | Dirección de observación |
|---|---|
| Alzado (vista frontal) | De frente |
| Planta (vista superior) | Desde arriba |
| Vista lateral izquierda | Desde la izquierda |
| Vista lateral derecha | Desde la derecha |
| Vista inferior | Desde abajo |
| Vista posterior | Desde atrás |

## 4. Elección del alzado y número mínimo de vistas

El **alzado** se elige primero y manda sobre el resto. Criterios, en orden:

1. Es la vista que **más informa** sobre la forma de la pieza.
2. Es la que presenta **menos aristas ocultas**.
3. Si es posible, muestra la pieza en su **posición de trabajo o de fabricación**.

Elegido el alzado, las demás vistas quedan determinadas. Y se dibuja **el mínimo número de vistas** que define la pieza sin ambigüedad: la mayoría se resuelve con **dos o tres**. Una vista de más no aporta y ensucia la lámina; una de menos deja el objeto indefinido.

## 5. Primer diedro y tercer diedro

| | Primer diedro (ISO-E) | Tercer diedro (ISO-A) |
|---|---|---|
| Uso | Chile, Europa, ISO | EE.UU., Canadá |
| El objeto está | Entre observador y plano | Detrás del plano |
| Planta | Debajo del alzado | Arriba del alzado |
| Lateral izquierda | A la derecha | A la izquierda |

En primer diedro la vista se dibuja **al lado opuesto** de donde se mira; en tercer diedro, **del mismo lado**. En el **cajetín** se declara el sistema con el símbolo del **cono truncado**: dos vistas del tronco de cono, cuya disposición relativa (círculo mayor hacia afuera o hacia adentro) indica el diedro. Confundirlos invierte la pieza y es una causa clásica de error de fabricación. En este curso se trabaja siempre en **primer diedro**.

## 6. Correspondencia entre vistas

Las vistas son proyecciones del mismo objeto, no dibujos sueltos:

- **Alzado – planta:** comparten los **anchos**. Toda arista vertical de una se prolonga a la otra.
- **Alzado – perfil:** comparten las **alturas**. Se transfieren con horizontales.
- **Planta – perfil:** comparten las **profundidades**. Se transfieren con compás o con la recta auxiliar a 45°.

Regla de trabajo: nunca se mide dos veces la misma dimensión. Se mide una vez y se traslada con líneas auxiliares finas.

## 7. Aristas ocultas y ejes de simetría

- **Línea de trazos (fina):** aristas y contornos que existen pero no se ven desde esa dirección —perforaciones, rebajes internos, caras traseras—. Se dibujan siempre que su omisión deje la pieza ambigua. Deben empezar y terminar con trazo.
- **Línea de trazo y punto (fina):** ejes de simetría, ejes de agujeros y de revolución. Se dibujan en toda pieza o detalle simétrico, y sobresalen 3 a 5 mm del contorno.

Si dos líneas coinciden, prevalece la de mayor jerarquía: arista visible → arista oculta → eje.

## 8. La isometría como vista de lectura

La isometría muestra las tres dimensiones en una sola imagen: los tres ejes forman **120°** entre sí, y en el papel se trazan como un eje vertical y dos a 30° de la horizontal. Sirve para **entender la forma** de un vistazo, y por eso acompaña a las vistas en la lámina.

Pero la medida la dan las vistas diédricas, no la isometría: en ella solo las líneas paralelas a los ejes se miden directamente, las oblicuas se deforman y las circunferencias aparecen como elipses. Por ahora se usa solo como lectura; los métodos de construcción se ven más adelante.

## 9. Taller doble de la clase

**(a) De la isometría a las tres vistas.** Dada una pieza en isometría, obtener alzado, planta y perfil izquierdo en primer diedro, en formato A4 con cajetín.

**(b) De las tres vistas a la isometría.** Dadas tres vistas, reconstruir la pieza y dibujarla en isometría.

**Criterios de corrección:**

1. **Correspondencia entre vistas:** alineación vertical y horizontal exacta, profundidades coincidentes.
2. **Uso correcto de grosores:** contorno visible grueso, ocultas y ejes finos, auxiliares finas.
3. **Cajetín completo:** título, escala, símbolo de diedro, autor, fecha.
