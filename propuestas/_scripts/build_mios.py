import sys
sys.path.insert(0, "/mnt/skills/plugins/plantilla-miguel/scripts")
from plantilla import Doc

LH = "Sistemas de Representación · PCI 1119"
LF = "Ingeniería Civil Industrial · UCT"
CF = "Prof. Miguel Godoy Díaz"


def bullets(d, items):
    for it in items:
        d.body("•  " + it)


def new(title, sub, rhead):
    d = Doc()
    d.title(title, sub)
    d.headers(lhead=LH, rhead=rhead, lfoot=LF, cfoot=CF)
    return d


# ------------------------------------------------------------------ 1. Qué se evalúa
d = new("Qué se evalúa en el cierre del ramo",
        "Lista de criterios · PCI 1119 · 2026-2 · documento de trabajo del docente", "Criterios de evaluación")
d.body("Esta lista reúne todo lo que se quiere observar en las actividades, el Proyecto 2, la presentación y "
       "el trabajo de investigación. Cada criterio tiene un código que se reutiliza en enunciados y pautas.")
d.h1("Dónde se evalúa cada cosa")
d.table(["Instancia", "Peso", "Medio", "Criterios"], [
    ["Actividad 6 · Cortes", "Actividades (30%)", "A mano, en clase", "C1 a C8"],
    ["Actividad 7 · Isométrico", "Actividades (30%)", "A mano, plantilla isométrica", "I1 a I7"],
    ["Actividad 8 · Vista auxiliar (opcional)", "Actividades (30%)", "A mano, en clase", "X1 a X5"],
    ["Proyecto 2 · Parte A", "40% del proyecto", "AutoCAD", "I1 a I6, A1 a A8"],
    ["Proyecto 2 · Parte B", "60% del proyecto", "AutoCAD", "V1 a V4, C1 a C8, A1 a A8"],
    ["Presentación", "Una actividad más, o bonificación", "Oral, 5 a 10 min", "P1 a P6"],
    ["Trabajo de investigación", "Bonificación o reemplazo de una actividad", "Informe breve", "R1 a R6"],
])
d.h1("Criterios")
d.h2("Vistas y acotado (V)")
d.table(["Código", "Qué se observa"], [
    ["V1", "Elección del alzado y número mínimo de vistas"],
    ["V2", "Disposición en primer diedro (ISO-E) y correspondencia entre vistas"],
    ["V3", "Tipos y grosores de línea según ISO 128: visible, oculta, eje"],
    ["V4", "Acotado completo, sin sobreacotar, con diámetros y radios bien indicados"],
])
d.h2("Cortes y secciones (C)")
d.table(["Código", "Qué se observa"], [
    ["C1", "Elección y posición del plano de corte"],
    ["C2", "Indicación del corte: traza, tramos gruesos, flechas en la dirección de observación, letras"],
    ["C3", "Rótulo A-A sobre la vista cortada"],
    ["C4", "Rayado a 45°, fino, uniforme, solo en material cortado y terminado en el contorno"],
    ["C5", "Vista cortada sin aristas ocultas"],
    ["C6", "Elementos que no se rayan a lo largo: nervios, ejes, pernos, chavetas"],
    ["C7", "Semicorte separado por línea de eje, solo en piezas simétricas"],
    ["C8", "Correspondencia con las demás vistas, limpieza y grosores"],
])
d.h2("Vistas auxiliares (X)")
d.table(["Código", "Qué se observa"], [
    ["X1", "Identifica la vista donde la cara inclinada se ve de canto"],
    ["X2", "Línea de referencia paralela a la arista de canto"],
    ["X3", "Proyectantes perpendiculares a la arista de canto"],
    ["X4", "Profundidades trasladadas correctamente: la cara queda en verdadera magnitud"],
    ["X5", "Vista auxiliar parcial, con línea de rotura y rotulado"],
])
d.h2("Isométrico (I)")
d.table(["Código", "Qué se observa"], [
    ["I1", "Ejes a 30° y verticales"],
    ["I2", "Medidas tomadas solo sobre direcciones isométricas"],
    ["I3", "Planos inclinados resueltos uniendo extremos"],
    ["I4", "Círculos como elipses en el isoplano correcto"],
    ["I5", "Arcos y tangencias limpias"],
    ["I6", "Solo aristas visibles"],
    ["I7", "Proporción, limpieza y grosores"],
])
d.h2("AutoCAD (A)")
d.table(["Código", "Qué se observa"], [
    ["A1", "Dibujo a escala 1:1 en el modelo, en milímetros"],
    ["A2", "Capas por tipo de línea, con grosor y tipo de línea asignados por capa"],
    ["A3", "Modo isométrico: isoplano correcto e isocírculos (ELLIPSE, Isocircle)"],
    ["A4", "Trazo limpio: sin líneas duplicadas, cabos sueltos ni cruces sin recortar"],
    ["A5", "Cotas en capa y estilo propios, legibles a la escala de impresión"],
    ["A6", "Rayado con HATCH (ANSI31) a escala adecuada, en su capa"],
    ["A7", "Presentación: cajetín ISO 7200 completo, ventana con escala normalizada"],
    ["A8", "Entrega: DWG que abre sin errores, PDF legible, nombre de archivo según enunciado"],
])
d.h2("Presentación (P)")
d.table(["Código", "Qué se observa"], [
    ["P1", "Respeta el tiempo: 5 a 10 minutos"],
    ["P2", "Estructura: pregunta, desarrollo, cierre con una idea central"],
    ["P3", "Al menos una figura o dibujo de elaboración propia"],
    ["P4", "Dominio del tema: explica sin leer y responde una pregunta"],
    ["P5", "Láminas legibles: poco texto, figuras grandes"],
    ["P6", "Fuentes citadas y uso de IA declarado"],
])
d.h2("Trabajo de investigación (R)")
d.table(["Código", "Qué se observa"], [
    ["R1", "Extensión acotada: 3 a 4 páginas de texto"],
    ["R2", "Cada párrafo tiene una idea principal identificable"],
    ["R3", "Contenido correcto y conectado con el ramo"],
    ["R4", "Figuras propias o citadas con su fuente y licencia"],
    ["R5", "Fuentes verificables: el estudiante las abrió y las leyó"],
    ["R6", "Declaración de uso de IA y punteo previo adjunto"],
])
d.h1("Decisiones pendientes")
bullets(d, [
    "Peso de la presentación: como actividad adicional dentro del 30%, o como bonificación.",
    "Si el trabajo de investigación es obligatorio, opcional con bonificación, o reemplaza la peor actividad.",
    "Si la vista auxiliar tiene actividad propia o queda solo como bonificación del Proyecto 2.",
    "Modalidad del Proyecto 2: individual o en parejas.",
])
d.save("01_Que_se_evalua.docx", pdf=True)

