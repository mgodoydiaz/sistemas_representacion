#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_pauta.py
=================

Lee los archivos JSON de datos (pauta_<pagina>_c<N>.json) que describen, en
coordenadas de reticula, la geometria vectorial de la pauta de correccion de
la Actividad 4 (Sistemas de Representacion), y produce:

  1. Un archivo DXF por cuadro y un DXF por lamina completa (6 cuadros en
     grilla 2x3), con capas separadas segun el tipo de linea:
       - LLENA   : linea continua (arista vista)
       - OCULTA  : linea de trazos (arista oculta)
       - EJE     : linea de trazo y punto (eje / centro)

  2. Por cada cuadro, dos PNG de 1000x1000 pixeles:
       - pauta_<pagina>_c<N>.png        : escala de grises, con la reticula
         de fondo (para que se vea similar a la hoja rectificada real).
       - pauta_<pagina>_c<N>_trazo.png  : RGBA, solo el trazo en negro con
         canal alfa, fondo transparente (sin la reticula).

Estos dos PNG usan el MISMO encuadre que el rectificador usa para las
fotos de los alumnos: el interior del cuadro (en coordenadas de reticula,
de 0 a casillas_ancho y de 0 a casillas_alto) se mapea linealmente -y de
forma INDEPENDIENTE en x e y- al lienzo completo de 1000x1000. Esto es
intencional: el rectificador tambien hace un warpPerspective del cuadro
real (que no es necesariamente cuadrado) a un lienzo cuadrado de 1000x1000,
por lo que la unica forma de que la pauta vectorial calce con las fotos
rectificadas de los alumnos es reproducir la MISMA deformacion no uniforme.

Uso:
    python3 generar_pauta.py --datos . --salida ../salida/pautas --dxf ./dxf
    python3 generar_pauta.py --datos . --salida ../salida/pautas --dxf ./dxf --cuadro vistas:3

