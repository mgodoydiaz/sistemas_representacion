"""Piezas del Proyecto 2 (PCI 1119, 2026-2): "Piezas de una válvula".

Cada pieza se define UNA sola vez como sólido 3D (CadQuery / OpenCascade). De ese
sólido se derivan, con eliminación de líneas ocultas (HLR), las tres vistas ISO-E
(primer diedro) y el isométrico, de modo que siempre son coherentes entre sí.
Las cotas se anclan a puntos 3D de la pieza y su valor se mide sobre la proyección.

Salida: figuras/Vn_vistas.(png|svg|pdf) y figuras/Vn_iso.(png|svg|pdf), n = 1..4.
Unidades: mm. Ejes de la pieza: X = ancho, Y = profundidad (hacia atrás), Z = alto.

Uso:  python3 piezas_proyecto2.py [V1 V2 ...]
Requiere: cadquery, shapely, matplotlib, numpy.
"""
import os
import sys
import numpy as np
import cadquery as cq
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union, linemerge

from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepLib import BRepLib
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.GeomAbs import GeomAbs_Line
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figuras_apunte_v3 as fa          # helpers del apunte (copia sin modificar)
from figuras_apunte_v3 import L, setup, dim, iso, K, plt

OUT = os.path.join(HERE, "figuras")
os.makedirs(OUT, exist_ok=True)

IN_PER_MM = 0.030          # pulgadas de figura por mm de dibujo (igual en todas)
FS = 8.0                   # tamaño de texto de cotas (pt)
LW_VIS = 1.7
LW_FINE = 0.6
LW_DIM = 0.55
S_ISO = np.sqrt(1.5)       # el isométrico se dibuja sin reducción (como ISODRAFT)
ARROW = "-|>,head_length=0.55,head_width=0.16"
ARROW2 = "<|-|>,head_length=0.55,head_width=0.16"


# ====================================================================== HLR
def _edges_to_polylines(compound):
    out = []
    if compound is None or compound.IsNull():
        return out
    BRepLib.BuildCurves3d_s(compound)
    exp = TopExp_Explorer(compound, TopAbs_EDGE)
    while exp.More():
        e = TopoDS.Edge_s(exp.Current())
        c = BRepAdaptor_Curve(e)
        if c.GetType() == GeomAbs_Line:
            a, b = c.Value(c.FirstParameter()), c.Value(c.LastParameter())
            pts = [(a.X(), a.Y()), (b.X(), b.Y())]
        else:
            d = GCPnts_QuasiUniformDeflection(c, 0.01)
            pts = [(d.Value(i).X(), d.Value(i).Y()) for i in range(1, d.NbPoints() + 1)]
        if len(pts) >= 2:
            out.append(np.array(pts))
        exp.Next()
    return out


def _dedupe(polys, blocked=None, tol=0.06, minlen=0.4):
    """Quita tramos repetidos (aristas que se proyectan una sobre otra)."""
    acc = blocked
    out = []
    for p in sorted(polys, key=lambda q: -LineString(q).length):
        ls = LineString(p)
        if ls.length < 1e-6:
            continue
        rest = ls if acc is None else ls.difference(acc)
        parts = [g for g in getattr(rest, "geoms", [rest])
                 if g.geom_type == "LineString" and g.length > minlen]
        if not parts:
            continue
        out.extend(parts)
        b = unary_union([g.buffer(tol, cap_style=2) for g in parts])
        acc = b if acc is None else acc.union(b)
    return out, acc


def project(shape, normal, xdir, hidden=True):
    """Proyección ortogonal con líneas ocultas. normal apunta hacia el observador.
    Devuelve (visibles, ocultas): listas de polilíneas Nx2 en coordenadas de vista."""
    algo = HLRBRep_Algo()
    algo.Add(shape)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*normal), gp_Dir(*xdir))))
    algo.Update()
    algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    vis = _edges_to_polylines(h.VCompound()) + _edges_to_polylines(h.OutLineVCompound())
    vis, acc = _dedupe(vis)
    hid = []
    if hidden:
        hid = _edges_to_polylines(h.HCompound()) + _edges_to_polylines(h.OutLineHCompound())
        hid, _ = _dedupe(hid, acc, minlen=0.8)
        if hid:
            m = linemerge(MultiLineString(hid))
            hid = list(getattr(m, "geoms", [m]))
    return [np.asarray(g.coords) for g in vis], [np.asarray(g.coords) for g in hid]


