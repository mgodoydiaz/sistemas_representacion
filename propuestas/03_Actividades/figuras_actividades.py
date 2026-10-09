"""Figuras de las Actividades 6 (Cortes) y 7 (Isometrico), PCI 1119.

Todas las vistas, cortes e isometricos se calculan desde la geometria 3D de cada
pieza (primitivas Box / Cyl / Prism sumadas y restadas). Las aristas se clasifican
como visibles u ocultas por trazado de rayos hacia el observador, de modo que
vistas e isometricos son coherentes entre si.

Sistema de la pieza: x = ancho (derecha), y = profundidad (hacia atras), z = alto.
Vistas en primer diedro (ISO-E): alzado desde el frente, planta debajo del alzado,
lateral izquierda a la derecha del alzado.

Uso:  python3 figuras_actividades.py [filtro]
Salida: figuras/*.png (300 dpi) y figuras/*.svg (figuras de enunciado).
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString, Point, box as sbox
from shapely.ops import unary_union, linemerge
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from shapely.ops import transform as stransform
warnings.filterwarnings('ignore', category=DeprecationWarning)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import helpers_apunte_v3 as H          # copia sin modificar de figuras_apunte_v3.py
from helpers_apunte_v3 import (setup, L, arc, circle, hatch, leader, note,
                               view_arrow, cut_trace, K, BLUE, GREY)

OUT = os.path.join(HERE, "figuras")
os.makedirs(OUT, exist_ok=True)

LW_VIS = 1.4      # gruesa
LW_THIN = 0.6     # fina (cotas, rayado, ejes)
LW_HID = 0.8      # ocultas
STEP = 0.2        # paso de muestreo de aristas (mm)
EPS = 0.02
TOL = 0.04


def save(fig, name, svg=False):
    path = os.path.join(OUT, name + ".png")
    fig.savefig(path, dpi=300, facecolor="white")
    if svg:
        fig.savefig(os.path.join(OUT, name + ".svg"), facecolor="white")
    plt.close(fig)
    return path


# =============================================================== primitivas 3D
def _others(a):
    return [i for i in range(3) if i != a]


def _rect(ax1, r1, ax2, r2):
    """Rectangulo shapely en el plano de dos ejes, ordenados por indice."""
    if ax1 > ax2:
        ax1, r1, ax2, r2 = ax2, r2, ax1, r1
    return sbox(r1[0], r2[0], r1[1], r2[1])


def _seg(p, q):
    p, q = np.asarray(p, float), np.asarray(q, float)
    n = max(2, int(np.linalg.norm(q - p) / STEP) + 1)
    return p + np.outer(np.linspace(0, 1, n), q - p)


class Box:
    def __init__(self, x, y, z, nohatch=False):
        self.lo = np.array([x[0], y[0], z[0]], float)
        self.hi = np.array([x[1], y[1], z[1]], float)
        self.nohatch = nohatch

    def inside(self, P, tol=0.0):
        return np.all((P >= self.lo + tol) & (P <= self.hi - tol), axis=1)

    def edges(self):
        lo, hi = self.lo, self.hi
        out = []
        for a in range(3):
            b, c = _others(a)
            for vb in (lo[b], hi[b]):
                for vc in (lo[c], hi[c]):
                    p = np.zeros(3); q = np.zeros(3)
                    p[a], q[a] = lo[a], hi[a]
                    p[b] = q[b] = vb
                    p[c] = q[c] = vc
                    out.append(_seg(p, q))
        return out

    def silhouettes(self, d):
        return []

    def section(self, k, val):
        if not (self.lo[k] < val < self.hi[k]):
            return None
        b, c = _others(k)
        return _rect(b, (self.lo[b], self.hi[b]), c, (self.lo[c], self.hi[c]))


class Cyl:
    """Cilindro de eje paralelo a un eje coordenado. base = punto del eje en el
    extremo inicial; h = largo en el sentido positivo del eje."""
    def __init__(self, axis, base, h, r, nohatch=False):
        self.a = "xyz".index(axis)
        self.base = np.array(base, float)
        self.h, self.r = float(h), float(r)
        self.nohatch = nohatch

    def inside(self, P, tol=0.0):
        a = self.a
        b, c = _others(a)
        rr = np.hypot(P[:, b] - self.base[b], P[:, c] - self.base[c])
        t = P[:, a] - self.base[a]
        return (rr <= self.r - tol) & (t >= tol) & (t <= self.h - tol)

    def _ring(self, t):
        a = self.a
        b, c = _others(a)
        n = max(24, int(2 * np.pi * self.r / STEP))
        q = np.linspace(0, 2 * np.pi, n + 1)
        P = np.zeros((n + 1, 3))
        P[:, a] = self.base[a] + t
        P[:, b] = self.base[b] + self.r * np.cos(q)
        P[:, c] = self.base[c] + self.r * np.sin(q)
        return P

    def edges(self):
        return [self._ring(0.0), self._ring(self.h)]

    def silhouettes(self, d):
        ax = np.zeros(3); ax[self.a] = 1.0
        n = np.cross(ax, d)
        if np.linalg.norm(n) < 1e-9:
            return []
        n /= np.linalg.norm(n)
        out = []
        for s in (-1, 1):
            p = self.base + s * self.r * n
            out.append(_seg(p, p + ax * self.h))
        return out

    def section(self, k, val):
        a = self.a
        if k == a:
            if not (self.base[a] < val < self.base[a] + self.h):
                return None
            b, c = _others(a)
            return Point(self.base[b], self.base[c]).buffer(self.r, 96)
        dd = val - self.base[k]
        if abs(dd) >= self.r:
            return None
        m = [i for i in range(3) if i not in (a, k)][0]
        half = np.sqrt(self.r ** 2 - dd ** 2)
        return _rect(a, (self.base[a], self.base[a] + self.h),
                     m, (self.base[m] - half, self.base[m] + half))


class Prism:
    """Prisma recto de base poligonal CONVEXA (sentido antihorario), extruido a lo
    largo de un eje. poly en los otros dos ejes, ordenados por indice."""
    def __init__(self, axis, poly, a0, a1, nohatch=False):
        self.a = "xyz".index(axis)
        self.poly = np.array(poly, float)
        self.a0, self.a1 = float(a0), float(a1)
        self.nohatch = nohatch

    def inside(self, P, tol=0.0):
        a = self.a
        b, c = _others(a)
        ok = (P[:, a] >= self.a0 + tol) & (P[:, a] <= self.a1 - tol)
        n = len(self.poly)
        for i in range(n):
            p, q = self.poly[i], self.poly[(i + 1) % n]
            e = (q - p) / np.linalg.norm(q - p)
            cr = e[0] * (P[:, c] - p[1]) - e[1] * (P[:, b] - p[0])
            ok &= cr >= tol
        return ok

    def _p3(self, uv, t):
        b, c = _others(self.a)
        p = np.zeros(3)
        p[self.a], p[b], p[c] = t, uv[0], uv[1]
        return p

    def edges(self):
        out = []
        n = len(self.poly)
        for i in range(n):
            p, q = self.poly[i], self.poly[(i + 1) % n]
            for t in (self.a0, self.a1):
                out.append(_seg(self._p3(p, t), self._p3(q, t)))
            out.append(_seg(self._p3(p, self.a0), self._p3(p, self.a1)))
        return out

    def silhouettes(self, d):
        return []

    def section(self, k, val):
        a = self.a
        if k == a:
            if not (self.a0 < val < self.a1):
                return None
            return Polygon(self.poly)
        b, c = _others(a)
        pg = Polygon(self.poly)
        minx, miny, maxx, maxy = pg.bounds
        if k == b:
            ln = LineString([(val, miny - 1), (val, maxy + 1)])
            idx, m = 1, c
        else:
            ln = LineString([(minx - 1, val), (maxx + 1, val)])
            idx, m = 0, b
        it = ln.intersection(pg)
        if it.is_empty or it.geom_type != "LineString":
            return None
        cs = np.asarray(it.coords)[:, idx]
        if cs.max() - cs.min() < 1e-9:
            return None
        return _rect(a, (self.a0, self.a1), m, (cs.min(), cs.max()))


class Solid:
    def __init__(self, adds, subs=(), extra=(), axes=(), name=""):
        self.adds, self.subs = list(adds), list(subs)
        self.extra = [np.asarray(e, float) for e in extra]
        self.axes = list(axes)        # [(p0, p1, r)] ejes de revolucion
        self.name = name

    def inside(self, P, clip=None):
        ok = np.zeros(len(P), bool)
        for s in self.adds:
            ok |= s.inside(P)
        for s in self.subs:
            ok &= ~s.inside(P)
        if clip is not None:
            k, val, sg = clip
            ok &= sg * (P[:, k] - val) >= 0
        return ok

    def deep(self, P, tol, clip=None):
        """True si P esta dentro del material a mas de tol de cualquier superficie
        (erosion aproximada con 6 vecinos). Evita falsos huecos en las caras de
        contacto entre primitivas sumadas."""
        ok = self.inside(P, clip)
        for a in range(3):
            for sg in (-tol, tol):
                if not ok.any():
                    return ok
                Q = P[ok].copy()
                Q[:, a] += sg
                ok[np.where(ok)[0]] = self.inside(Q, clip)
        return ok

    def candidates(self, d):
        out = []
        for s in self.adds + self.subs:
            out += [(e, False) for e in s.edges()]
            out += [(e, True) for e in s.silhouettes(d)]
        out += [(e, True) for e in self.extra]
        return out

    def section(self, k, val, hatch_only=False):
        adds = [s.section(k, val) for s in self.adds
                if not (hatch_only and s.nohatch)]
        subs = [s.section(k, val) for s in self.subs]
        g = unary_union([a for a in adds if a is not None])
        v = [s for s in subs if s is not None]
        if v:
            g = g.difference(unary_union(v))
        return g

    def bounds(self):
        lo = np.min([getattr(s, "lo", None) if isinstance(s, Box) else _bb(s)[0]
                     for s in self.adds], axis=0)
        hi = np.max([getattr(s, "hi", None) if isinstance(s, Box) else _bb(s)[1]
                     for s in self.adds], axis=0)
        return lo, hi


def _bb(s):
    pts = np.vstack(s.edges())
    return pts.min(axis=0), pts.max(axis=0)


# ==================================================================== vistas
S2, S3, S6 = np.sqrt(2), np.sqrt(3), np.sqrt(6)
ISO_K = np.sqrt(1.5)     # dibujo isometrico: medidas reales sobre los ejes


class View:
    """right, up: vectores de pantalla; tov: hacia el observador."""
    def __init__(self, kind, ox=0.0, oy=0.0):
        self.kind = kind
        if kind == "front":
            r, u = (1, 0, 0), (0, 0, 1)
        elif kind == "top":
            r, u = (1, 0, 0), (0, 1, 0)
        elif kind == "left":
            r, u = (0, -1, 0), (0, 0, 1)
        elif kind == "iso":        # observador delante, a la izquierda y arriba
            r = np.array((1, -1, 0)) / S2 * ISO_K
            u = np.array((1, 1, 2)) / S6 * ISO_K
        self.r, self.u = np.array(r, float), np.array(u, float)
        self.tov = np.cross(self.r, self.u)
        self.tov /= np.linalg.norm(self.tov)
        self.o = np.array([ox, oy], float)

    def p(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        return np.column_stack([P @ self.r, P @ self.u]) + self.o

    def pt(self, x, y, z):
        return tuple(self.p([(x, y, z)])[0])


def _real_mask(solid, P, sil, clip):
    """True donde el punto de la polilinea es arista real (o superficie, si sil)."""
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    ref = np.array([0.36, 0.48, 0.8])
    e1 = np.cross(T, ref)
    e1 /= np.linalg.norm(e1, axis=1)[:, None]
    e2 = np.cross(T, e1)
    N = 16
    ang = np.radians(7.3) + np.arange(N) * 2 * np.pi / N
    cnt = np.zeros(len(P), int)
    for q in ang:
        cnt += solid.inside(P + EPS * (np.cos(q) * e1 + np.sin(q) * e2), clip)
    if sil:
        return (cnt > 0) & (cnt < N)
    return (cnt > 0) & (cnt < N) & (np.abs(cnt - N // 2) > 1)


def _visible_mask(solid, P, tov, clip, Lmax):
    hid = np.zeros(len(P), bool)
    s = np.arange(0.12, Lmax, 0.2)
    for i in range(0, len(s), 40):
        idx = np.where(~hid)[0]
        if len(idx) == 0:
            break
        ss = s[i:i + 40]
        Q = (P[idx][:, None, :] + ss[None, :, None] * tov[None, None, :]).reshape(-1, 3)
        ins = solid.deep(Q, TOL, clip).reshape(len(idx), len(ss)).any(axis=1)
        hid[idx[ins]] = True
    return ~hid


_CACHE = {}


def classify(solid, V, clip=None):
    """Devuelve (visibles, ocultas): listas de polilineas 2D en coords de la vista
    SIN desplazar (origen 0)."""
    key = (solid.name, V.kind, clip)
    if key in _CACHE:
        return _CACHE[key]
    lo, hi = solid.bounds()
    Lmax = np.linalg.norm(hi - lo) + 2
    vis, hid = [], []
    V0 = View(V.kind)
    for P, sil in solid.candidates(V.tov):
        if clip is not None:
            k, val, sg = clip
            P = P[sg * (P[:, k] - val) > 1e-6]
            if len(P) < 3:
                continue
        if len(P) < 3:
            continue
        real = _real_mask(solid, P, sil, clip)
        if not real.any():
            continue
        v = np.zeros(len(P), bool)
        v[real] = _visible_mask(solid, P[real], V.tov, clip, Lmax)
        state = np.where(~real, 0, np.where(v, 1, 2))
        # corta tambien donde hay saltos (por el recorte)
        jump = np.r_[False, np.linalg.norm(np.diff(P, axis=0), axis=1) > 3 * STEP + 0.5]
        start = 0
        for i in range(1, len(P) + 1):
            if i == len(P) or state[i] != state[start] or jump[i]:
                if state[start] != 0 and i - start >= 2:
                    q = V0.p(P[start:i])
                    if np.linalg.norm(q.max(axis=0) - q.min(axis=0)) > (1.5 if sil else 0.3):
                        (vis if state[start] == 1 else hid).append(q)
                start = i
    _CACHE[key] = (vis, hid)
    return vis, hid


def _draw_lines(ax, geom, kind, lw, z, color=K):
    if geom.is_empty:
        return
    lines = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "LineString"]
    if not lines:
        return
    geom = linemerge(lines) if len(lines) > 1 else lines[0]
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type == "LineString" and g.length > 0.25:
            L(ax, np.asarray(g.coords), kind, color, z, lw)


def _simplify(q):
    return unary_union([LineString(q).simplify(0.01)])   # disuelve tramos repetidos


def draw_view(ax, solid, V, hidden=True, clip=None, region=None, lw=LW_VIS,
              axes=True, axis_ext=4, color=K):
    """Dibuja la vista V del solido. region: poligono shapely (coords de pantalla)
    que limita lo que se dibuja (para el semicorte)."""
    vis, hid = classify(solid, V, clip)
    off = lambda q: q + V.o
    vlines = [_simplify(off(q)) for q in vis]
    cover = unary_union([l.buffer(0.18, 4) for l in vlines]) if vlines else Polygon()
    for l in vlines:
        g = l if region is None else l.intersection(region)
        _draw_lines(ax, g, "vis", lw, 4, color)
    if hidden:
        for q in hid:
            l = _simplify(off(q)).difference(cover)
            if region is not None:
                l = l.intersection(region)
            if l.is_empty:
                continue
            _draw_lines(ax, l, "hid", LW_HID, 3, color)
            cover = cover.union(l.buffer(0.18, 4))
    if axes:
        draw_axes(ax, solid, V, axis_ext, region)


def draw_axes(ax, solid, V, ext=4, region=None, only=None):
    for i, (p0, p1, r) in enumerate(solid.axes):
        if only is not None and i not in only:
            continue
        a, b = V.p([p0])[0], V.p([p1])[0]
        if np.linalg.norm(b - a) < 1e-6:
            e = r + ext
            segs = [[(a[0] - e, a[1]), (a[0] + e, a[1])],
                    [(a[0], a[1] - e), (a[0], a[1] + e)]]
        else:
            d = (b - a) / np.linalg.norm(b - a)
            segs = [[a - d * ext, b + d * ext]]
        for s in segs:
            g = LineString(s)
            if region is not None:
                g = g.intersection(region)
            _draw_lines(ax, g, "axis", LW_THIN, 2)


def draw_section(ax, solid, V, plane, region=None, sp=2.6, lw=LW_VIS, hidden=False,
                 axes=True, axis_ext=4, angle=45):
    """Vista cortada: contorno de la seccion, rayado y aristas visibles detras del
    plano. plane = (indice_eje, valor). Los solidos nohatch (nervios) no se rayan."""
    k, val = plane
    sg = -1 if V.tov[k] > 0 else 1          # se conserva el lado alejado del observador
    clip = (k, val, sg)
    b, c = _others(k)

    def to2d(u, w):
        P = np.zeros((np.size(u), 3))
        P[:, k], P[:, b], P[:, c] = val, np.ravel(u), np.ravel(w)
        q = V.p(P)
        return q[:, 0], q[:, 1]

    full = stransform(to2d, solid.section(k, val))
    mat = stransform(to2d, solid.section(k, val, hatch_only=True))
    if region is not None:
        full, mat = full.intersection(region), mat.intersection(region)
    hatch(ax, mat, angle=angle, sp=sp, lw=0.55, z=2)
    for g in (full, mat):
        bd = g.boundary
        if region is not None:       # no dibujar el limite artificial del semicorte
            bd = bd.difference(region.boundary.buffer(0.05))
        _draw_lines(ax, bd, "vis", lw, 5)
    draw_view(ax, solid, V, hidden=hidden, clip=clip, region=region, lw=lw,
              axes=axes, axis_ext=axis_ext)
    return full, mat


# ====================================================================== cotas
ARROW = "<|-|>,head_length=0.42,head_width=0.13"


def _dimline(ax, p0, p1, color):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ln = np.linalg.norm(p1 - p0)
    if ln < 8:          # cota pequena: flechas por fuera
        u = (p1 - p0) / ln
        kw = dict(arrowstyle="-|>,head_length=0.42,head_width=0.13", lw=LW_THIN,
                  color=color, shrinkA=0, shrinkB=0)
        ax.annotate("", xy=p0, xytext=p0 - u * 6, arrowprops=kw, zorder=6)
        ax.annotate("", xy=p1, xytext=p1 + u * 6, arrowprops=kw, zorder=6)
        L(ax, [p0, p1], "thin", color, 6, LW_THIN)
        return
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle=ARROW, lw=LW_THIN, color=color,
                                shrinkA=0, shrinkB=0), zorder=6)


def _txt(ax, x, y, s, fs, color, rot=0, ha="center", va="center"):
    ax.text(x, y, s, color=color, fontsize=fs, ha=ha, va=va, rotation=rot, zorder=7,
            bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none"))


def hdim(ax, x0, x1, y, text, yfrom=None, fs=7, color=K, tx=None):
    """Cota horizontal a la altura y. yfrom: de donde nacen las lineas auxiliares
    (escalar o par). tx: posicion x del texto si no va centrado."""
    if yfrom is not None:
        yf = (yfrom, yfrom) if np.isscalar(yfrom) else yfrom
        sgn = 1 if y > yf[0] else -1
        for x, f in ((x0, yf[0]), (x1, yf[1])):
            L(ax, [(x, f + sgn * 0.8), (x, y + sgn * 1.5)], "thin", color, 5, LW_THIN)
    _dimline(ax, (x0, y), (x1, y), color)
    _txt(ax, (x0 + x1) / 2 if tx is None else tx, y, text, fs, color)
    if tx is not None and not (min(x0, x1) <= tx <= max(x0, x1)):
        xe = x1 if abs(tx - x1) < abs(tx - x0) else x0
        L(ax, [(xe, y), (tx, y)], "thin", color, 5, LW_THIN)


def vdim(ax, y0, y1, x, text, xfrom=None, fs=7, color=K, ty=None):
    if xfrom is not None:
        xf = (xfrom, xfrom) if np.isscalar(xfrom) else xfrom
        sgn = 1 if x > xf[0] else -1
        for y, f in ((y0, xf[0]), (y1, xf[1])):
            L(ax, [(f + sgn * 0.8, y), (x + sgn * 1.5, y)], "thin", color, 5, LW_THIN)
    _dimline(ax, (x, y0), (x, y1), color)
    _txt(ax, x, (y0 + y1) / 2 if ty is None else ty, text, fs, color, rot=90)
    if ty is not None and not (min(y0, y1) <= ty <= max(y0, y1)):
        ye = y1 if abs(ty - y1) < abs(ty - y0) else y0
        L(ax, [(x, ye), (x, ty)], "thin", color, 5, LW_THIN)


def lead(ax, xy_text, xy_pt, s, fs=7, ha="left", color=K, va="center"):
    """Linea de referencia con flecha (para diametros de agujeros)."""
    ax.annotate(s, xy=xy_pt, xytext=xy_text, color=color, fontsize=fs, ha=ha, va=va,
                zorder=8, bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"),
                arrowprops=dict(arrowstyle="-|>,head_length=0.42,head_width=0.13",
                                lw=LW_THIN, color=color, shrinkA=1.5, shrinkB=0))


def label(ax, x, y, s, fs=7.5, color=K, ha="center", weight="normal"):
    ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va="center", zorder=8,
            fontweight=weight)


def trace_arrow(ax, p, d, letter=None, lpos=None, alen=11, fs=10):
    p, d = np.asarray(p, float), np.asarray(d, float)
    view_arrow(ax, tuple(p + d * 0.8), tuple(p + d * alen), letter, lpos, fs)


# ===================================================================== PIEZAS
# ---------------------------------------------------------------- A6-1: buje
def buje():
    holes = [Cyl("z", (30 * np.cos(a), 30 * np.sin(a), 0), 15, 5)
             for a in np.radians([0, 90, 180, 270])]
    axes = [((0, 0, 0), (0, 0, 50), 20)]
    axes += [((30 * np.cos(a), 30 * np.sin(a), 0), (30 * np.cos(a), 30 * np.sin(a), 15), 5)
             for a in np.radians([0, 90, 180, 270])]
    return Solid([Cyl("z", (0, 0, 0), 15, 40), Cyl("z", (0, 0, 15), 35, 20)],
                 [Cyl("z", (0, 0, 0), 50, 10)] + holes, axes=axes, name="buje")


# ------------------------------------------------------------- A6-2: soporte
SN = dict(L=100, W=40, e=10, Dc=30, H=45, d=16, dh=8, sh=84, rib_t=6, rib_foot=70,
          rib_h=40)


def soporte_nervio():
    g = SN
    hl, hw = g["L"] / 2, g["W"] / 2
    rc = g["Dc"] / 2
    xf = g["rib_foot"] / 2
    slope = (g["rib_h"] - g["e"]) / (xf - rc)          # pendiente del nervio
    xi = rc - 2                                        # enterrado en el cilindro
    zi = g["rib_h"] + slope * 2
    t = g["rib_t"] / 2
    ribs = [Prism("y", [(xi, g["e"]), (xf, g["e"]), (xi, zi)], -t, t, nohatch=True),
            Prism("y", [(-xi, g["e"]), (-xi, zi), (-xf, g["e"])], -t, t, nohatch=True)]
    hx = g["sh"] / 2
    adds = [Box((-hl, hl), (-hw, hw), (0, g["e"])),
            Cyl("z", (0, 0, g["e"]), g["H"] - g["e"], rc)] + ribs
    subs = [Cyl("z", (0, 0, 0), g["H"], g["d"] / 2),
            Cyl("z", (-hx, 0, 0), g["e"], g["dh"] / 2),
            Cyl("z", (hx, 0, 0), g["e"], g["dh"] / 2)]
    axes = [((0, 0, 0), (0, 0, g["H"]), rc),
            ((-hx, 0, 0), (-hx, 0, g["e"]), g["dh"] / 2),
            ((hx, 0, 0), (hx, 0, g["e"]), g["dh"] / 2)]
    # encuentro de los nervios con el cilindro (no son aristas de ninguna primitiva)
    zs = lambda x: g["e"] + slope * (xf - abs(x))
    extra = []
    xs = np.sqrt(rc ** 2 - t ** 2)
    yy = np.linspace(-t, t, 40)
    for sx in (-1, 1):
        for sy in (-1, 1):
            extra.append(_seg((sx * xs, sy * t, g["e"]), (sx * xs, sy * t, zs(xs))))
        xa = sx * np.sqrt(rc ** 2 - yy ** 2)
        extra.append(np.column_stack([xa, yy, zs(xa)]))
    return Solid(adds, subs, extra=extra, axes=axes, name="soporte_nervio")


# ------------------------------------------------------------- A6-3: valvula
VA = dict(Ltot=140, Df=70, ef=12, Dn=36, Db=50, Lb=60, Dc=20, Dch=30, Lch=40,
          Hn=45, Hf=55, Dbf=70)


def _inter_eq(R, n=400):
    """Interseccion de dos cilindros perpendiculares de igual radio R (eje x y eje
    z, z >= 0): dos semielipses planas en x = +z y x = -z."""
    t = np.radians(np.linspace(-89.9, 89.9, n))
    out = []
    for s in (-1, 1):
        out.append(np.column_stack([s * R * np.cos(t), R * np.sin(t), R * np.cos(t)]))
    return out


def valvula():
    g = VA
    hl = g["Ltot"] / 2
    adds = [Cyl("x", (-hl, 0, 0), g["ef"], g["Df"] / 2),
            Cyl("x", (hl - g["ef"], 0, 0), g["ef"], g["Df"] / 2),
            Cyl("x", (-hl + g["ef"], 0, 0), g["Ltot"] - 2 * g["ef"], g["Dn"] / 2),
            Cyl("x", (-g["Lb"] / 2, 0, 0), g["Lb"], g["Db"] / 2),
            Cyl("z", (0, 0, 0), g["Hn"], g["Db"] / 2),
            Cyl("z", (0, 0, g["Hn"]), g["Hf"] - g["Hn"], g["Dbf"] / 2)]
    subs = [Cyl("x", (-hl, 0, 0), g["Ltot"], g["Dc"] / 2),
            Cyl("x", (-g["Lch"] / 2, 0, 0), g["Lch"], g["Dch"] / 2),
            Cyl("z", (0, 0, 0), g["Hf"], g["Dch"] / 2)]
    extra = _inter_eq(g["Db"] / 2) + _inter_eq(g["Dch"] / 2)
    axes = [((-hl, 0, 0), (hl, 0, 0), g["Df"] / 2),
            ((0, 0, -g["Db"] / 2), (0, 0, g["Hf"]), g["Dbf"] / 2)]
    return Solid(adds, subs, extra=extra, axes=axes, name="valvula")


# --------------------------------------------------------- A7-1: escalonada
def escalonada():
    return Solid([Box((0, 60), (0, 40), (0, 10)),
                  Box((20, 60), (0, 40), (10, 25)),
                  Box((40, 60), (20, 40), (25, 40))], name="escalonada")


# ------------------------------------------------------ A7-2: plano inclinado
def cuna():
    return Solid([Box((0, 60), (0, 40), (0, 15)),
                  Prism("y", [(5, 15), (60, 15), (60, 40), (35, 40)], 0, 40)],
                 [Box((0, 60), (10, 30), (30, 40))],
                 extra=[_seg((23, 10, 30), (23, 30, 30)),
                        _seg((23, 10, 30), (35, 10, 40)),
                        _seg((23, 30, 30), (35, 30, 40))], name="cuna")


# ----------------------------------------- A7-3: soporte respaldo redondeado
# Geometria del profesor: X ancho, Y profundidad (respaldo al fondo, Y 0..10), Z alto.
# En este script y crece hacia atras, por lo que y = 60 - Y.
def soporte_respaldo():
    adds = [Box((0, 40), (0, 60), (0, 10)),
            Box((0, 40), (50, 60), (10, 30)),
            Cyl("y", (20, 50, 30), 10, 20)]
    subs = [Cyl("z", (20, 20, 0), 10, 5),
            Cyl("y", (20, 50, 30), 10, 10)]
    axes = [((20, 20, 0), (20, 20, 10), 5), ((20, 50, 30), (20, 60, 30), 20)]
    return Solid(adds, subs, axes=axes, name="soporte_respaldo")


# ==================================================================== FIGURAS
def vlabel(ax, x, y, s):
    ax.text(x, y, s, fontsize=6.5, color="#444444", ha="center", va="center",
            fontstyle="italic", zorder=8)


def bnote(ax, xy_text, xy_pt, s, ha="left", fs=7):
    leader(ax, xy_text, xy_pt, s, fs=fs, ha=ha, color=BLUE)


def pitch_circle(ax, V, r=30):
    c = V.pt(0, 0, 0)
    L(ax, arc(c, r, 0, 360, 240), "axis", lw=LW_THIN, z=2)


# ----------------------------------------------------------------- A6 - Ej. 1
def _a6_1_base(ax, cut):
    s = buje()
    Vf, Vt = View("front"), View("top", 0, -62)
    if cut:
        draw_section(ax, s, Vf, (1, 0.0))
    else:
        draw_view(ax, s, Vf)
    draw_view(ax, s, Vt)
    pitch_circle(ax, Vt)
    return s, Vf, Vt


def fig_a6_1():
    fig, ax = setup((-72, 78), (-120, 68), 2.8)
    _a6_1_base(ax, False)
    vdim(ax, 0, 50, -52, "50", xfrom=(-40, -20))
    vdim(ax, 0, 15, 50, "15", xfrom=40)
    hdim(ax, -20, 20, 58, "Ø40", yfrom=50)
    hdim(ax, -40, 40, -110, "Ø80", yfrom=-62)
    lead(ax, (30, -22), (30 * np.cos(np.radians(52)), -62 + 30 * np.sin(np.radians(52))), "Ø60")
    lead(ax, (47, -98), (30 + 5 * np.cos(np.radians(-50)), -62 + 5 * np.sin(np.radians(-50))),
         "4 × Ø10")
    lead(ax, (-64, -98), (-10 * np.cos(np.radians(40)), -62 - 10 * np.sin(np.radians(40))),
         "Ø20", ha="left")
    vlabel(ax, -60, 58, "Alzado")
    vlabel(ax, -60, -24, "Planta")
    return save(fig, "A6_ej1_buje", svg=True)


def fig_a6_1_sol():
    fig, ax = setup((-82, 118), (-112, 72), 4.6)
    _a6_1_base(ax, True)
    ax.text(0, 62, "A-A", fontsize=11, ha="center", va="center", fontweight="bold")
    cut_trace(ax, [(-54, -62), (54, -62)], thick_len=8)
    for x in (-50, 50):
        trace_arrow(ax, (x, -62), (0, 1), "A", (x + (-5 if x < 0 else 5), -53))
    bnote(ax, (56, 60), (13, 62), "C3: rótulo A-A")
    bnote(ax, (56, 38), (15, 34), "C4: rayado fino a 45°,\nsolo material cortado")
    bnote(ax, (56, 18), (30, 8), "C5: sin ocultas;\nagujeros en blanco")
    bnote(ax, (60, -30), (51, -50), "C2: flechas hacia\ndonde se mira")
    bnote(ax, (60, -84), (45, -63.5), "C1, C2: traza por el eje,\ngruesa en los extremos")
    bnote(ax, (-80, 34), (0, 40), "eje sin\nrayar", ha="left")
    return save(fig, "A6_ej1_buje_solucion")


# ----------------------------------------------------------------- A6 - Ej. 2
def fig_a6_2():
    fig, ax = setup((-72, 76), (-94, 62), 3.9)
    s = soporte_nervio()
    Vf, Vt = View("front"), View("top", 0, -45)
    draw_view(ax, s, Vf)
    draw_view(ax, s, Vt)
    vdim(ax, 0, 10, -57, "10", xfrom=-50, ty=-6)
    vdim(ax, 0, 45, -65, "45", xfrom=(-50, -15))
    vdim(ax, 0, 40, 60, "40", xfrom=(50, 15))
    hdim(ax, -8, 8, 51, "Ø16", yfrom=45, tx=-17)
    hdim(ax, -15, 15, 57, "Ø30", yfrom=45)
    hdim(ax, -35, 35, -72, "70", yfrom=-48)
    hdim(ax, -42, 42, -79, "84", yfrom=-45)
    hdim(ax, -50, 50, -86, "100", yfrom=-65)
    vdim(ax, -65, -25, 58, "40", xfrom=50)
    vdim(ax, -48, -42, -25, "6", xfrom=None, ty=-32)
    lead(ax, (52, -18), (42 + 4 * np.cos(np.radians(60)), -45 + 4 * np.sin(np.radians(60))),
         "2 × Ø8")
    vlabel(ax, -45, 30, "Alzado")
    vlabel(ax, -62, -30, "Planta")
    return save(fig, "A6_ej2_soporte_nervio", svg=True)


def fig_a6_2_sol():
    fig, ax = setup((-100, 112), (-90, 62), 5.4)
    s = soporte_nervio()
    Vf, Vt = View("front"), View("top", 0, -45)
    left, right = sbox(-200, -200, 0, 200), sbox(0, -200, 200, 200)
    draw_view(ax, s, Vf, hidden=False, region=left, axes=False)
    draw_section(ax, s, Vf, (1, 0.0), region=right, axes=False)
    draw_axes(ax, s, Vf, only=[0, 2])
    draw_view(ax, s, Vt)
    cut_trace(ax, [(60, -45), (0, -45), (0, -72)], thick_len=7)
    trace_arrow(ax, (56, -45), (0, 1))
    bnote(ax, (-98, 52), (-0.5, 49), "C7: las mitades se separan\ncon línea de eje, no gruesa", ha="left")
    bnote(ax, (-98, 26), (-22, 20), "mitad en vista:\nsin ocultas (C5)", ha="left")
    bnote(ax, (48, 44), (23, 22), "C6: nervio cortado\na lo largo: sin rayar")
    bnote(ax, (62, 22), (30, 5), "C4: rayado a 45°\nsolo en el material")
    bnote(ax, (66, -28), (57, -36), "C2: una flecha;\ntraza en L")
    bnote(ax, (-98, -82), (-1, -70), "C1: el plano llega hasta el eje\ny sale por el frente", ha="left")
    return save(fig, "A6_ej2_soporte_nervio_solucion")


# ----------------------------------------------------------------- A6 - Ej. 3
VOX = 152       # posicion de la vista lateral de la valvula


def fig_a6_3():
    fig, ax = setup((-94, 204), (-62, 78), 6.5)
    s = valvula()
    Vf, Vl = View("front"), View("left", VOX, 0)
    draw_view(ax, s, Vf)
    draw_view(ax, s, Vl)
    # longitudes
    hdim(ax, -70, -58, -45, "12", yfrom=-35, tx=-80)
    hdim(ax, -30, 30, -45, "60", yfrom=-25)
    hdim(ax, -70, 70, -54, "140", yfrom=-35)
    # diametros del tramo horizontal
    vdim(ax, -35, 35, -84, "Ø70", xfrom=-70)
    vdim(ax, -25, 25, -44, "Ø50", xfrom=-30)
    vdim(ax, -18, 18, 44, "Ø36")
    vdim(ax, -10, 10, 79, "Ø20", xfrom=70)
    # boca superior
    vdim(ax, 0, 45, 88, "45", xfrom=(74, 35))
    vdim(ax, 0, 55, 96, "55", xfrom=(74, 35))
    hdim(ax, -15, 15, 62, "Ø30", yfrom=55)
    hdim(ax, -35, 35, 70, "Ø70", yfrom=55)
    hdim(ax, VOX - 25, VOX + 25, 40, "Ø50", tx=VOX + 38)
    lead(ax, (24, -39), (8, -15), "cámara Ø30 × 40", ha="left")
    vlabel(ax, -52, 50, "Alzado")
    vlabel(ax, VOX, -45, "Vista lateral izquierda")
    return save(fig, "A6_ej3_valvula", svg=True)


def fig_a6_3_sol():
    fig, ax = setup((-110, 240), (-62, 76), 6.5)
    s = valvula()
    Vf, Vl = View("front"), View("left", VOX, 0)
    draw_section(ax, s, Vf, (1, 0.0), sp=3.0)
    draw_view(ax, s, Vl)
    ax.text(0, 66, "A-A", fontsize=11, ha="center", va="center", fontweight="bold")
    cut_trace(ax, [(VOX, -48), (VOX, 68)], thick_len=8)
    for z in (-44, 64):
        trace_arrow(ax, (VOX, z), (-1, 0), "A", (VOX - 9, z + (5 if z > 0 else -5)))
    bnote(ax, (-108, 62), (-14, 66), "C3: rótulo", ha="left")
    bnote(ax, (-108, 44), (-20, 30), "C4: mismo rayado en\ntoda la pieza cortada", ha="left")
    bnote(ax, (48, 62), (7, 7), "intersección de los agujeros Ø30:\nrectas a 45°, visibles detrás del plano")
    bnote(ax, (-108, -48), (-45, -4), "C5: conducto y cámara\nen blanco, sin ocultas", ha="left")
    bnote(ax, (VOX + 12, -50), (VOX + 1.5, -40), "C1, C2: plano longitudinal\npor el eje; flechas hacia\nla vista cortada")
    return save(fig, "A6_ej3_valvula_solucion")


# ================================================================ ACTIVIDAD 7
def _three(ax, s, gap=28):
    lo, hi = s.bounds()
    Vf = View("front")
    Vt = View("top", 0, -hi[1] - gap)
    Vl = View("left", hi[0] + gap + hi[1], 0)
    for V in (Vf, Vt, Vl):
        draw_view(ax, s, V)
    return Vf, Vt, Vl


def fig_a7_1():
    fig, ax = setup((-30, 140), (-97, 52), 3.3)
    s = escalonada()
    Vf, Vt, Vl = _three(ax, s)
    vdim(ax, 0, 10, -7, "10", xfrom=0, ty=-5.5)
    vdim(ax, 0, 25, -15, "25", xfrom=(0, 20))
    vdim(ax, 0, 40, -23, "40", xfrom=(0, 40))
    hdim(ax, 0, 20, -76, "20", yfrom=-68)
    hdim(ax, 0, 40, -83, "40", yfrom=(-68, -68))
    hdim(ax, 0, 60, -90, "60", yfrom=-68)
    vdim(ax, -48, -28, 67, "20", xfrom=60)
    vdim(ax, -68, -28, 75, "40", xfrom=60)
    vlabel(ax, 30, 46, "Alzado")
    vlabel(ax, 108, 46, "Lateral izquierda")
    vlabel(ax, 108, -48, "Planta (bajo el alzado)")
    return save(fig, "A7_p1_escalonada", svg=True)


def fig_a7_2():
    fig, ax = setup((-26, 140), (-97, 58), 3.3)
    s = cuna()
    Vf, Vt, Vl = _three(ax, s)
    vdim(ax, 0, 15, -8, "15", xfrom=0)
    vdim(ax, 0, 40, -16, "40", xfrom=(0, 35))
    vdim(ax, 0, 30, 68, "30", xfrom=60)
    hdim(ax, 0, 5, -76, "5", yfrom=-68, tx=-8)
    hdim(ax, 0, 35, -83, "35", yfrom=-68)
    hdim(ax, 0, 60, -90, "60", yfrom=-68)
    vdim(ax, -68, -28, 68, "40", xfrom=60)
    ox = Vl.o[0]
    hdim(ax, ox - 10, ox, 47, "10", yfrom=40)
    hdim(ax, ox - 30, ox - 10, 47, "20", yfrom=40)
    vlabel(ax, 22, 46, "Alzado")
    vlabel(ax, 108, -10, "Lateral izquierda")
    vlabel(ax, 108, -48, "Planta (bajo el alzado)")
    return save(fig, "A7_p2_plano_inclinado", svg=True)


def fig_a7_3():
    fig, ax = setup((-30, 150), (-112, 64), 4.6)
    s = soporte_respaldo()
    Vf, Vt, Vl = _three(ax, s)
    ox = Vl.o[0]
    oy = Vt.o[1]
    vdim(ax, 0, 30, -9, "30", xfrom=(0, 0))
    lead(ax, (-26, 56), (20 + 20 * np.cos(np.radians(125)), 30 + 20 * np.sin(np.radians(125))), "R20")
    lead(ax, (42, 56), (20 + 10 * np.cos(np.radians(50)), 30 + 10 * np.sin(np.radians(50))), "Ø20")
    # lateral
    hdim(ax, ox - 60, ox - 50, 57, "10", yfrom=50, tx=ox - 40)
    hdim(ax, ox - 60, ox, -9, "60", yfrom=0)
    vdim(ax, 0, 10, ox + 8, "10", xfrom=ox, ty=16)
    # planta
    hdim(ax, 0, 20, oy - 8, "20", yfrom=(oy, oy + 20 - 7))
    hdim(ax, 0, 40, oy - 16, "40", yfrom=oy)
    vdim(ax, oy + 20, oy + 60, 49, "40", xfrom=(27, 40))
    lead(ax, (-24, oy + 36), (20 - 5 * np.cos(np.radians(40)), oy + 20 + 5 * np.sin(np.radians(40))), "Ø10")
    vlabel(ax, 20, -20, "Alzado")
    vlabel(ax, ox - 22, 30, "Lateral izquierda")
    vlabel(ax, 100, -60, "Planta (bajo el alzado)")
    return save(fig, "A7_p3_soporte_respaldo", svg=True)


# ------------------------------------------------------- isometricos (pauta)
EX = View("iso").p([(1, 0, 0)])[0]
EY = View("iso").p([(0, 1, 0)])[0]
EZ = View("iso").p([(0, 0, 1)])[0]


def iso_grid(ax, xlim, ylim, step=10):
    R = max(xlim[1] - xlim[0], ylim[1] - ylim[0]) * 1.5
    n = int(R / step) + 2
    kw = dict(color="#D9D9D9", lw=0.4, zorder=0)
    for i in range(-n, n + 1):
        for d in (EX, EY):
            p = np.array([0, i * step])
            ax.plot([p[0] - d[0] * R, p[0] + d[0] * R], [p[1] - d[1] * R, p[1] + d[1] * R], **kw)
        x = i * step * EX[0]
        ax.plot([x, x], [-R, R], **kw)


def iso_axes(ax, V, o=(0, 0, 0), ln=14):
    o = np.array(o, float)
    for d, name in (((1, 0, 0), "X"), ((0, -1, 0), None), ((0, 0, 1), "Z")):
        pass
    for d, name in (((1, 0, 0), "X"), ((0, 1, 0), "Y"), ((0, 0, 1), "Z")):
        a = V.p([o])[0]
        b = V.p([o + np.array(d) * ln])[0]
        ax.annotate("", xy=b, xytext=a,
                    arrowprops=dict(arrowstyle="-|>,head_length=0.4,head_width=0.14",
                                    lw=0.8, color=BLUE, shrinkA=0, shrinkB=0), zorder=9)
        t = V.p([o + np.array(d) * (ln + 4)])[0]
        ax.text(t[0], t[1], name, color=BLUE, fontsize=7, ha="center", va="center")


def _iso_fig(solid, xlim, ylim, width, triad):
    fig, ax = setup(xlim, ylim, width)
    iso_grid(ax, xlim, ylim)
    V = View("iso")
    draw_view(ax, solid, V, hidden=False, axes=False, lw=1.9)
    iso_axes(ax, V, triad)
    return fig, ax, V


def fig_a7_1_sol():
    s = escalonada()
    fig, ax, V = _iso_fig(s, (-86, 76), (-8, 96), 3.4, (40, -25, 0))
    bnote(ax, (-84, 80), V.pt(30, 0, 25), "I2: 20, 40 y 60 se miden\nsobre la dirección X", ha="left")
    bnote(ax, (-84, 6), V.pt(0, 20, 5), "I6: solo aristas\nvisibles", ha="left")
    return save(fig, "A7_p1_escalonada_solucion")


def fig_a7_2_sol():
    s = cuna()
    fig, ax, V = _iso_fig(s, (-86, 76), (-8, 96), 3.4, (40, -25, 0))
    for p in ((5, 0, 15), (35, 0, 40), (23, 10, 30)):
        q = V.pt(*p)
        ax.plot(*q, "o", ms=3.2, color=BLUE, zorder=9)
    bnote(ax, (-84, 82), V.pt(20, 0, 27.5), "I3: se ubican los extremos\n(5; 15) y (35; 40) y se unen", ha="left")
    bnote(ax, (-84, 8), V.pt(23, 12, 30), "fondo de la ranura a 30:\ncorta al plano inclinado", ha="left")
    return save(fig, "A7_p2_plano_inclinado_solucion")


def fig_a7_3_sol():
    s = soporte_respaldo()
    fig, ax, V = _iso_fig(s, (-106, 72), (-8, 100), 4.6, (35, -22, 0))
    # rombos de construccion de las elipses (cuadrados circunscritos proyectados)
    def rombo(pts):
        q = V.p(pts + [pts[0]])
        ax.plot(q[:, 0], q[:, 1], "-", color=BLUE, lw=0.6, zorder=6)
    rombo([(10, 50, 20), (30, 50, 20), (30, 50, 40), (10, 50, 40)])
    rombo([(0, 50, 10), (40, 50, 10), (40, 50, 50), (0, 50, 50)])
    rombo([(15, 15, 10), (25, 15, 10), (25, 25, 10), (15, 25, 10)])
    bnote(ax, (-104, 90), V.pt(10, 50, 40), "I4: elipses en el isoplano\nfrontal (rombo auxiliar)", ha="left")
    bnote(ax, (-104, 8), V.pt(15, 25, 10), "I4: elipse en el isoplano\nhorizontal", ha="left")
    bnote(ax, (22, 92), V.pt(20 + 14.1, 55, 30 + 14.1), "I5: tangente común\na los dos arcos")
    bnote(ax, (-104, 50), V.pt(0, 50, 30), "I5: el arco nace\na la altura 30", ha="left")
    return save(fig, "A7_p3_soporte_respaldo_solucion")


FIGS = [fig_a6_1, fig_a6_2, fig_a6_3, fig_a6_1_sol, fig_a6_2_sol, fig_a6_3_sol,
        fig_a7_1, fig_a7_2, fig_a7_3, fig_a7_1_sol, fig_a7_2_sol, fig_a7_3_sol]

if __name__ == "__main__":
    sel = sys.argv[1:]
    for f in FIGS:
        if not sel or any(x in f.__name__ for x in sel):
            print(f())
