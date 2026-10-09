# -*- coding: utf-8 -*-
"""
Nucleo de correccion de la Actividad 1 (reconocimiento de vistas con color).
PCI1119 Sistemas de Representacion.

No depende de tkinter ni del portapapeles: recibe una imagen PIL y devuelve el
resultado. Asi la interfaz grafica y las pruebas headless usan el mismo motor.

Requiere solamente: pillow y numpy.
"""

import json
import os
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

# Compatibilidad entre Pillow antiguo y nuevo
_R = getattr(Image, "Resampling", Image)
BILINEAL = _R.BILINEAR
LANCZOS = _R.LANCZOS

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto
# La pauta procesada es comun a todas las secciones: vive junto a los scripts,
# no dentro de la carpeta de cada seccion.
CARPETA_PAUTA = contexto.CARPETA_PAUTA

# Colores del codigo del applet (RGB exactos)
ANCHO_BUSQUEDA = 260.0

COLORES_CODIGO = {
    "rojo": (255, 0, 0),
    "amarillo": (255, 255, 0),
    "cyan": (0, 255, 255),
    "naranjo": (255, 187, 0),
    "verde": (0, 255, 0),
    "azul": (0, 0, 255),
    "marron": (204, 102, 102),
}
# Colores que NO son respuesta del alumno
COLORES_NEUTROS = {
    "blanco": (255, 255, 255),
    "negro": (0, 0, 0),
    "fondo": (243, 240, 231),
}


# ---------------------------------------------------------------- utilidades

def _a_rgb(img):
    """PIL -> ndarray uint8 HxWx3, descartando transparencia sobre blanco."""
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        fondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(fondo, img)
    return np.asarray(img.convert("RGB"), dtype=np.uint8)


def _mascara_tinta(rgb):
    """Pixeles de linea negra / texto. Usa el canal maximo para no confundir
    los colores saturados (el rojo puro tiene media baja pero maximo 255)."""
    maxc = rgb.max(axis=2).astype(np.int16)
    p98 = float(np.percentile(maxc, 98))
    umbral = max(70.0, 0.42 * p98)
    return maxc < umbral


def _mascara_saturada(rgb):
    """Pixeles de color fuerte (las caras pintadas)."""
    x = rgb.astype(np.int16)
    return (x.max(axis=2) - x.min(axis=2)) > 55


def _dilatar(m, k=1):
    """Dilatacion binaria con desplazamientos de numpy (sin opencv)."""
    out = m.copy()
    for _ in range(k):
        acc = out.copy()
        acc[1:, :] |= out[:-1, :]
        acc[:-1, :] |= out[1:, :]
        acc[:, 1:] |= out[:, :-1]
        acc[:, :-1] |= out[:, 1:]
        out = acc
    return out


def _erosionar(m, k=1):
    out = m.copy()
    for _ in range(k):
        acc = out.copy()
        acc[1:, :] &= out[:-1, :]
        acc[:-1, :] &= out[1:, :]
        acc[:, 1:] &= out[:, :-1]
        acc[:, :-1] &= out[:, 1:]
        out = acc
    return out


def _componentes(m):
    """Etiquetado de componentes conexas por BFS. Pensado para mascaras chicas
    (se usa sobre una version reducida a 200 px de ancho)."""
    alto, ancho = m.shape
    etiquetas = np.zeros((alto, ancho), dtype=np.int32)
    actual = 0
    cajas = []
    for y0 in range(alto):
        for x0 in range(ancho):
            if not m[y0, x0] or etiquetas[y0, x0]:
                continue
            actual += 1
            cola = deque([(y0, x0)])
            etiquetas[y0, x0] = actual
            minx = maxx = x0
            miny = maxy = y0
            area = 0
            while cola:
                y, x = cola.popleft()
                area += 1
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < alto and 0 <= nx < ancho and m[ny, nx] and not etiquetas[ny, nx]:
                        etiquetas[ny, nx] = actual
                        cola.append((ny, nx))
            cajas.append({"id": actual, "area": area,
                          "bbox": (minx, miny, maxx, maxy)})
    return etiquetas, cajas


