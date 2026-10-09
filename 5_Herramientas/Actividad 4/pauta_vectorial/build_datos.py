#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera los 12 JSON de la pauta vectorial (6 vistas + 6 isometricos) a partir
de las coordenadas leidas a mano desde el enunciado y desde la pauta escaneada
del profesor. Este script se corre UNA VEZ para producir los datos; despues
de generados, los JSON se pueden editar directamente a mano (ver LEEME.md).
"""
import json
import math
import os

OUT_DIR = "/home/claude/a4/pauta_vectorial"

# ---------------------------------------------------------------------------
# VISTAS (reticula cuadrada). Calibracion medida sobre enunciado_actividad4.pdf
# pagina 2 (hoja de respuesta en blanco, reticula cuadrada): 17 casillas de
# ancho x 20 casillas de alto por cuadro (ver LEEME.md para el detalle de la
# medicion en pixeles).
# ---------------------------------------------------------------------------
CASILLAS_V = {"tipo": "cuadrada", "casillas_ancho": 17, "casillas_alto": 20}


def seg(a, b, tipo, vista):
    return {"clase": "segmento", "a": list(a), "b": list(b), "tipo": tipo, "vista": vista}


def circ(c, r, tipo, vista):
    return {"clase": "circulo", "centro": list(c), "radio": r, "tipo": tipo, "vista": vista}


def poly(pts, tipo, vista, cerrado=True):
    """Convierte una polilinea en una lista de segmentos individuales."""
    out = []
    n = len(pts)
    rango = n if cerrado else n - 1
    for i in range(rango):
        a = pts[i]
        b = pts[(i + 1) % n]
        out.append(seg(a, b, tipo, vista))
    return out


def build_vistas(n, elementos, dudoso=False, nota=""):
    d = {
        "pagina": "vistas",
        "cuadro": n,
        "reticula": CASILLAS_V,
        "disposicion": "alzado arriba (ancho completo); planta abajo-izquierda; "
                       "perfil abajo-derecha (junto a planta, NO junto al alzado) "
                       "-- disposicion verificada contra pauta_p2_vistas.png",
        "elementos": elementos,
    }
    if dudoso:
        d["dudoso"] = True
    if nota:
        d["nota"] = nota
    return d


# === CUADRO 1 : pieza 1 (escuadra en L) =====================================
e1 = []
# alzado
e1 += poly([(1, 11), (9, 11), (9, 19), (1, 19)], "llena", "alzado")
e1.append(seg((1, 17), (9, 17), "llena", "alzado"))
e1.append(seg((1, 15.5), (9, 15.5), "llena", "alzado"))
e1.append(seg((3, 11), (3, 19), "oculta", "alzado"))
e1.append(seg((7, 11), (7, 19), "oculta", "alzado"))
# planta (debajo del alzado, mismo ancho x1-9)
e1 += poly([(1, 9), (1, 1), (2, 1), (2, 3), (7, 3), (7, 1), (8, 1), (8, 9)], "llena", "planta", cerrado=True)
e1.append(seg((1, 7), (8, 7), "oculta", "planta"))
e1.append(seg((1, 5), (8, 5), "llena", "planta"))
# perfil (a la derecha de la planta)
e1 += poly([(10, 1), (17, 1), (17, 8), (16, 8), (16, 9), (14, 9), (14, 3), (10, 3)], "llena", "perfil")
e1.append(seg((14, 3), (17, 3), "llena", "perfil"))

# === CUADRO 2 : pieza 2 (bloque escalonado) =================================
# NOTA: lectura de menor confianza (transcrita a mano desde un dibujo con
# varios trazos finos superpuestos); topologia y proporciones generales
# verificadas, detalle exacto de escalones queda marcado como dudoso.
e2 = []
e2 += poly([(1, 19), (9, 19), (9, 13), (7, 13), (7, 11), (4, 11), (4, 17), (1, 17)], "llena", "alzado")
e2.append(seg((7, 15), (9, 15), "llena", "alzado"))
e2 += poly([(1, 9), (8, 9), (8, 5), (6, 5), (6, 3), (3, 3), (3, 7), (1, 7)], "llena", "planta")
e2 += poly([(10, 9), (16, 9), (16, 5), (14, 5), (14, 3), (11, 3), (11, 7), (10, 7)], "llena", "perfil")

# === CUADRO 3 : pieza 3 (bloque en L con taladro circular) =================
e3 = []
e3 += poly([(1, 19), (15, 19), (15, 9), (9, 9), (9, 13), (1, 13)], "llena", "alzado")
e3.append(seg((1, 16), (15, 16), "llena", "alzado"))
e3.append(seg((5, 16), (5, 19), "oculta", "alzado"))
e3.append(seg((11, 16), (11, 19), "oculta", "alzado"))
e3.append(seg((8, 13), (8, 19), "eje", "alzado"))
# planta con el circulo (taladro)
e3 += poly([(1, 1), (15, 1), (15, 9), (1, 9)], "llena", "planta")
e3.append(seg((1, 4), (15, 4), "llena", "planta"))
e3.append(circ((8, 5), 3, "llena", "planta"))
e3.append(seg((8, 2), (8, 8), "eje", "planta"))
e3.append(seg((4, 5), (12, 5), "eje", "planta"))
# perfil (con lineas ocultas del taladro)
e3 += poly([(10, 1), (17, 1), (17, 9), (13, 9), (13, 4), (10, 4)], "llena", "perfil")
e3.append(seg((12, 1), (12, 4), "llena", "perfil"))
e3.append(seg((13, 7), (17, 7), "oculta", "perfil"))
e3.append(seg((13, 6), (17, 6), "eje", "perfil"))

# === CUADRO 4 : pieza 4 (bloque con esquina redondeada y 2 resaltes) ========
e4 = []
e4 += poly([(1, 11), (13, 11), (13, 19), (1, 19)], "llena", "alzado")
e4.append(seg((5, 11), (5, 19), "llena", "alzado"))
e4.append(seg((5, 15), (13, 15), "oculta", "alzado"))
# esquina redondeada aproximada como una pequena escalera de peldanos finos
# (asi la dibujo el profesor a mano sobre la reticula cuadrada)
for yy in (13, 14.6, 16.2, 17.8):
    e4.append(seg((1, yy), (5, yy), "llena", "alzado"))
# planta
e4 += poly([(1, 9), (3, 9), (3, 7), (8, 7), (8, 1), (1, 1)], "llena", "planta")
e4.append(seg((1, 3), (8, 3), "oculta", "planta"))
# perfil: arco con dos resaltes cuadrados y una pequena muesca en la base
e4 += poly([
    (10, 1), (10, 6), (11, 7), (11, 8), (12, 8), (12, 7),
    (13, 7), (13, 8), (14, 8), (14, 7), (15, 7), (16, 6),
    (16, 1), (15, 1), (15, 1.5), (14, 1.5), (14, 1),
], "llena", "perfil")

# === CUADRO 5 : pieza 5 (escalera con rampa) ================================
e5 = []
e5 += poly([(1, 11), (9, 11), (9, 19), (1, 19)], "llena", "alzado")
e5.append(seg((2, 19), (2, 17), "llena", "alzado"))
e5.append(seg((1, 17), (4, 17), "llena", "alzado"))
e5.append(seg((4, 17), (4, 14), "llena", "alzado"))
e5.append(seg((1, 14), (6, 14), "llena", "alzado"))
e5 += poly([(1, 1), (9, 1), (9, 9), (1, 9)], "llena", "planta")
e5.append(seg((2, 9), (9, 1), "llena", "planta"))
e5.append(seg((1, 6), (5, 6), "llena", "planta"))
e5.append(seg((1, 3), (7, 3), "llena", "planta"))
e5 += poly([(10, 1), (12, 1), (12, 3), (13, 3), (13, 5), (14, 5), (14, 9), (17, 9), (17, 1)], "llena", "perfil")

# === CUADRO 6 : pieza 6 (cuna triangular) ===================================
e6 = []
e6 += poly([(1, 15), (9, 15), (9, 19)], "llena", "alzado")
e6 += poly([(1, 1), (9, 1), (9, 5)], "llena", "planta")
e6 += poly([(10, 1), (15, 1), (15, 4)], "llena", "perfil")

VISTAS = {
    1: (e1, False, ""),
    2: (e2, True, "Transcripcion de menor confianza: se preservan la disposicion "
                   "y el caracter escalonado de la pieza, pero el detalle fino de "
                   "los escalones en la pauta manuscrita tiene trazos superpuestos "
                   "dificiles de leer con certeza. Revisar a mano contra "
                   "pautas/pauta_p2_vistas.png (cuadro rotulado '2' en la hoja, "
                   "que corresponde a la pieza 2 del enunciado)."),
    3: (e3, False, ""),
    4: (e4, False, "El achaflanado/redondeo de la esquina se aproximo con una "
                    "diagonal simple; en la pauta a mano esta dibujado como una "
                    "pequena escalera de varios peldanos finos."),
    5: (e5, False, ""),
    6: (e6, False, ""),
}

# ---------------------------------------------------------------------------
# ISOMETRICOS (reticula isometrica). Ver LEEME.md para la conversion de
# pasos de reticula (a 30 grados / a 150 grados / verticales) a coordenadas
# cartesianas. Calibracion aproximada medida sobre la hoja en blanco
# (enunciado pagina 4): 14 x 16 unidades utiles por cuadro.
# ---------------------------------------------------------------------------
CASILLAS_I = {"tipo": "isometrica", "casillas_ancho": 14, "casillas_alto": 16,
              "angulos_grados": [30, 90, 150]}

COS30 = math.cos(math.radians(30))
SIN30 = math.sin(math.radians(30))


def P(a, b, c):
    """Convierte pasos de reticula isometrica (a: pasos a +30 grados,
    b: pasos a +150 grados, c: pasos verticales) a coordenadas cartesianas
    en unidades de arista de reticula, con origen arbitrario. Ver LEEME.md."""
    x = (a - b) * COS30
    y = (a + b) * SIN30 + c
    return (round(x, 3), round(y, 3))


def isoseg(p1, p2, tipo, offset=(0, 0)):
    x1, y1 = p1
    x2, y2 = p2
    return seg((x1 + offset[0], y1 + offset[1]), (x2 + offset[0], y2 + offset[1]), tipo, "isometrico")


def build_iso(n, elementos, dudoso=False, nota=""):
    d = {
        "pagina": "isometricos",
        "cuadro": n,
        "reticula": CASILLAS_I,
        "elementos": elementos,
    }
    if dudoso:
        d["dudoso"] = True
    if nota:
        d["nota"] = nota
    return d


NOTA_ISO_GENERAL = (
    "Geometria isometrica reconstruida de forma aproximada a partir de las "
    "vistas dadas en el enunciado (pagina 3) y confirmada solo a grandes "
    "rasgos contra pauta_p3_isometricos.png (proporciones generales y "
    "aristas principales). El detalle fino de intersecciones no fue "
    "verificado vertice a vertice contra el trazo a mano del profesor; "
    "revisar manualmente antes de usar para calificar con exigencia."
)

ISO = {}

# --- Pieza 1: piramide de base cuadrada apoyada de lado (tienda) -----------
off = (5, 3)
o = P(0, 0, 0)
a4 = P(4, 0, 0)
b4 = P(4, 4, 0)
o4 = P(0, 4, 0)
apex = P(2, 2, 3)
el = []
el.append(isoseg(o, a4, "llena", off))
el.append(isoseg(a4, b4, "llena", off))
el.append(isoseg(b4, o4, "llena", off))
el.append(isoseg(o4, o, "oculta", off))
el.append(isoseg(o, apex, "llena", off))
el.append(isoseg(a4, apex, "llena", off))
el.append(isoseg(b4, apex, "llena", off))
el.append(isoseg(o4, apex, "oculta", off))
ISO[1] = build_iso(1, el, dudoso=True, nota=NOTA_ISO_GENERAL)

# --- Pieza 2: prisma en cuna (rampa que baja desde la arista trasera hasta
# la arista frontal inferior) -----------------------------------------------
off = (2, 2)
b000 = P(0, 0, 0)
b400 = P(4, 0, 0)
b440 = P(4, 4, 0)
b040 = P(0, 4, 0)
t004 = P(0, 0, 3)
t044 = P(0, 4, 3)
el = []
el.append(isoseg(b000, b400, "llena", off))
el.append(isoseg(b400, b440, "llena", off))
el.append(isoseg(b440, b040, "llena", off))
el.append(isoseg(b040, b000, "oculta", off))
el.append(isoseg(b000, t004, "llena", off))
el.append(isoseg(b040, t044, "oculta", off))
el.append(isoseg(t004, t044, "llena", off))
el.append(isoseg(t004, b400, "llena", off))
el.append(isoseg(t044, b440, "llena", off))
# diagonal de la cara superior inclinada (arista vista de la rampa)
el.append(isoseg(t004, b440, "llena", off))
ISO[2] = build_iso(2, el, dudoso=True, nota=NOTA_ISO_GENERAL)

# --- Pieza 3: prisma con techo a dos aguas (forma de casa) ------------------
off = (2, 2)
b000 = P(0, 0, 0)
b500 = P(5, 0, 0)
b550 = P(5, 5, 0)
b050 = P(0, 5, 0)
t002 = P(0, 0, 2)
t502 = P(5, 0, 2)
t552 = P(5, 5, 2)
t052 = P(0, 5, 2)
ridge0 = P(2.5, 0, 3.5)
ridge5 = P(2.5, 5, 3.5)
el = []
el.append(isoseg(b000, b500, "llena", off))
el.append(isoseg(b500, b550, "llena", off))
el.append(isoseg(b550, b050, "llena", off))
el.append(isoseg(b050, b000, "oculta", off))
el.append(isoseg(b000, t002, "llena", off))
el.append(isoseg(b500, t502, "llena", off))
el.append(isoseg(b550, t552, "llena", off))
el.append(isoseg(b050, t052, "oculta", off))
el.append(isoseg(t002, ridge0, "llena", off))
el.append(isoseg(t502, ridge0, "llena", off))
el.append(isoseg(t552, ridge5, "llena", off))
el.append(isoseg(t052, ridge5, "oculta", off))
el.append(isoseg(ridge0, ridge5, "oculta", off))
ISO[3] = build_iso(3, el, dudoso=True, nota=NOTA_ISO_GENERAL)

# --- Pieza 4: prisma en cuna (variante de la pieza 2, corte por la arista
# lateral derecha en vez de la trasera) --------------------------------------
off = (2, 2)
b000 = P(0, 0, 0)
b400 = P(4, 0, 0)
b440 = P(4, 4, 0)
b040 = P(0, 4, 0)
t400 = P(4, 0, 3)
t440 = P(4, 4, 3)
el = []
el.append(isoseg(b000, b400, "llena", off))
el.append(isoseg(b400, b440, "llena", off))
el.append(isoseg(b440, b040, "llena", off))
el.append(isoseg(b040, b000, "oculta", off))
el.append(isoseg(b400, t400, "llena", off))
el.append(isoseg(b440, t440, "llena", off))
el.append(isoseg(t400, t440, "llena", off))
el.append(isoseg(t400, b000, "llena", off))
el.append(isoseg(t440, b040, "oculta", off))
ISO[4] = build_iso(4, el, dudoso=True, nota=NOTA_ISO_GENERAL)

# --- Pieza 5: bloque con protuberancia piramidal/tronco central ------------
off = (1, 2)
b000 = P(0, 0, 0)
b600 = P(6, 0, 0)
b630 = P(6, 3, 0)
b030 = P(0, 3, 0)
t002 = P(0, 0, 2)
t602 = P(6, 0, 2)
t632 = P(6, 3, 2)
t032 = P(0, 3, 2)
# tronco/piramide central sobre la cara superior
c1 = P(2, 1, 2)
c2 = P(4, 1, 2)
c3 = P(4, 2, 2)
c4 = P(2, 2, 2)
apex = P(3, 1.5, 4.5)
el = []
el.append(isoseg(b000, b600, "llena", off))
el.append(isoseg(b600, b630, "llena", off))
el.append(isoseg(b630, b030, "llena", off))
el.append(isoseg(b030, b000, "oculta", off))
el.append(isoseg(b000, t002, "llena", off))
el.append(isoseg(b600, t602, "llena", off))
el.append(isoseg(b630, t632, "llena", off))
el.append(isoseg(b030, t032, "oculta", off))
el.append(isoseg(t002, t602, "llena", off))
el.append(isoseg(t602, t632, "llena", off))
el.append(isoseg(t632, t032, "llena", off))
el.append(isoseg(t032, t002, "oculta", off))
el.append(isoseg(c1, apex, "llena", off))
el.append(isoseg(c2, apex, "llena", off))
el.append(isoseg(c3, apex, "llena", off))
el.append(isoseg(c4, apex, "oculta", off))
# pequena muesca rectangular en la base frontal (visible en la pauta)
n1 = P(4.5, 0, 0)
n2 = P(5, 0, 0)
n3 = P(5, 0, 1)
n4 = P(4.5, 0, 1)
el.append(isoseg(n1, n4, "llena", off))
el.append(isoseg(n4, n3, "llena", off))
el.append(isoseg(n3, n2, "llena", off))
ISO[5] = build_iso(5, el, dudoso=True, nota=NOTA_ISO_GENERAL)

# --- Pieza 6: prisma con corte diagonal y division vertical ----------------
off = (2, 2)
b000 = P(0, 0, 0)
b400 = P(4, 0, 0)
b440 = P(4, 4, 0)
b040 = P(0, 4, 0)
t004 = P(0, 0, 4)
t404 = P(4, 0, 4)
t440 = P(4, 4, 4)
t044 = P(0, 4, 4)
mid_top = P(2, 0, 4)
mid_bot = P(2, 0, 0)
el = []
el.append(isoseg(b000, b400, "llena", off))
el.append(isoseg(b400, b440, "llena", off))
el.append(isoseg(b440, b040, "llena", off))
el.append(isoseg(b040, b000, "oculta", off))
el.append(isoseg(b000, t004, "llena", off))
el.append(isoseg(b400, t404, "llena", off))
el.append(isoseg(b440, t440, "llena", off))
el.append(isoseg(b040, t044, "oculta", off))
el.append(isoseg(t004, t404, "llena", off))
el.append(isoseg(mid_top, mid_bot, "llena", off))
el.append(isoseg(mid_bot, t440, "llena", off))
el.append(isoseg(mid_top, t440, "llena", off))
ISO[6] = build_iso(6, el, dudoso=True, nota=NOTA_ISO_GENERAL)

# ---------------------------------------------------------------------------
os.makedirs(OUT_DIR, exist_ok=True)
for n, (elementos, dudoso, nota) in VISTAS.items():
    d = build_vistas(n, elementos, dudoso, nota)
    with open(os.path.join(OUT_DIR, f"pauta_vistas_c{n}.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _reencuadrar_iso(d, margen_frac=0.08):
    """Reescala y centra los elementos de un cuadro isometrico para que
    ocupen la mayor parte del cuadro (como en la pauta a mano del
    profesor), preservando los angulos de 30/90/150 grados (escala
    UNIFORME en x e y, nunca independiente, para no deformar el isometrico)."""
    ancho = d["reticula"]["casillas_ancho"]
    alto = d["reticula"]["casillas_alto"]
    xs, ys = [], []
    for el in d["elementos"]:
        if el["clase"] == "segmento":
            xs += [el["a"][0], el["b"][0]]
            ys += [el["a"][1], el["b"][1]]
        elif el["clase"] == "circulo":
            xs += [el["centro"][0] - el["radio"], el["centro"][0] + el["radio"]]
            ys += [el["centro"][1] - el["radio"], el["centro"][1] + el["radio"]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0
    margen_x = ancho * margen_frac
    margen_y = alto * margen_frac
    disp_w = ancho - 2 * margen_x
    disp_h = alto - 2 * margen_y
    escala = min(disp_w / w, disp_h / h) if w > 0 and h > 0 else 1.0
    cx0 = (x0 + x1) / 2.0
    cy0 = (y0 + y1) / 2.0
    cx1 = ancho / 2.0
    cy1 = alto / 2.0

    def tr(pt):
        return (round((pt[0] - cx0) * escala + cx1, 3), round((pt[1] - cy0) * escala + cy1, 3))

    for el in d["elementos"]:
        if el["clase"] == "segmento":
            el["a"] = list(tr(el["a"]))
            el["b"] = list(tr(el["b"]))
        elif el["clase"] == "circulo":
            el["centro"] = list(tr(el["centro"]))
            el["radio"] = round(el["radio"] * escala, 3)
    return d


for n, d in ISO.items():
    d = _reencuadrar_iso(d)
    with open(os.path.join(OUT_DIR, f"pauta_isometricos_c{n}.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

print("JSON generados en", OUT_DIR)
