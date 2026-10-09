"""Genera una lámina A4 vertical con cajetín ISO 7200 (180 x 36 mm) en DXF.
El cajetín es un bloque con atributos: en AutoCAD se llena con doble clic.
Uso: python3 cajetin_iso7200.py   (requiere: pip install ezdxf)"""
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

doc = ezdxf.new("R2010", setup=True)          # setup=True carga tipos de línea y estilos
doc.units = ezdxf.units.MM
doc.header["$MEASUREMENT"] = 1; doc.header["$INSUNITS"] = 4
CAPAS = [("Visible", 7, "Continuous", 50), ("Oculta", 7, "DASHED", 25), ("Ejes", 7, "CENTER", 25),
         ("Cotas", 7, "Continuous", 25), ("Rayado", 7, "Continuous", 25), ("Auxiliar", 8, "Continuous", 13),
         ("Cajetin", 7, "Continuous", 25), ("Cajetin_grueso", 7, "Continuous", 50), ("Ventanas", 8, "Continuous", 13)]
for n, c, lt, lw in CAPAS:
    doc.layers.add(n, color=c, linetype=lt, lineweight=lw)
doc.layers.get("Ventanas").dxf.plot = 0
doc.styles.add("ISO", font="isocp.shx")

blk = doc.blocks.new("CAJETIN_ISO7200")       # origen: esquina inferior derecha
W, Hh = 180, 36
def L(p, q, capa="Cajetin"): blk.add_line(p, q, dxfattribs={"layer": capa})
def rect(x0, y0, x1, y1, capa): blk.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": capa})
rect(-W, 0, 0, Hh, "Cajetin_grueso"); rect(-W, 0, 0, 12, "Cajetin_grueso")
L((-W, 24), (0, 24))
filas = [  # (y, [(ancho, rótulo, tag, valor por defecto, altura)])
    (0,  [(60, "Propietario legal", "PROPIETARIO", "Universidad Católica de Temuco", 2.5), (80, "Título", "TITULO", "TÍTULO DE LA LÁMINA", 3.5), (40, "N.º de identificación", "NUMERO", "PCI1119-G3-L01", 2.5)]),
    (12, [(50, "Tipo de documento", "TIPO", "Plano de pieza", 2.5), (50, "Autor", "AUTOR", "Nombre Apellido", 2.5), (40, "Aprobado por", "APROBADO", "M. Godoy", 2.5), (40, "Fecha", "FECHA", "2026-11-01", 2.5)]),
    (24, [(30, "Escala", "ESCALA", "1:1", 3.5), (30, "", None, None, 0), (30, "Unidades", "UNIDADES", "mm", 2.5), (30, "Hoja", "HOJA", "1/1", 2.5), (60, "Formato", "FORMATO", "A4", 2.5)]),
]
for y, celdas in filas:
    x = -W
    for i, (w, rot, tag, val, h) in enumerate(celdas):
        if i: L((x, y), (x, y + 12))
        if rot: blk.add_text(rot, height=1.8, dxfattribs={"layer": "Cajetin", "style": "ISO", "color": 8}).set_placement((x + 1.5, y + 9.4), align=TA.LEFT)
        if tag:
            a = blk.add_attdef(tag, (x + 1.5, y + 2.2), dxfattribs={"layer": "Cajetin", "style": "ISO", "height": h, "prompt": rot})
            a.dxf.text = val
        x += w
# símbolo de primer diedro (celda x de -150 a -120, y de 24 a 36)
cx, cy = -143.5, 30
blk.add_lwpolyline([(cx - 5, cy - 2), (cx + 5, cy - 4), (cx + 5, cy + 4), (cx - 5, cy + 2)], close=True, dxfattribs={"layer": "Cajetin"})
blk.add_line((cx - 7, cy), (cx + 7, cy), dxfattribs={"layer": "Ejes"})
c2 = (-128, 30)
for r in (2, 4): blk.add_circle(c2, r, dxfattribs={"layer": "Cajetin"})
blk.add_line((c2[0] - 5.5, cy), (c2[0] + 5.5, cy), dxfattribs={"layer": "Ejes"}); blk.add_line((c2[0], cy - 5.5), (c2[0], cy + 5.5), dxfattribs={"layer": "Ejes"})

msp = doc.modelspace()                        # lámina A4 vertical de ejemplo
msp.add_lwpolyline([(0, 0), (210, 0), (210, 297), (0, 297)], close=True, dxfattribs={"layer": "Auxiliar"})
msp.add_lwpolyline([(20, 10), (200, 10), (200, 287), (20, 287)], close=True, dxfattribs={"layer": "Cajetin_grueso"})
ins = msp.add_blockref("CAJETIN_ISO7200", (200, 10), dxfattribs={"layer": "Cajetin"})
ins.add_auto_attribs({a.dxf.tag: a.dxf.text for a in blk.query("ATTDEF")})
doc.set_modelspace_vport(height=320, center=(105, 148))
doc.saveas("Lamina_A4_cajetin_ISO7200.dxf")
print("ok")