def caja_de_contenido(rgb, umbral_rel=0.10, max_bloques=None):
    """Devuelve el bounding box (x0, y0, x1, y1) de las 4 piezas dibujadas.

    Se apoya SOLO en los pixeles de color fuerte: asi ignora barras de estado,
    barras de navegacion, migas de pan, titulos, numeros de pagina y cualquier
    texto negro que rodee a la lamina. Despues descarta el panel derecho del
    applet (la pieza modelo y la leyenda) si quedo dentro del recorte."""
    alto, ancho = rgb.shape[:2]
    escala = min(1.0, 300.0 / max(ancho, 1))
    ah, aw = max(1, int(alto * escala)), max(1, int(ancho * escala))
    chico = np.asarray(Image.fromarray(rgb).resize((aw, ah), BILINEAL))

    m = _dilatar(_mascara_saturada(chico), 3)
    etiquetas, cajas = _componentes(m)
    if not cajas:
        # sin color: caemos a la tinta, por si es una lamina sin pintar
        m = _dilatar(_mascara_tinta(chico), 3)
        etiquetas, cajas = _componentes(m)
        if not cajas:
            return (0, 0, ancho, alto), 0.0

    # Filtro de forma: una pieza isometrica es un bloque compacto. Las barras de
    # estado y de navegacion son franjas larguisimas y planas; las migas de pan
    # y el texto son ralos. Ambos se descartan aqui.
    compactas = []
    for c in cajas:
        x0, y0, x1, y1 = c["bbox"]
        w = x1 - x0 + 1; h = y1 - y0 + 1
        razon = w / float(h)
        llenado = c["area"] / float(w * h)
        if 0.20 <= razon <= 5.0 and llenado >= 0.30:
            compactas.append(c)
    if compactas:
        cajas = compactas

    cajas.sort(key=lambda c: -c["area"])
    mayor = cajas[0]["area"]
    buenas = [c for c in cajas if c["area"] >= umbral_rel * mayor]
    if max_bloques:
        buenas = sorted(buenas, key=lambda c: -c["area"])[:max_bloques]

    # Panel derecho: la pieza modelo queda como un bloque suelto a la derecha y
    # es mucho mas chico que la suma de las piezas del panel izquierdo.
    buenas.sort(key=lambda c: c["bbox"][0])
    if len(buenas) >= 2:
        for k in range(len(buenas) - 1, 0, -1):
            izquierda = buenas[:k]
            derecha = buenas[k:]
            corte_izq = max(c["bbox"][2] for c in izquierda)
            inicio_der = min(c["bbox"][0] for c in derecha)
            if inicio_der - corte_izq < 4:
                continue  # no hay banda vacia real, no se puede separar aqui
            area_izq = sum(c["area"] for c in izquierda)
            area_der = sum(c["area"] for c in derecha)
            ancho_total = max(c["bbox"][2] for c in buenas) - min(c["bbox"][0] for c in buenas) + 1
            centro = (corte_izq + inicio_der) / 2.0
            rel = (centro - min(c["bbox"][0] for c in buenas)) / float(max(ancho_total, 1))
            if area_der < 0.35 * area_izq and rel > 0.55:
                buenas = izquierda
                break

    minx = min(c["bbox"][0] for c in buenas)
    miny = min(c["bbox"][1] for c in buenas)
    maxx = max(c["bbox"][2] for c in buenas)
    maxy = max(c["bbox"][3] for c in buenas)

    # Margen para no cortar las lineas negras del contorno de las piezas
    margen = max(2, int(0.012 * max(maxx - minx, maxy - miny)))
    minx = max(0, minx - margen); miny = max(0, miny - margen)
    maxx = min(aw - 1, maxx + margen); maxy = min(ah - 1, maxy + margen)

    inv = 1.0 / escala
    caja = (int(minx * inv), int(miny * inv),
            int(min(ancho, (maxx + 1) * inv)), int(min(alto, (maxy + 1) * inv)))
    cobertura = float(m.sum()) / float(aw * ah)
    return caja, cobertura