VIEWS = {   # normal (hacia el observador), dirección x de la vista
    "alzado":  ((0, -1, 0), (1, 0, 0)),     # local (x, z)
    "planta":  ((0, 0, 1), (1, 0, 0)),      # local (x, y)   fondo hacia arriba
    "lateral": ((-1, 0, 0), (0, -1, 0)),    # local (-y, z)  lateral izquierda
}


def local(kind, P):
    x, y, z = P
    return {"alzado": (x, z), "planta": (x, y), "lateral": (-y, z)}[kind]


# ====================================================================== cotas 2D
def _txt(ax, xy, s, rot=0, ha="center", va="center", fs=FS, bg=True):
    kw = dict(bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none")) if bg else {}
    ax.text(xy[0], xy[1], s, color=K, fontsize=fs, ha=ha, va=va, rotation=rot,
            rotation_mode="anchor", zorder=7, **kw)


def _ext(ax, a, b, gap=1.2, over=1.8):
    """Línea auxiliar de cota desde el punto a hasta el punto b (pasa over)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = np.linalg.norm(b - a)
    if n < gap + 0.2:
        return
    d = (b - a) / n
    L(ax, [a + d * gap, b + d * over], "thin", K, z=5, lw=LW_DIM)


def _dimline(ax, p0, p1, text, toff=2.6, tshift=0.0, out=None):
    """Línea de cota entre p0 y p1 con el texto sobre la línea.
    out: None = flechas por dentro; +1 / -1 = flechas por fuera y texto fuera,
    más allá de p1 (+1) o de p0 (-1); 0 = flechas por fuera, texto centrado."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    n = np.linalg.norm(p1 - p0)
    d = (p1 - p0) / n
    rot = np.degrees(np.arctan2(d[1], d[0]))
    flip = rot > 90.01 or rot <= -89.99
    if flip:
        rot += 180 if rot < 0 else -180
    nrm = np.array([-d[1], d[0]]) * (-1 if flip else 1)
    if out is None:
        ax.annotate("", xy=p1, xytext=p0, zorder=6,
                    arrowprops=dict(arrowstyle=ARROW2, lw=LW_DIM, color=K,
                                    shrinkA=0, shrinkB=0))
        m = (p0 + p1) / 2 + d * tshift + nrm * toff
        _txt(ax, m, text, rot)
        return
    kw = dict(arrowstyle=ARROW, lw=LW_DIM, color=K, shrinkA=0, shrinkB=0)
    ax.annotate("", xy=p0, xytext=p0 - d * 6, arrowprops=kw, zorder=6)
    ax.annotate("", xy=p1, xytext=p1 + d * 6, arrowprops=kw, zorder=6)
    L(ax, [p0, p1], "thin", K, z=6, lw=LW_DIM)
    if out == 0:
        _txt(ax, (p0 + p1) / 2 + d * tshift + nrm * toff, text, rot)
    else:
        w = 0.62 * FS / 72 / IN_PER_MM * len(text) * 0.5 + 7.5
        base = (p1 + d * w) if out > 0 else (p0 - d * w)
        if out > 0:
            L(ax, [p1, p1 + d * (2 * w - 7)], "thin", K, z=6, lw=LW_DIM)
        else:
            L(ax, [p0, p0 - d * (2 * w - 7)], "thin", K, z=6, lw=LW_DIM)
        _txt(ax, base + nrm * toff, text, rot)


def _leader(ax, tip, elbow, text, shelf=None, fs=FS):
    """Línea de referencia con flecha en tip, quiebre en elbow y texto en repisa."""
    tip, elbow = np.asarray(tip, float), np.asarray(elbow, float)
    ax.annotate("", xy=tip, xytext=elbow, zorder=6,
                arrowprops=dict(arrowstyle=ARROW, lw=LW_DIM, color=K, shrinkA=0, shrinkB=0))
    right = elbow[0] >= tip[0] if shelf is None else shelf > 0
    lines = text.split("\n")
    w = 0.60 * fs / 72 / IN_PER_MM * max(len(s) for s in lines) + 1.5
    end = elbow + np.array([w if right else -w, 0])
    L(ax, [elbow, end], "thin", K, z=6, lw=LW_DIM)
    mid = (elbow + end) / 2
    _txt(ax, (mid[0], mid[1] + 2.5), lines[0], fs=fs, bg=False)
    for i, s in enumerate(lines[1:]):
        _txt(ax, (mid[0], mid[1] - 2.9 - 4.3 * i), s, fs=fs, bg=False)


def fmt(v):
    r = round(v)
    assert abs(v - r) < 1e-6, f"cota no entera: {v}"
    return str(int(r))


# ====================================================================== vista
class View:
    def __init__(self, ax, pieza, kind, off, hidden=True):
        self.ax, self.kind, self.off, self.pz = ax, kind, np.asarray(off, float), pieza
        n, xd = VIEWS[kind]
        self.normal = np.array(n, float)
        vis, hid = project(pieza.shape, n, xd, hidden)
        for p in hid:
            L(ax, p + self.off, "hid", K, z=3, lw=LW_FINE)
        for p in vis:
            L(ax, p + self.off, "vis", K, z=4, lw=LW_VIS)
        self._axes()

    # -- coordenadas
    def P(self, P3):
        return np.asarray(local(self.kind, P3), float) + self.off

    def T(self, u, v):
        return np.array([u, v], float) + self.off

    # -- ejes
    def _axes(self, ext=4.0):
        segs = []
        for f in self.pz.feats:
            p0, p1, r = np.array(f[0], float), np.array(f[1], float), f[2]
            d = (p1 - p0) / np.linalg.norm(p1 - p0)
            if abs(d @ self.normal) > 0.99:
                c = self.P(p0)
                e = r + ext
                segs.append(LineString([c - (e, 0), c + (e, 0)]))
                segs.append(LineString([c - (0, e), c + (0, e)]))
            else:
                segs.append(LineString([self.P(p0 - d * ext), self.P(p1 + d * ext)]))
        if not segs:
            return
        for s in _merge_collinear(segs):
            L(self.ax, s, "axis", K, z=2, lw=LW_FINE)

    # -- cotas (los puntos son 3D; `at` es la coordenada local de la línea de cota)
    def hdim(self, A, B, at, text=None, pre="", **kw):
        a, b = self.P(A), self.P(B)
        if a[0] > b[0]:
            a, b = b, a
        y = at + self.off[1]
        _ext(self.ax, a, (a[0], y)); _ext(self.ax, b, (b[0], y))
        _dimline(self.ax, (a[0], y), (b[0], y), pre + (text or fmt(b[0] - a[0])), **kw)

    def vdim(self, A, B, at, text=None, pre="", **kw):
        a, b = self.P(A), self.P(B)
        if a[1] > b[1]:
            a, b = b, a
        x = at + self.off[0]
        _ext(self.ax, a, (x, a[1])); _ext(self.ax, b, (x, b[1]))
        _dimline(self.ax, (x, a[1]), (x, b[1]), pre + (text or fmt(b[1] - a[1])), **kw)

    def lead(self, tip3, elbow_uv, text, **kw):
        tip = self.P(tip3) if len(tip3) == 3 else self.T(*tip3)
        _leader(self.ax, tip, self.T(*elbow_uv), text, **kw)

    def circ_lead(self, C3, r, ang, elbow_uv, text, **kw):
        """Referencia a un círculo de centro C3 y radio r, tocándolo en el ángulo ang."""
        c = self.P(C3)
        a = np.radians(ang)
        _leader(self.ax, c + r * np.array([np.cos(a), np.sin(a)]), self.T(*elbow_uv), text, **kw)

    def label(self, text, uv):
        _txt(self.ax, self.T(*uv), text, fs=7.5, bg=False)


def _merge_collinear(segs):
    """Une segmentos colineales que se solapan o tocan (ejes coincidentes)."""
    items = []
    for s in segs:
        a, b = np.array(s.coords[0]), np.array(s.coords[-1])
        if np.linalg.norm(b - a) < 1e-6:
            continue
        d = (b - a) / np.linalg.norm(b - a)
        if d[0] < -1e-9 or (abs(d[0]) < 1e-9 and d[1] < 0):
            d, a, b = -d, b, a
        c = a[0] * d[1] - a[1] * d[0]                 # distancia con signo al origen
        items.append((tuple(np.round(d, 4)), round(c, 3), a @ d, b @ d, d))
    out = []
    groups = {}
    for it in items:
        groups.setdefault(it[:2], []).append(it)
    for (dk, c), g in groups.items():
        d = g[0][4]
        nrm = np.array([d[1], -d[0]])
        iv = sorted((it[2], it[3]) for it in g)
        cur = list(iv[0])
        for a, b in iv[1:]:
            if a <= cur[1] + 1e-6:
                cur[1] = max(cur[1], b)
            else:
                out.append([d * cur[0] + nrm * c, d * cur[1] + nrm * c]); cur = [a, b]
        out.append([d * cur[0] + nrm * c, d * cur[1] + nrm * c])
    return out


# ====================================================================== isométrico
ISO_N = (1, -1, 1)
ISO_X = (1, 1, 0)


class Iso:
    def __init__(self, ax, pieza, off=(0, 0), axes=True):
        self.ax, self.pz, self.off = ax, pieza, np.asarray(off, float)
        vis, _ = project(pieza.shape, ISO_N, ISO_X, hidden=False)
        for p in vis:
            L(ax, p * S_ISO + self.off, "vis", K, z=4, lw=LW_VIS)
        if axes:
            self._axes()

    def P(self, P3):
        return np.asarray(iso(*P3), float) * S_ISO + self.off

    def _axes(self, ext=3.0):
        for f in self.pz.feats:
            p0, p1, r = np.array(f[0], float), np.array(f[1], float), f[2]
            if len(f) > 3 and f[3] == "noiso":
                continue
            d = (p1 - p0) / np.linalg.norm(p1 - p0)
            for e in np.eye(3):
                if abs(e @ d) > 0.5:
                    continue
                L(self.ax, [self.P(p1 - e * (r + ext)), self.P(p1 + e * (r + ext))],
                  "axis", K, z=5, lw=LW_FINE)

    def dim(self, A, B, off, text=None, pre="", **kw):
        """Cota entre los puntos 3D A y B; off = vector 3D de las líneas auxiliares."""
        A, B, off = (np.asarray(v, float) for v in (A, B, off))
        _ext(self.ax, self.P(A), self.P(A + off)); _ext(self.ax, self.P(B), self.P(B + off))
        _dimline(self.ax, self.P(A + off), self.P(B + off),
                 pre + (text or fmt(np.linalg.norm(B - A))), **kw)

    def dimx(self, A, B, A2, B2, text=None, pre="", **kw):
        """Cota con líneas auxiliares A->A2 y B->B2 y línea de cota A2-B2."""
        A, B, A2, B2 = (np.asarray(v, float) for v in (A, B, A2, B2))
        _ext(self.ax, self.P(A), self.P(A2)); _ext(self.ax, self.P(B), self.P(B2))
        _dimline(self.ax, self.P(A2), self.P(B2),
                 pre + (text or fmt(np.linalg.norm(B2 - A2))), **kw)

    def notes(self, *lines):
        """Bloque de notas en la esquina inferior izquierda de la lámina."""
        x0 = self.ax.get_xlim()[0] + 5
        y0 = self.ax.get_ylim()[0] + 13 + 4.6 * len(lines)
        _txt(self.ax, (x0, y0), "Notas:", ha="left", fs=7.5, bg=False)
        for i, s in enumerate(lines):
            _txt(self.ax, (x0, y0 - 4.6 * (i + 1)), f"{i + 1}. {s}", ha="left", fs=7.5,
                 bg=False)

    def lead(self, tip3, d_elbow, text, **kw):
        tip = self.P(tip3)
        _leader(self.ax, tip, tip + np.asarray(d_elbow, float), text, **kw)


# ====================================================================== piezas
class Pieza:
    def __init__(self, cod, nombre, wp, feats):
        self.cod, self.nombre = cod, nombre
        s = wp.clean().val().wrapped
        BRepLib.EncodeRegularity_s(s)
        self.shape = s
        self.feats = feats      # ejes: (p0, p1, radio[, "noiso"]); p1 = extremo visible


def cyl_z(r, z0, z1, x=0, y=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def cyl_x(r, x0, x1, y=0, z=0):
    return cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(r).extrude(x1 - x0)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def prism_xz(pts, y0, y1):
    """Prisma de perfil (x, z) extruido entre y0 e y1."""
    w = cq.Workplane("XY").polyline([(x, z) for x, z in pts]).close().extrude(y1 - y0)
    return w.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y1, 0))