# ------------------------------------------------------------------ 2. Temas + presentación
d = new("Presentación y trabajo de investigación",
        "Enunciado y lista de temas · PCI 1119 Sistemas de Representación · 2026-2", "Presentación e investigación")
d.h1("En qué consiste")
d.body("Usted elegirá un tema de la lista (o propondrá uno) y lo expondrá ante el curso. La presentación es "
       "breve: 5 minutos es una buena duración y 10 minutos es el máximo. Se corta al llegar al límite.")
d.body("El tema se puede desarrollar además como trabajo de investigación escrito o como un dibujo complejo. "
       "Modalidad: individual o en parejas [por confirmar]. Fecha: [por definir].")
d.h1("Especificaciones de la presentación")
d.table(["Aspecto", "Requisito"], [
    ["Duración", "5 a 10 minutos. Más 2 minutos de preguntas"],
    ["Láminas", "Entre 5 y 8. Una idea por lámina"],
    ["Estructura", "1) Pregunta o problema. 2) Desarrollo en 2 o 3 puntos. 3) Un ejemplo dibujado. 4) Cierre con la idea central. 5) Fuentes"],
    ["Texto", "Máximo 30 palabras por lámina. Letra de 24 puntos o más"],
    ["Figuras", "Al menos una figura o dibujo hecho por usted (a mano, en AutoCAD o por código). Las ajenas llevan fuente"],
    ["Exposición", "Sin leer. En parejas, hablan ambos"],
    ["Fuentes", "Mínimo 3, que usted haya abierto y leído. Wikipedia sirve para partir, no como única fuente"],
    ["Uso de IA", "Permitido para buscar y ordenar. Se declara en la última lámina qué herramienta se usó y para qué"],
    ["Entrega", "PDF de la presentación en Blackboard antes de la clase"],
])
d.h2("Cómo se evalúa")
d.table(["Criterio", "Puntos"], [
    ["P1 Respeta el tiempo (5 a 10 min)", "15"],
    ["P2 Estructura clara, con una idea central", "20"],
    ["P3 Figura o dibujo propio, correcto", "20"],
    ["P4 Dominio: explica sin leer, responde una pregunta", "25"],
    ["P5 Láminas legibles", "10"],
    ["P6 Fuentes y declaración de IA", "10"],
])
d.destacado(2, "Una presentación de 5 minutos bien preparada vale más que una de 10 minutos leída.")
d.h1("Temas propuestos")
d.h2("Historia y fundamentos")
bullets(d, [
    "Gaspard Monge y el nacimiento de la geometría descriptiva.",
    "Del tablero al CAD: evolución de los tipos de dibujo técnico, desde los planos en tinta hasta el modelado 3D y BIM.",
    "Reglas básicas de la geometría descriptiva: verdadera magnitud, abatimiento y cambio de plano.",
    "Sistema europeo y sistema americano: por qué existen dos y qué países usan cada uno.",
    "Perspectivas: isométrica, dimétrica, caballera y cónica. Cuándo conviene cada una.",
    "La isometría en los videojuegos y la ilustración.",
])
d.h2("Normas y representación")
bullets(d, [
    "Normas ISO, DIN, ASME y NCh: quién las escribe y cómo se relacionan.",
    "Tolerancias y ajustes: qué significa una cota como Ø20 H7.",
    "Simbología de soldadura o de rugosidad en un plano.",
    "Representación de roscas y elementos normalizados (pernos, tuercas, rodamientos).",
    "Desarrollos de superficies: cómo se fabrica un ducto, un codo o un cono en plancha.",
    "Planos de arquitectura: planta, elevación y corte de una vivienda.",
    "Diagramas de proceso e instrumentación (P&ID): cómo se dibuja una planta industrial.",
])
d.h2("Piezas y conjuntos")
bullets(d, [
    "Cómo funciona y cómo se dibuja una válvula: de globo, de compuerta, de bola o de retención.",
    "Plano de conjunto y despiece: lista de partes y globos.",
    "Ingeniería inversa: medir una pieza real con pie de metro y levantar su plano.",
    "Una pieza complicada: intersección de cilindros, engranajes o una hélice.",
    "Del plano a la fabricación: cómo lee un plano un tornero, una cortadora láser o una impresora 3D.",
])
d.h2("Automatización y programación")
bullets(d, [
    "Formatos CAD: DWG, DXF, STEP, STL y PDF. Qué guarda cada uno y cuándo usarlo.",
    "Dibujar con Python: generar un DXF con la biblioteca ezdxf (un cajetín, una brida paramétrica).",
    "El módulo turtle de Python: programar una proyección isométrica a partir de coordenadas 3D.",
    "Dibujo paramétrico: una pieza que se redibuja al cambiar una medida.",
    "Automatización dentro de AutoCAD: scripts, AutoLISP y bloques dinámicos.",
    "Dibujo vectorial frente a imagen de píxeles: por qué un plano no es una foto.",
    "Inteligencia artificial y dibujo técnico: qué puede y qué no puede hacer hoy con un plano.",
])
d.h1("Formato del trabajo de investigación (si corresponde)")
d.table(["Aspecto", "Requisito"], [
    ["Extensión", "3 a 4 páginas de texto, más figuras. No se lee más allá de la página 5"],
    ["Estructura", "Pregunta, desarrollo en 3 o 4 secciones, conclusión de un párrafo, fuentes"],
    ["Párrafos", "Máximo 6 líneas. Cada uno con una idea principal"],
    ["Figuras", "Al menos 2, una de ellas propia"],
    ["Anexo obligatorio", "El punteo inicial de ideas y la declaración de uso de IA"],
])
d.body("La guía \"Uso de IA en el trabajo de investigación\" explica cómo ordenar las ideas y controlar la extensión.")
d.save("05_Presentacion_y_temas_de_investigacion.docx", pdf=True)

