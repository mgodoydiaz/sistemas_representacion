# Proyecto 2 · Piezas de una válvula · Notas para el profesor

Borrador. Todo lo marcado [por confirmar] o [por definir] en el enunciado sigue abierto.

## Cómo se generó

- `piezas_proyecto2.py` define cada pieza una sola vez como sólido 3D (CadQuery, núcleo OpenCascade) y de ahí proyecta alzado, planta, lateral izquierda e isométrico con eliminación de líneas ocultas. Vistas e isométrico son coherentes por construcción.
- Las cotas se anclan a puntos 3D y su valor se mide sobre la proyección. El script falla si alguna cota no es entera.
- El dibujo se hace con matplotlib y los helpers de `figuras_apunte_v3.py` (copia sin modificar).
- `build_proyecto2.py` arma el .docx y el .pdf con la plantilla del profesor.
- Dependencias: `cadquery`, `shapely`, `matplotlib`, `python-docx`, LibreOffice.
- Regenerar: `python3 piezas_proyecto2.py && python3 build_proyecto2.py`.
- Las figuras no están a escala de impresión. El isométrico se dibuja sin reducción (como ISODRAFT).

Ejes de la pieza: X ancho, Y profundidad, Z alto. Origen en el centro de la base. Las cuatro piezas son simétricas respecto de los planos X = 0 e Y = 0.

## V1 Bonete (80 × 80 × 60)

- Brida cuadrada 80 × 80 × 12, esquinas R12.
- 4 agujeros Ø10 pasantes, centros en cuadro de 56 × 56 (concéntricos con los R12).
- Cuello Ø40 desde z = 12 hasta z = 60.
- Paso del vástago Ø16 pasante. Caja de empaquetadura Ø28, profundidad 25 desde arriba.
- 2 nervios de espesor 8 en el plano Y = 0. Van desde el borde de la brida (x = ±40, z = 12) hasta el cuello a z = 42 (30 sobre la brida).
- Detalle: el nervio toca el cilindro en x = 19,6 (no en 20). En el alzado se ve un escalón de 0,4 mm. Es geometría real. A los estudiantes se les puede aceptar el encuentro en x = 20.
- Corte recomendado: semicorte en el alzado por el plano Y = 0, o corte total A-A por el mismo plano. El plano corta los nervios a lo largo, así que no se rayan. Es la variante que evalúa esa convención.
- Los 4 agujeros no quedan en el plano de corte. Se resuelven en la planta con «4 × Ø10» o con un corte alineado (opcional).
- Vistas suficientes: alzado con corte y planta.
- Isométrico: isocírculos solo en el isoplano superior. Dificultad en las esquinas R12 y en el encuentro nervio y cuello.

## V2 Prensaestopas (110 × 40 × 50)

- Brida oblonga 110 × 40 × 12, extremos R20.
- 2 ranuras cerradas de 12 × 20. Centros de arco a x = ±31 y ±39 (62 entre centros interiores, 8 entre centros de cada ranura).
- Casquillo Ø30 desde z = 12 hasta z = 50, con chaflán 2 × 45° arriba.
- Agujero Ø16 pasante. Rebaje Ø22, profundidad 8, por la cara inferior.
- Corte recomendado: corte total A-A por el plano Y = 0 en el alzado. Muestra ranuras, agujero y rebaje en una sola vista. El semicorte también sirve.
- Vistas suficientes: alzado con corte y planta.
- Isométrico: solo isoplano superior. Es la pieza más simple en la Parte A. El rebaje inferior no se ve.

## V3 Yugo (110 × 40 × 84)