def v1_bonete():
    """Bonete: brida cuadrada 80x80x12 (esquinas R12), cuello Ø40 hasta z=60,
    paso del vástago Ø16 y caja de empaquetadura Ø28 x 25, 4 agujeros Ø10 a 56x56,
    2 nervios de espesor 8 en el plano de simetría frontal, desde el borde de la
    brida (z=12) hasta el cuello a z=42."""
    s = box(-40, 40, -40, 40, 0, 12).edges("|Z").fillet(12)
    s = s.union(cyl_z(20, 12, 60))
    for sg in (1, -1):
        s = s.union(prism_xz([(sg * 15, 12), (sg * 40, 12), (sg * 20, 42), (sg * 15, 42)], -4, 4))
    s = s.cut(cyl_z(8, 0, 60)).cut(cyl_z(14, 35, 60))
    feats = [((0, 0, 0), (0, 0, 60), 20)]
    for sx in (1, -1):
        for sy in (1, -1):
            s = s.cut(cyl_z(5, 0, 12, 28 * sx, 28 * sy))
            f = ((28 * sx, 28 * sy, 0), (28 * sx, 28 * sy, 12), 5)
            feats.append(f + ("noiso",) if (sx, sy) == (-1, 1) else f)
    return Pieza("V1", "Bonete", s, feats)


