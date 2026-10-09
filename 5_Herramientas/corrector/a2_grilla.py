# -*- coding: utf-8 -*-
"""Grilla de celdas para la actividad 2.

La reticula se deduce del nivel del ejercicio, no de las guias punteadas
del dibujo (esas se confunden con las lineas ocultas). Cada pieza cabe en
un cubo de NxNxN modulos, asi que cada vista es una malla de N columnas
por N filas sobre la caja del trazo.
"""
import numpy as np

MODULOS = {"elemental": 2, "medio": 3, "alto": 4}
VISTAS = ("alzado", "perfil", "planta")


def caja(mascara):
    ys, xs = np.nonzero(mascara)
    if len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def modulo(cajas, n):
    """Lado del cuadrito en pixeles, comun a las tres vistas."""
    lados = [max(c[2] - c[0], c[3] - c[1]) for c in cajas.values() if c]
    return max(lados) / float(n) if lados else None


def celdas_vista(cja, s, pad=2):
    """Lista de (fila, col, x0, y0, x1, y1) de una vista.

    Las celdas se solapan `pad` pixeles: las lineas del dibujo caen sobre
    los bordes de la malla y deben contar para las celdas de ambos lados.
    """
    x0, y0, x1, y1 = cja
    cols = max(1, int(round((x1 - x0) / s)))
    filas = max(1, int(round((y1 - y0) / s)))
    cw = (x1 - x0) / cols
    ch = (y1 - y0) / filas
    out = []
    for i in range(filas):
        for j in range(cols):
            out.append((i, j,
                        int(round(x0 + j * cw)) - pad, int(round(y0 + i * ch)) - pad,
                        int(round(x0 + (j + 1) * cw)) + pad, int(round(y0 + (i + 1) * ch)) + pad))
    return filas, cols, out


def grilla(mascaras, nivel, pad=2):
    """mascaras: {'alzado': bool[h,w], ...}. Devuelve {vista: (filas, cols, celdas)}."""
    n = MODULOS[nivel]
    cajas = {k: caja(v) for k, v in mascaras.items()}
    s = modulo(cajas, n)
    if not s:
        return {}
    return {k: celdas_vista(cajas[k], s, pad) for k in mascaras if cajas[k]}


def recorte(m, c):
    _, _, x0, y0, x1, y1 = c
    return m[max(0, y0):y1, max(0, x0):x1]
