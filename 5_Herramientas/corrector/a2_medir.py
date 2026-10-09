# -*- coding: utf-8 -*-
"""
Actividad 2: identifica que ejercicio resolvio el alumno y mide cuanto se
aparta de la pauta, vista por vista.

Esta version SOLO MIDE. No pone puntaje ni genera reportes: entrega los
numeros para que el profesor decida los umbrales mirando casos reales.

    python a2_medir.py "<carpeta del alumno>"
    python a2_medir.py "<carpeta de entregas>" --todos
    python a2_medir.py "<carpeta>" --csv salida.csv

Como funciona
-------------
Cada imagen del applet trae cuatro cuadrantes: alzado arriba-izquierda, perfil
arriba-derecha, planta abajo-izquierda, y la pieza isometrica abajo-derecha.
Las tres primeras las dibuja el alumno; la cuarta la dibuja el applet.

Identificar cual de las 44 piezas es no es trivial: el applet asigna los colores
de las caras AL AZAR, asi que la pieza 3D no se puede comparar por color entre
una captura y otra. Se combinan tres senales:

  1. el nivel, que viene en el nombre del archivo (elemental / medio / alto)
  2. el parecido del trazo de las tres vistas contra la pauta
  3. el parecido de las fronteras entre caras de la pieza 3D, que sobreviven al
     cambio de colores

y despues una asignacion global, para que dos imagenes del mismo alumno no
reclamen la misma pieza.
"""

import argparse
import csv
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto

PAUTA_A2 = os.path.join(contexto.HERRAMIENTAS, "pauta_actividad2")
NIVEL_ARCHIVO = {"ele": "elemental", "med": "medio", "alto": "alto"}
VISTAS = ("alzado", "perfil", "planta")
IMG = (".jpg", ".jpeg", ".png")

# La pieza isometrica manda al identificar: la dibuja el applet, no el alumno,
# asi que es la misma siempre que el ejercicio sea el mismo. Las vistas apoyan,
# pero pesan menos porque justamente son lo que el alumno puede equivocar.
PESO_VISTAS = 0.45
PESO_3D = 0.55
TOLERANCIA_TAM = 8   # px de diferencia que se aceptan y se corrigen reescalando
# Tolerancia al comparar el trazo. No se corrige precision de pixel: una captura
# con otro zoom desplaza las lineas uno o dos pixeles y eso no es un error del
# alumno. Se engordan ambos trazos antes de medir el solape.
DILATA_TRAZO = 2


# ------------------------------------------------------------------ imagenes

def cuadrantes(a):
    """alzado, perfil, planta, pieza3d. El applet usa siempre esta disposicion,
    que es la de primer diedro: planta debajo del alzado, perfil a su derecha."""
    h, w = a.shape[:2]
    my, mx = h // 2, w // 2
    return a[:my, :mx], a[:my, mx:], a[my:, :mx], a[my:, mx:]


def trazo(q):
    """Lineas del dibujo: rojo oscuro, tanto las visibles como las ocultas."""
    r = q[:, :, 0].astype(int)
    g = q[:, :, 1].astype(int)
    b = q[:, :, 2].astype(int)
    return (r > 70) & (r < 190) & (g < 90) & (b < 90)


def trazo_continuo(q):
    """Solo las lineas visibles, descartando los trazos discontinuos.

    Se aproxima por grosor: la linea llena es mas gruesa que la de trazos. Se
    queda con los pixeles que sobreviven a una erosion suave."""
    m = trazo(q)
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    return e


def bordes(q):
    """Frontera entre regiones de color. Es la misma aunque el applet cambie
    los colores de las caras, que es justo lo que hace entre captura y captura."""
    g = q.astype(np.int16)
    dx = np.abs(np.diff(g, axis=1)).sum(2)
    dy = np.abs(np.diff(g, axis=0)).sum(2)
    m = np.zeros(q.shape[:2], bool)
    m[:, :-1] |= dx > 90
    m[:, 1:] |= dx > 90
    m[:-1, :] |= dy > 90
    m[1:, :] |= dy > 90
    return m


def dilatar(m, k=1):
    o = m.copy()
    for _ in range(k):
        n = o.copy()
        n[1:, :] |= o[:-1, :]
        n[:-1, :] |= o[1:, :]
        n[:, 1:] |= o[:, :-1]
        n[:, :-1] |= o[:, 1:]
        o = n
    return o