def v2_prensaestopas():
    """Prensaestopas: brida oblonga 110x40x12 (extremos R20) con 2 ranuras cerradas
    de 12x20 (centros de arco a x = 31 y 39), casquillo Ø30 hasta z=50 con chaflán
    2x45°, agujero Ø16 pasante y rebaje Ø22 x 8 por la cara inferior."""
    s = cq.Workplane("XY").slot2D(110, 40).extrude(12)
    s = s.union(cyl_z(15, 12, 50))
    s = s.faces(">Z").edges().chamfer(2)
    s = s.cut(cyl_z(8, 0, 50)).cut(cyl_z(11, 0, 8))
    feats = [((0, 0, 0), (0, 0, 50), 15)]
    for sg in (1, -1):
        s = s.cut(cq.Workplane("XY").center(35 * sg, 0).slot2D(20, 12).extrude(12))
        for xc in (31, 39):
            feats.append(((xc * sg, 0, 0), (xc * sg, 0, 12), 6))
    return Pieza("V2", "Prensaestopas", s, feats)


def v3_yugo():
    """Yugo: base 110x40x12 con agujero central Ø24 y 2 agujeros Ø10 (centros a 90),
    2 columnas de 12x30 hasta z=62, puente de 64x30x14 con chaflanes 8x8,
    cubo Ø28 hasta z=84 con agujero Ø16, y agujero Ø10 transversal en las columnas."""
    s = box(-55, 55, -20, 20, 0, 12)
    for sg in (1, -1):
        s = s.union(box(min(20 * sg, 32 * sg), max(20 * sg, 32 * sg), -15, 15, 12, 62))
    s = s.union(prism_xz([(-32, 62), (32, 62), (32, 68), (24, 76), (-24, 76), (-32, 68)], -15, 15))
    s = s.union(cyl_z(14, 76, 84))
    s = s.cut(cyl_z(8, 62, 84)).cut(cyl_z(12, 0, 12)).cut(cyl_x(5, -32, 32, 0, 40))
    feats = [((0, 0, 0), (0, 0, 84), 14),
             ((-32, 0, 40), (32, 0, 40), 5)]
    for sg in (1, -1):
        s = s.cut(cyl_z(5, 0, 12, 45 * sg, 0))
        f = ((45 * sg, 0, 0), (45 * sg, 0, 12), 5)
        feats.append(f + ("noiso",) if sg < 0 else f)
    return Pieza("V3", "Yugo", s, feats)