- Base 110 × 40 × 12. Agujero central Ø24 pasante. 2 agujeros Ø10 pasantes a x = ±45 (90 entre centros, 10 de cada extremo).
- 2 columnas de 12 × 30 (x de 20 a 32, y de -15 a 15), desde z = 12 hasta el puente.
- Puente de 64 × 30, cara superior a z = 76, con chaflanes de 8 × 45° en los extremos. Ventana de 40 × 50 (techo a z = 62).
- Cubo Ø28 de alto 8 (hasta z = 84). Agujero Ø16 pasante por cubo y puente.
- Agujero transversal Ø10 a z = 40, pasante por las dos columnas.
- Corte recomendado: corte total A-A por el plano Y = 0 en el alzado. Corta base, columnas, puente y los cinco agujeros. Las columnas no son nervios: sí se rayan.
- Vistas suficientes: alzado con corte y planta. La lateral ayuda a ver el Ø10 como círculo.
- Isométrico: isoplano superior y lateral (agujero Ø10). En isométrico el chaflán izquierdo se ve de canto.

## V4 Cuerpo (90 × 50 × 60)

- Bloque 50 × 50 × 60.
- 2 bocas Ø40 de largo 20, coaxiales, eje a z = 30. Largo total 90.
- Paso Ø24 pasante a lo largo de X.
- Alojamiento de la compuerta: ranura de 12 (en X) × 34 (en Y), profundidad 48 desde la cara superior (fondo a z = 12).
- 4 agujeros ciegos Ø8, profundidad 12, centros en cuadro de 36 × 36.
- Se evitó a propósito la intersección de dos cilindros: el alojamiento es prismático, así que todo son rectas y círculos.
- Corte recomendado: corte total A-A por el plano Y = 0 en el alzado (paso y alojamiento). Los agujeros Ø8 quedan fuera del plano: se aceptan con nota en la planta, con un corte parcial o con un corte por planos paralelos.
- Vistas suficientes: alzado con corte, planta y lateral (círculos de las bocas).
- Isométrico: isoplano superior (agujeros) y lateral (bocas).

## Cómo se da el interior en los isométricos

No se usó el cuarto retirado. Los interiores se dan con notas («Ø28, prof. 25», «Ø24 pasante») y un bloque de notas al pie de cada lámina. Así el estudiante de la Parte B tiene que construir el corte por su cuenta. Lo mismo para resaltes difíciles de acotar limpio en isométrico («Cubo Ø28, alto 8», «2 bocas Ø40, largo 20»).

En las láminas de vistas, las profundidades también van como nota para no acotar sobre aristas ocultas.

## Asignación sugerida

Dificultad estimada. Parte A: V2 baja, V4 media, V1 y V3 media alta. Parte B: V2 baja, V3 media, V4 media alta, V1 alta (nervios).

Cuatro combinaciones equilibradas, cada pieza una vez por parte:

| Grupo | Parte A | Parte B |
|---|---|---|
| 1 | V2 | V1 |
| 2 | V1 | V2 |
| 3 | V3 | V4 |
| 4 | V4 | V3 |

Hay 12 pares ordenados posibles si se necesita más variedad.

## Decisiones abiertas

1. Modalidad individual o en parejas.
2. Fechas de lanzamiento y entrega. Medio de entrega.
3. Bonificación de hasta 5 décimas. La vista auxiliar solo aplica a V1 y V3. V2 y V4 no tienen cara plana inclinada: quedan con la opción de Python, o se les agrega un chaflán.
4. Formato de hoja. A 1:1 las vistas más el isométrico de la Parte B no caben cómodas en A4. Se propuso A4 para la Parte A y A3 para la Parte B.
5. Grosores de la tabla de capas (0,50 y 0,25 mm). Ajustar a lo que se usó en la plantilla de clases.
6. Conversión de puntaje a nota: el enunciado solo dice 0,4 × A + 0,6 × B. Falta la escala.
7. Puntajes de la rúbrica y niveles (100 %, 60 %, 30 %, 0 %): propuesta mía.
8. Parte A sin acotar el isométrico. Si se quiere evaluar cotas isométricas hay que agregar un criterio.
9. Las piezas no forman un conjunto ensamblable (la caja Ø28 de V1 y el casquillo Ø30 de V2 no calzan). Si se quiere un conjunto, se ajustan diámetros.
10. V2 es más simple que las demás. Se puede compensar con la asignación o agregándole un detalle.
11. Si se quiere una pauta, el mismo script puede generar las vistas cortadas de cada pieza. No está hecho.
