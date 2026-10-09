"""Figuras del Apunte Unidad 1 v3 (PCI 1119). Genera figuras/apunte_*.png a 200 dpi.
Unidades del dibujo en mm. Negro = dibujo técnico; azul #2E5E8C = anotación didáctica.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle, Rectangle
from shapely.geometry import Polygon, LineString, Point, box, MultiLineString
from shapely.ops import unary_union

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "lines.scale_dashes": False,
    "lines.solid_capstyle": "round",
    "lines.dash_capstyle": "butt",
})

K = "black"
BLUE = "#2E5E8C"
RED = "#B03A2E"
GREY = "#A8A8A8"
TH = 2.0     # gruesa
TN = 0.8     # fina
DASH = (0, (5, 2.5))
CENTER = (0, (14, 2.5, 2, 2.5))


# ------------------------------------------------------------------ utilidades
def setup(xlim, ylim, width_in):
    w = xlim[1] - xlim[0]
    h = ylim[1] - ylim[0]
    fig = plt.figure(figsize=(width_in, width_in * h / w))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    return path


def L(ax, pts, kind="vis", color=K, z=3, lw=None):
    pts = np.asarray(pts, float)
    style = {"vis": ("-", TH), "thin": ("-", TN), "hid": (DASH, TN),
             "axis": (CENTER, TN)}[kind]
    ax.plot(pts[:, 0], pts[:, 1], linestyle=style[0], lw=lw or style[1],
            color=color, zorder=z, solid_capstyle="round" if kind == "vis" else "butt")


def poly_outline(ax, pts, kind="vis", color=K, z=3, lw=None):
    pts = list(pts) + [pts[0]]
    L(ax, pts, kind, color, z, lw)


def arc(c, r, t0, t1, n=120, rx=None, ry=None, rot=0.0):
    rx = r if rx is None else rx
    ry = r if ry is None else ry
    t = np.linspace(np.radians(t0), np.radians(t1), n)
    x = rx * np.cos(t)
    y = ry * np.sin(t)
    ca, sa = np.cos(rot), np.sin(rot)
    return np.column_stack([c[0] + ca * x - sa * y, c[1] + sa * x + ca * y])


def circle(ax, c, r, kind="vis", color=K, z=3, lw=None):
    L(ax, arc(c, r, 0, 360, 200), kind, color, z, lw)


def centermarks(ax, c, r, ext=4, color=K, z=2, h=True, v=True):
    if h:
        L(ax, [(c[0] - r - ext, c[1]), (c[0] + r + ext, c[1])], "axis", color, z)
    if v:
        L(ax, [(c[0], c[1] - r - ext), (c[0], c[1] + r + ext)], "axis", color, z)


def hatch(ax, geom, angle=45, sp=2.5, color=K, lw=0.7, z=2, xf=None, phase=0.0,
          offsets=None):
    """Rayado de líneas paralelas recortadas exactamente a la geometría (shapely).
    xf: función opcional que transforma puntos (x, y) -> (u, v) (para isometría)."""
    if geom.is_empty:
        return
    minx, miny, maxx, maxy = geom.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    R = np.hypot(maxx - minx, maxy - miny)
    a = np.radians(angle)
    d = np.array([np.cos(a), np.sin(a)])
    nrm = np.array([-np.sin(a), np.cos(a)])
    k = np.arange(-R, R + sp, sp) + phase if offsets is None else np.asarray(offsets)
    for off in k:
        p0 = np.array([cx, cy]) + nrm * off - d * R
        p1 = np.array([cx, cy]) + nrm * off + d * R
        seg = LineString([p0, p1]).intersection(geom)
        if seg.is_empty:
            continue
        parts = getattr(seg, "geoms", [seg])
        for s in parts:
            if s.geom_type != "LineString":
                continue
            pts = np.asarray(s.coords)
            if xf is not None:
                pts = np.array([xf(*p) for p in pts])
            ax.plot(pts[:, 0], pts[:, 1], "-", lw=lw, color=color, zorder=z,
                    solid_capstyle="butt")


def fill_white(ax, pts, z):
    ax.add_patch(MPoly(np.asarray(pts), closed=True, facecolor="white",
                       edgecolor="none", zorder=z))


def dim(ax, p0, p1, text, off=(0, 0), color=BLUE, fs=8, ext=True, rot=None,
        tpos=None, lw=0.7):
    """Cota: línea con flechas entre p0 y p1 (ya desplazados), texto centrado."""
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="<|-|>,head_length=0.45,head_width=0.16",
                                lw=lw, color=color, shrinkA=0, shrinkB=0), zorder=6)
    m = ((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1])
    if tpos is not None:
        m = tpos
    if rot is None:
        rot = np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0]))
        if rot > 90 or rot < -90:
            rot += 180
    ax.text(m[0], m[1], text, color=color, fontsize=fs, ha="center", va="center",
            rotation=rot, zorder=7,
            bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))


def small_dim(ax, a, b, text, horizontal=True, tside=1, fs=7, color=BLUE):
    """Cota de una separación pequeña: flechas por fuera apuntando a cada línea."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    kw = dict(arrowstyle="-|>,head_length=0.45,head_width=0.16", lw=0.7, color=color,
              shrinkA=0, shrinkB=0)
    ax.annotate("", xy=a, xytext=a - d * 7, arrowprops=kw, zorder=6)
    ax.annotate("", xy=b, xytext=b + d * 7, arrowprops=kw, zorder=6)
    L(ax, [a, b], "thin", color, z=6, lw=0.7)
    if horizontal:
        pos = (b + d * 9) if tside > 0 else (a - d * 9)
        ax.text(pos[0], pos[1], text, color=color, fontsize=fs,
                ha="left" if tside > 0 else "right", va="center", zorder=7)
    else:
        m = (a + b) / 2
        ax.text(m[0] + 2.5 * tside, m[1], text, color=color, fontsize=fs,
                ha="left" if tside > 0 else "right", va="center", zorder=7)


def ext_line(ax, p0, p1, color=BLUE):
    L(ax, [p0, p1], "thin", color, z=5, lw=0.6)


def note(ax, x, y, s, fs=8, ha="left", va="center", color=BLUE, style="normal",
         weight="normal", z=8, bg=False):
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="square,pad=0.15", fc="white", ec="none")
    ax.text(x, y, s, color=color, fontsize=fs, ha=ha, va=va, fontstyle=style,
            fontweight=weight, zorder=z, **kw)


def leader(ax, xy_text, xy_pt, s, fs=8, ha="left", color=BLUE):
    ax.annotate(s, xy=xy_pt, xytext=xy_text, color=color, fontsize=fs, ha=ha,
                va="center", zorder=8,
                arrowprops=dict(arrowstyle="-|>,head_length=0.35,head_width=0.13",
                                lw=0.7, color=color, shrinkA=2, shrinkB=0))