def v4_cuerpo():
    """Cuerpo: bloque 50x50x60, 2 bocas Ø40 de largo 20 (largo total 90) con eje a
    z=30, paso Ø24 pasante, alojamiento de la compuerta 12x34 de profundidad 48
    desde la cara superior y 4 agujeros ciegos Ø8 x 12 a 36x36."""
    s = box(-25, 25, -25, 25, 0, 60)
    s = s.union(cyl_x(20, -45, 45, 0, 30))
    s = s.cut(cyl_x(12, -45, 45, 0, 30)).cut(box(-6, 6, -17, 17, 12, 60))
    feats = [((-45, 0, 30), (45, 0, 30), 20),
             ((0, 0, 0), (0, 0, 60), 17, "noiso")]
    for sx in (1, -1):
        for sy in (1, -1):
            s = s.cut(cyl_z(4, 48, 60, 18 * sx, 18 * sy))
            feats.append(((18 * sx, 18 * sy, 48), (18 * sx, 18 * sy, 60), 4))
    return Pieza("V4", "Cuerpo", s, feats)


# ====================================================================== láminas
def _save(fig, name):
    paths = []
    for ext in ("png", "svg", "pdf"):
        p = os.path.join(OUT, f"{name}.{ext}")
        fig.savefig(p, dpi=300, facecolor="white")
        paths.append(p)
    plt.close(fig)
    return paths[0]


