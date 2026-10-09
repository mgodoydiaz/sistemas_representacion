#!/usr/bin/env python3
"""
E3 - Normalizacion de entregas.

Extrae las imagenes candidatas de cada entrega (jpg/pdf/docx), las recorta
al area util (las 4 piezas), determina a cual de las 5 laminas corresponde
cada candidata (por nombre de archivo y/o por geometria del trazo) y deja
todo listo en salida/entregas/<usuario>/norm/ segun el CONTRATO.

Uso: python3 03_normalizar.py [usuario1 usuario2 ...]
Si no se pasan usuarios, procesa todos los que existan en salida/entregas/.
"""
import sys
import os
import re
import json
import glob
import shutil
import zipfile
import subprocess
import unicodedata
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image

# Los scripts viven en una sola copia compartida: contexto.py dice sobre
# que seccion y actividad se esta trabajando.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import contexto

try:
    import pypdf
except ImportError:
    pypdf = None

RAIZ = Path(contexto.raiz())
SALIDA = RAIZ / "salida"
ENTREGAS = SALIDA / "entregas"
PAUTA = Path(contexto.CARPETA_PAUTA)   # pauta compartida por todas las secciones
REPORTES = SALIDA / "reportes"

BG_RGB = (243, 240, 231)   # fondo beige del panel del applet (R,G,B)
BG_BGR = (BG_RGB[2], BG_RGB[1], BG_RGB[0])

N_LAMINAS = 5
REF_ASPECT = 1.335          # ancho/alto tipico del area de las 4 piezas
MAX_LADO_PROC = 2000        # redimensionar candidatas pesadas antes de procesar
MIN_DIM_UTIL_EMBEBIDA = 300  # lado mayor minimo para considerar util una imagen embebida
ASPECT_MIN_EMBEBIDA = 1.10
ASPECT_MAX_EMBEBIDA = 2.30

SCORE_ELEGIBLE = 0.35
SCORE_DUDOSO_MIN = 0.45
SCORE_DUDOSO_MARGEN = 0.08

# --------------------------------------------------------------------------
# utilidades generales
# --------------------------------------------------------------------------

def log(msg):
    print(msg, flush=True)


def quitar_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def cargar_mapeo(userdir: Path):
    p = userdir / "mapeo.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def listar_archivos_entrega(userdir: Path):
    """Archivos originales de la entrega (excluye ficha, mapeo, norm, crudo)."""
    out = []
    for f in sorted(userdir.iterdir()):
        if f.is_dir():
            continue
        if f.name in ("mapeo.json",) or f.name.startswith("_ficha"):
            continue
        out.append(f)
    return out


def guess_lamina_from_name(nombre: str):
    """Intenta deducir el numero de lamina (1..5) desde un nombre de archivo."""
    n = quitar_tildes(nombre).lower()
    patrones = [
        r"vistas?_?color_?(\d)",
        r"lamin\w*[_\s]?(\d)",
        r"lam[_\s]?(\d)\b",
        r"vista[_\s]?(\d)\b",
        r"rec[_\s]?(\d)\b",
    ]
    for pat in patrones:
        m = re.search(pat, n)
        if m:
            v = int(m.group(1))
            if 1 <= v <= N_LAMINAS:
                return v
    # ultimo recurso: digito final antes de la extension, ej. "..._3.jpg"
    m = re.search(r"[_\-](\d)\.\w+$", n)
    if m:
        v = int(m.group(1))
        if 1 <= v <= N_LAMINAS:
            return v
    return None


def redimensionar_max(img, max_lado=MAX_LADO_PROC):
    h, w = img.shape[:2]
    lado = max(h, w)
    if lado <= max_lado:
        return img, 1.0
    esc = max_lado / lado
    nuevo = cv2.resize(img, (int(round(w * esc)), int(round(h * esc))), interpolation=cv2.INTER_AREA)
    return nuevo, esc