def iou(x, y):
    u = np.count_nonzero(x | y)
    return np.count_nonzero(x & y) / u if u else 0.0



# ------------------------------------------- normalizacion por caja de dibujo

def caja(m):
    """Bounding box de lo dibujado: (x0, y0, x1, y1) o None si esta vacio."""
    if not m.any():
        return None
    ys = np.where(m.any(axis=1))[0]
    xs = np.where(m.any(axis=0))[0]
    return int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1


def encajar_en(m_alumno, m_pauta):
    """Lleva el dibujo del alumno a la caja del dibujo de la pauta.

    Sin esto, un alumno que dibuje las mismas vistas pero mas chicas o corridas
    daria cero coincidencia: ninguna linea caeria sobre la otra. Lo que se
    evalua es la FORMA de la vista, no el tamano al que la dibujo ni donde la
    puso dentro del recuadro."""
    ca, cp = caja(m_alumno), caja(m_pauta)
    if ca is None or cp is None:
        return m_alumno
    ax0, ay0, ax1, ay1 = ca
    px0, py0, px1, py1 = cp
    recorte = Image.fromarray((m_alumno[ay0:ay1, ax0:ax1] * 255).astype(np.uint8))
    ancho, alto = max(1, px1 - px0), max(1, py1 - py0)
    recorte = recorte.resize((ancho, alto), Image.BILINEAR)
    lienzo = Image.new("L", (m_pauta.shape[1], m_pauta.shape[0]), 0)
    lienzo.paste(recorte, (px0, py0))
    return np.asarray(lienzo) > 60


def iou_encajado(m_alumno, m_pauta, k=DILATA_TRAZO):
    """Solape despues de igualar las cajas, que es lo que de verdad importa."""
    a = dilatar(encajar_en(m_alumno, m_pauta), k)
    b = dilatar(m_pauta, k)
    return iou(a, b)