def encajar(rgb, caja_origen, caja_destino, tam_destino, relleno=(243, 240, 231)):
    """Recorta rgb segun caja_origen y lo escala para que ocupe caja_destino
    dentro de un lienzo de tamano tam_destino."""
    x0, y0, x1, y1 = caja_origen
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(rgb.shape[1], max(x1, x0 + 1)); y1 = min(rgb.shape[0], max(y1, y0 + 1))
    recorte = Image.fromarray(rgb[y0:y1, x0:x1])
    dx0, dy0, dx1, dy1 = caja_destino
    ancho = max(1, dx1 - dx0); alto = max(1, dy1 - dy0)
    recorte = recorte.resize((ancho, alto), BILINEAL)
    lienzo = Image.new("RGB", (tam_destino[0], tam_destino[1]), relleno)
    lienzo.paste(recorte, (dx0, dy0))
    return np.asarray(lienzo, dtype=np.uint8)


def _iou(a, b):
    u = np.count_nonzero(a | b)
    return 0.0 if u == 0 else np.count_nonzero(a & b) / float(u)


# -------------------------------------------------------------------- pautas

class Pauta(object):
    def __init__(self, lamina, datos, ref, mask):
        self.lamina = lamina
        self.leyenda = datos["leyenda"]
        self.piezas = datos["piezas"]
        self.ref = ref
        self.mask = mask
        self.caras = []
        for p in datos["piezas"]:
            for c in p["caras"]:
                d = dict(c)
                d["pieza"] = p["pieza"]
                self.caras.append(d)
        # indice global de cada cara dentro de la mascara (1..M, mismo orden)
        for i, c in enumerate(self.caras):
            c["indice"] = i + 1
        self.tinta = _mascara_tinta(ref)
        self.caja, _ = caja_de_contenido(ref)
        # Version reducida: la busqueda de encuadre se hace aqui, no a tamano real
        self.fs = ANCHO_BUSQUEDA / float(ref.shape[1])
        self.tam_s = (max(1, int(ref.shape[1] * self.fs)),
                      max(1, int(ref.shape[0] * self.fs)))
        chica = np.asarray(Image.fromarray(ref).resize(self.tam_s, BILINEAL))
        self.tinta_s = _dilatar(_mascara_tinta(chica), 1)


def cargar_pautas(carpeta=None):
    carpeta = carpeta or CARPETA_PAUTA
    pautas = {}
    for n in range(1, 6):
        j = os.path.join(carpeta, "lamina%d.json" % n)
        r = os.path.join(carpeta, "lamina%d_ref.png" % n)
        m = os.path.join(carpeta, "lamina%d_mask.png" % n)
        if not (os.path.exists(j) and os.path.exists(r) and os.path.exists(m)):
            continue
        with open(j, "r", encoding="utf-8") as f:
            datos = json.load(f)
        ref = _a_rgb(Image.open(r))
        mask = np.asarray(Image.open(m)).astype(np.int32)
        pautas[n] = Pauta(n, datos, ref, mask)
    return pautas


# --------------------------------------------------- identificacion y ajuste