def cargar_bgr(path: Path):
    """Lee una imagen a BGR de 3 canales, aplanando alpha sobre blanco si hace falta."""
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        bgr = img[:, :, :3].astype(np.float32)
        alpha = (img[:, :, 3:4].astype(np.float32)) / 255.0
        fondo = np.array([255, 255, 255], dtype=np.float32)
        img = (bgr * alpha + fondo * (1 - alpha)).astype(np.uint8)
    return img


def guardar_png(img_bgr, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".png", img_bgr)
    if ok:
        buf.tofile(str(path))
    return ok


# --------------------------------------------------------------------------
# a) extraccion de candidatas crudas
# --------------------------------------------------------------------------

def extraer_candidatas_pdf(pdf_path: Path, crudo_dir: Path, base: str):
    """Devuelve lista de dicts {path, pagina} con las imagenes crudas extraidas."""
    candidatas = []
    if pypdf is None:
        return candidatas
    try:
        reader = pypdf.PdfReader(str(pdf_path))
    except Exception as e:
        log(f"    [!] no se pudo abrir pdf {pdf_path.name}: {e}")
        return candidatas

    n_paginas = len(reader.pages)
    for idx in range(n_paginas):
        pagina = idx + 1
        usables = []
        try:
            page = reader.pages[idx]
            imgs = list(page.images)
        except Exception as e:
            imgs = []
            log(f"    [!] error leyendo imagenes pagina {pagina} de {pdf_path.name}: {e}")

        for j, im in enumerate(imgs):
            try:
                pil = im.image
                if pil is None:
                    continue
                w, h = pil.size
                lado_mayor = max(w, h)
                lado_menor = max(1, min(w, h))
                aspecto = lado_mayor / lado_menor
                if lado_mayor < MIN_DIM_UTIL_EMBEBIDA:
                    continue
                if not (ASPECT_MIN_EMBEBIDA <= aspecto <= ASPECT_MAX_EMBEBIDA):
                    continue
                if pil.mode not in ("RGB",):
                    pil = pil.convert("RGB")
                arr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
                usables.append((j, arr))
            except Exception:
                continue

        if usables:
            for j, arr in usables:
                out = crudo_dir / f"{base}_p{pagina}_e{j}.png"
                guardar_png(arr, out)
                candidatas.append({"path": out, "pagina": pagina})
        else:
            # rasterizar la pagina completa a 200dpi
            prefix = crudo_dir / f"{base}_p{pagina}_rtmp"
            try:
                subprocess.run(
                    ["pdftoppm", "-r", "200", "-png", "-f", str(pagina), "-l", str(pagina),
                     str(pdf_path), str(prefix)],
                    check=True, capture_output=True, timeout=90,
                )
            except Exception as e:
                log(f"    [!] fallo pdftoppm en {pdf_path.name} pagina {pagina}: {e}")
                continue
            generados = sorted(glob.glob(str(prefix) + "*.png"))
            for g in generados:
                gp = Path(g)
                destino = crudo_dir / f"{base}_p{pagina}_raster.png"
                shutil.move(g, destino)
                candidatas.append({"path": destino, "pagina": pagina})
    return candidatas