# ------------------------------------------------------------------ 3. Guía IA
d = new("Uso de IA en el trabajo de investigación",
        "Guía breve para estudiantes · PCI 1119 Sistemas de Representación · 2026-2", "Guía de uso de IA")
d.h1("La regla")
d.body("En este trabajo usted puede usar herramientas de IA (ChatGPT, Claude, Gemini, Copilot) para buscar "
       "información y ordenar ideas. Lo que se evalúa es que el texto final sea breve, correcto y suyo: que "
       "usted pueda explicar cada párrafo sin leerlo.")
d.destacado(1, "El problema de la IA no es que escriba mal. Es que escribe de más. Su tarea es decidir qué se "
               "dice y cuánto.")
d.h1("Método en cinco pasos")
d.table(["Paso", "Qué hace usted", "Qué hace la IA"], [
    ["1. Punteo propio", "Anota a mano 5 a 8 puntos: qué quiere decir, qué no sabe, qué ejemplo usará", "Nada todavía"],
    ["2. Exploración", "Pregunta, compara respuestas y pide fuentes. Abre las fuentes y las lee", "Explica, sugiere y propone fuentes"],
    ["3. Ideas por párrafo", "Escribe una frase por párrafo: la idea principal de cada uno. Son 8 a 12 frases", "Puede ayudar a ordenarlas"],
    ["4. Redacción con límite", "Redacta, o pide redactar, cada párrafo desde su frase, con tope de palabras", "Redacta dentro del límite"],
    ["5. Recorte y verificación", "Lee en voz alta, borra lo que sobra, comprueba datos y nombres en las fuentes", "Puede revisar ortografía"],
])
d.body("Los pasos 1 y 3 son suyos. Se entregan como anexo y son la evidencia de que el trabajo fue pensado.")
d.h1("Cómo limitar la extensión")
bullets(d, [
    "Fije el presupuesto antes de escribir: 3 a 4 páginas, 10 párrafos como máximo, 90 palabras por párrafo.",
    "Una idea por párrafo. Si un párrafo tiene dos ideas, se divide o se borra una.",
    "Pida longitud exacta: \"en 80 palabras\", no \"resumido\".",
    "Prohíba el relleno: sin introducción general, sin frases de cierre, sin repetir la pregunta.",
    "Después de cada respuesta de la IA, quédese solo con lo que respondería a un compañero que pregunta \"¿y eso qué significa?\".",
    "Prefiera una figura a un párrafo cuando se describe una forma o un procedimiento.",
    "Dos pasadas por la IA suelen bastar. A la tercera el texto se alarga y se vuelve genérico.",
])
d.h1("Instrucciones útiles para copiar")
d.code("Voy a escribir sobre [tema] para un curso de dibujo técnico de primer año.\n"
       "Estos son mis puntos: [pegar punteo].\n"
       "No redactes. Dime qué falta, qué sobra y en qué orden los pondrías.", highlight=False)