def _alinear_contra(rgb, caja_est, pauta, refinar=True):
    """Encaja la imagen del alumno en el sistema de coordenadas de la pauta.

    La busqueda del encuadre se hace sobre una version reducida (rapida) y solo
    el encuadre ganador se aplica a tamano real."""
    W = pauta.ref.shape[1]
    H = pauta.ref.shape[0]
    px0, py0, px1, py1 = pauta.caja
    w0 = px1 - px0
    h0 = py1 - py0
    fs = pauta.fs
    Ws, Hs = pauta.tam_s

    # Fuente recortada y ya reducida: todas las pruebas parten de aqui
    x0, y0, x1, y1 = caja_est
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(rgb.shape[1], max(x1, x0 + 1)); y1 = min(rgb.shape[0], max(y1, y0 + 1))
    fuente = Image.fromarray(rgb[y0:y1, x0:x1])
    fw = max(1, int((x1 - x0) * fs * 1.3))
    fh = max(1, int((y1 - y0) * fs * 1.3))
    fuente_np = np.asarray(fuente.resize((fw, fh), BILINEAL), dtype=np.uint8)
    caja_fuente = (0, 0, fw, fh)

    def prueba(ds, dx, dy):
        nw = int(w0 * (1 + ds)); nh = int(h0 * (1 + ds))
        nx0 = px0 + dx - (nw - w0) // 2
        ny0 = py0 + dy - (nh - h0) // 2
        destino = (int(nx0 * fs), int(ny0 * fs),
                   int((nx0 + nw) * fs), int((ny0 + nh) * fs))
        cand = encajar(fuente_np, caja_fuente, destino, (Ws, Hs))
        s = _iou(_dilatar(_mascara_tinta(cand), 1), pauta.tinta_s)
        return s, (nx0, ny0, nw, nh)

    mejor_s, mejor_p = prueba(0.0, 0, 0)
    if refinar:
        for ds in (-0.06, -0.03, 0.0, 0.03, 0.06):
            for dx in (-12, -8, -4, 0, 4, 8, 12):
                for dy in (-12, -8, -4, 0, 4, 8, 12):
                    if ds == 0.0 and dx == 0 and dy == 0:
                        continue
                    s, pr = prueba(ds, dx, dy)
                    if s > mejor_s:
                        mejor_s, mejor_p = s, pr

    nx0, ny0, nw, nh = mejor_p
    img = encajar(rgb, caja_est, (nx0, ny0, nx0 + nw, ny0 + nh), (W, H))
    return img, mejor_s


def identificar(rgb, pautas, lamina_forzada=None, caja=None):
    """Decide a que lamina corresponde la imagen y la alinea.
    Devuelve dict con lamina, imagen alineada, score y el ranking completo."""
    if caja is None:
        caja, _ = caja_de_contenido(rgb)
    cobertura = 0.0
    candidatas = [lamina_forzada] if lamina_forzada else sorted(pautas.keys())

    # Primera pasada barata: sin refinamiento, solo para ordenar.
    ranking = []
    for n in candidatas:
        _, s = _alinear_contra(rgb, caja, pautas[n], refinar=False)
        ranking.append((n, s))
    ranking.sort(key=lambda t: -t[1])

    # Refinamos solo las dos mejores.
    finalistas = ranking[:2] if len(ranking) > 1 else ranking
    mejores = []
    for n, _ in finalistas:
        img, s = _alinear_contra(rgb, caja, pautas[n], refinar=True)
        mejores.append((n, s, img))
    mejores.sort(key=lambda t: -t[1])

    n, score, img = mejores[0]
    segundo = mejores[1][1] if len(mejores) > 1 else 0.0
    return {
        "lamina": n,
        "imagen": img,
        "score": score,
        "margen": score - segundo,
        "ranking": ranking,
        "caja": caja,
        "cobertura": cobertura,
    }


# ----------------------------------------------------------------- puntuacion

def _paleta(pauta):
    nombres = []
    valores = []
    for k in pauta.leyenda.keys():
        if k in COLORES_CODIGO:
            nombres.append(k)
            valores.append(COLORES_CODIGO[k])
    for k, v in COLORES_NEUTROS.items():
        nombres.append(k)
        valores.append(v)
    return nombres, np.array(valores, dtype=np.int16)


