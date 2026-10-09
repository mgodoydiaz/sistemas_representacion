"""Figuras del apunte "Dibujo isométrico en AutoCAD" (PCI 1119).
Genera figuras/isocad_*.png a 200 dpi. Reutiliza los helpers de figuras_apunte_v3.py.
Dibujo isométrico SIN reducción: las medidas reales se llevan sobre los ejes.
Ejes de la pieza: X ancho (va hacia 330°), Y profundidad (hacia 210°, el fondo queda
hacia 30°), Z alto (90°). El observador ve las caras +X (isoplano derecho),
+Y (isoplano izquierdo) y +Z (isoplano superior).
"""
import numpy as np
from matplotlib.textpath import TextPath
from matplotlib.patches import PathPatch, Polygon as MPoly
from matplotlib.transforms import Affine2D
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon, LineString

import figuras_apunte_v3 as H
from figuras_apunte_v3 import (setup, save, L, note, leader, circled_num, red_x,
                               fill_white, K, BLUE, RED, GREY, TH, TN)

C30, S30 = np.cos(np.radians(30)), 0.5
FP = FontProperties(family="DejaVu Sans")
AR = dict(arrowstyle="-|>,head_length=0.45,head_width=0.16", lw=0.7, color=BLUE,
          shrinkA=0, shrinkB=0)


def proj(ox=0.0, oy=0.0, s=1.0):
    """Devuelve P(x, y, z) -> punto 2D del dibujo isométrico (sin reducción)."""
    def P(x, y, z):
        return np.array([ox + s * C30 * (x - y), oy + s * (z - S30 * (x + y))])
    return P


def ring(P, c, r, plane, t0=0, t1=360, n=181):
    """Círculo 3D proyectado punto a punto (así la elipse sale exacta).
    plane: 'xz' (isoplano izquierdo), 'xy' (superior), 'yz' (derecho)."""
    t = np.radians(np.linspace(t0, t1, n))
    u, v = r * np.cos(t), r * np.sin(t)
    cx, cy, cz = c
    if plane == "xz":
        pts = [P(cx + a, cy, cz + b) for a, b in zip(u, v)]
    elif plane == "xy":
        pts = [P(cx + a, cy + b, cz) for a, b in zip(u, v)]
    else:
        pts = [P(cx, cy + a, cz + b) for a, b in zip(u, v)]
    return np.array(pts)


def S(ax, P, a, b, kind="vis", color=K, lw=None, z=3):
    L(ax, [P(*a), P(*b)], kind, color, z, lw)


def path3(ax, P, pts, kind="vis", color=K, lw=None, z=3, close=False):
    q = [P(*p) for p in pts]
    if close:
        q.append(q[0])
    L(ax, q, kind, color, z, lw)


