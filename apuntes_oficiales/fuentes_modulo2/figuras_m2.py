import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import helpers_v3 as H
from helpers_v3 import L, circle, arc, dim, note, leader, setup, poly_outline, centermarks, K, BLUE, GREY
from shapely.geometry import Polygon, box
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")
def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=220, facecolor="white"); plt.close(fig)

def rrect(w, h, r, ox=0, oy=0):
    pts = []
    for (cx, cy, a0) in [(w - r, r, -90), (w - r, h - r, 0), (r, h - r, 90), (r, r, 180)]:
        pts += [(ox + x, oy + y) for x, y in arc((cx, cy), r, a0, a0 + 90, 20)]
    return pts
HOLES = [(10, 10), (90, 10), (90, 50), (10, 50)]

def placa(ax, ox=0, oy=0, paso=9, color=K):
    if paso == 1: poly_outline(ax, [(ox, oy), (ox + 100, oy), (ox + 100, oy + 60), (ox, oy + 60)], "vis", color)
    else: poly_outline(ax, rrect(100, 60, 10, ox, oy), "vis", color)
    if paso >= 3:
        L(ax, [(ox - 5, oy + 30), (ox + 105, oy + 30)], "axis", color); L(ax, [(ox + 50, oy - 5), (ox + 50, oy + 65)], "axis", color)
        for x, y in HOLES: centermarks(ax, (ox + x, oy + y), 5, 3, color)
    if paso >= 4:
        circle(ax, (ox + 50, oy + 30), 15, "vis", color)
        for x, y in HOLES: circle(ax, (ox + x, oy + y), 5, "vis", color)

def fig_capas():
    fig, ax = setup((0, 150), (0, 52), 5.6)
    filas = [("Visible", "vis", "Continuous · 0,50 mm", "contornos y aristas vistas"),
             ("Oculta", "hid", "HIDDEN · 0,25 mm", "aristas ocultas"),
             ("Ejes", "axis", "CENTER · 0,25 mm", "ejes y centros de agujeros"),
             ("Cotas", "thin", "Continuous · 0,25 mm", "cotas y textos"),
             ("Rayado", "thin", "Continuous · 0,25 mm", "rayado de cortes")]
    for i, (n, k, t, u) in enumerate(filas):
        y = 46 - i * 10
        ax.text(2, y, n, fontsize=9, va="center", fontweight="bold", color=K)
        L(ax, [(24, y), (62, y)], k)
        ax.text(66, y, t, fontsize=8, va="center", color=K); ax.text(108, y, u, fontsize=8, va="center", color=BLUE)
    save(fig, "m2_base_01_capas.png")

def fig_pasos():
    fig, axs = plt.subplots(2, 2, figsize=(7.0, 4.9))
    tit = ["RECTANG: contorno 100 × 60", "FILLET: esquinas R10", "Capa Ejes: LINE por los centros", "CIRCLE, COPY y MIRROR: agujeros"]
    for i, ax in enumerate(axs.flat):
        ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-12, 112); ax.set_ylim(-10, 84)
        placa(ax, 0, 0, i + 1)
        ax.add_patch(plt.Circle((-5, 76), 4.5, color=BLUE)); ax.text(-5, 76, str(i + 1), color="white", fontsize=9, ha="center", va="center", fontweight="bold")
        ax.text(2, 76, tit[i], fontsize=8.5, color=BLUE, va="center", fontweight="bold")
    fig.subplots_adjust(wspace=0.03, hspace=0.03, left=0.01, right=0.99, top=0.99, bottom=0.01)
    save(fig, "m2_base_02_pasos.png")