d.code("Idea principal del párrafo: [una frase].\n"
       "Escríbelo en 80 palabras como máximo, en español claro,\n"
       "sin introducción ni frase de cierre y sin adjetivos de relleno.", highlight=False)
d.code("Dame 3 fuentes que pueda abrir para verificar esto, con su enlace.\n"
       "Si no estás seguro de que existan, dilo.", highlight=False)
d.code("Este texto tiene 600 palabras. Redúcelo a 300 sin perder\n"
       "ninguna de estas ideas: [pegar las frases del paso 3].", highlight=False)
d.h1("Lo que la IA hace mal")
d.table(["Riesgo", "Cómo se nota", "Qué hacer"], [
    ["Inventa fuentes y números de norma", "El enlace no existe o el libro no aparece en ningún catálogo", "Abrir cada fuente antes de citarla"],
    ["Texto largo y genérico", "Se puede borrar un párrafo y no se pierde nada", "Volver a las frases del paso 3"],
    ["Errores técnicos con tono seguro", "Confunde primer y tercer diedro, o corte con sección", "Contrastar con el apunte del curso"],
    ["Figuras incorrectas", "Dibujos generados con vistas que no corresponden entre sí", "Dibujar las figuras usted mismo"],
])
d.h1("Declaración de uso de IA")
d.body("Al final del trabajo, en tres líneas: qué herramienta usó, para qué (buscar, ordenar, redactar, "
       "corregir) y qué partes escribió usted sin ayuda. Declarar el uso no descuenta puntaje. No declararlo, sí.")
d.h1("Lista de control antes de entregar")
bullets(d, [
    "El texto tiene 4 páginas o menos.",
    "Puedo decir la idea de cada párrafo en una frase.",
    "Abrí y leí todas las fuentes que cito.",
    "Hay al menos una figura hecha por mí.",
    "Adjunté el punteo inicial y la declaración de uso de IA.",
])
d.save("06_Guia_uso_de_IA_en_investigacion.docx", pdf=True)
print("ok")