def iso_text(ax, pos, s, a, b, size=4.0, color=BLUE, bg=True, z=8, lift=0.0):
    """Texto "acostado" en un isoplano: la línea base sigue al vector a y los trazos
    verticales al vector b (ambos 2D). Equivale al ángulo oblicuo de un estilo de texto."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    if a[0] < 0:
        a = -a
    if a[0] * b[1] - a[1] * b[0] < 0:
        b = -b
    tp = TextPath((0, 0), s, size=size, prop=FP)
    bb = tp.get_extents()
    cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
    pos = np.asarray(pos, float) + b * lift
    M = Affine2D(np.array([[a[0], b[0], pos[0] - a[0] * cx - b[0] * cy],
                           [a[1], b[1], pos[1] - a[1] * cx - b[1] * cy],
                           [0, 0, 1]]))
    if bg:
        w, h = (bb.x1 - bb.x0) / 2 + 0.6, (bb.y1 - bb.y0) / 2 + 0.6
        quad = [pos + a * i * w + b * j * h for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        ax.add_patch(MPoly(quad, closed=True, fc="white", ec="none", zorder=z - 1))
    ax.add_patch(PathPatch(tp, transform=M + ax.transData, fc=color, ec="none", zorder=z))


def dim3(ax, P, p0, p1, off, text, size=4.0, gap=1.5, over=2.0, lift=2.6, txt=True):
    """Cota isométrica: línea de cota paralela a la arista p0-p1, desplazada el vector
    3D off; líneas de referencia paralelas a off (cota oblicua)."""
    p0, p1, off = (np.asarray(v, float) for v in (p0, p1, off))
    n = off / np.linalg.norm(off)
    a0, a1 = P(*(p0 + off)), P(*(p1 + off))
    for p in (p0, p1):
        L(ax, [P(*(p + n * gap)), P(*(p + off + n * over))], "thin", BLUE, 5, 0.6)
    ax.annotate("", xy=a1, xytext=a0, zorder=6,
                arrowprops=dict(arrowstyle="<|-|>,head_length=0.45,head_width=0.16",
                                lw=0.7, color=BLUE, shrinkA=0, shrinkB=0))
    if txt:
        d2 = a1 - a0
        n2 = P(*n) - P(0, 0, 0)
        up = n2 if (d2[0] * n2[1] - d2[1] * n2[0]) * (1 if d2[0] >= 0 else -1) > 0 else -n2
        iso_text(ax, (a0 + a1) / 2, text, d2, up, size=size, lift=lift, bg=False)
    return a0, a1


def dot(ax, p, color=BLUE, ms=3.5, z=9):
    ax.plot([p[0]], [p[1]], "o", color=color, ms=ms, zorder=z)


def arrow(ax, p0, p1, color=BLUE, lw=0.9):
    ax.annotate("", xy=p1, xytext=p0, zorder=7,
                arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.2", lw=lw,
                                color=color, shrinkA=0, shrinkB=0))


def box_edges(ax, P, x0, x1, y0, y1, z0, z1, kind="vis", lw=None, color=K, z=3):
    """Aristas visibles de una caja (caras +X, +Y, +Z)."""
    path3(ax, P, [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)], kind, color, lw, z, True)
    path3(ax, P, [(x0, y1, z1), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
          kind, color, lw, z)
    S(ax, P, (x1, y1, z0), (x1, y1, z1), kind, color, lw, z)


# ============================================================ pieza guía
CR = (20, 10, 30)        # centro del respaldo en la cara delantera (Y = 10)
CRB = (20, 0, 30)        # el mismo centro en la cara trasera (Y = 0)
CB = (20, 40, 10)        # centro del agujero de la base (cara superior)
T_SIL = 135              # generatriz de contorno del cilindro R20 (normal ⟂ visual)


def back_hole_visible(P):
    """Tramo del borde trasero del agujero Ø20 que se ve a través del agujero."""
    front = Polygon(ring(P, CR, 10, "xz"))
    back = LineString(ring(P, CRB, 10, "xz", 0, 360, 721))
    g = back.intersection(front)
    geoms = list(getattr(g, "geoms", [g]))
    return [np.asarray(q.coords) for q in geoms if q.length > 0.5]


def base_edges(ax, P, lw=None, kind="vis", full_top=False):
    yb = 0 if full_top else 10
    path3(ax, P, [(0, 60, 0), (40, 60, 0), (40, 0, 0)], kind, lw=lw)
    path3(ax, P, [(0, 60, 0), (0, 60, 10), (40, 60, 10), (40, 60, 0)], kind, lw=lw)
    path3(ax, P, [(0, 60, 10), (0, yb, 10)], kind, lw=lw)
    path3(ax, P, [(40, 60, 10), (40, yb, 10)], kind, lw=lw)
    if full_top:
        path3(ax, P, [(0, 0, 10), (40, 0, 10), (40, 0, 0)], kind, lw=lw)


def pieza(ax, P, lw=None, hole_base=True, hole_resp=True, axes=True):
    """Soporte con respaldo redondeado: solo aristas visibles."""
    base_edges(ax, P, lw)
    S(ax, P, (0, 10, 10), (40, 10, 10), lw=lw)                 # pie del respaldo
    S(ax, P, (0, 10, 10), (0, 10, 30), lw=lw)
    S(ax, P, (40, 10, 10), (40, 10, 30), lw=lw)
    S(ax, P, (40, 0, 0), (40, 0, 30), lw=lw)
    L(ax, ring(P, CR, 20, "xz", 0, 180), "vis", lw=lw)        # arco delantero
    L(ax, ring(P, CRB, 20, "xz", 0, T_SIL), "vis", lw=lw)     # arco trasero visible
    q = np.radians(T_SIL)
    S(ax, P, (20 + 20 * np.cos(q), 0, 30 + 20 * np.sin(q)),
      (20 + 20 * np.cos(q), 10, 30 + 20 * np.sin(q)), lw=lw)   # línea tangente
    if hole_resp:
        L(ax, ring(P, CR, 10, "xz"), "vis", lw=lw)
        for seg in back_hole_visible(P):
            L(ax, seg, "vis", lw=lw)
    if hole_base:
        L(ax, ring(P, CB, 5, "xy"), "vis", lw=lw)
    if axes:
        e = 4
        S(ax, P, (20 - 20 - e, 10, 30), (20 + 20 + e, 10, 30), "axis", z=2)
        S(ax, P, (20, 10, 10 - e), (20, 10, 50 + e), "axis", z=2)
        if hole_base:
            S(ax, P, (20 - 5 - e, 40, 10), (20 + 5 + e, 40, 10), "axis", z=2)
            S(ax, P, (20, 40 - 5 - e, 10), (20, 40 + 5 + e, 10), "axis", z=2)


# ============================================================ FIG 1
def fig_isoplanos():
    fig, ax = setup((0, 214), (0, 70), 6.4)
    # (a) ejes isométricos
    o = np.array([30.0, 14.0])
    L(ax, [o + (-27, 0), o + (27, 0)], "thin", GREY, 2, 0.7)
    for ang, lab, dx, dy in ((30, "30°", 4, 1), (90, "90°", 0, 3.5), (150, "150°", -5, 1)):
        d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        arrow(ax, o, o + d * 34, K, 1.5)
        note(ax, *(o + d * 37 + (dx, dy)), lab, fs=8, ha="center", weight="bold")
    for r, a1 in ((13, 30), (18, 150)):
        L(ax, H.arc(o, r, 0, a1), "thin", BLUE, 4, 0.7)
    note(ax, o[0] + 15, o[1] + 3.3, "30°", fs=6.5)
    note(ax, o[0] - 10, o[1] + 20, "150°", fs=6.5, ha="right")
    dot(ax, o, K, 3)
    note(ax, 30, 4, "Ángulos medidos desde la horizontal", fs=6.5, ha="center")
    note(ax, 30, 66, "(a) Ejes isométricos", fs=8, ha="center", weight="bold")

    # (b) cubo con los tres isoplanos
    a = 27
    P = proj(107, 7 + a, 1)          # el vértice (a, a, 0) queda en (107, 7)
    box_edges(ax, P, 0, a, 0, a, 0, a)
    m = a / 2
    ux, uy, uz = P(1, 0, 0) - P(0, 0, 0), P(0, 1, 0) - P(0, 0, 0), np.array([0, 1.0])
    iso_text(ax, P(m, a, m) + (0, 5.5), "IZQUIERDO", ux, uz, 3.2, bg=False)
    iso_text(ax, P(m, a, m) + (0, 0.5), "(Left)", ux, uz, 3.0, bg=False)
    iso_text(ax, P(m, a, m) + (0, -5.5), "90° y 150°", ux, uz, 3.0, color=K, bg=False)
    iso_text(ax, P(a, m, m) + (0, 5.5), "DERECHO", uy, uz, 3.2, bg=False)
    iso_text(ax, P(a, m, m) + (0, 0.5), "(Right)", uy, uz, 3.0, bg=False)
    iso_text(ax, P(a, m, m) + (0, -5.5), "30° y 90°", uy, uz, 3.0, color=K, bg=False)
    iso_text(ax, P(m, m, a) + (0, 4.4), "SUPERIOR", ux, uy, 3.2, bg=False)
    iso_text(ax, P(m, m, a) + (0, 0), "(Top)", ux, uy, 3.0, bg=False)
    iso_text(ax, P(m, m, a) + (0, -4.6), "30° y 150°", ux, uy, 3.0, color=K, bg=False)
    note(ax, 107, 2.5, "F5 o Ctrl+E cambia de isoplano", fs=6.5, ha="center")
    note(ax, 107, 66, "(b) Los tres isoplanos", fs=8, ha="center", weight="bold")

    # (c) arista inclinada
    P = proj(172, 36.5, 0.8)
    prof = [(0, 0), (40, 0), (40, 10), (15, 28), (0, 28)]
    d = 22
    path3(ax, P, [(x, d, z) for x, z in prof], close=True)
    path3(ax, P, [(40, d, 0), (40, 0, 0), (40, 0, 10), (15, 0, 28), (0, 0, 28), (0, d, 28)])
    S(ax, P, (40, d, 10), (40, 0, 10)); S(ax, P, (15, d, 28), (15, 0, 28))
    A, B = P(15, d, 28), P(40, d, 10)
    S(ax, P, (15, d, 28), (40, d, 28), "thin", GREY, 0.7, 2)
    S(ax, P, (40, d, 28), (40, d, 10), "thin", GREY, 0.7, 2)
    dot(ax, A); dot(ax, B)
    note(ax, A[0] - 1.5, A[1] + 3.8, "A", fs=8, ha="center", weight="bold")
    note(ax, B[0] + 4.5, B[1] + 0.5, "B", fs=8, ha="center", weight="bold")
    dim3(ax, P, (0, d, 0), (40, d, 0), (0, 9, 0), "40", size=3.6)
    dim3(ax, P, (0, d, 0), (0, d, 28), (-9, 0, 0), "28", size=3.6)
    iso_text(ax, P(27.5, d, 28) + (0, 2.4), "25", ux, uz, 3.2, color="#777777", bg=False)
    iso_text(ax, P(40, d, 19) + (2.6, 0.5), "18", uz, ux, 3.2, color="#777777", bg=False)
    note(ax, 176, 66, "(c) Arista inclinada", fs=8, ha="center", weight="bold")
    note(ax, 176, 5.2, "Ubique A y B midiendo sobre los ejes", fs=6.5, ha="center")
    note(ax, 176, 1.8, "y una A con B. No mida sobre la inclinada.", fs=6.5, ha="center")
    return save(fig, "isocad_01_isoplanos.png")


# ============================================================ FIG 2
def fig_circle_vs_isocircle():
    fig, ax = setup((0, 150), (0, 72), 4.6)
    a, r = 28, 10
    for k, ox in enumerate((38, 112)):
        P = proj(ox, 8 + a, 1)
        box_edges(ax, P, 0, a, 0, a, 0, a)
        m = a / 2
        cs = [((m, a, m), "xz"), ((a, m, m), "yz"), ((m, m, a), "xy")]
        for c, pl in cs:
            if k == 0:
                H.circle(ax, P(*c), r, "vis", lw=1.4)
            else:
                L(ax, ring(P, c, r, pl), "vis", lw=1.4)
                e = r + 3
                if pl == "xz":
                    S(ax, P, (m - e, a, m), (m + e, a, m), "axis", z=2); S(ax, P, (m, a, m - e), (m, a, m + e), "axis", z=2)
                elif pl == "yz":
                    S(ax, P, (a, m - e, m), (a, m + e, m), "axis", z=2); S(ax, P, (a, m, m - e), (a, m, m + e), "axis", z=2)
                else:
                    S(ax, P, (m - e, m, a), (m + e, m, a), "axis", z=2); S(ax, P, (m, m - e, a), (m, m + e, a), "axis", z=2)
    note(ax, 38, 68.5, "CIRCLE", fs=9, ha="center", weight="bold", color=RED)
    note(ax, 38, 2.5, "Incorrecto: el círculo no se deforma con la cara", fs=6.3, ha="center", color=RED)
    red_x(ax, 21, 68.5, 2.6)
    note(ax, 112, 68.5, "ELLIPSE, opción Isocircle", fs=9, ha="center", weight="bold")
    note(ax, 112, 2.5, "Correcto: un isocírculo por isoplano", fs=6.3, ha="center")
    ax.plot([141.5, 143.7, 148], [68.5, 66.2, 71.5], color=BLUE, lw=2, zorder=9)
    return save(fig, "isocad_02_circle_vs_isocircle.png")


# ============================================================ FIG 3
def fig_pieza_medidas():
    fig, ax = setup((-70, 82), (-64, 62), 4.9)
    P = proj(0, 0, 1)
    pieza(ax, P)
    sz = 4.0
    dim3(ax, P, (0, 60, 0), (20, 60, 0), (0, 9, 0), "20", sz)
    dim3(ax, P, (0, 60, 0), (40, 60, 0), (0, 19, 0), "40", sz)
    dim3(ax, P, (40, 0, 0), (40, 10, 0), (9, 0, 0), "10", sz)
    dim3(ax, P, (40, 0, 0), (40, 60, 0), (19, 0, 0), "60", sz)
    dim3(ax, P, (0, 60, 0), (0, 60, 10), (-9, 0, 0), "10", sz)
    dim3(ax, P, (0, 60, 10), (0, 40, 10), (-9, 0, 0), "20", sz)
    dim3(ax, P, (40, 0, 0), (40, 0, 30), (0, -10, 0), "30", sz)
    # línea de referencia desde el centro del agujero de la base
    S(ax, P, (20 - 9, 40, 10), (0, 40, 10), "thin", BLUE, 0.5, 2)
    # radios y diámetros
    q = np.radians(75)
    leader(ax, (-22, 56), P(20 + 20 * np.cos(q), 10, 30 + 20 * np.sin(q)), "R20", fs=8.5, ha="right")
    q = np.radians(200)
    leader(ax, (-36, 30), P(20 + 10 * np.cos(q), 10, 30 + 10 * np.sin(q)), "Ø20 pasante", fs=8.5, ha="right")
    q = np.radians(150)
    leader(ax, (-50, 8), P(20 + 5 * np.cos(q), 40 + 5 * np.sin(q), 10), "Ø10", fs=8.5, ha="right")
    # triada de ejes
    o = np.array([62.0, -50.0])
    for v, lab in (((1, 0, 0), "X"), ((0, 1, 0), "Y"), ((0, 0, 1), "Z")):
        d = P(*v) - P(0, 0, 0)
        arrow(ax, o, o + d * 13, BLUE, 1.0)
        note(ax, *(o + d * 16.5), lab, fs=8, ha="center", weight="bold")
    note(ax, 44, 52, "Medidas en mm", fs=7.5, ha="left")
    note(ax, 44, 47, "Agujeros centrados", fs=7.5, ha="left")
    note(ax, 44, 42.6, "en el ancho (X = 20)", fs=7.5, ha="left")
    return save(fig, "isocad_03_pieza_guia.png")


# ============================================================ FIG 4
def fig_construccion():
    W, Hh = 96, 92
    fig, ax = setup((0, 3 * W), (0, 2 * Hh), 6.5)
    thin, new = 0.9, 2.0
    q = np.radians(T_SIL)
    tl = [(20 + 20 * np.cos(q), 0, 30 + 20 * np.sin(q)), (20 + 20 * np.cos(q), 10, 30 + 20 * np.sin(q))]

    def panel(i):
        col, row = i % 3, i // 3
        x0, y0 = col * W, (1 - row) * Hh
        ax.add_patch(MPoly([(x0 + 1, y0 + 1), (x0 + W - 1, y0 + 1), (x0 + W - 1, y0 + Hh - 1),
                            (x0 + 1, y0 + Hh - 1)], closed=True, fc="none", ec=GREY, lw=0.6, zorder=1))
        circled_num(ax, x0 + 8, y0 + Hh - 8, i + 1, r=4.6, fs=9)
        return proj(x0 + 54, y0 + 37.5, 0.68), x0, y0

    def cap(x0, y0, l1, l2=""):
        note(ax, x0 + 15, y0 + Hh - 6.3, l1, fs=7, weight="bold")
        if l2:
            note(ax, x0 + 15, y0 + Hh - 11.3, l2, fs=6.3)

    def resp_box(P, lw):
        path3(ax, P, [(0, 10, 10), (0, 10, 50), (40, 10, 50), (40, 10, 10), (0, 10, 10)], lw=lw)
        path3(ax, P, [(0, 10, 50), (0, 0, 50), (40, 0, 50), (40, 10, 50)], lw=lw)
        path3(ax, P, [(40, 0, 50), (40, 0, 10)], lw=lw)

    def leftovers(P):
        path3(ax, P, [(0, 10, 10), (0, 0, 10), (40, 0, 10)], "thin", GREY, 0.8, 2)

    # 1 base
    P, x0, y0 = panel(0)
    base_edges(ax, P, new, full_top=True)
    cap(x0, y0, "Caja de la base", "LINE con Ortho: 40 × 60 × 10")
    A = P(40, 60, 0)
    dot(ax, A)
    note(ax, A[0] + 3.5, A[1] - 0.5, "A (inicio)", fs=6.5)
    iso_text(ax, (P(0, 60, 0) + P(40, 60, 0)) / 2 + (-2, -3.5), "40", P(1, 0, 0) - P(0, 0, 0), (0, 1), 3.4, bg=False)
    iso_text(ax, (P(40, 0, 0) + P(40, 60, 0)) / 2 + (2.5, -3.5), "60", P(0, 1, 0) - P(0, 0, 0), (0, 1), 3.4, bg=False)
    iso_text(ax, P(0, 60, 5) + (-3.5, 0.5), "10", (0, 1), P(1, 0, 0) - P(0, 0, 0), 3.4, bg=False)

    # 2 respaldo como caja
    P, x0, y0 = panel(1)
    base_edges(ax, P, thin); S(ax, P, (40, 0, 0), (40, 0, 10), lw=thin); leftovers(P)
    resp_box(P, new)
    cap(x0, y0, "Caja del respaldo", "40 × 10 × 50, al fondo")
    iso_text(ax, P(0, 10, 30) + (-3.5, 0.5), "40", (0, 1), P(1, 0, 0) - P(0, 0, 0), 3.4, bg=False)
    iso_text(ax, P(40, 5, 50) + (6.5, 4.4), "10", P(0, 1, 0) - P(0, 0, 0), (0, 1), 3.4, bg=False)

    # 3 centro e isocírculos
    P, x0, y0 = panel(2)
    base_edges(ax, P, thin); S(ax, P, (40, 0, 0), (40, 0, 10), lw=thin); leftovers(P)
    resp_box(P, thin)
    S(ax, P, (20, 10, 10), (20, 10, 50), "thin", BLUE, 0.7, 4)
    S(ax, P, (0, 10, 30), (40, 10, 30), "thin", BLUE, 0.7, 4)
    L(ax, ring(P, CR, 20, "xz"), "vis", lw=new)
    L(ax, ring(P, CR, 10, "xz"), "vis", lw=new)
    c = P(*CR); dot(ax, c)
    leader(ax, (c[0] - 22, c[1] + 6), c, "C", fs=7.5, ha="right")
    cap(x0, y0, "Isocírculos R20 y Ø20", "Isoplano izquierdo, centro C")

    # 4 copiar y tangente
    P, x0, y0 = panel(3)
    base_edges(ax, P, thin); S(ax, P, (40, 0, 0), (40, 0, 10), lw=thin); leftovers(P)
    resp_box(P, thin)
    L(ax, ring(P, CR, 20, "xz"), "vis", lw=thin); L(ax, ring(P, CR, 10, "xz"), "vis", lw=thin)
    L(ax, ring(P, CRB, 20, "xz"), "vis", lw=new); L(ax, ring(P, CRB, 10, "xz"), "vis", lw=new)
    path3(ax, P, tl, lw=new)
    for p in tl:
        dot(ax, P(*p), ms=3)
    leader(ax, (x0 + 28, y0 + 66), (P(*tl[0]) + P(*tl[1])) / 2 + (-0.3, 0.3), "tangente", fs=6.5, ha="right")
    c0, c1 = P(*CR), P(*CRB)
    arrow(ax, c0, c1, BLUE, 1.0); dot(ax, c0, ms=2.5)
    leader(ax, (x0 + 80, y0 + 14), (c0 + c1) / 2 + (0.4, -0.4), "10 a 30°", fs=6.5, ha="center")
    cap(x0, y0, "COPY hacia el fondo", "10 mm a 30° y línea tangente")

    # 5 recortar
    P, x0, y0 = panel(4)
    pieza(ax, P, lw=new, hole_base=False, axes=False)
    for a_, b_ in (((0, 10, 30), (0, 10, 50)), ((0, 10, 50), (40, 10, 50)), ((40, 10, 50), (40, 10, 30)),
                   ((0, 10, 50), (0, 0, 50)), ((0, 0, 50), (40, 0, 50)), ((40, 10, 50), (40, 0, 50)),
                   ((40, 0, 50), (40, 0, 30))):
        S(ax, P, a_, b_, "hid", GREY, 0.7, 2)
    L(ax, ring(P, CR, 20, "xz", 180, 360), "hid", GREY, 2, 0.7)
    cap(x0, y0, "TRIM y ERASE", "Se borra lo gris (sobrantes)")

    # 6 agujero de la base, ejes y capas
    P, x0, y0 = panel(5)
    pieza(ax, P, lw=new)
    S(ax, P, (20, 60, 10), (20, 40, 10), "thin", BLUE, 0.7, 4)
    c = P(*CB); dot(ax, c, ms=2.5)
    cap(x0, y0, "Agujero Ø10, ejes y capas", "Isoplano superior")
    return save(fig, "isocad_04_construccion.png")


# ============================================================ FIG 5
def fig_cotas():
    fig, ax = setup((0, 204), (0, 86), 5.9)
    a, b, h = 44, 30, 18
    for k, ox in enumerate((44, 142)):
        P = proj(ox, 55, 1)
        box_edges(ax, P, 0, a, 0, b, 0, h)
        ux, uy = P(1, 0, 0) - P(0, 0, 0), P(0, 1, 0) - P(0, 0, 0)
        if k == 1:
            dim3(ax, P, (0, b, 0), (a, b, 0), (0, 12, 0), "44", 4.2)
            dim3(ax, P, (a, 0, 0), (a, b, 0), (12, 0, 0), "30", 4.2)
            dim3(ax, P, (0, b, 0), (0, b, h), (-12, 0, 0), "18", 4.2)
        else:
            def aligned(p0, p1, side, text, d=10.5):
                p0, p1 = P(*p0), P(*p1)
                t = (p1 - p0) / np.linalg.norm(p1 - p0)
                n = np.array([-t[1], t[0]]) * side
                for p in (p0, p1):
                    L(ax, [p + n * 1.5, p + n * (d + 2)], "thin", BLUE, 5, 0.6)
                ax.annotate("", xy=p1 + n * d, xytext=p0 + n * d, zorder=6,
                            arrowprops=dict(arrowstyle="<|-|>,head_length=0.45,head_width=0.16",
                                            lw=0.7, color=BLUE, shrinkA=0, shrinkB=0))
                rot = np.degrees(np.arctan2(t[1], t[0]))
                if rot > 90 or rot <= -90:
                    rot += 180
                up = np.array([-np.sin(np.radians(rot)), np.cos(np.radians(rot))])
                m = (p0 + p1) / 2 + n * d + up * 3.0
                ax.text(m[0], m[1], text, color=BLUE, fontsize=8, ha="center", va="center",
                        rotation=rot, rotation_mode="anchor", zorder=7)
            aligned((0, b, 0), (a, b, 0), -1, "44")
            aligned((a, 0, 0), (a, b, 0), -1, "30")
            aligned((0, b, 0), (0, b, h), 1, "18")
    note(ax, 50, 82, "Solo DIMALIGNED", fs=9, ha="center", weight="bold", color=RED)
    note(ax, 50, 2.5, "La cota no parece estar sobre la cara", fs=6.5, ha="center", color=RED)
    note(ax, 148, 82, "DIMALIGNED + DIMEDIT, Oblique", fs=9, ha="center", weight="bold")
    P = proj(142, 55, 1)
    m1, m2, m3 = P(a / 2, b + 12, 0), P(a + 12, b / 2, 0), P(-12, b, h / 2)
    note(ax, m1[0] - 9, m1[1] - 9, "Oblique 30", fs=6.5, ha="center")
    note(ax, m2[0] + 11, m2[1] - 9, "Oblique -30", fs=6.5, ha="center")
    note(ax, m3[0] - 3, m3[1] + 17, "Oblique -30", fs=6.5, ha="center")
    note(ax, 148, 2.5, "Líneas de referencia y texto paralelos a los ejes", fs=6.5, ha="center")
    return save(fig, "isocad_05_cotas.png")


FIGS = [fig_isoplanos, fig_circle_vs_isocircle, fig_pieza_medidas, fig_construccion, fig_cotas]

if __name__ == "__main__":
    import sys
    # comprobación numérica de la elipse isométrica (semiejes 1,2247 r y 0,7071 r)
    e = ring(proj(), (0, 0, 0), 1.0, "xy", n=3601)
    rr = np.hypot(e[:, 0], e[:, 1])
    assert abs(rr.max() - 1.2247) < 1e-3 and abs(rr.min() - 0.7071) < 1e-3, (rr.max(), rr.min())
    sel = sys.argv[1:]
    for f in FIGS:
        if not sel or any(s in f.__name__ for s in sel):
            print(f())
