import sys
sys.path.insert(0, "/mnt/skills/plugins/plantilla-miguel/scripts")
from plantilla import Doc
def nuevo(t):
    d = Doc(); d.title(t, "x"); d.headers(lhead="x", rhead="x", lfoot="x", cfoot="x"); return d
def bl(d, items):
    for i in items: d.body("•  " + i)
F = "figuras/"

# ============================================================ AutoCAD base
d = nuevo("AutoCAD base")
d.h1("Para qué sirve este apunte")
d.body("Hasta ahora usted dibujó a mano. En AutoCAD las reglas del dibujo técnico son las mismas: tipos de línea, grosores, cotas y cajetín. Cambia la herramienta. Este apunte deja el archivo preparado y enseña los comandos mínimos para dibujar y acotar una pieza plana.")
d.destacado(1, "En AutoCAD se dibuja siempre a escala 1:1 y en milímetros. La escala se decide al imprimir, no al dibujar.")
d.body("Los comandos se escriben en inglés. En AutoCAD en español funcionan con un guion bajo delante, por ejemplo _LINE. Entre paréntesis va el atajo de teclado.")
d.h1("Preparar el archivo")
d.table(["Paso", "Comando", "Qué se hace"], [
    ["1", "NEW", "Parta de la plantilla métrica acadiso.dwt"],
    ["2", "UNITS", "Tipo Decimal, precisión 0.0, unidad de inserción Milímetros"],
    ["3", "LAYER (LA)", "Cree las capas de la tabla siguiente"],
    ["4", "SAVEAS", "Guarde como .dwg. Para reutilizar las capas, guarde además como plantilla .dwt"],
])
d.h1("Capas: un tipo de línea por capa")
d.body("Una capa agrupa objetos que comparten tipo de línea, grosor y color. Es la forma de cumplir ISO 128 sin configurar cada línea por separado.")
d.image(F + "m2_base_01_capas.png", width_in=5.4, caption="Figura 1. Capas mínimas del curso.")
bl(d, [
    "Los tipos HIDDEN y CENTER se cargan con el botón Load dentro de LAYER, en la columna Linetype.",
    "Si los trazos se ven continuos, ajuste la escala de tipo de línea con LTSCALE (pruebe 0.5 o 1).",
    "Para ver los grosores en pantalla active el botón Lineweight de la barra de estado.",
    "Color, tipo de línea y grosor de cada objeto deben quedar en ByLayer.",
    "Agregue una capa Auxiliar para líneas de construcción y una capa Cajetín.",
])
d.destacado(2, "Antes de dibujar, mire qué capa está activa. Cambiar un objeto de capa: selecciónelo y elija la capa en la lista desplegable.")
d.h1("Ayudas de precisión")
d.table(["Ayuda", "Tecla", "Para qué sirve"], [
    ["Object Snap (referencia a objetos)", "F3", "Engancha a puntos exactos: Endpoint, Midpoint, Center, Quadrant, Intersection"],
    ["Ortho", "F8", "Obliga a dibujar horizontal o vertical"],
    ["Polar Tracking", "F10", "Guía en ángulos fijos, por ejemplo cada 45°"],
    ["Dynamic Input", "F12", "Muestra distancia y ángulo junto al cursor"],
])
d.destacado(1, "Nunca dibuje a ojo. Cada punto se indica con una medida escrita o con una referencia a objeto.")
d.h1("Indicar puntos y medidas")
d.image(F + "m2_base_04_coordenadas.png", width_in=3.6, caption="Figura 2. Tres formas de indicar un punto.")
d.table(["Forma", "Se escribe", "Significa"], [
    ["Absoluta", "20,10", "X = 20, Y = 10 desde el origen"],
    ["Relativa", "@50,0", "50 a la derecha del último punto"],
    ["Polar", "@40<60", "40 de largo a 60° desde el último punto"],
    ["Distancia directa", "50 y Enter", "Con Ortho activo: mueva el cursor en la dirección y escriba el largo"],
])
d.body("El separador decimal es el punto y la coma separa X de Y: 12.5,30.")
d.h1("Comandos para dibujar y modificar")
d.table(["Comando", "Atajo", "Uso"], [
    ["LINE", "L", "Segmentos rectos"],
    ["RECTANG", "REC", "Rectángulo por dos esquinas. Segunda esquina: @100,60"],
    ["CIRCLE", "C", "Centro y radio. Opción D para escribir el diámetro"],
    ["OFFSET", "O", "Copia paralela a una distancia"],
    ["TRIM / EXTEND", "TR / EX", "Recorta o alarga hasta otro objeto"],
    ["FILLET", "F", "Redondea una esquina. Opción R para el radio"],
    ["CHAMFER", "CHA", "Chaflán. Opción D para las distancias"],
    ["COPY / MOVE", "CO / M", "Copia o mueve con punto base y punto de destino"],
    ["MIRROR", "MI", "Copia simétrica respecto de un eje"],
    ["ERASE", "E", "Borra. También la tecla Supr"],
    ["ZOOM", "Z, luego E", "Extents: muestra todo el dibujo"],
])
d.h1("Ejemplo resuelto: placa base")
d.body("Placa de 100 × 60 con esquinas R10, agujero central Ø30 y cuatro agujeros Ø10 a 80 × 40 entre centros.")
d.image(F + "m2_base_02_pasos.png", width_in=5.2, caption="Figura 3. Construcción de la placa en cuatro pasos.")
d.table(["Paso", "Capa", "Qué se hace"], [
    ["1", "Visible", "RECTANG, primera esquina 0,0 y segunda @100,60"],
    ["2", "Visible", "FILLET, opción R = 10, y clic en los dos lados de cada esquina"],
    ["3", "Ejes", "LINE por los puntos medios (Midpoint) y ejes cortos en los centros 10,10 · 90,10 · 90,50 · 10,50. Sobresalen unos 3 mm del contorno"],
    ["4", "Visible", "CIRCLE Ø30 en la intersección de los ejes. CIRCLE Ø10 en 10,10 y luego MIRROR dos veces, usando los ejes como línea de simetría"],
])
d.h1("Acotar")
d.body("Las cotas van en la capa Cotas. El estilo se configura una vez con DIMSTYLE (D): parta del estilo ISO-25, con altura de texto 3.5 y flechas de 3.")
d.image(F + "m2_base_03_placa_acotada.png", width_in=4.2, caption="Figura 4. Placa acotada: tamaño, posición de agujeros, diámetros y radio.")
d.table(["Comando", "Atajo", "Cota"], [
    ["DIMLINEAR", "DLI", "Horizontal o vertical entre dos puntos"],
    ["DIMALIGNED", "DAL", "Paralela a una arista inclinada"],
    ["DIMDIAMETER", "DDI", "Diámetro de un círculo, con el símbolo Ø"],
    ["DIMRADIUS", "DRA", "Radio de un arco, con la letra R"],
    ["DIMANGULAR", "DAN", "Ángulo entre dos líneas"],
])
bl(d, [
    "Para anotar 4 × Ø10 haga doble clic sobre el texto de la cota y escriba 4 × delante del valor.",
    "No escriba las medidas a mano: la cota debe leer la medida real del dibujo. Si sale un número raro, el dibujo está mal.",
    "Aplique lo ya visto: sin sobreacotar, cotas fuera de la pieza, las menores más cerca del contorno.",
])
d.h1("Errores frecuentes")
d.table(["Error", "Cómo se ve", "Cómo evitarlo"], [
    ["Todo en la capa 0", "Un solo grosor y sin trazos", "Elegir la capa antes de dibujar"],
    ["Dibujar a escala", "Las cotas marcan la mitad o el doble", "Dibujar 1:1. La escala va en la presentación"],
    ["Puntos a ojo", "Líneas que no cierran al hacer zoom", "Object Snap activo y medidas escritas"],
    ["Coma decimal", "12,5 se interpreta como X = 12, Y = 5", "Decimal con punto: 12.5"],
    ["Cotas editadas a mano", "El número no coincide con el dibujo", "Corregir la geometría, no el texto"],
    ["Líneas duplicadas", "Trazos más gruesos al imprimir", "OVERKILL elimina duplicados"],
])
d.destacado(3, "Regla de oro: capa correcta, medida escrita, referencia a objeto. En ese orden, siempre.")
d.h1("Taller de la clase")
d.body("1. Cree su plantilla PCI1119.dwt con las capas de la Figura 1 y el estilo de cota.")
d.body("2. Dibuje y acote la placa base de la Figura 4.")
d.body("3. Entregue el archivo DWG. La impresión a PDF se ve en el apunte de vistas y cortes en AutoCAD.")
d.save("fuente_AutoCAD_base.docx", pdf=False)