def _frame(ax, xlim, ylim, titulo):
    x0, x1 = xlim
    y0, y1 = ylim
    L(ax, [(x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x1 - 1, y1 - 1), (x0 + 1, y1 - 1),
           (x0 + 1, y0 + 1)], "thin", K, z=1, lw=0.8)
    L(ax, [(x0 + 1, y0 + 9), (x1 - 1, y0 + 9)], "thin", K, z=1, lw=0.8)
    ax.text(x0 + 4, y0 + 5, titulo, fontsize=7.5, ha="left", va="center", color=K)
    ax.text(x1 - 4, y0 + 5, "PCI 1119 · Proyecto 2 · Cotas en mm", fontsize=7.5,
            ha="right", va="center", color=K)


def sheet(xlim, ylim):
    return setup(xlim, ylim, IN_PER_MM * (xlim[1] - xlim[0]))


DIMS_VISTAS = {}
DIMS_ISO = {}
LAYOUT = {   # límites de lámina de vistas, origen de planta y lateral, límites iso
    "V1": dict(vx=(-72, 150), vy=(-138, 82), pl=(0, -65), la=(100, 0),
               ix=(-112, 118), iy=(-88, 118)),
    "V2": dict(vx=(-88, 142), vy=(-104, 74), pl=(0, -52), la=(100, 0),
               ix=(-112, 96), iy=(-78, 98)),
    "V3": dict(vx=(-88, 172), vy=(-102, 112), pl=(0, -50), la=(112, 0),
               ix=(-104, 108), iy=(-82, 124)),
    "V4": dict(vx=(-80, 140), vy=(-128, 82), pl=(0, -76), la=(100, 0),
               ix=(-96, 110), iy=(-70, 112)),
}
PIEZAS = {"V1": v1_bonete, "V2": v2_prensaestopas, "V3": v3_yugo, "V4": v4_cuerpo}


def lam_vistas(pz):
    lay = LAYOUT[pz.cod]
    fig, ax = sheet(lay["vx"], lay["vy"])
    al = View(ax, pz, "alzado", (0, 0))
    pl = View(ax, pz, "planta", lay["pl"])
    la = View(ax, pz, "lateral", lay["la"])
    if pz.cod in DIMS_VISTAS:
        DIMS_VISTAS[pz.cod](al, pl, la)
    _frame(ax, lay["vx"], lay["vy"],
           f"{pz.cod} · {pz.nombre} · Vistas en ISO-E (primer diedro)")
    return _save(fig, f"{pz.cod}_vistas")


def lam_iso(pz):
    lay = LAYOUT[pz.cod]
    fig, ax = sheet(lay["ix"], lay["iy"])
    io = Iso(ax, pz)
    if pz.cod in DIMS_ISO:
        DIMS_ISO[pz.cod](io)
    _frame(ax, lay["ix"], lay["iy"], f"{pz.cod} · {pz.nombre} · Isométrico")
    return _save(fig, f"{pz.cod}_iso")



# ====================================================================== cotas
def circ_pt(c, r, ang, plane="z"):
    """Punto 3D de un círculo de centro c y radio r (ángulo en grados)."""
    a = np.radians(ang)
    c = np.asarray(c, float)
    if plane == "z":
        return c + r * np.array([np.cos(a), np.sin(a), 0])
    return c + r * np.array([0, np.cos(a), np.sin(a)])       # plano x = cte


# ---------------------------------------------------------------- V1 bonete
SIM = "Pieza simétrica respecto de sus dos planos verticales medios."


def v1_vistas(al, pl, la):
    al.vdim((-40, 0, 0), (-40, 0, 12), -50)
    al.vdim((-40, 0, 12), (-20, 0, 42), -50)
    al.vdim((-40, 0, 0), (-20, 0, 60), -60)
    la.hdim((0, 20, 60), (0, -20, 60), 68, pre="Ø")
    pl.hdim((-28, -28, 0), (28, -28, 0), -49)
    pl.hdim((-40, -28, 0), (40, -28, 0), -58)
    pl.vdim((28, -28, 0), (28, 28, 0), 50)
    pl.vdim((28, -40, 0), (28, 40, 0), 59)
    pl.vdim((-40, -4, 0), (-40, 4, 0), -48, out=1)
    pl.circ_lead((28, 28, 0), 5, 50, (38, 46), "4 × Ø10")
    pl.circ_lead((-28, -28, 0), 12, 225, (-46, -46), "R12", shelf=-1)
    pl.circ_lead((0, 0, 0), 14, 125, (-18, 48), "Ø16 pasante\nØ28, prof. 25", shelf=-1)