def fig_placa_cotas():
    fig, ax = setup((-28, 150), (-30, 86), 5.4)
    placa(ax)
    c = K
    dim(ax, (0, -14), (100, -14), "100", off=(0, 3), color=c); dim(ax, (10, 72), (90, 72), "80", off=(0, 3), color=c)
    dim(ax, (-14, 0), (-14, 60), "60", off=(-3, 0), color=c); dim(ax, (114, 10), (114, 50), "40", off=(3, 0), color=c)
    for x in (0, 100): L(ax, [(x, -2), (x, -17)], "thin")
    for x in (10, 90): L(ax, [(x, 57), (x, 75)], "thin")
    for y in (0, 60): L(ax, [(-2, y), (-17, y)], "thin")
    for y in (10, 50): L(ax, [(97, y), (117, y)], "thin")
    leader(ax, (120, -10), (50 + 15 * np.cos(-0.6), 30 + 15 * np.sin(-0.6)), "Ø30", fs=9, color=c)
    leader(ax, (118, 68), (90 + 5 * 0.7, 50 + 5 * 0.7), "4 × Ø10", fs=9, color=c)
    leader(ax, (-24, 78), (10 - 7, 50 + 7), "R10", fs=9, color=c)
    save(fig, "m2_base_03_placa_acotada.png")

def fig_coordenadas():
    fig, ax = setup((-12, 120), (-12, 62), 4.6)
    ax.annotate("", xy=(112, 0), xytext=(-5, 0), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1)); ax.annotate("", xy=(0, 56), xytext=(0, -5), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1))
    ax.text(114, 0, "X", fontsize=8, color=GREY, va="center"); ax.text(0, 58, "Y", fontsize=8, color=GREY, ha="center")
    A = (20, 10); B = (70, 10); C = (70 + 40 * np.cos(np.radians(60)), 10 + 40 * np.sin(np.radians(60)))
    L(ax, [A, B, C], "vis")
    for p, t, o in [(A, "20,10\nabsoluta", (-2, -8)), (B, "@50,0\nrelativa", (0, -8)), (C, "@40<60\npolar", (8, 3))]:
        ax.plot(*p, "o", ms=4, color=BLUE, zorder=6); ax.text(p[0] + o[0], p[1] + o[1], t, fontsize=8, color=BLUE, ha="center", va="center")
    L(ax, arc(B, 12, 0, 60, 20), "thin", BLUE); ax.text(87, 15, "60°", fontsize=7.5, color=BLUE)
    L(ax, [B, (95, 10)], "thin", GREY)
    save(fig, "m2_base_04_coordenadas.png")

# ---------------- vistas y cortes
P2_HID = [(-40, 0), (40, 0), (40, 15), (20, 15), (20, 50), (-20, 50), (-20, 15), (-40, 15)]
def alzado_ocultas(ax, ox, oy, color=K):
    T = lambda pts: [(x + ox, y + oy) for x, y in pts]
    poly_outline(ax, T(P2_HID), "vis", color)
    for s in (-1, 1):
        L(ax, T([(s * 10, 0), (s * 10, 50)]), "hid", color)
        for x in (25, 35): L(ax, T([(s * x, 0), (s * x, 15)]), "hid", color)
        L(ax, T([(s * 30, -3), (s * 30, 18)]), "axis", color)
    L(ax, T([(0, -5), (0, 55)]), "axis", color)

def fig_proyeccion():
    fig, ax = setup((-70, 110), (-52, 128), 4.6)
    H.p2_planta(ax, 0, 0); alzado_ocultas(ax, 0, 62)
    for x in (-40, -35, -25, -20, -10, 10, 20, 25, 35, 40):
        ax.plot([x, x], [-50, 126], color=BLUE, lw=0.5, ls=(0, (6, 3)), zorder=1)
    note(ax, 48, 100, "XLINE vertical\ndesde cada punto\nde la planta", fs=8)
    note(ax, -66, 90, "ALZADO", fs=7.5, color=K); note(ax, -66, -30, "PLANTA", fs=7.5, color=K)
    note(ax, 48, 30, "capa Auxiliar:\nse apaga al final", fs=8)
    save(fig, "m2_vc_01_proyeccion.png")