def aristas_pieza(q, margen=6):
    """Aristas de la pieza isometrica, insensibles al color de las caras.

    El applet reparte los colores al azar en cada carga, y en el nivel alto los
    pinta con degradados. Un degradado no es una arista: se difumina primero
    para aplanarlo y solo sobrevive el salto de una frontera real entre caras.

    Se descarta un margen en el borde del cuadrante: al difuminar, el limite de
    la imagen genera un salto artificial que es identico en todas las piezas y
    haria que todas se parecieran entre si."""
    im = Image.fromarray(q.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    g = np.asarray(im, dtype=np.int16)
    dx = np.abs(np.diff(g, axis=1)).sum(2)
    dy = np.abs(np.diff(g, axis=0)).sum(2)
    m = np.zeros(q.shape[:2], bool)
    m[:, :-1] |= dx > 70
    m[:, 1:] |= dx > 70
    m[:-1, :] |= dy > 70
    m[1:, :] |= dy > 70
    if margen:
        m[:margen, :] = False
        m[-margen:, :] = False
        m[:, :margen] = False
        m[:, -margen:] = False
    return m


# -------------------------------------------------------------------- pautas

def cargar_pautas():
    pautas = {}
    for f in sorted(os.listdir(PAUTA_A2)):
        if not f.lower().endswith(IMG):
            continue
        partes = f.replace(".jpg", "").split("_")
        nivel = NIVEL_ARCHIVO.get(partes[2] if len(partes) > 2 else "", "?")
        a = np.asarray(Image.open(os.path.join(PAUTA_A2, f)).convert("RGB"))
        q = cuadrantes(a)
        pautas[f] = {
            "nivel": nivel,
            "shape": a.shape,
            "vistas_crudas": [trazo(x) for x in q[:3]],
            "vistas_cont_crudas": [trazo_continuo(x) for x in q[:3]],
            "vistas": [dilatar(trazo(x), DILATA_TRAZO) for x in q[:3]],
            "vistas_cont": [dilatar(trazo_continuo(x), DILATA_TRAZO) for x in q[:3]],
            "p3d": dilatar(aristas_pieza(q[3]), 2),
        }
    if not pautas:
        raise SystemExit("No hay pautas en %s" % PAUTA_A2)
    return pautas


def nivel_de(nombre):
    n = nombre.lower()
    for k in ("elemental", "medio", "alto"):
        if k in n:
            return k
    return None


# --------------------------------------------------------------- comparacion

def abrir_ajustada(ruta, tamanos):
    """Abre la imagen y, si su tamano difiere de alguna pauta por unos pocos
    pixeles, la reescala a ese tamano. Los navegadores guardan la captura con
    uno o dos pixeles de mas segun el zoom, y sin esto no calzaria nada."""
    im = Image.open(ruta).convert("RGB")
    w, h = im.size
    for (pw, ph) in tamanos:
        if (w, h) == (pw, ph):
            return np.asarray(im)
    for (pw, ph) in tamanos:
        if abs(w - pw) <= TOLERANCIA_TAM and abs(h - ph) <= TOLERANCIA_TAM:
            # Se RECORTA o rellena, nunca se reescala: reescalar mueve las
            # lineas una fraccion de pixel y un trazo fino deja de solapar con
            # el de la pauta, lo que se leeria como error del alumno.
            lienzo = Image.new("RGB", (pw, ph), (243, 240, 233))
            ox, oy = (pw - w) // 2, (ph - h) // 2
            lienzo.paste(im, (ox, oy))
            return np.asarray(lienzo)
    return np.asarray(im)


def candidatas(ruta, pautas):
    tamanos = sorted({(p["shape"][1], p["shape"][0]) for p in pautas.values()})
    a = abrir_ajustada(ruta, tamanos)
    q = cuadrantes(a)
    sv = [trazo(x) for x in q[:3]]
    svc = [trazo_continuo(x) for x in q[:3]]
    s3 = dilatar(aristas_pieza(q[3]), 2)
    niv = nivel_de(os.path.basename(ruta))

    filas = []
    for nom, p in pautas.items():
        if p["shape"] != a.shape:
            continue
        if niv and p["nivel"] != niv:
            continue
        por_vista = [iou_encajado(sv[i], p["vistas_crudas"][i]) for i in range(3)]
        por_vista_c = [iou_encajado(svc[i], p["vistas_cont_crudas"][i]) for i in range(3)]
        tri = iou(s3, p["p3d"])
        score = PESO_VISTAS * float(np.mean(por_vista)) + PESO_3D * tri
        filas.append({
            "pauta": nom, "score": score, "sim3d": tri,
            "vistas": por_vista, "vistas_cont": por_vista_c,
        })
    filas.sort(key=lambda d: -d["score"])
    return filas


def procesar_alumno(carpeta, pautas, temporal=None):
    rutas = []
    for raiz, _, nombres in os.walk(carpeta):
        if os.path.basename(raiz) in ("mosaicos", "vistas", "norm"):
            continue
        for n in sorted(nombres):
            if n.lower().endswith(IMG):
                rutas.append(os.path.join(raiz, n))

    # PDF y Word: se extraen las imagenes con el mismo codigo de la Actividad 1
    hay_doc = any(f.lower().endswith((".pdf", ".docx"))
                  for _, _, fs in os.walk(carpeta) for f in fs)
    if hay_doc and temporal:
        try:
            import corregir_entrega as ce
            rutas += [r for r in ce.reunir_candidatas(carpeta, temporal)
                      if r not in rutas]
        except Exception as e:
            print("  aviso: no pude extraer de PDF/Word (%s)" % e)

    if not rutas:
        return []

    todas = [(r, candidatas(r, pautas)) for r in rutas]
    # asignacion global: una pauta no puede quedar asignada a dos imagenes
    pares = sorted(((c["score"], r, c["pauta"], c)
                    for r, cs in todas for c in cs), key=lambda t: -t[0])
    usados, asignado = set(), {}
    for _, r, pau, c in pares:
        if r in asignado or pau in usados:
            continue
        asignado[r] = c
        usados.add(pau)

    salida = []
    for r, cs in todas:
        c = asignado.get(r)
        if c is None:
            salida.append({"archivo": r, "pauta": None})
            continue
        segunda = next((x["score"] for x in cs if x["pauta"] != c["pauta"]), 0.0)
        salida.append({
            "archivo": r, "pauta": c["pauta"],
            "nivel": pautas[c["pauta"]]["nivel"],
            "score": c["score"], "sim3d": c["sim3d"],
            "margen": (c["score"] - segunda) / max(c["score"], 1e-6),
            "vistas": dict(zip(VISTAS, c["vistas"])),
            "vistas_cont": dict(zip(VISTAS, c["vistas_cont"])),
        })
    return salida


def main():
    ap = argparse.ArgumentParser(
        description="Mide las entregas de la Actividad 2 contra la pauta")
    ap.add_argument("ruta", help="carpeta de un alumno, o de entregas con --todos")
    ap.add_argument("--todos", action="store_true",
                    help="tratar cada subcarpeta como un alumno distinto")
    ap.add_argument("--csv", help="guardar los numeros en este CSV")
    ap.add_argument("--carpeta", help=argparse.SUPPRESS)
    args = ap.parse_args()

    pautas = cargar_pautas()
    print("Pautas cargadas: %d  (%s)" % (
        len(pautas), ", ".join("%s %d" % (n, sum(1 for p in pautas.values() if p["nivel"] == n))
                               for n in ("elemental", "medio", "alto"))))

    alumnos = ([(d, os.path.join(args.ruta, d))
                for d in sorted(os.listdir(args.ruta))
                if os.path.isdir(os.path.join(args.ruta, d))]
               if args.todos else [(os.path.basename(os.path.normpath(args.ruta)), args.ruta)])

    filas_csv = []
    for nombre, carpeta in alumnos:
        tmp = tempfile.mkdtemp(prefix="a2_")
        try:
            res = procesar_alumno(carpeta, pautas, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print("\n" + "=" * 92)
        print("%s   (%d imagen(es))" % (nombre, len(res)))
        print("=" * 92)
        if not res:
            print("  sin imagenes")
            continue
        print("  %-30s %-24s %-9s %-22s %s" % (
            "archivo", "ejercicio", "certeza", "IoU por vista (A/P/Pl)", "solo visibles"))
        print("  " + "-" * 88)
        for r in res:
            if not r["pauta"]:
                print("  %-30s %s" % (os.path.basename(r["archivo"])[:30], "no identificado"))
                continue
            v = r["vistas"]; vc = r["vistas_cont"]
            print("  %-30s %-24s %5.0f%%   %5.2f %5.2f %5.2f      %5.2f %5.2f %5.2f" % (
                os.path.basename(r["archivo"])[:30], r["pauta"], 100 * r["score"],
                v["alzado"], v["perfil"], v["planta"],
                vc["alzado"], vc["perfil"], vc["planta"]))
            filas_csv.append([nombre, os.path.basename(r["archivo"]), r["pauta"],
                              r["nivel"], round(r["score"], 3), round(r["margen"], 3),
                              round(r["sim3d"], 3)]
                             + [round(v[k], 3) for k in VISTAS]
                             + [round(vc[k], 3) for k in VISTAS])

    if args.csv and filas_csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["alumno", "archivo", "pauta", "nivel", "certeza", "margen", "sim_3d",
                        "iou_alzado", "iou_perfil", "iou_planta",
                        "iou_alzado_visible", "iou_perfil_visible", "iou_planta_visible"])
            w.writerows(filas_csv)
        print("\nCSV: %s" % args.csv)



# --------------------------------------------- uso desde la ventana de pegar

FONDO_APPLET = (243, 240, 233)


def ajustar_a_pauta(im, pautas):
    """Recibe una imagen PIL y la deja del tamano de la pauta que le calce.

    Nunca reescala si la diferencia es chica: recorta o rellena. Reescalar
    mueve las lineas una fraccion de pixel y un trazo fino dejaria de solapar
    con el de la pauta, lo que se leeria como error del alumno."""
    im = im.convert("RGB")
    tamanos = sorted({(p["shape"][1], p["shape"][0]) for p in pautas.values()})
    w, h = im.size
    for (pw, ph) in tamanos:
        if (w, h) == (pw, ph):
            return im
    for (pw, ph) in tamanos:
        if abs(w - pw) <= TOLERANCIA_TAM and abs(h - ph) <= TOLERANCIA_TAM:
            lienzo = Image.new("RGB", (pw, ph), FONDO_APPLET)
            lienzo.paste(im, ((pw - w) // 2, (ph - h) // 2))
            return lienzo
    # Diferencia grande: el recorte no coincide con el canvas del applet.
    # Aqui si toca reescalar, y se avisa afuera con la certeza baja.
    objetivo = min(tamanos, key=lambda t: abs(t[0] / t[1] - w / max(h, 1)))
    return im.resize(objetivo, Image.LANCZOS)


def evaluar_imagen(im, pautas, nivel=None):
    """Identifica que ejercicio es y mide cada vista. Devuelve el ranking."""
    im = ajustar_a_pauta(im, pautas)
    a = np.asarray(im)
    q = cuadrantes(a)
    sv = [trazo(x) for x in q[:3]]
    svc = [trazo_continuo(x) for x in q[:3]]
    s3 = dilatar(aristas_pieza(q[3]), 2)

    filas = []
    for nom, p in pautas.items():
        if p["shape"] != a.shape:
            continue
        if nivel and p["nivel"] != nivel:
            continue
        v = [iou_encajado(sv[i], p["vistas_crudas"][i]) for i in range(3)]
        vc = [iou_encajado(svc[i], p["vistas_cont_crudas"][i]) for i in range(3)]
        tri = iou(s3, p["p3d"])
        filas.append({
            "pauta": nom, "nivel": p["nivel"],
            "score": PESO_VISTAS * float(np.mean(v)) + PESO_3D * tri,
            "sim3d": tri,
            "vistas": dict(zip(VISTAS, v)),
            "vistas_cont": dict(zip(VISTAS, vc)),
        })
    filas.sort(key=lambda d: -d["score"])
    return im, filas


def render_comparacion(im_alumno, nombre_pauta, ancho_max=1180, encajar=True):
    """Tres paneles: pauta, entrega, y las diferencias de trazo.

    Con `encajar`, cada vista del alumno se lleva a la caja de la vista de la
    pauta antes de comparar. Sin eso, un alumno que dibuje la forma correcta
    pero mas grande o corrida sale con TODO marcado, que es exactamente el
    ruido que hace inservible el panel."""
    pa = Image.open(os.path.join(PAUTA_A2, nombre_pauta)).convert("RGB")
    a = np.asarray(im_alumno)
    b = np.asarray(pa)
    if a.shape != b.shape:
        a = np.asarray(im_alumno.resize(pa.size, Image.LANCZOS))

    h, w = a.shape[:2]
    my, mx = h // 2, w // 2
    regiones = [(slice(0, my), slice(0, mx)),
                (slice(0, my), slice(mx, w)),
                (slice(my, h), slice(0, mx))]

    diff = a.copy()
    for ry, rx in regiones:
        ta = trazo(a[ry, rx])
        tb = trazo(b[ry, rx])
        if encajar:
            ta = encajar_en(ta, tb)
        ta = dilatar(ta, 1)
        tb = dilatar(tb, 1)
        sub = diff[ry, rx]
        sub[ta & ~tb] = (255, 0, 255)
        sub[tb & ~ta] = (255, 140, 0)
        sub[ta & tb] = (60, 160, 60)
        diff[ry, rx] = sub

    etiqueta_diff = ("DIFERENCIAS   verde = calza   magenta = sobra   naranjo = falta"
                     + ("   (tamano igualado)" if encajar else ""))
    paneles = [("PAUTA  " + nombre_pauta.replace("vistas_n_", "").replace(".jpg", ""), pa),
               ("ENTREGA", Image.fromarray(a)),
               (etiqueta_diff, Image.fromarray(diff))]
    sep = 10
    alto = max(p.height for _, p in paneles) + 24
    ancho = sum(p.width for _, p in paneles) + sep * (len(paneles) - 1)
    lienzo = Image.new("RGB", (ancho, alto), (255, 255, 255))
    d = ImageDraw.Draw(lienzo)
    x = 0
    for etiqueta, img in paneles:
        lienzo.paste(img, (x, 24))
        d.text((x + 4, 7), etiqueta, fill=(30, 30, 30))
        x += img.width + sep
    if lienzo.width > ancho_max:
        f = ancho_max / float(lienzo.width)
        lienzo = lienzo.resize((ancho_max, int(lienzo.height * f)), Image.LANCZOS)
    return lienzo



if __name__ == "__main__":
    main()