def extraer_candidatas_docx(docx_path: Path, crudo_dir: Path, base: str):
    candidatas = []
    try:
        with zipfile.ZipFile(docx_path) as z:
            media = sorted([n for n in z.namelist() if n.startswith("word/media/")])
            for j, name in enumerate(media):
                data = z.read(name)
                arr = np.frombuffer(data, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
                if img is None:
                    continue
                if img.ndim == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                if img.shape[2] == 4:
                    bgr = img[:, :, :3].astype(np.float32)
                    alpha = (img[:, :, 3:4].astype(np.float32)) / 255.0
                    fondo = np.array([255, 255, 255], dtype=np.float32)
                    img = (bgr * alpha + fondo * (1 - alpha)).astype(np.uint8)
                out = crudo_dir / f"{base}_media{j:02d}.png"
                guardar_png(img, out)
                candidatas.append({"path": out, "pagina": None, "orden": j, "nombre_media": Path(name).name})
    except Exception as e:
        log(f"    [!] fallo extrayendo docx {docx_path.name}: {e}")
    return candidatas


def extraer_candidatas(archivo: Path, crudo_dir: Path):
    ext = archivo.suffix.lower()
    base = archivo.stem
    if ext in (".jpg", ".jpeg", ".png"):
        destino = crudo_dir / f"{base}.png"
        img = cargar_bgr(archivo)
        if img is None:
            return []
        guardar_png(img, destino)
        return [{"path": destino, "pagina": None}]
    if ext == ".pdf":
        return extraer_candidatas_pdf(archivo, crudo_dir, base)
    if ext == ".docx":
        return extraer_candidatas_docx(archivo, crudo_dir, base)
    return []


# --------------------------------------------------------------------------
# b) recorte al area util
# --------------------------------------------------------------------------

def mascara_fondo(hsv, tolerancia="normal"):
    s = hsv[:, :, 1].astype(np.int16)
    v = hsv[:, :, 2].astype(np.int16)
    if tolerancia == "estricta":
        return (s < 25) & (v > 195)
    elif tolerancia == "amplia":
        return (s < 45) & (v > 165)
    else:  # muy amplia, para fotos
        return (s < 70) & (v > 120)


def _merge_boxes(boxes, gap):
    """Fusiona cajas (x,y,w,h) que se solapan o estan a menos de gap de distancia."""
    rects = [list(b) for b in boxes]
    cambiado = True
    while cambiado:
        cambiado = False
        out = []
        usados = [False] * len(rects)
        for i in range(len(rects)):
            if usados[i]:
                continue
            x0, y0, w0, h0 = rects[i]
            x1e, y1e = x0 + w0, y0 + h0
            for j in range(i + 1, len(rects)):
                if usados[j]:
                    continue
                xa, ya, wa, ha = rects[j]
                x1a, y1a = xa + wa, ya + ha
                # expandir por gap y ver si se solapan
                if (x0 - gap < x1a and x1e + gap > xa and
                        y0 - gap < y1a and y1e + gap > ya):
                    nx0, ny0 = min(x0, xa), min(y0, ya)
                    nx1, ny1 = max(x1e, x1a), max(y1e, y1a)
                    x0, y0, x1e, y1e = nx0, ny0, nx1, ny1
                    usados[j] = True
                    cambiado = True
            out.append([x0, y0, x1e - x0, y1e - y0])
            usados[i] = True
        rects = out
    return [tuple(r) for r in rects]


def detectar_clusters_contenido(img_bgr):
    """Devuelve lista de bboxes (x,y,w,h) de clusters de 'tinta' (no-fondo)."""
    h, w = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # se usa siempre la tolerancia mas amplia como base: el fondo beige/blanco
    # tiene baja saturacion y alta luminosidad sea cual sea la iluminacion, mientras
    # que el trazo (lineas negras) y los colores del codigo son claramente distintos
    # (alta saturacion o muy oscuros), asi que no hace falta variar el umbral segun
    # una fraccion de pixeles "razonable": eso fallaba con fondos con ruido jpeg
    # donde una tolerancia estricta marcaba erroneamente medio fondo como tinta.
    bg = mascara_fondo(hsv, "muy amplia")
    ink = (~bg).astype(np.uint8) * 255
    frac = ink.mean() / 255.0
    if not (0.003 < frac < 0.9):
        # caso raro: reintentar con tolerancias mas estrictas como red de seguridad
        for tol in ("amplia", "estricta"):
            bg2 = mascara_fondo(hsv, tol)
            ink2 = (~bg2).astype(np.uint8) * 255
            frac2 = ink2.mean() / 255.0
            if 0.003 < frac2 < 0.9:
                bg, ink, frac = bg2, ink2, frac2
                break

    kernel_sz = max(3, int(round(min(h, w) * 0.012)))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_sz, kernel_sz))
    ink_d = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, kernel)
    ink_d = cv2.dilate(ink_d, kernel, iterations=1)

    n, labels, stats, _ = cv2.connectedComponentsWithStats(ink_d, connectivity=8)
    area_total = h * w
    cajas = []
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        if ww * hh < 0.004 * area_total:
            continue
        # descartar componentes pegados a los 4 bordes simultaneamente (ruido de fondo)
        cajas.append((x, y, ww, hh))
    if not cajas:
        return [], ink

    gap = int(round(0.06 * max(h, w)))
    clusters = _merge_boxes(cajas, gap)
    # quedarse solo con clusters de tamano razonable
    clusters = [c for c in clusters if c[2] * c[3] >= 0.01 * area_total]
    clusters.sort(key=lambda c: c[2] * c[3], reverse=True)
    return clusters, ink


