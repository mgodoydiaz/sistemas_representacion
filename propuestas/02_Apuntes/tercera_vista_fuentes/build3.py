import sys
sys.path.insert(0, "/mnt/skills/plugins/plantilla-miguel/scripts")
from plantilla import Doc
d = Doc()
d.title("La tercera vista", "Apunte breve · PCI 1119 Sistemas de Representación · 2026-2")
d.headers(lhead="Sistemas de Representación · PCI 1119", rhead="La tercera vista",
          lfoot="Ingeniería Civil Industrial · UCT", cfoot="Prof. Miguel Godoy Díaz")
d.h1("El problema")
d.body("Se entregan dos vistas de una pieza, por ejemplo alzado y planta, y se pide dibujar la que falta. "
       "Es el ejercicio clásico de lectura de planos: obliga a imaginar la pieza en tres dimensiones a partir de dos dibujos planos.")
d.destacado(1, "Tercera vista: vista que se deduce de otras dos ya dibujadas, usando la correspondencia entre vistas.")
d.h1("Qué comparte cada par de vistas")
d.body("Cada vista muestra dos de las tres dimensiones de la pieza. Por eso dos vistas vecinas siempre comparten una.")
d.table(["Par de vistas", "Dimensión compartida", "Cómo se traslada"], [
    ["Alzado y planta", "Ancho", "Líneas verticales: una está bajo la otra"],
    ["Alzado y lateral", "Altura", "Líneas horizontales: una está al lado de la otra"],
    ["Planta y lateral", "Fondo (profundidad)", "No están alineadas: se usa una recta a 45° o el compás"],
])
d.image("t3_01_correspondencia.png", width_in=2.9, caption="Figura 1. Correspondencia entre vistas en primer diedro (ISO-E).")
d.body("En primer diedro la lateral izquierda va a la derecha del alzado: lo de atrás queda junto al alzado y el frente hacia afuera.")
d.h1("Procedimiento")
d.table(["Paso", "Qué se hace"], [
    ["1", "Ubique el lugar de la vista que falta y trace una recta auxiliar a 45° desde la esquina entre la planta y la lateral"],
    ["2", "Lleve cada altura del alzado con líneas horizontales finas"],
    ["3", "Lleve cada fondo de la planta con horizontales hasta la recta a 45° y desde ahí suba con verticales"],
    ["4", "Los cruces son los vértices posibles. Una los que correspondan y decida qué aristas son visibles y cuáles ocultas"],
])
d.image("t3_02_pasos.png", width_in=3.7, caption="Figura 2. Obtención de la lateral izquierda a partir de alzado y planta.")
d.destacado(2, "No todos los cruces son vértices. En el paso 4 hay que mirar la pieza: cada línea de una vista es una arista, una cara vista de canto o el contorno de una superficie curva.")
d.h1("Cómo decidir en el paso 4")
for t in [
    "•  Una superficie que se ve como área en una vista se ve como línea en al menos una de las otras dos.",
    "•  Recorra el alzado punto por punto: cada vértice tiene su altura en el alzado y su fondo en la planta.",
    "•  Una arista tapada por material, mirando desde el lado de la vista, se dibuja con línea de trazos.",
]:
    d.body(t)
d.h1("Dos vistas no siempre bastan")
d.body("Hay piezas distintas que comparten dos vistas. En ese caso el ejercicio tiene más de una respuesta correcta, y en un plano real la tercera vista es obligatoria.")
d.image("t3_03_ambiguedad.png", width_in=4.2, caption="Figura 3. Un mismo alzado y una misma planta admiten varias laterales.")
d.h1("Errores frecuentes")
d.table(["Error", "Cómo se ve", "Cómo evitarlo"], [
    ["Fondo medido al revés", "La lateral queda en espejo: el frente junto al alzado", "Usar siempre la recta a 45°, no copiar medidas a ojo"],
    ["Vista mal ubicada", "La lateral izquierda a la izquierda del alzado", "En ISO-E, lo que se ve desde la izquierda se dibuja a la derecha"],
    ["Unir todos los cruces", "Aparecen aristas que la pieza no tiene", "Revisar cada línea contra el alzado y la planta"],
    ["Olvidar las ocultas", "Faltan agujeros o rebajes interiores", "Preguntarse qué queda tapado desde ese lado"],
    ["Líneas auxiliares gruesas", "No se distingue la pieza de la construcción", "Auxiliares finas y suaves, contorno grueso al final"],
])
d.destacado(3, "Regla de oro: ancho bajo el alzado, altura al lado del alzado, fondo por la recta a 45°.")
d.h1("Taller")
d.body("1. Repita la Figura 2 en su croquera y dibuje además la lateral derecha de la misma pieza. Si duda, haga antes un croquis isométrico.")
d.body("2. Para el alzado y la planta de la Figura 3, dibuje una cuarta lateral posible, distinta de A, B y C.")
d.body("3. Elija dos ejercicios de nivel medio de educacionplastica.net/vistas.html, tape una vista y dedúzcala de las otras dos.")
d.save("Apunte_La_Tercera_Vista.docx", pdf=True)