def puntuar(img_alineada, pauta):
    """Clasifica el color de cada cara por voto de mayoria sobre todos los
    pixeles de la cara segun la mascara de la pauta."""
    nombres, paleta = _paleta(pauta)

    x = img_alineada.astype(np.int16)
    # distancia a cada color de la paleta
    d = np.abs(x[:, :, None, :] - paleta[None, None, :, :]).sum(axis=3)
    cerca = d.argmin(axis=2)
    dist_min = d.min(axis=2)
    # pixeles demasiado lejos de todo -> categoria "otro"
    otro = dist_min > 190

    detalle = []
    correctas = 0
    pix_total = 0
    pix_codigo = 0
    for cara in pauta.caras:
        sel = (pauta.mask == cara["indice"])
        total = int(sel.sum())
        if total == 0:
            continue
        vals = cerca[sel]
        es_otro = otro[sel]
        conteo = {}
        for i, n in enumerate(nombres):
            c = int(np.count_nonzero((vals == i) & (~es_otro)))
            if c:
                conteo[n] = c
        n_otro = int(np.count_nonzero(es_otro))
        if n_otro:
            conteo["otro"] = n_otro

        # voto de mayoria entre colores del codigo
        del_codigo = {k: v for k, v in conteo.items() if k in COLORES_CODIGO}
        if del_codigo:
            detectado = max(del_codigo, key=del_codigo.get)
            apoyo = del_codigo[detectado] / float(total)
        else:
            detectado = max(conteo, key=conteo.get) if conteo else "indeterminado"
            apoyo = (conteo.get(detectado, 0) / float(total)) if conteo else 0.0

        # si casi no hay color del codigo, la cara quedo sin pintar
        cobertura_codigo = sum(del_codigo.values()) / float(total)
        pix_total += total
        pix_codigo += sum(del_codigo.values())
        if cobertura_codigo < 0.25:
            blancos = conteo.get("blanco", 0) / float(total)
            detectado = "sin pintar" if blancos > 0.25 else "indeterminado"
            apoyo = max(blancos, apoyo)

        ok = (detectado == cara["color"])
        if ok:
            correctas += 1
        detalle.append({
            "id": cara["id"],
            "pieza": cara["pieza"],
            "indice": cara["indice"],
            "esperado": cara["color"],
            "detectado": detectado,
            "correcto": ok,
            "apoyo": round(apoyo, 3),
            "area": total,
        })

    total_caras = len(detalle)
    puntaje = 100.0 * correctas / total_caras if total_caras else 0.0
    # Cobertura de color: que fraccion de los pixeles de las caras de la pauta
    # cae sobre un color del codigo en la imagen del alumno. Es la senal que
    # distingue un calce real de una pagina en blanco o de un recorte corrido:
    # una hoja vacia se lee con "certeza" altisima pero cobertura casi nula.
    cobertura_color = (pix_codigo / float(pix_total)) if pix_total else 0.0
    return {
        "lamina": pauta.lamina,
        "cobertura_color": round(cobertura_color, 3),
        "caras_total": total_caras,
        "caras_correctas": correctas,
        "puntaje": round(puntaje, 1),
        "detalle": detalle,
        "errores": [d for d in detalle if not d["correcto"]],
    }


ESTRATEGIAS = (
    {"umbral_rel": 0.10, "max_bloques": None, "nombre": "normal"},
    {"umbral_rel": 0.30, "max_bloques": None, "nombre": "solo bloques grandes"},
    {"umbral_rel": 0.10, "max_bloques": 4, "nombre": "las 4 piezas mayores"},
)
COBERTURA_BUENA = 0.85


def _un_intento(rgb, pautas, lamina_forzada, caja):
    ident = identificar(rgb, pautas, lamina_forzada, caja=caja)
    pauta = pautas[ident["lamina"]]
    res = puntuar(ident["imagen"], pauta)
    apoyos = [d["apoyo"] for d in res["detalle"]] or [0.0]
    confianza = sum(apoyos) / len(apoyos)
    res["confianza"] = round(confianza, 3)
    res["calidad"] = round(res["cobertura_color"] * confianza
                           + 0.15 * ident["score"], 4)
    res["_ident"] = ident
    return res