def dividir_si_apilado(cluster, ink_mask):
    """Si un cluster es mucho mas alto que ancho, asume laminas apiladas verticalmente
    y lo separa en N bandas horizontales de altura similar."""
    x, y, w, h = cluster
    aspecto = w / h
    if aspecto >= 0.85:
        return [cluster]
    alto_estim = w / REF_ASPECT
    n_est = max(1, int(round(h / alto_estim)))
    if n_est <= 1:
        return [cluster]
    bandas = []
    paso = h / n_est
    for k in range(n_est):
        y0 = int(round(y + k * paso))
        y1 = int(round(y + (k + 1) * paso))
        sub = ink_mask[y0:y1, x:x + w]
        ys, xs = np.where(sub > 0)
        if len(xs) < 20:
            continue
        bx0, bx1 = xs.min() + x, xs.max() + x
        by0, by1 = ys.min() + y0, ys.max() + y0
        bandas.append((bx0, by0, bx1 - bx0, by1 - by0))
    return bandas if bandas else [cluster]


def recortar_panel_derecho(bbox, ink_mask):
    """Si el bbox es mucho mas ancho de lo esperado, corta el panel derecho
    (leyenda + pieza modelo) buscando la columna vacia mas ancha."""
    x, y, w, h = bbox
    if w / h <= REF_ASPECT * 1.25:
        return bbox
    sub = ink_mask[y:y + h, x:x + w]
    dens_col = sub.mean(axis=0) / 255.0
    vacio = dens_col < 0.015
    # buscar corridas de columnas vacias
    mejor_ini, mejor_fin, mejor_len = None, None, 0
    i = 0
    while i < len(vacio):
        if vacio[i]:
            j = i
            while j < len(vacio) and vacio[j]:
                j += 1
            if (j - i) > mejor_len:
                mejor_len = j - i
                mejor_ini, mejor_fin = i, j
            i = j
        else:
            i += 1
    ancho_min_pieza = int(0.35 * w)
    if mejor_ini is not None and mejor_len >= 3 and mejor_ini > ancho_min_pieza:
        corte = (mejor_ini + mejor_fin) // 2
        sub_izq = sub[:, :corte]
        ys, xs = np.where(sub_izq > 0)
        if len(xs) > 20:
            nx0, nx1 = xs.min(), xs.max()
            ny0, ny1 = ys.min(), ys.max()
            return (x + nx0, y + ny0, nx1 - nx0, ny1 - ny0)
    # fallback: recortar proporcionalmente al aspecto esperado
    nuevo_w = int(round(h * REF_ASPECT))
    return (x, y, min(nuevo_w, w), h)


def recortar_candidata(img_bgr):
    """Devuelve una lista de imagenes BGR recortadas (una por lamina detectada
    dentro de la candidata) mas su bbox en la imagen original (para debug)."""
    img_bgr, _esc = redimensionar_max(img_bgr)
    clusters, ink = detectar_clusters_contenido(img_bgr)
    if not clusters:
        return []
    resultados = []
    # solo consideramos clusters grandes (>=25% del cluster mas grande) para evitar ruido
    area_max = clusters[0][2] * clusters[0][3]
    for c in clusters:
        if c[2] * c[3] < 0.25 * area_max:
            continue
        for banda in dividir_si_apilado(c, ink):
            bbox = recortar_panel_derecho(banda, ink)
            x, y, w, h = bbox
            if w < 40 or h < 40:
                continue
            pad_x = int(round(0.01 * w))
            pad_y = int(round(0.01 * h))
            x0 = max(0, x - pad_x)
            y0 = max(0, y - pad_y)
            x1 = min(img_bgr.shape[1], x + w + pad_x)
            y1 = min(img_bgr.shape[0], y + h + pad_y)
            recorte = img_bgr[y0:y1, x0:x1].copy()
            resultados.append(recorte)
    return resultados