# ============================================================ Vistas y cortes
d = nuevo("Vistas y cortes en AutoCAD")
d.h1("Para qué sirve este apunte")
d.body("Usted ya sabe dibujar vistas y cortes a mano y conoce los comandos básicos de AutoCAD. Este apunte une ambas cosas: cómo mantener la correspondencia entre vistas, cómo rayar un corte y cómo sacar la lámina con cajetín a PDF.")
d.body("Pieza guía: el buje con brida del apunte de cortes (brida Ø80 × 15, cubo Ø40 hasta 50 de alto, agujero central Ø20 y cuatro agujeros Ø10 sobre Ø60).")
d.h1("Vistas alineadas: líneas de proyección")
d.body("A mano, la correspondencia se logra con la regla T y la escuadra. En AutoCAD se logra con líneas de construcción infinitas.")
d.image(F + "m2_vc_01_proyeccion.png", width_in=3.6, caption="Figura 1. La planta se dibuja primero. Las XLINE verticales llevan cada ancho al alzado.")
d.table(["Paso", "Comando", "Qué se hace"], [
    ["1", "CIRCLE", "Dibuje la vista que tiene los círculos (aquí, la planta) con sus ejes"],
    ["2", "XLINE (XL), opción V", "En la capa Auxiliar, una vertical por cada cuadrante y cada centro de la planta"],
    ["3", "LINE y OFFSET", "Línea de base del alzado y las alturas 15 y 50 con OFFSET"],
    ["4", "TRIM", "Recorte y pase los tramos definitivos a las capas Visible, Oculta y Ejes"],
    ["5", "LAYER", "Apague la capa Auxiliar. No la borre: sirve para corregir"],
])
bl(d, [
    "Para la vista lateral use XLINE horizontal desde el alzado. El fondo se lleva desde la planta con una XLINE a 45°, igual que en el apunte de la tercera vista.",
    "Disposición en primer diedro (ISO-E): planta bajo el alzado, lateral izquierda a la derecha.",
    "Deje al menos 20 mm entre vistas para las cotas.",
])
d.h1("Del alzado con ocultas al alzado en corte")
d.image(F + "m2_vc_02_corte.png", width_in=4.2, caption="Figura 2. Corte total A-A del buje con brida.")
d.table(["Paso", "Comando", "Qué se hace"], [
    ["1", "COPY", "Copie el alzado con ocultas hacia un lado, para conservar el original mientras trabaja"],
    ["2", "Lista de capas", "Las ocultas que el plano corta pasan a la capa Visible: ahora son contornos"],
    ["3", "ERASE", "Borre las ocultas que quedan. Una vista cortada no lleva ocultas"],
    ["4", "HATCH (H)", "Capa Rayado, patrón ANSI31, clic dentro de cada zona de material cortado"],
    ["5", "PLINE y TEXT", "En la planta: traza del plano, flechas y letras. Sobre el alzado: rótulo A-A"],
])
d.h2("Rayado con HATCH")
bl(d, [
    "ANSI31 ya viene inclinado a 45°. El ángulo se deja en 0.",
    "La zona debe estar cerrada. Si HATCH no la reconoce, hay una esquina abierta: haga zoom y revise con Endpoint.",
    "Los agujeros no se rayan: haga clic solo dentro del material.",
    "La misma pieza lleva el mismo rayado en todas sus zonas. Dos piezas en contacto: una a 0 y la otra con ángulo 90.",
    "Nervios y ejes cortados a lo largo no se rayan, igual que a mano.",
])
d.image(F + "m2_vc_03_rayado_escala.png", width_in=4.6, caption="Figura 3. Efecto de la escala del patrón (Hatch Pattern Scale).")
d.body("Ajuste la escala del patrón hasta que las líneas queden a 2 o 3 mm entre sí en el papel. Para una lámina a 1:1 pruebe con escala 1; si la lámina va a 1:2, use 2.")
d.h2("Indicación del plano de corte")
bl(d, [
    "Traza: línea en la capa Ejes sobre el eje de la planta, que sobresalga unos 10 mm de la pieza.",
    "Extremos gruesos: PLINE (PL), opción Width, ancho 1, de unos 8 mm de largo.",
    "Flechas: PLINE con ancho inicial 3 y final 0, de unos 10 mm, apuntando hacia donde se mira.",
    "Letras y rótulo: TEXT, altura 5, en la capa Cotas.",
])
d.h1("Acotar una vista cortada")
bl(d, [
    "Los diámetros se acotan de preferencia en la vista cortada, con DIMLINEAR, anteponiendo el símbolo Ø al texto (%%c en el editor de cotas).",
    "Si una cota cae sobre el rayado, AutoCAD no lo interrumpe solo: saque la cota fuera de la pieza.",
    "Los cuatro agujeros se acotan en la planta: 4 × Ø10 y el diámetro Ø60 de la circunferencia de centros.",
])
d.h1("La lámina: presentación, ventana y cajetín")
d.destacado(1, "La pieza vive en el modelo a 1:1. El cajetín vive en la presentación a 1:1. La escala del dibujo se fija en la ventana.")
d.image(F + "m2_vc_04_presentacion.png", width_in=4.3, caption="Figura 4. Modelo y presentación.")
d.table(["Paso", "Comando", "Qué se hace"], [
    ["1", "Pestaña Layout1", "Pase a la presentación. Borre la ventana que viene por defecto"],
    ["2", "PAGESETUP", "Modify: impresora DWG To PDF.pc3, papel ISO A4 o A3, escala de trazado 1:1, estilo monochrome.ctb"],
    ["3", "RECTANG o INSERT", "Dibuje o inserte el recuadro y el cajetín ISO 7200 en la capa Cajetín"],
    ["4", "MVIEW (MV)", "En una capa Ventanas, marque dos esquinas dentro del recuadro"],
    ["5", "Escala de la ventana", "Seleccione el borde de la ventana y elija una escala normalizada en la barra de estado: 1:1, 1:2, 1:5"],
    ["6", "Bloquear", "Con la ventana seleccionada, en Properties (Ctrl+1) ponga Display locked en Yes"],
    ["7", "PLOT (Ctrl+P)", "Vista previa y generar el PDF"],
])
bl(d, [
    "Para que el borde de la ventana no se imprima, marque la capa Ventanas como no imprimible (icono de impresora en LAYER).",
    "Si la lámina va a 1:2, las cotas se verían a la mitad de su tamaño. Corrija con la escala general del estilo de cota (DIMSCALE = 2).",
    "La escala que se escribe en el cajetín es la de la ventana.",
])
d.h1("Errores frecuentes")
d.table(["Error", "Cómo se ve", "Cómo evitarlo"], [
    ["Vistas desalineadas", "El alzado no calza con la planta", "Construir siempre con XLINE"],
    ["Ocultas dentro del corte", "Trazos sobre el rayado", "Borrar las ocultas de la vista cortada"],
    ["Rayado en los agujeros", "El hueco aparece como material", "Clic solo en zonas de material"],
    ["Rayado a escala equivocada", "Mancha negra o casi invisible", "Ajustar la escala del patrón y revisar la vista previa"],
    ["Cajetín escalado", "Letras enormes o diminutas", "Cajetín en la presentación, a escala 1"],
    ["Ventana sin escala normalizada", "Escala 1:1.37 o similar", "Elegir la escala de la lista y bloquear la ventana"],
    ["PDF en colores", "Líneas grises o de color", "Estilo de trazado monochrome.ctb"],
])
d.destacado(3, "Regla de oro: construir con líneas de proyección, rayar solo material, escalar solo la ventana.")
d.h1("Taller de la clase")
d.body("1. Dibuje la planta y el alzado en corte total A-A del buje con brida, con sus capas.")
d.body("2. Acote la pieza completa sin sobreacotar.")
d.body("3. Arme la lámina A4 con cajetín, a escala 1:1, y entregue DWG y PDF.")
d.save("fuente_Vistas_y_cortes_en_AutoCAD.docx", pdf=False)
print("ok")