def v1_iso(io):
    io.dim((-28, -28, 12), (28, -28, 12), (0, -32, 0))
    io.dim((-40, -28, 12), (40, -28, 12), (0, -42, 0))
    io.dim((28, -28, 12), (28, 28, 12), (38, 0, 0))
    io.dim((28, -40, 12), (28, 40, 12), (48, 0, 0))
    io.dim((-28, -40, 0), (-28, -40, 12), (-26, 0, 0))
    io.dim((40, -4, 12), (40, 4, 12), (8, 0, 0), out=1)
    io.dimx((20, 40, 12), (20, 0, 42), (20, 50, 12), (20, 50, 42))
    io.dimx((20, 40, 12), (20, 0, 60), (20, 60, 12), (20, 60, 60))
    io.lead(circ_pt((-28, -28, 12), 5, 110), (-16, 22), "4 × Ø10", shelf=-1)
    io.lead(circ_pt((28, -28, 12), 12, -45), (-3, -24), "R12", shelf=-1)
    io.lead(circ_pt((0, 0, 60), 20, 170), (-22, 6), "Ø40", shelf=-1)
    io.lead(circ_pt((0, 0, 60), 14, 100), (-4, 26), "Ø16 pasante\nØ28, prof. 25")
    io.notes(SIM, "Nervios de espesor 8, desde el borde de la brida hasta el cuello.")


# ---------------------------------------------------------------- V2 prensaestopas
def v2_vistas(al, pl, la):
    al.vdim((-55, 0, 0), (-55, 0, 12), -64)
    al.vdim((-55, 0, 0), (-13, 0, 50), -73)
    al.hdim((-15, 0, 48), (15, 0, 48), 58, pre="Ø")
    al.lead((14, 0, 49), (30, 60), "2 × 45°")
    al.lead((11, 0, 8), (30, -9), "Ø22, prof. 8")
    pl.hdim((-31, 0, 0), (31, 0, 0), -29)
    pl.hdim((31, 0, 0), (39, 0, 0), -29, out=1)
    pl.hdim((-55, 0, 0), (55, 0, 0), -38)
    pl.vdim((35, -20, 0), (35, 20, 0), 63)
    pl.vdim((-35, -6, 0), (-35, 6, 0), -63)
    pl.circ_lead((0, 0, 0), 8, 60, (22, 27), "Ø16 pasante")


def v2_iso(io):
    c = 20 / np.sqrt(2)
    io.dim((-31, 0, 12), (31, 0, 12), (0, -48, 0))
    io.dim((31, 0, 12), (39, 0, 12), (0, -48, 0), out=1)
    io.dim((-55, 0, 12), (55, 0, 12), (0, -58, 0))
    io.dim((-39, -6, 12), (-39, 6, 12), (-23, 0, 0))
    io.dim((-35, -20, 12), (-35, 20, 12), (-37, 0, 0))
    io.dimx((35 + c, c, 0), (35 + c, c, 12), (62, c, 0), (62, c, 12))
    io.dimx((13, 20, 12), (13, 0, 50), (13, 56, 12), (13, 56, 50))
    io.lead(circ_pt((0, 0, 48), 15, 170), (-18, 10), "Ø30", shelf=-1)
    io.lead(circ_pt((0, 0, 50), 8, 120), (-8, 24), "Ø16 pasante", shelf=-1)
    io.lead(circ_pt((0, 0, 49), 14, -40), (34, -4), "2 × 45°")
    io.notes(SIM, "Por la cara inferior: rebaje coaxial Ø22, prof. 8.")


# ---------------------------------------------------------------- V3 yugo
def v3_vistas(al, pl, la):
    al.vdim((-55, 0, 0), (-55, 0, 12), -64)
    al.vdim((-55, 0, 0), (-36, 0, 40), -73)
    al.vdim((55, 0, 0), (24, 0, 76), 64)
    al.vdim((55, 0, 0), (14, 0, 84), 73)
    al.vdim((10, 0, 12), (10, 0, 62), 10)
    al.hdim((-20, 0, 25), (20, 0, 25), 25, tshift=-9)
    al.hdim((-14, 0, 84), (14, 0, 84), 92, pre="Ø")
    al.hdim((-32, 0, 68), (32, 0, 68), 101)
    al.lead((-28, 0, 72), (-44, 84), "8 × 45°", shelf=-1)
    pl.hdim((-45, 0, 0), (45, 0, 0), -31)
    pl.hdim((-55, -20, 0), (55, -20, 0), -40)
    pl.vdim((32, -15, 0), (32, 15, 0), 64)
    pl.vdim((55, -20, 0), (55, 20, 0), 73)
    pl.circ_lead((45, 0, 0), 5, 60, (52, 27), "2 × Ø10")
    pl.circ_lead((0, 0, 0), 8, 120, (-10, 27), "Ø16", shelf=-1)
    pl.circ_lead((0, 0, 0), 12, 290, (14, -25), "Ø24 (base)")
    la.circ_lead((0, 0, 40), 5, 30, (22, 52), "Ø10 pasante")