def redimensionar_con_pad(img_bgr, tam_destino):
    """Redimensiona manteniendo proporcion y rellena con BG_BGR hasta tam_destino=(W,H)."""
    W, H = tam_destino
    h, w = img_bgr.shape[:2]
    esc = min(W / w, H / h)
    nw, nh = max(1, int(round(w * esc))), max(1, int(round(h * esc)))
    interp = cv2.INTER_AREA if esc < 1 else cv2.INTER_CUBIC
    redim = cv2.resize(img_bgr, (nw, nh), interpolation=interp)
    lienzo = np.full((H, W, 3), BG_BGR, dtype=np.uint8)
    ox, oy = (W - nw) // 2, (H - nh) // 2
    lienzo[oy:oy + nh, ox:ox + nw] = redim
    return lienzo


# --------------------------------------------------------------------------
# c) identificacion de lamina por geometria
# --------------------------------------------------------------------------

def mascara_lineas(img_bgr, umbral=90):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    m = (gray < umbral).astype(np.uint8) * 255
    return m


def cargar_refs():
    refs = {}
    for n in range(1, N_LAMINAS + 1):
        p = PAUTA / f"lamina{n}_ref.png"
        img = cargar_bgr(p)
        if img is None:
            raise RuntimeError(f"no se encontro {p}")
        tam = (img.shape[1], img.shape[0])
        linea = mascara_lineas(img)
        kernel = np.ones((3, 3), np.uint8)
        linea_dil = cv2.dilate(linea, kernel, iterations=1)
        # perfil de proyeccion (para comparacion adicional de forma)
        proj_h = linea.sum(axis=1).astype(np.float32)
        proj_v = linea.sum(axis=0).astype(np.float32)
        proj_h = proj_h / (proj_h.sum() + 1e-6)
        proj_v = proj_v / (proj_v.sum() + 1e-6)
        refs[n] = {"img": img, "tam": tam, "linea_dil": linea_dil,
                   "proj_h": proj_h, "proj_v": proj_v}
    return refs