Requiere: Python 3.10+, numpy, Pillow (PIL), ezdxf.
"""
import argparse
import glob
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

try:
    import ezdxf
except ImportError:  # pragma: no cover
    print("Falta ezdxf. Instalar con: pip install ezdxf", file=sys.stderr)
    raise

# ---------------------------------------------------------------------------
# Parametros de dibujo
# ---------------------------------------------------------------------------
CANVAS = 1000          # lado del lienzo final en pixeles
SUPERSAMPLE = 4        # factor de sobre-muestreo para antialiasing tipo lapiz
GROSOR_PX = 5          # grosor de trazo aproximado en el lienzo de 1000 (4 a 6 px)
COLOR_TRAZO = (35, 35, 35)     # gris oscuro, no negro puro (aspecto lapiz)
ALPHA_TRAZO = 235
COLOR_GRID_CUADRADA = 222      # gris claro para la reticula cuadrada de fondo
COLOR_GRID_ISO = 222
COLOR_FONDO = 250               # blanco-hueso del papel

# Capas DXF -> (nombre, color ACI, tipo de linea)
CAPAS = {
    "llena":  ("LLENA",  7,  "CONTINUOUS"),
    "oculta": ("OCULTA", 1,  "DASHED"),
    "eje":    ("EJE",    5,  "DASHDOT"),
}


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------
def cargar_json_cuadro(datos_dir, pagina, cuadro):
    path = os.path.join(datos_dir, f"pauta_{pagina}_c{cuadro}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_cuadros(datos_dir):
    """Devuelve [(pagina, cuadro, path), ...] ordenado, a partir de los
    archivos pauta_<pagina>_c<N>.json presentes en datos_dir."""
    out = []
    for path in sorted(glob.glob(os.path.join(datos_dir, "pauta_*_c*.json"))):
        base = os.path.basename(path)[len("pauta_"):-len(".json")]
        pagina, _, resto = base.rpartition("_c")
        try:
            n = int(resto)
        except ValueError:
            continue
        out.append((pagina, n, path))
    out.sort(key=lambda t: (t[0], t[1]))
    return out


def bbox_reticula(d):
    r = d["reticula"]
    return 0.0, 0.0, float(r["casillas_ancho"]), float(r["casillas_alto"])


# ---------------------------------------------------------------------------
# DXF
# ---------------------------------------------------------------------------
def _asegurar_capas(doc):
    for _, (nombre, color, tipo) in CAPAS.items():
        if nombre not in doc.layers:
            doc.layers.add(name=nombre, color=color, linetype=tipo)


def _asegurar_linetypes(doc):
    # ezdxf trae DASHED/DASHDOT en sus linetypes estandar via load_linetypes,
    # pero si el doc nuevo no los tiene, los definimos a mano.
    defs = {
        "DASHED": ("Dashed", [0.6, -0.3]),
        "DASHDOT": ("Dash dot", [0.8, -0.2, 0.0, -0.2]),
    }
    for name, (desc, pattern) in defs.items():
        if name not in doc.linetypes:
            doc.linetypes.add(name, pattern=[sum(abs(p) for p in pattern)] + pattern, description=desc)


def _agregar_elementos_msp(msp, elementos, offset=(0.0, 0.0)):
    ox, oy = offset
    for el in elementos:
        capa = CAPAS.get(el.get("tipo", "llena"), CAPAS["llena"])[0]
        if el["clase"] == "segmento":
            a = (el["a"][0] + ox, el["a"][1] + oy)
            b = (el["b"][0] + ox, el["b"][1] + oy)
            msp.add_line(a, b, dxfattribs={"layer": capa})
        elif el["clase"] == "circulo":
            c = (el["centro"][0] + ox, el["centro"][1] + oy)
            msp.add_circle(c, el["radio"], dxfattribs={"layer": capa})


def generar_dxf_cuadro(d, path_out):
    doc = ezdxf.new(setup=True)
    _asegurar_linetypes(doc)
    _asegurar_capas(doc)
    msp = doc.modelspace()
    _agregar_elementos_msp(msp, d["elementos"])
    doc.saveas(path_out)


def generar_dxf_lamina(cuadros_pagina, pagina, path_out, margen=4.0):
    """cuadros_pagina: lista de (n, d) para n=1..6 de una misma pagina.
    Los ordena en grilla 2x3 (fila1: 1,2,3 ; fila2: 4,5,6), separados por
    un margen, replicando la disposicion fisica de la lamina impresa."""
    doc = ezdxf.new(setup=True)
    _asegurar_linetypes(doc)
    _asegurar_capas(doc)
    msp = doc.modelspace()

    # calcular tamano de casilla maximo para espaciar parejo
    anchos = [bbox_reticula(d)[2] for _, d in cuadros_pagina]
    altos = [bbox_reticula(d)[3] for _, d in cuadros_pagina]
    w = max(anchos) if anchos else 17.0
    h = max(altos) if altos else 20.0

    posiciones = {1: (0, 1), 2: (1, 1), 3: (2, 1), 4: (0, 0), 5: (1, 0), 6: (2, 0)}
    for n, d in cuadros_pagina:
        col, fila = posiciones.get(n, (0, 0))
        ox = col * (w + margen)
        oy = fila * (h + margen)
        _agregar_elementos_msp(msp, d["elementos"], offset=(ox, oy))
        # marco del cuadro (linea llena) para referencia visual
        cw, ch = bbox_reticula(d)[2], bbox_reticula(d)[3]
        msp.add_lwpolyline(
            [(ox, oy), (ox + cw, oy), (ox + cw, oy + ch), (ox, oy + ch), (ox, oy)],
            dxfattribs={"layer": "LLENA"},
        )
    doc.saveas(path_out)


# ---------------------------------------------------------------------------
# Rasterizado PNG
# ---------------------------------------------------------------------------
def _transform(pt, bbox, canvas):
    """Mapea (x,y) en coordenadas de reticula [x0,x1]x[y0,y1] al lienzo de
    canvas x canvas pixeles, con origen abajo-izquierda -> arriba-izquierda
    (se invierte el eje Y porque en la imagen Y crece hacia abajo)."""
    x0, y0, x1, y1 = bbox
    x, y = pt
    px = (x - x0) / (x1 - x0) * canvas
    py = canvas - (y - y0) / (y1 - y0) * canvas
    return (px, py)


def _dibujar_elementos(draw, elementos, bbox, canvas, color, ancho):
    for el in elementos:
        if el["clase"] == "segmento":
            a = _transform(el["a"], bbox, canvas)
            b = _transform(el["b"], bbox, canvas)
            tipo = el.get("tipo", "llena")
            if tipo == "llena":
                draw.line([a, b], fill=color, width=ancho)
            elif tipo == "oculta":
                _linea_punteada(draw, a, b, color, ancho, patron=[9 * SUPERSAMPLE, 6 * SUPERSAMPLE])
            elif tipo == "eje":
                _linea_punteada(draw, a, b, color, max(1, ancho - 2),
                                 patron=[16 * SUPERSAMPLE, 5 * SUPERSAMPLE, 3 * SUPERSAMPLE, 5 * SUPERSAMPLE])
            else:
                draw.line([a, b], fill=color, width=ancho)
        elif el["clase"] == "circulo":
            cx, cy = _transform(el["centro"], bbox, canvas)
            # el radio puede escalar distinto en x/y si el cuadro no es
            # cuadrado; usamos el promedio de la escala en cada eje.
            x0, y0, x1, y1 = bbox
            sx = canvas / (x1 - x0)
            sy = canvas / (y1 - y0)
            rx = el["radio"] * sx
            ry = el["radio"] * sy
            bbox_el = [cx - rx, cy - ry, cx + rx, cy + ry]
            draw.ellipse(bbox_el, outline=color, width=ancho)


def _linea_punteada(draw, a, b, color, ancho, patron):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    largo = math.hypot(dx, dy)
    if largo < 1e-6:
        return
    ux, uy = dx / largo, dy / largo
    pos = 0.0
    i = 0
    dibujar = True
    while pos < largo:
        paso = patron[i % len(patron)]
        fin = min(pos + paso, largo)
        if dibujar:
            p1 = (ax + ux * pos, ay + uy * pos)
            p2 = (ax + ux * fin, ay + uy * fin)
            draw.line([p1, p2], fill=color, width=ancho)
        pos = fin
        dibujar = not dibujar
        i += 1


def _dibujar_reticula_fondo(draw, d, bbox, canvas):
    r = d["reticula"]
    x0, y0, x1, y1 = bbox
    if r["tipo"] == "cuadrada":
        nx, ny = int(round(r["casillas_ancho"])), int(round(r["casillas_alto"]))
        for i in range(nx + 1):
            x = i
            p1 = _transform((x, 0), bbox, canvas)
            p2 = _transform((x, ny), bbox, canvas)
            draw.line([p1, p2], fill=COLOR_GRID_CUADRADA, width=1)
        for j in range(ny + 1):
            y = j
            p1 = _transform((0, y), bbox, canvas)
            p2 = _transform((x1, y), bbox, canvas)
            draw.line([p1, p2], fill=COLOR_GRID_CUADRADA, width=1)
    else:
        # reticula isometrica: lineas a 30, 90 y 150 grados dentro del bbox
        cos30 = math.cos(math.radians(30))
        sin30 = math.sin(math.radians(30))
        paso = 1.0
        n = int(max(r["casillas_ancho"], r["casillas_alto"]) / (paso * sin30)) + 4
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        largo = max(x1 - x0, y1 - y0) * 1.5
        for k in range(-n, n + 1):
            # verticales (90 grados): x = k*paso*cos30 (offset desde el centro)
            xline = cx + k * paso * cos30
            if x0 - 2 <= xline <= x1 + 2:
                p1 = _transform((xline, y0 - 2), bbox, canvas)
                p2 = _transform((xline, y1 + 2), bbox, canvas)
                draw.line([p1, p2], fill=COLOR_GRID_ISO, width=1)
            # lineas a +30 grados
            base = cx + k * paso * cos30
            p1 = _transform((base - largo * cos30, cy - largo * sin30), bbox, canvas)
            p2 = _transform((base + largo * cos30, cy + largo * sin30), bbox, canvas)
            draw.line([p1, p2], fill=COLOR_GRID_ISO, width=1)
            # lineas a 150 grados
            p1 = _transform((base + largo * cos30, cy - largo * sin30), bbox, canvas)
            p2 = _transform((base - largo * cos30, cy + largo * sin30), bbox, canvas)
            draw.line([p1, p2], fill=COLOR_GRID_ISO, width=1)


def generar_png_cuadro(d, path_gris, path_trazo):
    bbox = bbox_reticula(d)
    hi = CANVAS * SUPERSAMPLE
    ancho_hi = GROSOR_PX * SUPERSAMPLE

    # --- version gris con reticula de fondo -------------------------------
    img_gris = Image.new("L", (hi, hi), color=COLOR_FONDO)
    draw_gris = ImageDraw.Draw(img_gris)
    _dibujar_reticula_fondo(draw_gris, d, bbox, hi)
    _dibujar_elementos(draw_gris, d["elementos"], bbox, hi, color=COLOR_TRAZO[0], ancho=ancho_hi)
    img_gris = img_gris.resize((CANVAS, CANVAS), Image.LANCZOS)
    img_gris.save(path_gris)

    # --- version trazo RGBA (sin reticula, fondo transparente) ------------
    img_trazo = Image.new("RGBA", (hi, hi), color=(0, 0, 0, 0))
    draw_trazo = ImageDraw.Draw(img_trazo)
    color_rgba = COLOR_TRAZO + (ALPHA_TRAZO,)
    _dibujar_elementos(draw_trazo, d["elementos"], bbox, hi, color=color_rgba, ancho=ancho_hi)
    img_trazo = img_trazo.resize((CANVAS, CANVAS), Image.LANCZOS)
    img_trazo.save(path_trazo)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Genera DXF y PNG de la pauta vectorial de la Actividad 4.")
    ap.add_argument("--datos", default=".", help="Carpeta con los pauta_<pagina>_c<N>.json")
    ap.add_argument("--salida", default="../salida/pautas", help="Carpeta de salida para los PNG (contrato del visor)")
    ap.add_argument("--dxf", default="./dxf", help="Carpeta de salida para los DXF")
    ap.add_argument("--cuadro", default=None,
                     help="Procesar solo un cuadro, formato pagina:N (ej: vistas:3). "
                          "Si se omite, procesa todos los cuadros encontrados.")
    args = ap.parse_args()

    datos_dir = os.path.abspath(args.datos)
    salida_dir = os.path.abspath(os.path.join(datos_dir, args.salida)) if not os.path.isabs(args.salida) else args.salida
    dxf_dir = os.path.abspath(os.path.join(datos_dir, args.dxf)) if not os.path.isabs(args.dxf) else args.dxf
    os.makedirs(salida_dir, exist_ok=True)
    os.makedirs(dxf_dir, exist_ok=True)

    cuadros = listar_cuadros(datos_dir)
    if args.cuadro:
        pagina_f, n_f = args.cuadro.split(":")
        cuadros = [(p, n, path) for (p, n, path) in cuadros if p == pagina_f and n == int(n_f)]
        if not cuadros:
            print(f"No se encontro el cuadro {args.cuadro} en {datos_dir}", file=sys.stderr)
            sys.exit(1)

    por_pagina = {}
    for pagina, n, path in cuadros:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        print(f"[{pagina} c{n}] generando DXF y PNG...")

        dxf_path = os.path.join(dxf_dir, f"pauta_{pagina}_c{n}.dxf")
        generar_dxf_cuadro(d, dxf_path)

        png_gris = os.path.join(salida_dir, f"pauta_{pagina}_c{n}.png")
        png_trazo = os.path.join(salida_dir, f"pauta_{pagina}_c{n}_trazo.png")
        generar_png_cuadro(d, png_gris, png_trazo)

        por_pagina.setdefault(pagina, []).append((n, d))

    # DXF por lamina completa (solo si se proceso el set completo de una pagina)
    for pagina, lista in por_pagina.items():
        if len(lista) >= 2:
            lista_ordenada = sorted(lista, key=lambda t: t[0])
            path_lamina = os.path.join(dxf_dir, f"pauta_{pagina}_lamina.dxf")
            generar_dxf_lamina(lista_ordenada, pagina, path_lamina)
            print(f"[{pagina}] DXF de lamina completa -> {path_lamina}")

    print("Listo.")


if __name__ == "__main__":
    main()