def v3_iso(io):
    io.dim((-55, -20, 0), (55, -20, 0), (0, -32, 0))
    io.dimx((45, 0, 12), (55, -20, 12), (45, -47, 12), (55, -47, 12), out=-1)
    io.dim((55, -20, 0), (55, 20, 0), (12, 0, 0))
    io.dim((-55, -20, 0), (-55, -20, 12), (-9, 0, 0))
    io.dim((-32, -15, 12), (-32, -15, 68), (-12, 0, 0))
    io.dim((-24, 15, 76), (24, 15, 76), (0, 15, 0))
    io.dim((32, -15, 68), (32, 15, 68), (12, 0, 0))
    io.dimx((32, 15, 12), (32, 0, 40), (32, 27, 12), (32, 27, 40))
    io.lead(circ_pt((0, 0, 84), 14, 190), (-20, 8), "Cubo Ø28, alto 8", shelf=-1)
    io.lead(circ_pt((0, 0, 84), 8, 150), (-14, 22), "Ø16 pasante", shelf=-1)
    io.lead((28, 0, 72), (38, 12), "8 × 45°")
    io.lead(circ_pt((45, 0, 12), 5, 20), (26, 14), "2 × Ø10")
    io.lead(circ_pt((32, 0, 40), 5, 90, "x"), (30, 17), "Ø10 pasante\n(ambas columnas)")
    io.notes(SIM, "Agujero central de la base: Ø24 pasante. Agujeros Ø10 a 10 de cada extremo.",
             "Ventana pasante de 40 × 50 entre las columnas.")


# ---------------------------------------------------------------- V4 cuerpo
def v4_vistas(al, pl, la):
    al.hdim((-25, 0, 0), (25, 0, 0), -10)
    al.hdim((-45, 0, 10), (45, 0, 10), -19)
    al.vdim((-45, 0, 10), (-45, 0, 50), -54, pre="Ø", tshift=9)
    al.vdim((-25, 0, 0), (-49, 0, 30), -63)
    al.vdim((25, 0, 0), (25, 0, 60), 55)
    pl.vdim((-25, -25, 0), (-25, 25, 0), -54)
    pl.hdim((-18, -18, 0), (18, -18, 0), -34)
    pl.vdim((18, -18, 0), (18, 18, 0), 54, tshift=8)
    pl.circ_lead((18, 18, 0), 4, 60, (26, 33), "4 × Ø8, prof. 12")
    pl.lead((0, 17, 0), (-10, 33), "Alojamiento 12 × 34\nprof. 48", shelf=-1)
    la.circ_lead((0, 0, 30), 12, 120, (-18, 69), "Ø24 pasante", shelf=-1)


def v4_iso(io):
    io.dim((-25, -25, 0), (25, -25, 0), (0, -18, 0))
    io.dim((-25, -25, 0), (-25, -25, 60), (-39, 0, 0))
    io.dim((-25, -25, 60), (-25, 25, 60), (-29, 0, 0))
    io.lead(circ_pt((18, 18, 60), 4, -10), (30, 4), "4 × Ø8, prof. 12")
    io.lead((0, 17, 60), (14, 26), "Alojamiento 12 × 34\nprof. 48")
    io.lead(circ_pt((45, 0, 30), 12, 60, "x"), (26, 12), "Ø24 pasante")
    io.lead(circ_pt((45, 0, 30), 20, -20, "x"), (16, -10), "2 bocas Ø40\nlargo 20")
    io.notes(SIM, "Eje de las bocas a 30 de la base.",
             "Centros de los 4 agujeros Ø8 en cuadro de 36 × 36.")


DIMS_VISTAS.update(V1=v1_vistas, V2=v2_vistas, V3=v3_vistas, V4=v4_vistas)
DIMS_ISO.update(V1=v1_iso, V2=v2_iso, V3=v3_iso, V4=v4_iso)


if __name__ == "__main__":
    sel = sys.argv[1:] or list(PIEZAS)
    for cod in sel:
        pz = PIEZAS[cod]()
        bb = cq.Shape.cast(pz.shape).BoundingBox()
        print(cod, pz.nombre, f"envolvente {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f}",
              f"volumen {cq.Shape.cast(pz.shape).Volume():.0f} mm3")
        print("  ", lam_vistas(pz))
        print("  ", lam_iso(pz))