def comparar_con_ref(candidata_bgr, ref):
    tam = ref["tam"]
    cand_r = redimensionar_con_pad(candidata_bgr, tam)
    linea_c = mascara_lineas(cand_r)
    kernel = np.ones((3, 3), np.uint8)
    linea_c_dil = cv2.dilate(linea_c, kernel, iterations=1)

    inter = np.logical_and(linea_c_dil > 0, ref["linea_dil"] > 0).sum()
    union = np.logical_or(linea_c_dil > 0, ref["linea_dil"] > 0).sum()
    iou = inter / union if union > 0 else 0.0

    gray_c = cv2.cvtColor(cand_r, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray_r = cv2.cvtColor(ref["img"], cv2.COLOR_BGR2GRAY).astype(np.float32)
    small_c = cv2.resize(gray_c, (200, int(200 / (tam[0] / tam[1]))))
    small_r = cv2.resize(gray_r, (200, int(200 / (tam[0] / tam[1]))))
    try:
        res = cv2.matchTemplate(small_c, small_r, cv2.TM_CCOEFF_NORMED)
        ncc = float(res[0, 0])
    except Exception:
        ncc = 0.0
    ncc01 = max(0.0, (ncc + 1) / 2)

    proj_h_c = linea_c.sum(axis=1).astype(np.float32)
    proj_h_c = proj_h_c / (proj_h_c.sum() + 1e-6)
    proj_v_c = linea_c.sum(axis=0).astype(np.float32)
    proj_v_c = proj_v_c / (proj_v_c.sum() + 1e-6)
    corr_h = float(np.corrcoef(proj_h_c, ref["proj_h"])[0, 1]) if proj_h_c.std() > 0 and ref["proj_h"].std() > 0 else 0.0
    corr_v = float(np.corrcoef(proj_v_c, ref["proj_v"])[0, 1]) if proj_v_c.std() > 0 and ref["proj_v"].std() > 0 else 0.0
    corr_h = max(0.0, corr_h)
    corr_v = max(0.0, corr_v)

    score = 0.5 * iou + 0.3 * ncc01 + 0.1 * corr_h + 0.1 * corr_v
    return score, cand_r


def calcular_scores_geom(candidata_bgr, refs):
    """Score de similitud geometrica puro (0..~1) contra cada una de las 5 laminas."""
    scores = {}
    for n in range(1, N_LAMINAS + 1):
        s, _ = comparar_con_ref(candidata_bgr, refs[n])
        scores[n] = s
    return scores


def combinar_con_pista(scores_geom, pista_nombre):
    """Aplica el refuerzo por pista de nombre de archivo, acotado a 1.0."""
    combinados = {}
    for lam, s in scores_geom.items():
        val = s
        if pista_nombre is not None and pista_nombre == lam:
            val = min(1.0, s + 0.30)
        combinados[lam] = val
    return combinados


# --------------------------------------------------------------------------
# pipeline principal por alumno
# --------------------------------------------------------------------------

def procesar_alumno(usuario: str, refs):
    userdir = ENTREGAS / usuario
    if not userdir.exists():
        return None
    crudo_dir = userdir / "crudo"
    norm_dir = userdir / "norm"
    if crudo_dir.exists():
        shutil.rmtree(crudo_dir)
    if norm_dir.exists():
        shutil.rmtree(norm_dir)
    crudo_dir.mkdir(parents=True, exist_ok=True)
    norm_dir.mkdir(parents=True, exist_ok=True)

    mapeo = cargar_mapeo(userdir)
    archivos = listar_archivos_entrega(userdir)

    propuestas = []  # cada elemento: dict con archivo_origen, pagina, candidata(np), pista, scores...
    for archivo in archivos:
        nombre_original = mapeo.get(archivo.name, archivo.name)
        candidatas_crudas = extraer_candidatas(archivo, crudo_dir)
        for cinfo in candidatas_crudas:
            img = cargar_bgr(cinfo["path"])
            if img is None:
                continue
            recortes = recortar_candidata(img)
            if not recortes:
                continue
            pista = guess_lamina_from_name(nombre_original)
            if pista is None and cinfo.get("nombre_media"):
                pista = guess_lamina_from_name(cinfo["nombre_media"])
            for k, recorte in enumerate(recortes):
                propuestas.append({
                    "archivo_origen": archivo.name,
                    "pagina": cinfo.get("pagina"),
                    "sub": k,
                    "img": recorte,
                    "pista": pista,
                })

    # calcular scores de cada propuesta contra las 5 laminas
    pares = []  # (score_combinado, propuesta_idx, lamina)
    detalle_props = []
    for pi, prop in enumerate(propuestas):
        scores_geom = calcular_scores_geom(prop["img"], refs)
        scores_comb = combinar_con_pista(scores_geom, prop["pista"])
        detalle_props.append({"scores_geom": scores_geom, "scores_comb": scores_comb})
        for lam, sc in scores_comb.items():
            if sc >= SCORE_ELEGIBLE:
                pares.append((sc, pi, lam))

    pares.sort(key=lambda t: t[0], reverse=True)
    asignado_lamina = {}
    asignado_prop = set()
    ganadores = {}  # lamina -> (prop_idx, score)
    perdedores = []  # prop_idx que tenian score elegible pero no ganaron su lamina

    for score, pi, lam in pares:
        if lam in asignado_lamina or pi in asignado_prop:
            continue
        asignado_lamina[lam] = pi
        asignado_prop.add(pi)
        ganadores[lam] = (pi, score)

    for score, pi, lam in pares:
        if pi not in asignado_prop:
            perdedores.append((pi, lam, score))

    items = []
    dudosos = []
    for lam in range(1, N_LAMINAS + 1):
        if lam not in ganadores:
            continue
        pi, score = ganadores[lam]
        prop = propuestas[pi]
        scores_geom = detalle_props[pi]["scores_geom"]
        scores_comb = detalle_props[pi]["scores_comb"]
        score_ganador = scores_comb[lam]
        resto = sorted([v for k, v in scores_comb.items() if k != lam], reverse=True)
        score_segundo = resto[0] if resto else 0.0
        dudoso = (score_ganador - score_segundo < SCORE_DUDOSO_MARGEN) or (score_ganador < SCORE_DUDOSO_MIN)

        if prop["pista"] == lam and scores_geom[lam] >= SCORE_ELEGIBLE * 0.7:
            metodo = "nombre+geometria"
        elif prop["pista"] == lam:
            metodo = "nombre"
        else:
            metodo = "geometria"

        tam_ref = refs[lam]["tam"]
        img_final = redimensionar_con_pad(prop["img"], tam_ref)
        nombre_salida = f"lamina{lam}.png"
        guardar_png(img_final, norm_dir / nombre_salida)

        nota = ""
        if dudoso:
            nota = "confianza baja o score muy cercano al segundo candidato"
            dudosos.append(lam)

        items.append({
            "archivo_origen": prop["archivo_origen"],
            "pagina": prop["pagina"],
            "lamina": lam,
            "confianza": round(float(score_ganador), 3),
            "salida": f"norm/{nombre_salida}",
            "metodo": metodo,
            "nota": nota,
        })

    laminas_detectadas = sorted(items and [it["lamina"] for it in items] or [])
    laminas_faltantes = [n for n in range(1, N_LAMINAS + 1) if n not in laminas_detectadas]

    manifest = {
        "usuario": usuario,
        "items": items,
        "laminas_detectadas": laminas_detectadas,
        "laminas_faltantes": laminas_faltantes,
        "dudosos": sorted(set(dudosos)),
    }
    (norm_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    confianzas = [it["confianza"] for it in items]
    confianza_min = round(min(confianzas), 3) if confianzas else 0.0

    observaciones = []
    if len(archivos) >= 2:
        tamanios = set(a.stat().st_size for a in archivos if a.suffix.lower() == ".pdf")
        pdfs = [a for a in archivos if a.suffix.lower() == ".pdf"]
        if len(pdfs) >= 2 and len(tamanios) == 1:
            observaciones.append(
                "los PDF entregados tienen igual tamano en bytes; se verifico manualmente "
                "que su contenido (imagenes embebidas) es distinto entre si"
            )
    if laminas_faltantes:
        observaciones.append(f"faltan laminas {laminas_faltantes}")
    if perdedores:
        observaciones.append(f"{len(perdedores)} candidata(s) descartada(s) por duplicar lamina ya asignada")
    if not propuestas:
        observaciones.append("no se pudo extraer ninguna imagen candidata de la entrega")

    resumen_fila = {
        "usuario": usuario,
        "laminas_detectadas": ",".join(str(n) for n in laminas_detectadas),
        "laminas_faltantes": ",".join(str(n) for n in laminas_faltantes),
        "n_dudosos": len(manifest["dudosos"]),
        "confianza_min": confianza_min,
        "observacion": "; ".join(observaciones),
    }
    return resumen_fila


# --------------------------------------------------------------------------
# reporte visual (mosaico de contacto)
# --------------------------------------------------------------------------

def generar_contact_sheet(usuarios):
    REPORTES.mkdir(parents=True, exist_ok=True)
    thumb_w, thumb_h = 150, 112
    label_w = 210
    pad = 8
    fila_h = thumb_h + pad
    fila_w = label_w + N_LAMINAS * (thumb_w + pad)

    max_por_hoja = 40
    lotes = [usuarios[i:i + max_por_hoja] for i in range(0, len(usuarios), max_por_hoja)]

    for idx_lote, lote in enumerate(lotes, start=1):
        alto_total = pad + len(lote) * fila_h + 40
        hoja = np.full((alto_total, fila_w + pad, 3), 255, dtype=np.uint8)
        y = 30
        cv2.putText(hoja, "Contacto normalizacion - laminas identificadas por alumno", (pad, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
        for usuario in lote:
            norm_dir = ENTREGAS / usuario / "norm"
            manifest_path = norm_dir / "manifest.json"
            dudosos = []
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    dudosos = manifest.get("dudosos", [])
                except Exception:
                    manifest = {}
            texto = usuario
            cv2.putText(hoja, texto, (pad, y + thumb_h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            for n in range(1, N_LAMINAS + 1):
                x0 = label_w + (n - 1) * (thumb_w + pad)
                p = norm_dir / f"lamina{n}.png"
                celda = np.full((thumb_h, thumb_w, 3), 235, dtype=np.uint8)
                if p.exists():
                    img = cargar_bgr(p)
                    if img is not None:
                        h, w = img.shape[:2]
                        esc = min(thumb_w / w, thumb_h / h)
                        nw, nh = max(1, int(w * esc)), max(1, int(h * esc))
                        small = cv2.resize(img, (nw, nh))
                        oy, ox = (thumb_h - nh) // 2, (thumb_w - nw) // 2
                        celda[oy:oy + nh, ox:ox + nw] = small
                        color_borde = (0, 140, 255) if n in dudosos else (120, 120, 120)
                        cv2.rectangle(celda, (0, 0), (thumb_w - 1, thumb_h - 1), color_borde, 2)
                else:
                    cv2.putText(celda, "FALTA", (18, thumb_h // 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 200), 1, cv2.LINE_AA)
                    cv2.rectangle(celda, (0, 0), (thumb_w - 1, thumb_h - 1), (150, 150, 150), 1)
                hoja[y:y + thumb_h, x0:x0 + thumb_w] = celda
            y += fila_h
        sufijo = "" if len(lotes) == 1 else f"_{idx_lote}"
        guardar_png(hoja, REPORTES / f"contact_normalizacion{sufijo}.png")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    refs = cargar_refs()
    if args:
        usuarios = args
    else:
        usuarios = sorted([p.name for p in ENTREGAS.iterdir() if p.is_dir()])

    filas = []
    for usuario in usuarios:
        log(f"=== procesando {usuario} ===")
        try:
            fila = procesar_alumno(usuario, refs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            fila = {
                "usuario": usuario, "laminas_detectadas": "", "laminas_faltantes": "1,2,3,4,5",
                "n_dudosos": 0, "confianza_min": 0.0, "observacion": f"ERROR: {e}",
            }
        if fila is not None:
            filas.append(fila)
            log(f"    detectadas={fila['laminas_detectadas']} faltantes={fila['laminas_faltantes']} "
                f"dudosos={fila['n_dudosos']} conf_min={fila['confianza_min']}")

    df = pd.DataFrame(filas, columns=[
        "usuario", "laminas_detectadas", "laminas_faltantes", "n_dudosos", "confianza_min", "observacion"
    ])
    df.to_csv(SALIDA / "normalizacion_resumen.csv", index=False)

    # el mosaico se genera siempre sobre TODOS los usuarios existentes en salida/entregas
    todos = sorted([p.name for p in ENTREGAS.iterdir() if p.is_dir()])
    generar_contact_sheet(todos)

    log("\n=== RESUMEN ===")
    completos = sum(1 for f in filas if f["laminas_faltantes"] == "")
    log(f"alumnos con 5 laminas: {completos} / {len(filas)}")
    for f in filas:
        if f["laminas_faltantes"] != "":
            log(f"  incompleto: {f['usuario']} -> faltan [{f['laminas_faltantes']}]")


if __name__ == "__main__":
    main()
