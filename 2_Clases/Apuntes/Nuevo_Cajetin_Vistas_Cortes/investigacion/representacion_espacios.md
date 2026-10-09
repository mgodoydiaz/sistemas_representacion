# Representación de espacios: bodegas, industrias y edificios

Notas de investigación para PCI 1119 Sistemas de Representación (Ing. Civil Industrial, UCT).
Fecha: 23-09-2026. Las fuentes van entre corchetes con su URL al final de cada punto.
Lo marcado **[NO VERIFICADO]** no se pudo confirmar en una fuente primaria.

---

## 1. Idea central: es la misma teoría de vistas y cortes

- Un plano de arquitectura es un sistema de proyecciones ortogonales, igual que el de una pieza. Lo que cambia es la escala y las convenciones.
- **Planta** = corte horizontal. El plano de corte se ubica a unos 1,2 m (4 ft) sobre el piso terminado, para cortar muros, puertas y ventanas. [Wikipedia, Floor plan: https://en.wikipedia.org/wiki/Floor_plan] [CUNY City Tech: https://openlab.citytech.cuny.edu/christo-arch1101-fall-2020/files/2020/09/Architectural-Drawings_Plan-Section-Elevation.pdf]
  - Lo cortado se dibuja con línea más gruesa; lo que queda bajo el plano, más fino; lo que queda sobre el plano (vigas, altillos), segmentado u omitido. [CUNY, misma URL]
  - En BIM (Revit) esto se controla con el "View Range": lo cortado por el plano de corte sale grueso y lo que está entre el corte y el fondo, fino. [BIM Pure: https://www.bimpure.com/blog/how-to-use-view-range-in-revit]
- **Corte o sección** = corte vertical; muestra alturas, niveles, estructura de techumbre. [CUNY, misma URL]
- **Elevación o fachada** = vista exterior ortogonal de un lado del edificio; se nombra por la orientación (norte, sur, etc.). [CUNY, misma URL]

### Equivalencias con piezas mecánicas

| Pieza mecánica | Edificio o nave | Comentario |
|---|---|---|
| Vista superior | Planta de techumbre (cubierta) | Vista, no corte |
| Corte horizontal | Planta de arquitectura | Corte a ~1,2 m del piso |
| Corte vertical A-A | Corte A-A | Misma línea de corte con flechas y letras |
| Vista frontal y laterales | Elevaciones / fachadas | Norte, sur, oriente, poniente |
| Detalle a mayor escala | Plano de detalle (1:20 a 1:5) | Uniones, andenes, escaleras |
| Plano de conjunto | Planta de emplazamiento / ubicación | Edificio dentro del terreno |

---

## 2. Tipos de planos de un espacio

| Plano | Qué muestra | Escala usual |
|---|---|---|
| Ubicación (location plan) | Terreno en la ciudad o sector | 1:1250, 1:1000, 1:500 |
| Emplazamiento (site plan) | Silueta del edificio, distancias a deslindes, accesos, norte | 1:200, 1:100 |
| Planta de arquitectura | Muros, vanos, ejes, cotas, niveles, recintos | 1:100, 1:50 |
| Cortes y elevaciones | Alturas, niveles, techumbre, fachada | 1:100, 1:50 |
| Plantas de recintos / interiores | Equipamiento, mobiliario | 1:50, 1:20 |
| Detalles | Uniones, encuentros, componentes | 1:10, 1:5, 1:2 |

Escalas por tipo: [First In Architecture: https://www.firstinarchitecture.co.uk/understanding-scales-and-scale-drawings/]

- ISO 7519:2025 define una jerarquía de planos: planos de sitio, planos de disposición del sitio, planos de disposición general, de montaje, de componentes y de detalle. Exige indicar la escala de cada vista y, en planos de sitio, el norte (de preferencia vertical) y la posición del edificio o del deslinde. No fija escalas numéricas. [ISO 7519:2025, muestra: https://cdn.standards.iteh.ai/samples/89718/3807035b2f954bc98668456e679dc0ce/ISO-7519-2025.pdf]
- En Chile, NCh 1471.Of1993 (= ISO 5455) fija las escalas normalizadas: 1:2, 1:5, 1:10, 1:20, 1:50, 1:100, 1:200, 1:500, 1:1000, 1:2000, 1:5000, 1:10000. [Academia.edu, resumen NCh 1471: https://www.academia.edu/39735316/]

### Lo que pide la OGUC (permiso de edificación)

- Art. 5.1.6: plantas, cortes y elevaciones a escala 1:50; si la planta mide más de 50 m de largo, puede ser 1:100. [Incove: https://www.incove.cl/post/permiso-de-edificaci%C3%B3n-obra-nueva-ampliaci%C3%B3n-mayor-a-100-m2] [Municipalidad de Calbuco: http://transparencia.municipalidadcalbuco.cl/procedimiento_solicitud_edificacion.pdf]
- Contenido: ubicación del predio; emplazamiento con silueta, cotas y distancias a deslindes; plantas de todos los pisos acotadas; cortes y elevaciones con niveles de pisos, línea de suelo natural y rasantes; planta de cubiertas; plano de cierros cuando corresponda. Cotas suficientes para calcular superficies, niveles, distanciamientos y alturas. [Calbuco, misma URL]
- Obra menor (art. 5.1.4 según Modulor): croquis de ubicación y plano de la obra a escala 1:100. [Modulor: https://modulor.cl/oguc/titulo-5/capitulo-1/disposiciones-generales-y-permisos-de-edificacion/]
- **[NO VERIFICADO]** La numeración exacta de los numerales (5.1.4 vs 5.1.6) difiere entre fuentes secundarias; conviene revisar el texto vigente de la OGUC en el sitio MINVU antes de citarlo en clase. El documento de Calbuco contiene una errata ("1:1000").

---

## 3. Líneas y achurados

### Grosores (ISO 128-23, hoy absorbida por ISO 128-2:2020)

- Tres anchos en razón 1:2:4. Ejemplo: 0,25 / 0,5 / 1,0 mm. [ISO 128-23, muestra: https://cdn.standards.iteh.ai/samples/22292/a9f6396b7eb94397aa5e41513ebf09b1/ISO-128-23-1999.pdf]
- ISO 128-23:1999 fue retirada en 2020 y reemplazada por ISO 128-2:2020. [ISO: https://www.iso.org/standard/22292.html]

| Tipo de línea | Uso en planos de construcción |
|---|---|
| Continua fina (01.1) | Cotas, líneas auxiliares, achurado, límites entre materiales |
| Continua gruesa (01.2) | Contorno de lo cortado cuando hay achurado; representación simplificada de puertas, ventanas y escaleras |
| Continua extragruesa (01.3) | Contorno de lo cortado cuando no hay achurado (muro "relleno") |
| Segmentada | Contornos ocultos (vigas sobre el plano de corte, etc.) |
| Trazo largo y punto | Planos de corte, ejes, simetría, líneas de referencia |

Fuente de la tabla: [ISO 128-23, muestra, misma URL]

### Achurados de materiales

- NCh 745.EOf1971: "Arquitectura y construcción. Designación y representación gráfica de materiales y elementos". [Listado NCh construcción: https://sf2217758f40e4116.jimcontent.com/download/version/1717367740/module/12526658631/name/NORMAS_CHILENAS_DE_CONSTRUCCI%C3%93N.pdf]
- NCh 2361.Of1996 (= ISO 4069): representación de áreas en secciones y vistas. [mismo listado] ISO 4069 fue retirada en 2004. [ISO: https://www.iso.org/standard/9784.html]
- **[NO VERIFICADO]** Patrones concretos de NCh 745 (hormigón, albañilería, madera, tierra). No se pudo acceder al texto. En clase conviene usar la regla general: el material cortado se achura o se rellena; el material visto no.

---

## 4. Simbología de planta

| Elemento | Cómo se dibuja | Fuente |
|---|---|---|
| Muro cortado | Dos líneas gruesas, relleno o achurado | ISO 128-23 |
| Puerta | Hoja como línea más arco de giro (cuarto de círculo) | RoomSketcher |
| Ventana | Rectángulo delgado en el muro con líneas finas | RoomSketcher |
| Escalera | Líneas paralelas (peldaños), flecha "SUBE"/"BAJA" desde el piso dibujado, línea de quiebre diagonal donde la corta el plano | Engineer Fix, RoomSketcher |
| Ejes estructurales | Trazo y punto; círculos en los extremos; letras en una dirección y números en la otra; cota entre ejes a centro | Studio Matrx |
| Nivel | NPT (nivel de piso terminado) con cota en metros; ±0,00 en acceso, + arriba, − abajo | Fenarq |
| Norte | Flecha, de preferencia hacia arriba de la lámina | ISO 7519:2025 |
| Línea de corte | Trazo y punto con extremos gruesos, flechas y letra (A-A) | ISO 128-23 |
| Cotas | En cadena, en metros con dos decimales; extremos con trazo oblicuo (convención arquitectónica) | [NO VERIFICADO: trazo oblicuo como norma; es práctica común] |

URLs: [RoomSketcher: https://www.roomsketcher.com/blog/floor-plan-symbols/] [Engineer Fix: https://engineerfix.com/how-to-properly-show-stairs-on-a-floor-plan/] [Studio Matrx: https://www.studiomatrx.org/guides/understanding-column-layout-drawings] [Fenarq: https://www.fenarq.com/arquitectura//2025/10/que-significa-npt-en-arquitectura.html]

- **[NO VERIFICADO]** Omitir las letras I y O en ejes (para no confundir con 1 y 0) es práctica frecuente, sin fuente normativa confirmada.

### Normas ISO y NCh relevantes

| Norma | Tema | Estado / nota |
|---|---|---|
| ISO 128-2:2020 | Líneas (incluye lo que era ISO 128-23) | Vigente |
| ISO 4157-1/-2/-3:1998 | Designación de edificios, partes, recintos (nombres, números, identificadores) | Ver ISO |
| ISO 7519:2025 | Principios de presentación de planos de disposición general y de montaje en construcción | Reemplaza a ISO 7519:1991 (retirada 2024) |
| NCh 2416.Of1997 | Equivalente chilena de ISO 7519 (versión 1991) | |
| NCh 2363.Of1996 | = ISO 8048: vistas, secciones y cortes en construcción | |
| NCh 2361.Of1996 | = ISO 4069: representación de áreas en secciones | |
| NCh 2362.Of1996 | = ISO 4068: líneas de referencia | |
| NCh 2223.Of1993 | = ISO 9431: zonas de dibujo, texto y rótulo en construcción | |
| NCh 745, 656, 657 | Designación gráfica, materiales, formatos y escalas en arquitectura | Antiguas (1970-71) |
| NCh 684.Of1978 | Coordinación modular: representación gráfica | |
| NCh 711 / NCh 712 | Símbolos sanitarios / eléctricos | |

Fuentes: [ISO 4157-1: https://www.iso.org/standard/26189.html] [ISO 4157-3: https://www.iso.org/standard/26950.html] [ISO 7519:2024: https://www.iso.org/standard/83163.html] [ISO 7519:1991: https://www.iso.org/standard/14288.html] [Listado NCh construcción, URL arriba]

- **[NO VERIFICADO]** Si las NCh 2416, 2361, 2363 siguen vigentes o fueron retiradas por el INN. El listado consultado es de 2004.

---

## 5. Espacios industriales y bodegas

### El plano de layout

- Es una planta (normalmente 1:100 a 1:500) donde el foco no es la construcción sino la **ubicación de equipos, racks, pasillos y flujos**.
- Método clásico: SLP de Muther (Systematic Layout Planning). Pasos: tabla de relaciones, requerimientos de espacio, diagrama de relaciones, layouts alternativos, evaluación, detalle del layout elegido. [Richard Muther Associates: https://richardmuther.com/wp-content/uploads/2014/06/RMA-1146-SLP-Overview-Mfg.pdf]
- Tabla de relaciones con letras A, E, I, O, U, X (de "absolutamente necesario" a "no deseable"). [misma URL]

### Racks, pasillos y andenes

| Elemento | Dato de diseño | Fuente |
|---|---|---|
| Pasillo, grúa contrapesada | ≥ 12 ft (~3,7 m) | Cisco-Eagle |
| Pasillo, reach truck | 8 a 11 ft (~2,4 a 3,4 m) | Cisco-Eagle |
| Pasillo muy angosto (VNA, turret) | < 5,5 ft (~1,7 m) | Cisco-Eagle |
| Altura de andén | 46 a 52 in (~1,17 a 1,32 m) | Nova Technology |
| Ancho de bahía de andén | ≥ 12 ft (3,7 m); 14 ft recomendado (4,3 m) | Nova Technology |
| Puerta de andén | 8 a 10 ft de ancho y alto (2,4 a 3,0 m) | Nova / Loading Dock Systems |
| Pasillo tras andenes | ≥ 15 ft (4,6 m) | Nova Technology |
| Espacio entre máquinas (Chile) | ≥ 150 cm por donde circulen personas | DS 594, art. 8 |

URLs: [Cisco-Eagle: https://www.cisco-eagle.com/blog/2013/05/31/key-considerations-for-warehouse-aisle-widths/] [Nova Technology: https://www.novalocks.com/design-the-loading-dock/] [Loading Dock Systems: https://www.loadingdock.com/blog/design-the-loading-dock-determine-door-sizes] [DS 594: https://www.dt.gob.cl/portal/1626/articles-119819_Fiscalizador_02.pdf]

- Los anchos de pasillo dependen del equipo. Siempre se verifica con la ficha del fabricante. [Cisco-Eagle]
- Representación de racks en planta: rectángulo por fila (profundidad de rack), subdividido por módulos o bahías; filas dobles espalda con espalda; pasillo acotado entre caras de rack. En corte o elevación: niveles de vigas y pallets. [NO VERIFICADO como norma; es práctica de layout]

### Flujos

- **Diagrama de recorrido (spaghetti)**: trayectoria del producto a lo largo del flujo de valor, dibujada sobre la planta. [Lean Enterprise Institute: https://www.lean.org/lexicon-terms/spaghetti-chart/]
- **Cursograma analítico (ASME)**: círculo = operación; flecha = transporte; cuadrado = inspección; triángulo = almacenamiento/espera. [processchart.com: http://www.processchart.com/method/symbols.htm] Nota: el estándar ASME clásico usa "D" para demora y triángulo para almacenamiento. [NO VERIFICADO en texto original ASME]
- Diagramas de proceso de planta química: ISO 10628-1:2014 y 10628-2:2012 (la versión 1997 fue retirada). Solo mención. [ISO: https://www.iso.org/standard/18721.html]

### Seguridad

- DS 594 art. 8: pasillos suficientemente amplios para movimiento seguro de personas y material. Art. 37: vías de evacuación con salidas en número, capacidad y ubicación adecuadas; puertas que no abran contra el sentido de evacuación. [DS 594, URL arriba]
- ISO 23601:2020: principios de diseño de planos de evacuación exhibidos en lugares de trabajo. [ISO: https://www.iso.org/standard/80678.html] Señales: ISO 7010.

### Software

- AutoCAD: capas por tipo de elemento. Formato AIA/NCS: disciplina-grupo mayor-grupo menor-estado, por ejemplo A-WALL, A-DOOR, A-GLAZ, A-ANNO-DIMS. [NCS: https://www.nationalcadstandard.org/ncs5/pdfs/ncs5_clg_lnf.pdf] Alternativa internacional: ISO 13567. [MorphoCAD: https://morphocad.com/blog/autocad-layer-naming-conventions]
- Revit / BIM: el modelo 3D genera plantas, cortes y elevaciones; el plano de corte de planta se ajusta con View Range. [BIM Pure, URL arriba]

---

## 6. Propuesta didáctica (2 clases de 80 min)

### Clase 1: de la pieza al edificio
1. (15 min) Puente: planta = corte horizontal; corte A-A = corte vertical; fachada = vista. Tabla de equivalencias.
2. (20 min) Líneas y símbolos: muro cortado, puerta con arco, ventana, escalera, ejes, NPT, norte, cotas en cadena.
3. (45 min) Terreno: por grupos de 3, levantar una sala o bodega del campus con huincha. Croquis a mano alzada acotado (planta y una altura).

### Clase 2: dibujo a escala y layout
1. (40 min) Pasar el croquis a planta 1:50 (o 1:100) en formato A3 con rótulo, ejes y cotas. Un corte A-A.
2. (30 min) Proponer un layout de racks o estaciones: pasillos acotados, flujo con flechas (spaghetti antes/después), vía de evacuación.
3. (10 min) Coevaluación rápida con la pauta.

### Pauta de corrección (sugerida)

| Criterio | Peso |
|---|---|
| Escala correcta y declarada; formato y rótulo | 10 % |
| Jerarquía de líneas (cortado grueso, visto fino, ejes trazo y punto) | 20 % |
| Simbología (puertas con arco, ventanas, NPT, norte, línea de corte) | 15 % |
| Cotas en cadena y totales; coherencia planta-corte | 20 % |
| Corte A-A con niveles | 10 % |
| Layout: pasillos acotados y justificados, flujo, evacuación | 20 % |
| Limpieza y legibilidad | 5 % |

---

## Puntos [NO VERIFICADO] (resumen)

1. Numeración exacta de artículos OGUC (5.1.4 / 5.1.6) y su texto vigente.
2. Patrones de achurado de NCh 745.
3. Vigencia actual de NCh 2416, 2361, 2363 y otras de 1993-1997.
4. Extremos de cota con trazo oblicuo como norma (es práctica común).
5. Omisión de letras I y O en ejes.
6. Representación de racks en planta como norma (es práctica, no norma).
7. Símbolo "D" de demora en ASME original.