def view_arrow(ax, tail, head, letter=None, lpos=None, fs=10):
    """Flecha de dirección de observación (negra, rellena) + letra mayúscula."""
    ax.annotate("", xy=head, xytext=tail,
                arrowprops=dict(arrowstyle="-|>,head_length=0.8,head_width=0.35",
                                lw=1.2, color=K, shrinkA=0, shrinkB=0), zorder=6)
    if letter:
        ax.text(lpos[0], lpos[1], letter, fontsize=fs, ha="center", va="center",
                fontweight="bold", color=K, zorder=7)


def cut_trace(ax, pts, thick_len=7, ext=0):
    """Traza de plano de corte: trazo y punto fino con tramos gruesos en extremos
    y en los quiebres."""
    pts = [np.array(p, float) for p in pts]
    L(ax, pts, "axis")
    def thick(a, b):
        d = (b - a) / np.linalg.norm(b - a)
        L(ax, [a, a + d * thick_len], "vis", lw=TH * 1.1)
    thick(pts[0], pts[1])
    thick(pts[-1], pts[-2])
    for i in range(1, len(pts) - 1):  # quiebres
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d1 = (a - b) / np.linalg.norm(a - b)
        d2 = (c - b) / np.linalg.norm(c - b)
        L(ax, [b + d1 * thick_len / 2, b, b + d2 * thick_len / 2], "vis", lw=TH * 1.1)