def corregir(img_pil, pautas, lamina_forzada=None):
    """Entrada principal: imagen PIL -> resultado completo.

    Prueba varias formas de recortar el area util y se queda con la que mejor
    calza. Una sola estrategia falla, por ejemplo, cuando la captura incluye la
    barra de botones del applet y el recorte queda corrido hacia arriba."""
    rgb = _a_rgb(img_pil)

    mejor = None
    usada = None
    for est in ESTRATEGIAS:
        caja, _ = caja_de_contenido(rgb, est["umbral_rel"], est["max_bloques"])
        try:
            res = _un_intento(rgb, pautas, lamina_forzada, caja)
        except Exception:
            continue
        if mejor is None or res["calidad"] > mejor["calidad"]:
            mejor = res
            usada = est["nombre"]
        if res["cobertura_color"] >= COBERTURA_BUENA:
            break

    if mejor is None:
        raise RuntimeError("No se pudo interpretar la imagen")

    res = mejor
    ident = res.pop("_ident")
    confianza = res["confianza"]
    res["score_alineacion"] = round(ident["score"], 3)
    res["margen"] = round(ident["margen"], 3)
    res["ranking"] = [(n, round(sc, 3)) for n, sc in ident["ranking"]]
    res["imagen_alineada"] = ident["imagen"]
    res["lamina_forzada"] = lamina_forzada is not None
    res["recorte"] = usada

    avisos = []
    if res["cobertura_color"] < 0.75:
        avisos.append("Solo el %.0f%% de las caras de la pauta cae sobre color en esta imagen. "
                      "Puede que no sea esta lamina, que el recorte este corrido, o que la "
                      "entrega no corresponda a esta actividad."
                      % (100 * res["cobertura_color"]))
    if confianza < 0.80:
        avisos.append("Lectura de color poco nitida (confianza %.0f%%). Suele pasar con capturas "
                      "muy chicas o fotos con brillo. Revisa a ojo." % (100 * confianza))
    elif confianza < 0.90:
        avisos.append("Confianza media (%.0f%%). Verifica las caras marcadas antes de anotar."
                      % (100 * confianza))
    rel = ident["margen"] / max(ident["score"], 1e-6)
    if not lamina_forzada and rel < 0.10:
        avisos.append("La lamina %d gano por poco margen. Si no calza, forzala en el selector."
                      % ident["lamina"])
    flojas = [d for d in res["detalle"] if d["apoyo"] < 0.55]
    if flojas:
        avisos.append("%d cara(s) se leyeron con poca certeza: %s"
                      % (len(flojas), ", ".join(d["id"] for d in flojas[:8])))
    res["avisos"] = avisos
    return res


# ------------------------------------------------------------------ dibujado

def _borde(m):
    return m & ~_erosionar(m, 1)


def render(res, pauta, ancho_max=1180):
    """Arma la imagen de resultado: pauta a la izquierda, entrega alineada a la
    derecha con las caras erradas marcadas."""
    izq = pauta.ref.copy()
    der = res["imagen_alineada"].copy()

    for d in res["errores"]:
        sel = (pauta.mask == d["indice"])
        b = _dilatar(_borde(sel), 1)
        color = (255, 0, 255) if d["detectado"] != "sin pintar" else (255, 140, 0)
        der[b] = color
        izq[b] = (120, 120, 120)

    ia = Image.fromarray(izq)
    ib = Image.fromarray(der)
    h = max(ia.height, ib.height)
    sep = 12
    lienzo = Image.new("RGB", (ia.width + ib.width + sep, h + 26), (255, 255, 255))
    lienzo.paste(ia, (0, 26))
    lienzo.paste(ib, (ia.width + sep, 26))
    dr = ImageDraw.Draw(lienzo)
    dr.text((6, 7), "PAUTA  -  lamina %d" % pauta.lamina, fill=(40, 40, 40))
    dr.text((ia.width + sep + 6, 7), "ENTREGA ALINEADA  -  caras erradas en magenta, sin pintar en naranjo",
            fill=(40, 40, 40))

    # rotulo del id sobre cada cara errada
    for d in res["errores"]:
        cara = next(c for c in pauta.caras if c["indice"] == d["indice"])
        px, py = cara["punto_seguro"]
        dr.text((ia.width + sep + px - 14, py + 26 - 5), d["id"], fill=(0, 0, 0))

    if lienzo.width > ancho_max:
        f = ancho_max / float(lienzo.width)
        lienzo = lienzo.resize((ancho_max, int(lienzo.height * f)), LANCZOS)
    return lienzo