def fig_corte():
    fig, ax = setup((-72, 128), (-58, 130), 4.8)
    H.p2_alzado_cortado(ax, 0, 62); ax.text(0, 122, "A-A", fontsize=12, ha="center", va="center", fontweight="bold")
    H.p2_planta(ax, 0, 0); H.cut_trace(ax, [(-54, 0), (54, 0)], thick_len=8)
    for x in (-50, 50): H.view_arrow(ax, (x, 0.8), (x, 12), "A", (x + (-5 if x < 0 else 5), 9))
    leader(ax, (60, 96), (30, 68), "HATCH · ANSI31\ncapa Rayado", fs=7.5)
    leader(ax, (60, -28), (46, -1.5), "PLINE con ancho\nen los extremos", fs=7.5)
    leader(ax, (62, 30), (51, 13), "flecha: PLINE\nde ancho 3 a 0", fs=7.5)
    leader(ax, (36, 124), (12, 122), "TEXT, altura 5", fs=7.5)
    leader(ax, (-68, 100), (-10, 80), "ocultas borradas\n(ERASE)", fs=7.5, ha="left")
    save(fig, "m2_vc_02_corte.png")

def fig_rayado_escala():
    fig, ax = setup((-4, 154), (-12, 44), 5.4)
    for i, (sp, t, ok) in enumerate([(0.9, "Escala muy chica:\nse imprime como mancha", False), (2.5, "Escala correcta:\n2 a 3 mm entre líneas", True), (9, "Escala muy grande:\ncasi no se ve", False)]):
        ox = i * 52
        g = box(ox, 0, ox + 40, 40).difference(box(ox + 12, 12, ox + 28, 28))
        H.hatch(ax, g, sp=sp)
        poly_outline(ax, [(ox, 0), (ox + 40, 0), (ox + 40, 40), (ox, 40)]); poly_outline(ax, [(ox + 12, 12), (ox + 28, 12), (ox + 28, 28), (ox + 12, 28)])
        ax.text(ox + 20, -6, t, fontsize=7.5, color=BLUE if ok else H.RED, ha="center", va="center")
    save(fig, "m2_vc_03_rayado_escala.png")

def fig_presentacion():
    fig, ax = setup((-120, 250), (-22, 318), 5.2)
    ax.text(-60, 250, "MODELO · escala 1:1", fontsize=8.5, ha="center", color=BLUE, fontweight="bold")
    H.p2_planta(ax, -60, 100); H.p2_alzado_cortado(ax, -60, 162)
    ax.text(-60, 40, "la pieza se dibuja\ncon sus medidas reales", fontsize=7.5, ha="center", color=BLUE)
    ax.annotate("", xy=(14, 150), xytext=(-10, 150), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.5))
    ax.text(125, 308, "PRESENTACIÓN · hoja A4 vertical", fontsize=8.5, ha="center", color=BLUE, fontweight="bold")
    poly_outline(ax, [(20, 0), (230, 0), (230, 297), (20, 297)], "thin")
    poly_outline(ax, [(40, 10), (220, 10), (220, 287), (40, 287)], "vis")
    poly_outline(ax, [(40, 10), (220, 10), (220, 46), (40, 46)], "vis", lw=1.2)
    for y in (22, 34): L(ax, [(40, y), (220, y)], "thin")
    ax.text(130, 28, "CAJETÍN · en la hoja, a escala 1", fontsize=7, ha="center", va="center")
    ax.plot([50, 210, 210, 50, 50], [56, 56, 277, 277, 56], color=BLUE, lw=1, ls=(0, (5, 3)))
    ax.text(54, 270, "ventana (MVIEW) · escala 1:1", fontsize=7.5, color=BLUE, va="center")
    H.p2_planta(ax, 130, 112); H.p2_alzado_cortado(ax, 130, 178)
    save(fig, "m2_vc_04_presentacion.png")

for f in (fig_capas, fig_pasos, fig_placa_cotas, fig_coordenadas, fig_proyeccion, fig_corte, fig_rayado_escala, fig_presentacion): f()
print(sorted(os.listdir(OUT)))