def freehand(p0, p1, amp=1.2, waves=1.5, n=80, seed=0):
    """Línea fina a mano alzada entre p0 y p1 (ondulada suave)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    t = np.linspace(0, 1, n)
    d = p1 - p0
    nrm = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * np.pi)
    w = amp * (np.sin(2 * np.pi * waves * t + ph) + 0.35 * np.sin(2 * np.pi * 2.3 * waves * t + 2 * ph))
    return p0 + np.outer(t, d) + np.outer(w, nrm)


def circled_num(ax, x, y, n, r=4.2, fs=9):
    ax.add_patch(Circle((x, y), r, facecolor=BLUE, edgecolor=BLUE, zorder=9))
    ax.text(x, y, str(n), color="white", fontsize=fs, ha="center", va="center",
            fontweight="bold", zorder=10)


def red_x(ax, x, y, s=3.0):
    ax.plot([x - s, x + s], [y - s, y + s], color=RED, lw=2, zorder=9)
    ax.plot([x - s, x + s], [y + s, y - s], color=RED, lw=2, zorder=9)


# ------------------------------------------------------------------ isometría
def iso(x, y, z):
    """Vista desde delante-derecha-arriba (d = (1,-1,1)); y crece hacia atrás."""
    return ((x + y) / np.sqrt(2), (-x + y + 2 * z) / np.sqrt(6))


def isoP(pts3):
    return np.array([iso(*p) for p in pts3])


# =================================================================== FIG 5
def fig_cajetin():
    W, H = 180, 36
    fig, ax = setup((-3, 262), (-9, 44), 6.4)
    rows = [  # (y0, [(ancho, campo, ejemplo)])
        (0, [(50, "Propietario legal", "UCT · PCI 1119"),
             (70, "Título", "SOPORTE ANGULAR"),
             (40, "N.º de identificación", "PCI1119-G3-L05"),
             (20, "Hoja", "1/1")]),
        (12, [(45, "Tipo de documento", "Lámina de ejercicio"),
              (45, "Creado por", "J. Soto"),
              (45, "Aprobado por", "M. Godoy"),
              (45, "Fecha de edición", "2026-09-23")]),
        (24, [(45, "Escala", "1:2"),
              (45, "Método de proyección", None),
              (45, "Unidades", "mm"),
              (45, "Formato", "A4")]),
    ]
    for y0, cells in rows:
        x = 0
        for w, name, val in cells:
            L(ax, [(x, y0), (x + w, y0), (x + w, y0 + 12), (x, y0 + 12), (x, y0)], "thin")
            ax.text(x + 1.2, y0 + 10.8, name, fontsize=6.0, color="#707070",
                    ha="left", va="top", zorder=5)
            if val:
                ax.text(x + w / 2, y0 + 4.2, val, fontsize=7.8 if len(val) < 16 else 6.6,
                        ha="center", va="center", zorder=5)
            else:  # símbolo de primer diedro
                cx, cy = x + w / 2 + 4, y0 + 4.0
                # tronco de cono: extremo menor a la izquierda
                tx = cx - 9
                trap = [(tx - 4.5, cy - 1.8), (tx + 4.5, cy - 3.2), (tx + 4.5, cy + 3.2),
                        (tx - 4.5, cy + 1.8)]
                poly_outline(ax, trap, "vis", lw=1.1)
                L(ax, [(tx - 6.5, cy), (tx + 6.5, cy)], "axis", lw=0.5)
                ccx = cx + 7
                circle(ax, (ccx, cy), 3.2, "vis", lw=1.1)
                circle(ax, (ccx, cy), 1.8, "vis", lw=1.1)
                L(ax, [(ccx - 4.8, cy), (ccx + 4.8, cy)], "axis", lw=0.5)
                L(ax, [(ccx, cy - 4.3), (ccx, cy + 4.3)], "axis", lw=0.5)
            x += w
    # contornos gruesos
    poly_outline(ax, [(0, 0), (W, 0), (W, H), (0, H)], "vis")
    poly_outline(ax, [(0, 0), (W, 0), (W, 12), (0, 12)], "vis")
    # llaves azules
    def brace(y0, y1, x=184, text=""):
        L(ax, [(x, y0 + 0.5), (x + 2, y0 + 0.5), (x + 2, y1 - 0.5), (x, y1 - 0.5)],
          "thin", BLUE, lw=1.0)
        L(ax, [(x + 2, (y0 + y1) / 2), (x + 4, (y0 + y1) / 2)], "thin", BLUE, lw=1.0)
        ax.text(x + 5.5, (y0 + y1) / 2, text, fontsize=6.6, color=BLUE,
                ha="left", va="center")
    brace(24, 36, text="Datos indicativos\n(fuera del cajetín en ISO 7200;\nzona suplementaria en NCh 14)")
    brace(0, 24, text="8 campos obligatorios\nISO 7200:2004\n(fila inferior: zona de\nidentificación)")
    dim(ax, (0, -5), (W, -5), "180", fs=7.5)
    ext_line(ax, (0, -0.5), (0, -7))
    ext_line(ax, (W, -0.5), (W, -7))
    dim(ax, (-0.1, 0), (-0.1, 0), "")  # sin efecto (mantener API)
    return save(fig, "apunte_03_cajetin_iso7200.png")


# =================================================================== FIG 6
def fig_lamina():
    fig, ax = setup((-30, 250), (-20, 320), 3.4)
    poly_outline(ax, [(0, 0), (210, 0), (210, 297), (0, 297)], "thin", lw=0.9)
    poly_outline(ax, [(20, 10), (200, 10), (200, 287), (20, 287)], "vis", lw=1.8)
    # cajetín simplificado 180 x 36
    x0, y0 = 20, 10
    poly_outline(ax, [(x0, y0), (x0 + 180, y0), (x0 + 180, y0 + 36), (x0, y0 + 36)], "vis", lw=1.6)
    L(ax, [(x0, y0 + 12), (x0 + 180, y0 + 12)], "vis", lw=1.4)
    L(ax, [(x0, y0 + 24), (x0 + 180, y0 + 24)], "thin")
    for xs in (50, 120, 160):
        L(ax, [(x0 + xs, y0), (x0 + xs, y0 + 12)], "thin")
    for xs in (45, 90, 135):
        L(ax, [(x0 + xs, y0 + 12), (x0 + xs, y0 + 36)], "thin")
    # señales de centrado
    for p, q in [((105, 0), (105, 15)), ((105, 297), (105, 282)),
                 ((0, 148.5), (25, 148.5)), ((210, 148.5), (195, 148.5))]:
        L(ax, [p, q], "vis", lw=1.6)
    ax.text(110, 165, "zona de dibujo", color=BLUE, fontsize=9, ha="center",
            va="center", fontstyle="italic")
    ax.text(110, 28, "cajetín", color=BLUE, fontsize=8, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"), zorder=8)
    # cotas
    dim(ax, (0, 250), (20, 250), "20", fs=7, off=(0, 6), rot=0)
    small_dim(ax, (200, 230), (210, 230), "10", True, 1)
    small_dim(ax, (60, 297), (60, 287), "10", False, 1)
    small_dim(ax, (10, 0), (10, 10), "10", False, 1)
    dim(ax, (20, -9), (200, -9), "180", fs=7.5)
    ext_line(ax, (20, -0.5), (20, -12))
    ext_line(ax, (200, -0.5), (200, -12))
    dim(ax, (218, 10), (218, 46), "36", fs=7.5, rot=90)
    ext_line(ax, (200.5, 46), (222, 46))
    ext_line(ax, (210.5, 10), (222, 10))
    dim(ax, (-14, 0), (-14, 297), "297", fs=7.5, rot=90)
    ext_line(ax, (-0.5, 0), (-17, 0)); ext_line(ax, (-0.5, 297), (-17, 297))
    dim(ax, (0, 312), (210, 312), "210", fs=7.5)
    ext_line(ax, (0, 297.5), (0, 315)); ext_line(ax, (210, 297.5), (210, 315))
    return save(fig, "apunte_02_lamina_a4.png")


# =================================================================== P1 geometría
S2 = np.sqrt(2) / 2
P1_FRONT = [(0, 0), (80, 0), (80, 20), (50, 50), (0, 50)]
E_DIR = np.array([S2, -S2])       # a lo largo de la arista de canto
N_DIR = np.array([S2, S2])        # normal exterior de la cara inclinada
E0 = np.array([50.0, 50.0])
FACE_LEN = 30 * np.sqrt(2)        # 42,43
HC = E0 + E_DIR * FACE_LEN / 2    # (65, 35)


def p1_alzado(ax, color=K, kind_vis="vis", hidden=True, axis=True, z=3):
    poly_outline(ax, P1_FRONT, kind_vis, color, z)
    if hidden:
        for s in (+6, -6):
            a = HC + E_DIR * s
            b = a + (-N_DIR) * (a[1] / S2)      # hasta z = 0
            L(ax, [a, b], "hid", color, z)
    if axis:
        a = HC + N_DIR * 5
        b = np.array([30.0, 0.0]) - N_DIR * 5
        L(ax, [a, b], "axis", color, z)


def p1_planta(ax, Y0, color=K, kind_vis="vis", hidden=True, z=3):
    """Planta con la cara trasera (y=40) en Y0 y la delantera en Y0-40."""
    Yp = lambda y: Y0 - (40 - y)
    poly_outline(ax, [(0, Yp(0)), (80, Yp(0)), (80, Yp(40)), (0, Yp(40))], kind_vis, color, z)
    L(ax, [(50, Yp(0)), (50, Yp(40))], kind_vis, color, z)
    L(ax, arc((65, Yp(20)), 0, 0, 360, 160, rx=6 * S2, ry=6), kind_vis, color, z)
    if hidden:
        L(ax, arc((30, Yp(20)), 0, 0, 360, 160, rx=6 / S2, ry=6), "hid", color, z)
        for yy in (14, 26):
            L(ax, [(30, Yp(yy)), (65, Yp(yy))], "hid", color, z)
    L(ax, [(19, Yp(20)), (73, Yp(20))], "axis", color, z)
    L(ax, [(65, Yp(20) - 9), (65, Yp(20) + 9)], "axis", color, z)


def fig_por_que_auxiliar():
    fig, ax = setup((-22, 215), (-78, 68), 6.2)
    p1_alzado(ax)
    Y0 = -18
    p1_planta(ax, Y0)
    note(ax, 40, 58, "ALZADO", fs=8, ha="center", color=K)
    note(ax, 40, Y0 - 48, "PLANTA", fs=8, ha="center", color=K)
    # proyectantes finas (correspondencia)
    for x in (50, 80):
        L(ax, [(x, -2), (x, Y0 + 2)], "thin", GREY, lw=0.5)
    # anotaciones
    dim(ax, (50, Y0 + 5), (80, Y0 + 5), "30", fs=7.5)
    dim(ax, E0 + N_DIR * 6, E0 + E_DIR * FACE_LEN + N_DIR * 6, "42,4", fs=7.5)
    leader(ax, (90, Y0 - 32), (68, Y0 - 22), "círculo Ø12 visto\ncomo elipse", fs=7.5)
    note(ax, 90, Y0 - 50, "Cara deformada en planta:\n30 mm en vez de 42,4 mm.", fs=7.5)
    leader(ax, (88, 18), (74, 26), "cara inclinada\nde canto", fs=7.5)
    # isometría a la derecha
    ox, oy = 160, 5
    def P(x, y, z):
        u, v = iso(x, y, z)
        return (ox + u * 0.62, oy + v * 0.62)
    V = lambda pts: [P(*p) for p in pts]
    front = [(0, 0, 0), (80, 0, 0), (80, 0, 20), (50, 0, 50), (0, 0, 50)]
    top = [(0, 0, 50), (50, 0, 50), (50, 40, 50), (0, 40, 50)]
    incl = [(50, 0, 50), (80, 0, 20), (80, 40, 20), (50, 40, 50)]
    right = [(80, 0, 0), (80, 40, 0), (80, 40, 20), (80, 0, 20)]
    for f in (front, top, incl, right):
        fill_white(ax, V(f), 2)
        poly_outline(ax, V(f), "vis", lw=1.5)
    c3 = np.array([65, 20, 35.0])
    e1 = np.array([0, 1, 0.0])
    e2 = np.array([S2, 0, -S2])
    t = np.linspace(0, 2 * np.pi, 160)
    pts = [P(*(c3 + 6 * (np.cos(a) * e1 + np.sin(a) * e2))) for a in t]
    L(ax, pts, "vis", lw=1.3)
    note(ax, 170, -26, "ISOMETRÍA", fs=8, ha="center", color=K)
    return save(fig, "apunte_07_por_que_auxiliar.png")


# =================================================================== FIG 8
def fig_auxiliar_pasos():
    D_LR = 15
    Y0 = -12
    xl, yl = (-18, 142), (-66, 110)
    fig = plt.figure(figsize=(6.2, 6.2 * (2 * (yl[1] - yl[0])) / (2 * (xl[1] - xl[0]))))
    titles = ["Arista de canto", "Línea de referencia", "Proyectantes perpendiculares",
              "Transferir profundidad y dibujar"]
    for k in range(4):
        r, c = divmod(k, 2)
        ax = fig.add_axes([c / 2, (1 - r) / 2, 0.5, 0.5])
        ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
        step = k + 1
        p1_alzado(ax, GREY, "thin", hidden=True, axis=False)
        p1_planta(ax, Y0, GREY, "thin", hidden=False)
        circled_num(ax, -10, 103, step)
        note(ax, -3, 103, titles[k], fs=8.5, color=BLUE, weight="bold")
        # paso 1: arista de canto
        A, B = E0, E0 + E_DIR * FACE_LEN
        L(ax, [A, B], "vis", BLUE if step == 1 else K, lw=2.6 if step == 1 else TH)
        if step == 1:
            leader(ax, (84, 48), (70, 30), "la cara inclinada\nse ve como línea", fs=7.5)
            note(ax, -8, -59.5, "Busque la vista donde la cara está de canto.", fs=7.2)
        if step >= 2:
            lr0 = E0 + N_DIR * D_LR + E_DIR * (-12)
            lr1 = E0 + N_DIR * D_LR + E_DIR * (FACE_LEN + 12)
            L(ax, [lr0, lr1], "thin", K, lw=0.9)
            note(ax, *(lr1 + E_DIR * 1 + N_DIR * 3), "LR", fs=8, color=BLUE, weight="bold")
            L(ax, [(-4, Y0), (86, Y0)], "thin", K, lw=0.9)
            note(ax, 88, Y0, "LR", fs=8, color=BLUE, weight="bold")
            if step == 2:
                note(ax, -8, -59.5, "LR paralela a la arista; en planta, en la cara trasera.", fs=7.2)
        if step >= 3:
            for s in (0, FACE_LEN / 2 - 6, FACE_LEN / 2, FACE_LEN / 2 + 6, FACE_LEN):
                a = E0 + E_DIR * s
                b = a + N_DIR * (D_LR + 48)
                L(ax, [a + N_DIR * 1, b], "thin", K, lw=0.5)
            if step == 3:
                # marca de ángulo recto en la LR
                q = E0 + E_DIR * FACE_LEN + N_DIR * D_LR
                sq = [q - E_DIR * 3, q - E_DIR * 3 + N_DIR * 3, q + N_DIR * 3]
                L(ax, sq, "thin", BLUE, lw=0.8)
                note(ax, -8, -59.5, "Proyectantes a 90° de la arista de canto.", fs=7.2)
        if step == 4:
            def Pa(s, d):
                return E0 + E_DIR * s + N_DIR * (D_LR + d)
            rect = [Pa(0, 0), Pa(FACE_LEN, 0), Pa(FACE_LEN, 40), Pa(0, 40)]
            poly_outline(ax, rect, "vis")
            hc = Pa(FACE_LEN / 2, 20)
            circle(ax, hc, 6, "vis", lw=1.6)
            L(ax, [hc - E_DIR * 10, hc + E_DIR * 10], "axis")
            L(ax, [hc - N_DIR * 10, hc + N_DIR * 10], "axis")
            # extensión parcial hacia la cara superior + rotura a mano alzada
            L(ax, [Pa(0, 0), Pa(-7, 0)], "vis")
            L(ax, [Pa(0, 40), Pa(-7, 40)], "vis")
            fh = freehand(Pa(-7, -1), Pa(-7, 41), amp=0.9, waves=1.2, seed=3)
            L(ax, fh, "thin")
            # profundidades
            dim(ax, (-9, Y0), (-9, Y0 - 40), "40", fs=7.5, rot=90)
            ext_line(ax, (-0.5, Y0 - 40), (-12, Y0 - 40))
            p0 = Pa(FACE_LEN + 5, 0)
            p1 = Pa(FACE_LEN + 5, 40)
            dim(ax, p0, p1, "40", fs=7.5)
            note(ax, -8, -59.5, "Misma profundidad medida desde la LR en ambas vistas.", fs=7.2)
            leader(ax, (2, 78), Pa(8, 30), "vista auxiliar\nparcial (VM)", fs=7.5)
    return save(fig, "apunte_08_auxiliar_pasos.png")


# =================================================================== P2 geometría
def p2_regions(side=+1):
    """Zonas macizas del corte por el eje (plano XZ), lado derecho (side=+1) o izq."""
    s = side
    A = Polygon([(s * 10, 0), (s * 25, 0), (s * 25, 15), (s * 20, 15), (s * 20, 50), (s * 10, 50)])
    B = Polygon([(s * 35, 0), (s * 40, 0), (s * 40, 15), (s * 35, 15)])
    return unary_union([A.buffer(0), B.buffer(0)])


P2_OUT = [(-40, 0), (40, 0), (40, 15), (20, 15), (20, 50), (-20, 50), (-20, 15), (-40, 15)]


def p2_alzado_cortado(ax, ox=0, oy=0, half=None, sep_axis=True):
    """half=None: corte total. half='semi': mitad izquierda en vista, derecha cortada."""
    T = lambda pts: [(x + ox, y + oy) for x, y in pts]
    from shapely import affinity
    if half is None:
        poly_outline(ax, T(P2_OUT), "vis")
        for side in (-1, 1):
            g = affinity.translate(p2_regions(side), ox, oy)
            hatch(ax, g)
            for x in (10, 25, 35):
                L(ax, T([(side * x, 0), (side * x, 15 if x > 10 else 50)]), "vis")
        L(ax, T([(0, -5), (0, 55)]), "axis")
        for x in (-30, 30):
            L(ax, T([(x, -3), (x, 18)]), "axis")
    else:
        # mitad izquierda: vista exterior sin ocultas
        L(ax, T([(0, 0), (-40, 0), (-40, 15), (-20, 15), (-20, 50), (0, 50)]), "vis")
        # mitad derecha: corte
        L(ax, T([(0, 0), (40, 0), (40, 15), (20, 15), (20, 50), (0, 50)]), "vis")
        g = affinity.translate(p2_regions(+1), ox, oy)
        hatch(ax, g)
        for x in (10, 25, 35):
            L(ax, T([(x, 0), (x, 15 if x > 10 else 50)]), "vis")
        if sep_axis:
            L(ax, T([(0, -5), (0, 55)]), "axis")
        else:
            L(ax, T([(0, 0), (0, 50)]), "vis")
        L(ax, T([(30, -3), (30, 18)]), "axis")


def p2_planta(ax, ox=0, oy=0):
    T = lambda p: (p[0] + ox, p[1] + oy)
    circle(ax, T((0, 0)), 40)
    circle(ax, T((0, 0)), 20)
    circle(ax, T((0, 0)), 10)
    for a in (0, 90, 180, 270):
        c = T((30 * np.cos(np.radians(a)), 30 * np.sin(np.radians(a))))
        circle(ax, c, 5)
    L(ax, arc(T((0, 0)), 30, 0, 360, 240), "axis")
    for a in (0, 90, 180, 270):
        c = np.array(T((30 * np.cos(np.radians(a)), 30 * np.sin(np.radians(a)))))
        rdir = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
        L(ax, [c - rdir * 0, c - rdir * 0], "thin")
    L(ax, [T((-45, 0)), T((45, 0))], "axis")
    L(ax, [T((0, -45)), T((0, 45))], "axis")


# =================================================================== FIG 9
def fig_que_es_cortar():
    fig, ax = setup((-62, 276), (-40, 60), 6.4)
    sc = 0.85
    # ---- (a) pieza completa con plano de corte
    oxa, oya = -8, 0
    def Pa(x, y, z):
        u, v = iso(x, y, z)
        return (oxa + sc * u, oya + sc * v)
    iso_p2(ax, Pa, half=False)
    # plano semitransparente y = 0
    Wa = lambda a, b, z: Pa((a - b) / np.sqrt(2), (a + b) / np.sqrt(2), z)
    pl = [Wa(-56, 0, -6), Wa(56, 0, -6), Wa(56, 0, 60), Wa(-56, 0, 60)]
    ax.add_patch(MPoly(np.array(pl), closed=True, facecolor=BLUE, alpha=0.13,
                       edgecolor=BLUE, lw=0.8, zorder=20))
    for z, segs in ((50, [(-20, -10), (10, 20)]),
                    (15, [(-40, -35), (-25, -20), (20, 25), (35, 40)])):
        for a0, a1 in segs:
            L(ax, [Wa(a0, 0, z), Wa(a1, 0, z)], "vis", BLUE, z=21, lw=1.8)
    note(ax, oxa - 50, 55, "plano de corte", fs=7.2)
    note(ax, oxa + 2, -34, "(a) Plano de corte por el eje", fs=7.5, ha="center", color=K)
    # ---- (b) mitad delantera retirada
    oxb = 108
    def Pb(x, y, z):
        u, v = iso(x, y, z)
        return (oxb + sc * u, oya + sc * v)
    iso_p2(ax, Pb, half=True)
    note(ax, oxb + 2, -34, "(b) Se retira la mitad delantera", fs=7.5, ha="center", color=K)
    # ---- (c) alzado cortado
    oxc, oyc = 218, -14
    from shapely import affinity
    s2 = 0.8
    ax2 = ax
    # dibujado a escala s2 mediante transformación manual
    def Tc(pts):
        return [(oxc + s2 * x, oyc + s2 * y) for x, y in pts]
    poly_outline(ax, Tc(P2_OUT), "vis", lw=1.6)
    for side in (-1, 1):
        g = affinity.scale(p2_regions(side), s2, s2, origin=(0, 0))
        g = affinity.translate(g, oxc, oyc)
        hatch(ax, g, sp=2.2)
        for x in (10, 25, 35):
            L(ax, Tc([(side * x, 0), (side * x, 15 if x > 10 else 50)]), "vis", lw=1.6)
    L(ax, Tc([(0, -5), (0, 55)]), "axis")
    for x in (-30, 30):
        L(ax, Tc([(x, -3), (x, 18)]), "axis")
    note(ax, oxc, -34, "(c) Vista cortada", fs=7.5, ha="center", color=K)
    # flechas azules entre paneles
    for x0, x1 in ((56, 72), (163, 180)):
        ax.annotate("", xy=(x1, 18), xytext=(x0, 18),
                    arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.3",
                                    lw=1.4, color=BLUE))
    leader(ax, (256, 52), (oxc + s2 * 15, oyc + s2 * 35), "se raya solo\nel material", fs=7, ha="center")
    leader(ax, (196, 52), (oxc - 3, oyc + s2 * 40), "hueco:\nsin rayar", fs=7, ha="center")
    return save(fig, "apunte_09_que_es_cortar.png")


def iso_p2(ax, P, half):
    """Isometría del buje con brida P2 (painter's algorithm).
    La pieza se gira 45° para que el plano de corte (b = 0, que contiene el eje y
    los agujeros a 0° y 180°) quede de frente al observador.
    half=True: solo la mitad trasera (b >= 0) con las caras cortadas rayadas."""
    from shapely.geometry import MultiPoint
    def W(a, b, z):                       # coordenadas de la pieza -> mundo
        return P((a - b) / np.sqrt(2), (a + b) / np.sqrt(2), z)

    def ring(R, z, t0, t1, ca=0, cb=0, n=120):
        t = np.radians(np.linspace(t0, t1, n))
        return [W(ca + R * np.cos(q), cb + R * np.sin(q), z) for q in t]

    def hull(R, z0, z1, t0, t1, zord):
        pts = np.array(ring(R, z0, t0, t1) + ring(R, z1, t0, t1))
        h = MultiPoint([tuple(p) for p in pts]).convex_hull
        fill_white(ax, np.asarray(h.exterior.coords), zord)

    def gen(R, t, z0, z1, zord, lw):
        q = np.radians(t)
        L(ax, [W(R * np.cos(q), R * np.sin(q), z0), W(R * np.cos(q), R * np.sin(q), z1)],
          "vis", z=zord, lw=lw)

    lw = 1.5
    t0, t1 = (0, 180) if half else (0, 360)
    # ---- brida
    hull(40, 0, 15, t0, t1, 1)
    L(ax, ring(40, 15, t0, t1), "vis", z=2, lw=lw)
    if not half:
        L(ax, ring(40, 0, 180, 360), "vis", z=2, lw=lw)
        gen(40, 0, 0, 15, 2, lw); gen(40, 180, 0, 15, 2, lw)
    # agujeros de la brida (a 0°, 90°, 180°, 270°)
    for a in (0, 90, 180, 270):
        ca, cb = 30 * np.cos(np.radians(a)), 30 * np.sin(np.radians(a))
        if half and a == 270:
            continue
        if half and a in (0, 180):
            L(ax, ring(5, 15, 0, 180, ca, cb), "vis", z=2, lw=1.1)
            L(ax, ring(5, 0, 0, 180, ca, cb), "vis", z=2, lw=0.9)
        else:
            L(ax, ring(5, 15, 0, 360, ca, cb), "vis", z=2, lw=1.1)
    # ---- cubo
    hull(20, 15, 50, t0, t1, 3)
    L(ax, ring(20, 50, t0, t1), "vis", z=4, lw=lw)
    if not half:
        L(ax, ring(20, 15, 180, 360), "vis", z=4, lw=lw)
        gen(20, 0, 15, 50, 4, lw); gen(20, 180, 15, 50, 4, lw)
    L(ax, ring(10, 50, t0, t1), "vis", z=4, lw=1.2)
    if half:
        L(ax, ring(10, 0, 0, 180), "vis", z=4, lw=0.9)
        # caras cortadas (b = 0)
        for side in (-1, 1):
            g = p2_regions(side)
            for part in getattr(g, "geoms", [g]):
                pts = [W(x, 0, z) for x, z in np.asarray(part.exterior.coords)]
                fill_white(ax, pts, 5)
                L(ax, pts, "vis", z=7, lw=lw)
            hatch(ax, g, sp=3.0, lw=0.55, z=6, xf=lambda x, z: W(x, 0, z))
    return W


# =================================================================== FIG 10
def fig_indicacion_AA():
    fig, ax = setup((-72, 128), (-58, 128), 5.0)
    oy_alz = 62
    p2_alzado_cortado(ax, 0, oy_alz)
    ax.text(0, oy_alz + 60, "A-A", fontsize=12, ha="center", va="center", fontweight="bold")
    # planta
    p2_planta(ax, 0, 0)
    # traza de corte sobre el eje horizontal
    cut_trace(ax, [(-54, 0), (54, 0)], thick_len=8)
    for x in (-50, 50):
        view_arrow(ax, (x, 0.8), (x, 12), "A", (x + (-5 if x < 0 else 5), 9))
    # proyectantes grises de correspondencia
    for x in (-40, 40):
        L(ax, [(x, 44), (x, oy_alz - 2)], "thin", GREY, lw=0.5)
    # llamadas
    leader(ax, (62, -30), (44, -1.5), "traza del plano\n(gruesa en extremos)", fs=7.5)
    leader(ax, (60, 32), (51, 13), "flecha = dirección\nen que se mira", fs=7.5)
    leader(ax, (40, oy_alz + 62), (12, oy_alz + 60), "rótulo de la vista", fs=7.5)
    leader(ax, (56, oy_alz + 36), (15, oy_alz + 30), "sin aristas ocultas", fs=7.5)
    note(ax, -66, oy_alz + 25, "VISTA\nCORTADA", fs=7.5, color=K)
    note(ax, -66, -28, "PLANTA", fs=7.5, color=K)
    return save(fig, "apunte_10_indicacion_AA.png")


# =================================================================== FIG 11
def fig_total_vs_semicorte():
    fig, ax = setup((-60, 210), (-60, 144), 6.0)
    oy = 62
    for ox, kind in ((0, "total"), (140, "semi")):
        if kind == "total":
            p2_alzado_cortado(ax, ox, oy)
            ax.text(ox, oy + 60, "A-A", fontsize=11, ha="center", fontweight="bold")
        else:
            p2_alzado_cortado(ax, ox, oy, half="semi")
        p2_planta(ax, ox, 0)
        if kind == "total":
            cut_trace(ax, [(ox - 54, 0), (ox + 54, 0)], thick_len=8)
            for x in (-50, 50):
                view_arrow(ax, (ox + x, 0.8), (ox + x, 12), "A", (ox + x + (-5 if x < 0 else 5), 9))
        else:
            cut_trace(ax, [(ox + 54, 0), (ox, 0), (ox, -54)], thick_len=8)
            view_arrow(ax, (ox + 50, 0.8), (ox + 50, 12))
        note(ax, ox, oy + 76, "Corte total" if kind == "total" else "Semicorte",
             fs=9.5, ha="center", color=BLUE, weight="bold")
    leader(ax, (90, oy + 40), (140, oy + 45), "límite entre mitades:\neje (trazo y punto)", fs=7.2, ha="center")
    leader(ax, (85, oy - 20), (118, oy + 25), "mitad en vista:\nsin ocultas", fs=7.2, ha="center")
    note(ax, 140, -56, "Traza en L y una sola flecha", fs=7.2, ha="center")
    note(ax, 0, -56, "Traza completa con letras", fs=7.2, ha="center")
    return save(fig, "apunte_12_total_vs_semicorte.png")


# =================================================================== FIG 12
def fig_rayado():
    fig, ax = setup((-4, 176), (-20, 150), 5.2)
    base = unary_union([box(0, 0, 15, 20), box(25, 0, 40, 20)])
    rows = [
        ("45° uniforme", "paralelo a un borde"),
        ("separación constante", "separación irregular"),
        ("misma pieza, mismo rayado", "direcciones distintas\nen la misma pieza"),
        ("rayado hasta el contorno", "cruza el contorno\ne invade el hueco"),
    ]
    for i, (ok, bad) in enumerate(rows):
        y0 = 108 - i * 36
        for j, x0 in enumerate((20, 108)):
            from shapely import affinity
            g = affinity.translate(base, x0, y0)
            left = affinity.translate(box(0, 0, 15, 20), x0, y0)
            right = affinity.translate(box(25, 0, 40, 20), x0, y0)
            wrong = j == 1
            # contornos
            for bx in (left, right):
                pts = list(np.asarray(bx.exterior.coords))
                if wrong and i == 3:
                    L(ax, pts, "thin")
                else:
                    L(ax, pts, "vis")
            L(ax, [(x0 + 15, y0), (x0 + 25, y0)], "vis" if not (wrong and i == 3) else "thin")
            L(ax, [(x0 + 15, y0 + 20), (x0 + 25, y0 + 20)], "vis" if not (wrong and i == 3) else "thin")
            L(ax, [(x0 + 20, y0 - 4), (x0 + 20, y0 + 24)], "axis")
            if not wrong:
                hatch(ax, g, 45, 2.5)
            else:
                if i == 0:
                    hatch(ax, g, 0, 2.5)
                elif i == 1:
                    # separaciones irregulares
                    rng = np.random.default_rng(7)
                    offs, o = [], -40.0
                    while o < 40:
                        offs.append(o)
                        o += rng.choice([0.9, 1.6, 2.5, 3.8, 5.2])
                    hatch(ax, g, 45, offsets=offs)
                elif i == 2:
                    hatch(ax, left, 45, 2.5)
                    hatch(ax, right, 135, 2.5)
                elif i == 3:
                    big = box(x0 - 3, y0 - 2, x0 + 43, y0 + 22)
                    hatch(ax, big, 45, 2.5)
            label = bad if wrong else ok
            note(ax, x0 + 20, y0 - 9, label, fs=8.6, ha="center", color=BLUE if not wrong else RED)
            if wrong:
                red_x(ax, x0 + 50, y0 + 10, 3)
            else:
                ax.text(x0 + 50, y0 + 10, "✓", color=BLUE, fontsize=13, ha="center",
                        va="center", fontweight="bold")
    note(ax, 40, 144, "Correcto", fs=11, ha="center", weight="bold")
    note(ax, 128, 144, "Incorrecto", fs=11, ha="center", color=RED, weight="bold")
    return save(fig, "apunte_11_rayado.png")


# =================================================================== P3 geometría
def p3_outline(ax, ox, oy, keyway_line=True, top_gap=False):
    T = lambda pts: [(x + ox, y + oy) for x, y in pts]
    up = [(1, 15), (60, 15), (60, 20), (140, 20), (140, 15), (199, 15)]
    if top_gap:
        L(ax, T([(0, 14), (1, 15), (60, 15), (60, 20), (80, 20)]), "vis")
        L(ax, T([(120, 20), (140, 20), (140, 15), (199, 15), (200, 14)]), "vis")
    else:
        L(ax, T([(0, 14)] + up + [(200, 14)]), "vis")
    L(ax, T([(0, -14)] + [(x, -y) for x, y in up] + [(200, -14)]), "vis")
    L(ax, T([(0, -14), (0, 14)]), "vis")
    L(ax, T([(200, -14), (200, 14)]), "vis")
    for x in (1, 199):
        L(ax, T([(x, -15), (x, 15)]), "vis", lw=1.2)
    for x in (60, 140):
        L(ax, T([(x, -20), (x, 20)]), "vis")
    L(ax, T([(-5, 0), (205, 0)]), "axis")
    if keyway_line:
        zk = np.sqrt(400 - 36)  # 19,08: arista del chavetero vista de frente
        L(ax, T([(80, zk), (120, zk)]), "vis", lw=1.4)
        L(ax, T([(80, zk), (80, 20)]), "vis", lw=1.4)
        L(ax, T([(120, zk), (120, 20)]), "vis", lw=1.4)


def shaft_section_geom(c, r=20, kw=12, kd=5):
    cx, cy = c
    g = Point(cx, cy).buffer(r, resolution=96)
    g = g.difference(box(cx - kw / 2, cy + r - kd, cx + kw / 2, cy + r + 1))
    return g


def draw_shaft_section(ax, c, kind="vis", lw=None):
    g = shaft_section_geom(c)
    L(ax, np.asarray(g.exterior.coords), kind, lw=lw)
    hatch(ax, g, 45, 2.5)
    L(ax, [(c[0] - 25, c[1]), (c[0] + 25, c[1])], "axis")
    L(ax, [(c[0], c[1] - 25), (c[0], c[1] + 25)], "axis")


def fig_parcial_secciones():
    fig, ax = setup((-12, 300), (-186, 40), 6.3)
    # (a) corte parcial
    oy = 0
    p3_outline(ax, 0, oy, keyway_line=False, top_gap=True)
    L(ax, [(80, np.sqrt(364)), (120, np.sqrt(364))], "vis", lw=1.4)
    fl = freehand((72, 20), (72, 7), 0.5, 0.7, 40, seed=1)
    fb = freehand((72, 7), (128, 7), 0.9, 1.5, 60, seed=2)
    fr = freehand((128, 7), (128, 20), 0.5, 0.7, 40, seed=4)
    for f_ in (fl, fr):
        f_[0, 0] = f_[0, 0]; 
    fl[0] = (72, 20); fl[-1] = fb[0] = (72, 7); fb[-1] = fr[0] = (128, 7); fr[-1] = (128, 20)
    region = Polygon(np.vstack([fl, fb[1:], fr[1:], [(72, 20)]])).buffer(0)
    sect = box(60, -20, 140, 20).difference(box(80, 15, 120, 25))
    hatch(ax, region.intersection(sect), 45, 2.5)
    for f_ in (fl, fb, fr):
        L(ax, f_, "thin")
    # chavetero en el corte parcial: fondo y paredes
    L(ax, [(80, 20), (80, 15), (120, 15), (120, 20)], "vis")
    note(ax, 212, 8, "(a) Corte parcial:\nlímite a mano alzada", fs=7.5)
    leader(ax, (150, 30), (112, 15.5), "fondo del chavetero:\nse ve su profundidad", fs=7)
    # (b) sección abatida
    oy = -68
    p3_outline(ax, 0, oy)
    c = (100, oy)
    g = shaft_section_geom(c)
    # blanco debajo para no mezclar con líneas del eje
    L(ax, np.asarray(g.exterior.coords), "thin", lw=1.0)
    hatch(ax, g, 45, 2.5)
    L(ax, [(100, oy - 25), (100, oy + 25)], "axis")
    note(ax, 212, oy + 8, "(b) Sección abatida:\ncontorno fino, en su lugar,\nsin letras", fs=7.5)
    # (c) sección desplazada
    oy = -128
    p3_outline(ax, 0, oy)
    cut_trace(ax, [(100, oy + 30), (100, oy - 30)], thick_len=7)
    view_arrow(ax, (100.8, oy + 26), (88, oy + 26), "B", (91, oy + 31))
    view_arrow(ax, (100.8, oy - 26), (88, oy - 26), "B", (91, oy - 31))
    cs = (255, oy + 2)
    draw_shaft_section(ax, cs, "vis")
    ax.text(cs[0], cs[1] + 34, "B-B", fontsize=11, ha="center", va="center", fontweight="bold")
    note(ax, 212, oy - 40, "(c) Sección desplazada:\ncontorno grueso, fuera\nde la vista, rotulada", fs=7.5)
    return save(fig, "apunte_13_parcial_secciones.png")


# =================================================================== FIG 14
def fig_conjunto():
    fig, ax = setup((-72, 150), (-60, 62), 5.6)
    # árbol Ø40, x -55..55, con roturas a mano alzada en los extremos
    L(ax, [(-55, 20), (-20, 20)], "vis"); L(ax, [(20, 20), (30, 20)], "vis")
    L(ax, [(30, 20), (55, 20)], "vis")
    L(ax, [(-55, -20), (55, -20)], "vis")
    L(ax, freehand((-55, -20), (-55, 20), 1.2, 1.2, 60, seed=5), "thin")
    L(ax, freehand((55, -20), (55, 20), 1.2, 1.2, 60, seed=6), "thin")
    L(ax, [(-62, 0), (62, 0)], "axis")
    # chaveta 12 x 8 (sección longitudinal): x -20..20, z 15..23
    poly_outline(ax, [(-20, 15), (20, 15), (20, 23), (-20, 23)], "vis")
    # cubo/polea Ø100 / Ø40, ancho 40
    hub_top = box(-20, 23, 20, 50).union(box(-20, 20, -20, 23))
    hub_bot = box(-20, -50, 20, -20)
    for g in (hub_top, hub_bot):
        pass
    L(ax, [(-20, 23), (-20, 50), (20, 50), (20, 23)], "vis")
    poly_outline(ax, [(-20, -20), (-20, -50), (20, -50), (20, -20)], "vis")
    hatch(ax, box(-20, 23, 20, 50), 45, 2.5)
    hatch(ax, box(-20, -50, 20, -20), 45, 2.5)
    # casquillo Ø50/Ø40, ancho 10, x 20..30 -> rayado opuesto
    for g in (box(20, 20, 30, 25), box(20, -25, 30, -20)):
        poly_outline(ax, list(np.asarray(g.exterior.coords))[:-1], "vis")
        hatch(ax, g, 135, 2.0)
    leader(ax, (70, 44), (10, 36), "polea: rayado a 45°", fs=7.5)
    leader(ax, (70, 30), (27, 23), "casquillo: rayado opuesto", fs=7.5)
    leader(ax, (70, 12), (12, 19), "chaveta: sin rayar", fs=7.5)
    leader(ax, (70, -8), (42, -10), "árbol: sin rayar", fs=7.5)
    note(ax, -70, -57, "Ejes, chavetas, pernos y nervios no se rayan si el plano pasa a lo largo de ellos.",
         fs=7.5)
    return save(fig, "apunte_14_eje_en_conjunto.png")


# =================================================================== FIG 15
def s_break(x0, r, a, flip=False, n=60):
    """Rotura en S (convención tradicional) para cilindro macizo de radio r en x0.
    Devuelve (curva_simple, lazo_poligono). flip invierte arriba/abajo."""
    z = np.linspace(0, r, n)
    bump = np.sin(np.pi * z / r)
    sg = -1 if flip else 1
    # mitad con lazo
    outer = np.column_stack([x0 + a * bump, sg * z])
    inner = np.column_stack([x0 - 0.45 * a * bump, sg * z])
    loop = np.vstack([outer, inner[::-1]])
    simple = np.column_stack([x0 - a * bump, -sg * z])
    return outer, inner, simple, loop


def fig_roturas_simetria():
    fig, ax = setup((-8, 250), (-150, 34), 6.2)
    R = 15
    # (a) variante ISO: mano alzada
    for row, oy in enumerate((0, -52)):
        xa, xb = 0, 180
        g1, g2 = 80, 96  # fin del tramo izquierdo / inicio del derecho
        L(ax, [(xa, oy - R), (xa, oy + R)], "vis")
        L(ax, [(xb, oy - R), (xb, oy + R)], "vis")
        for s in (1, -1):
            L(ax, [(xa, oy + s * R), (g1, oy + s * R)], "vis")
            L(ax, [(g2, oy + s * R), (xb, oy + s * R)], "vis")
        L(ax, [(xa - 5, oy), (g1 + 4, oy)], "axis")
        L(ax, [(g2 - 4, oy), (xb + 5, oy)], "axis")
        if row == 0:
            L(ax, freehand((g1, oy - R), (g1, oy + R), 1.3, 1.0, 50, seed=8), "thin")
            L(ax, freehand((g2, oy - R), (g2, oy + R), 1.3, 1.0, 50, seed=9), "thin")
            note(ax, 192, oy + 4, "Mano alzada\n(ISO 128-3)", fs=7.5)
        else:
            for x0, flip in ((g1, False), (g2, True)):
                outer, inner, simple, loop = s_break(x0, R, 5.5, flip)
                off = np.array([0, oy])
                L(ax, outer + off, "thin", lw=1.0)
                L(ax, inner + off, "thin", lw=1.0)
                L(ax, simple + off, "thin", lw=1.0)
                hatch(ax, Polygon(loop + off), 45, 1.4, lw=0.5)
            note(ax, 192, oy + 4, "Rotura en S\n(convención\ntradicional)", fs=7.5)
        dim(ax, (xa, oy + R + 8), (xb, oy + R + 8), "600", fs=8)
        ext_line(ax, (xa, oy + R + 1), (xa, oy + R + 11))
        ext_line(ax, (xb, oy + R + 1), (xb, oy + R + 11))
    note(ax, 0, -80, "(a) Eje Ø30 × 600 acortado: se acota la longitud real y la línea de cota no se corta.",
         fs=7.3)
    # (c) placa simétrica dibujada a medias
    ox, oy = 60, -118
    L(ax, [(ox, oy - 20), (ox + 40, oy - 20), (ox + 40, oy + 20), (ox, oy + 20)], "vis")
    L(ax, [(ox, oy - 27), (ox, oy + 27)], "axis")
    for s in (1, -1):
        yy = oy + s * 24
        for dx in (-1.3, 1.3):
            pass
        L(ax, [(ox - 3, yy - 1.2), (ox + 3, yy - 1.2)], "thin", lw=1.0)
        L(ax, [(ox - 3, yy + 1.2), (ox + 3, yy + 1.2)], "thin", lw=1.0)
    circle(ax, (ox + 20, oy), 5)
    centermarks(ax, (ox + 20, oy), 5, 4)
    leader(ax, (ox + 60, oy + 18), (ox + 3.5, oy + 24), "símbolo de simetría:\ndos trazos cortos paralelos", fs=7.3)
    note(ax, ox + 60, oy - 8, "(b) Placa 80 × 40 simétrica,\ndibujada solo hasta su eje", fs=7.3)
    return save(fig, "apunte_15_roturas_simetria.png")


FIGS = [fig_cajetin, fig_lamina, fig_por_que_auxiliar, fig_auxiliar_pasos,
        fig_que_es_cortar, fig_indicacion_AA, fig_total_vs_semicorte, fig_rayado,
        fig_parcial_secciones, fig_conjunto, fig_roturas_simetria]

if __name__ == "__main__":
    import sys
    sel = sys.argv[1:]
    for f in FIGS:
        if not sel or any(s in f.__name__ for s in sel):
            print(f())
