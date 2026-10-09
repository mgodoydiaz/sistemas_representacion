#!/usr/bin/env python3
"""
02_pauta.py -- Etapa E2 del corrector Actividad 1.

Procesa las 5 capturas de la pauta (Pauta/imagen1..5.png) y para cada una:
  - detecta el area util (recuadro izquierdo con las 4 piezas isometricas)
  - lee la leyenda de colores del panel derecho (OCR con respaldo por regla)
  - segmenta cada cara de cada pieza por color
  - agrupa las caras en 4 piezas (grilla 2x2)
  - numera piezas y caras de forma estable
  - calcula el punto seguro de muestreo de cada cara (lejos de bordes)
  - escribe json, mascara 16 bits e imagen anotada por lamina
  - escribe un resumen csv con conteos de caras por color y pieza

Comentarios y mensajes en espanol, sin emojis.
"""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

# Los scripts viven en una sola copia compartida: contexto.py dice sobre
# que seccion y actividad se esta trabajando.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import contexto

RAIZ = Path(contexto.raiz())
PAUTA_DIR = Path(contexto.PAUTA_IMAGENES)
SALIDA_DIR = Path(contexto.CARPETA_PAUTA)
SALIDA_DIR.mkdir(parents=True, exist_ok=True)

N_LAMINAS = 5

# Color de fondo del panel (interior de los recuadros de la app), en RGB.
PANEL_BG = np.array([243, 240, 231])

# Paleta de colores conocidos del codigo del applet, en RGB. El nombre "marron"
# no aparece en el CONTRATO.md original (que solo lista hasta azul), pero la
# lamina 5 agrega una septima categoria "Alzado + Planta + Perfil" con un color
# cafe/rosado que hay que soportar igual; se deja documentado aqui.
PALETTE = {
    "rojo": (255, 0, 0),
    "amarillo": (255, 255, 0),
    "cyan": (0, 255, 255),
    "naranjo": (255, 187, 0),
    "verde": (0, 255, 0),
    "azul": (0, 0, 255),
    "marron": (204, 102, 102),
}

# Mapeo de respaldo por regla conocida (se usa si el OCR de la leyenda falla).
REGLA_ETIQUETAS = {
    "rojo": "Alzado",
    "amarillo": "Planta",
    "cyan": "Perfil",
    "naranjo": "Alzado + Planta",
    "verde": "Perfil + Planta",
    "azul": "Alzado + Perfil",
    "marron": "Alzado + Planta + Perfil",
}

VOCAB = ["Alzado", "Planta", "Perfil"]

# Recorte de respaldo si la deteccion automatica del area util falla (valores
# aproximados observados en las capturas de referencia, 921x639 aprox).
RECORTE_DEFECTO = (10, 55, 662, 495)  # x, y, w, h

AREA_MIN_CARA = 150
TOLERANCIA_COLOR = 40
TOLERANCIA_SWATCH = 60


def leer_imagen(path):
    img_bgr = cv2.imread(str(path))
    if img_bgr is None:
        raise FileNotFoundError(f"no se pudo leer {path}")
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img_bgr, img_rgb


def detectar_area_util(img_rgb):
    """Detecta el recuadro izquierdo (toolbar + grilla de piezas) como el
    componente conexo mas grande del color de fondo del panel, restringido a
    la mitad izquierda de la imagen. Dentro de ese recuadro el separador
    horizontal bajo la barra de botones corta la conectividad del fondo, asi
    que el componente mas grande resultante es exactamente el area con las
    4 piezas (sin la barra de botones arriba).
    Devuelve (x, y, w, h) o None si la deteccion falla.
    """
    diff = np.abs(img_rgb.astype(int) - PANEL_BG).sum(axis=2)
    mask = (diff < 10).astype(np.uint8)
    num, _labels, stats, _cents = cv2.connectedComponentsWithStats(mask, connectivity=4)
    mejor = None
    for i in range(1, num):
        x, y, w, h, area = stats[i]
        if x > img_rgb.shape[1] * 0.7:
            continue
        if w < 100 or h < 100:
            continue
        if mejor is None or area > mejor[4]:
            mejor = (x, y, w, h, area)
    if mejor is None:
        return None
    x, y, w, h, _area = mejor
    return int(x), int(y), int(w), int(h)


def detectar_swatches(img_rgb):
    """Busca los cuadraditos de color de la leyenda en el panel derecho.
    Para cada color conocido de la paleta, busca el componente conexo mas
    grande de forma cuadrada (14-36 px de lado) en x>680 que coincida con
    ese color dentro de tolerancia. Devuelve dict nombre -> dict con bbox y
    rgb real (mediana del parche).
    """
    H, W = img_rgb.shape[:2]
    x0_panel = int(W * 0.735)  # aprox 680/921, se ajusta al ancho real
    encontrados = {}
    for nombre, rgb in PALETTE.items():
        objetivo = np.array(rgb)
        diff = np.abs(img_rgb.astype(int) - objetivo).sum(axis=2)
        mask = (diff < TOLERANCIA_SWATCH).astype(np.uint8)
        mask[:, :x0_panel] = 0
        num, _labels, stats, _cents = cv2.connectedComponentsWithStats(mask, connectivity=8)
        mejor = None
        for i in range(1, num):
            x, y, w, h, area = stats[i]
            if w < 14 or w > 36 or h < 14 or h > 36:
                continue
            if abs(int(w) - int(h)) > 10:
                continue
            if area < 150:
                continue
            if mejor is None or area > mejor[4]:
                mejor = (x, y, w, h, area)
        if mejor is not None:
            x, y, w, h, _area = mejor
            parche = img_rgb[y:y + h, x:x + w].reshape(-1, 3)
            mediana = tuple(int(v) for v in np.median(parche, axis=0))
            encontrados[nombre] = {"x": int(x), "y": int(y), "w": int(w), "h": int(h), "rgb": mediana}
    return encontrados


def _levenshtein(a, b):
    a, b = a.upper(), b.upper()
    if a == b:
        return 0
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            costo = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + costo)
        prev = cur
    return prev[m]


def _limpiar_ocr(texto):
    permitido = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+ ")
    limpio = "".join(c for c in texto if c in permitido)
    return " ".join(limpio.split())


def _match_vocab(token):
    token = token.strip()
    if not token:
        return None
    mejor_palabra, mejor_dist = None, 99
    for palabra in VOCAB:
        d = _levenshtein(token, palabra)
        if d < mejor_dist:
            mejor_dist, mejor_palabra = d, palabra
    if mejor_dist <= 2:
        return mejor_palabra
    return None


def ocr_etiqueta(img_bgr, swatches, nombre):
    """Ejecuta tesseract sobre la region de texto a la derecha del cuadradito
    de color `nombre` y devuelve una etiqueta reconstruida ("Alzado + Planta")
    o None si no se pudo reconocer con confianza."""
    s = swatches[nombre]
    x, y, w, h = s["x"], s["y"], s["w"], s["h"]
    H, W = img_bgr.shape[:2]
    vecino_x = None
    for n2, s2 in swatches.items():
        if n2 == nombre:
            continue
        if abs(s2["y"] - y) < 12 and s2["x"] > x:
            if vecino_x is None or s2["x"] < vecino_x:
                vecino_x = s2["x"]
    x1 = (vecino_x - 5) if vecino_x else min(W, x + w + 200)
    x0 = x + w + 3
    y0 = max(0, y - 4)
    y1 = min(H, y + h + 4)
    if x1 <= x0 or y1 <= y0:
        return None
    recorte = img_bgr[y0:y1, x0:x1]
    recorte_grande = cv2.resize(recorte, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gris = cv2.cvtColor(recorte_grande, cv2.COLOR_BGR2GRAY)
    _thr, binaria = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # El archivo temporal se escribe FUERA de la carpeta conectada (RAIZ), en
    # el directorio temporal del sistema: la carpeta conectada puede no
    # permitir borrar archivos sin permiso explicito del usuario.
    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / f"_tmp_ocr_{nombre}.png"
    cv2.imwrite(str(tmp_path), binaria)
    try:
        resultado = subprocess.run(
            ["tesseract", str(tmp_path), "stdout", "--psm", "7"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return None
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
    texto = _limpiar_ocr(resultado.stdout)
    if not texto:
        return None
    partes = [p for p in texto.split("+")]
    palabras = []
    for parte in partes:
        m = _match_vocab(parte)
        if m is None:
            return None
        palabras.append(m)
    if not palabras:
        return None
    return " + ".join(palabras)


def construir_leyenda(img_bgr, img_rgb, swatches):
    """Arma el diccionario {nombre_color: etiqueta} intentando OCR primero.
    Si el OCR falla para cualquier color detectado, se usa la regla conocida
    para TODOS los colores de la lamina (para no mezclar origenes distintos
    en una misma leyenda) y se marca el origen como 'regla'."""
    etiquetas_ocr = {}
    ocr_completo = True
    for nombre in swatches:
        etiqueta = ocr_etiqueta(img_bgr, swatches, nombre)
        if etiqueta is None:
            ocr_completo = False
            break
        etiquetas_ocr[nombre] = etiqueta

    if ocr_completo and etiquetas_ocr:
        return etiquetas_ocr, "ocr"

    etiquetas_regla = {nombre: REGLA_ETIQUETAS[nombre] for nombre in swatches}
    return etiquetas_regla, "regla"


def segmentar_caras(crop_rgb, swatches):
    """Para cada color detectado en la leyenda, segmenta las caras dentro del
    recorte del area util. Devuelve dict nombre -> lista de componentes
    (x,y,w,h,area,cx,cy,mascara_local) y la mascara union de todos los
    colores (para el clustering de piezas)."""
    caras_por_color = {}
    union_mask = np.zeros(crop_rgb.shape[:2], dtype=np.uint8)
    for nombre, info in swatches.items():
        objetivo = np.array(info["rgb"])
        diff = np.abs(crop_rgb.astype(int) - objetivo).sum(axis=2)
        cmask = (diff < TOLERANCIA_COLOR).astype(np.uint8)
        num, labels, stats, cents = cv2.connectedComponentsWithStats(cmask, connectivity=8)
        comps = []
        for i in range(1, num):
            x, y, w, h, area = stats[i]
            if area < AREA_MIN_CARA:
                continue
            cx, cy = cents[i]
            comp_mask = (labels == i).astype(np.uint8)
            comps.append({
                "bbox": (int(x), int(y), int(w), int(h)),
                "area": int(area),
                "centroide": (float(cx), float(cy)),
                "mask": comp_mask,
                "rgb": info["rgb"],
            })
        caras_por_color[nombre] = comps
        union_mask |= cmask
    return caras_por_color, union_mask


def detectar_piezas(union_mask):
    """Agrupa la mascara union en 4 piezas (grilla 2x2) dilatando fuertemente
    y buscando componentes conexas grandes. Prueba varios tamanos de kernel
    hasta obtener exactamente 4 piezas."""
    for ks in (13, 15, 17, 19, 23, 27, 31, 35, 41):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
        dil = cv2.dilate(union_mask, kernel, iterations=1)
        num, labels, stats, cents = cv2.connectedComponentsWithStats(dil, connectivity=8)
        piezas = []
        for i in range(1, num):
            x, y, w, h, area = stats[i]
            if area < 1000:
                continue
            piezas.append({"label": i, "bbox": (int(x), int(y), int(w), int(h)), "centroide": cents[i]})
        if len(piezas) == 4:
            return piezas, labels
    # si no se logro exactamente 4, devolver el mejor intento (con el ultimo kernel)
    return piezas, labels


def numerar_piezas(piezas):
    """Numera las piezas 1=arriba-izq, 2=arriba-der, 3=abajo-izq, 4=abajo-der
    segun la posicion del centroide en la grilla 2x2."""
    xs = sorted(p["centroide"][0] for p in piezas)
    ys = sorted(p["centroide"][1] for p in piezas)
    x_mitad = (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2 if len(xs) >= 2 else xs[0]
    y_mitad = (ys[len(ys) // 2 - 1] + ys[len(ys) // 2]) / 2 if len(ys) >= 2 else ys[0]
    for p in piezas:
        cx, cy = p["centroide"]
        col = 0 if cx < x_mitad else 1
        fila = 0 if cy < y_mitad else 1
        p["numero"] = fila * 2 + col + 1
    return sorted(piezas, key=lambda p: p["numero"])


def punto_seguro_de_mascara(mask_uint8):
    """Calcula el punto interior mas alejado del borde de la mascara y su
    radio (distancia en pixeles), usando distance transform."""
    dist = cv2.distanceTransform(mask_uint8, cv2.DIST_L2, 5)
    _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(dist)
    # max_loc = (x, y)
    return (int(max_loc[0]), int(max_loc[1])), float(max_val)


def dibujar_anotada(crop_bgr, caras_info):
    """Dibuja sobre una copia del recorte el id de cada cara en su punto
    seguro, en negro con halo blanco."""
    anotada = crop_bgr.copy()
    for info in caras_info:
        x, y = info["punto_seguro"]
        texto = info["id"]
        fuente = cv2.FONT_HERSHEY_SIMPLEX
        escala = 0.38
        grosor_halo = 3
        grosor_texto = 1
        (tw, th), _base = cv2.getTextSize(texto, fuente, escala, grosor_texto)
        org = (int(x - tw / 2), int(y + th / 2))
        cv2.putText(anotada, texto, org, fuente, escala, (255, 255, 255), grosor_halo, cv2.LINE_AA)
        cv2.putText(anotada, texto, org, fuente, escala, (0, 0, 0), grosor_texto, cv2.LINE_AA)
    return anotada


def procesar_lamina(n):
    """Procesa una lamina completa y devuelve (info_json, filas_resumen,
    advertencias)."""
    advertencias = []
    ruta = PAUTA_DIR / f"imagen{n}.png"
    img_bgr, img_rgb = leer_imagen(ruta)

    area = detectar_area_util(img_rgb)
    if area is None:
        advertencias.append(f"lamina {n}: fallo la deteccion automatica del area util, se usa recorte por defecto")
        area = RECORTE_DEFECTO
    ax, ay, aw, ah = area
    crop_rgb = img_rgb[ay:ay + ah, ax:ax + aw].copy()
    crop_bgr = img_bgr[ay:ay + ah, ax:ax + aw].copy()

    ref_path = SALIDA_DIR / f"lamina{n}_ref.png"
    cv2.imwrite(str(ref_path), crop_bgr)

    swatches = detectar_swatches(img_rgb)
    if not swatches:
        advertencias.append(f"lamina {n}: no se detectaron cuadraditos de leyenda")

    leyenda, origen = construir_leyenda(img_bgr, img_rgb, swatches)

    # recorte de la leyenda completa (desde el primer swatch hasta el borde
    # derecho de la imagen, con margen), para verificacion visual manual.
    if swatches:
        ys = [s["y"] for s in swatches.values()]
        xs = [s["x"] for s in swatches.values()]
        y0 = max(0, min(ys) - 15)
        y1 = min(img_bgr.shape[0], max(s["y"] + s["h"] for s in swatches.values()) + 15)
        x0 = max(0, min(xs) - 10)
        x1 = img_bgr.shape[1]
        leyenda_crop = img_bgr[y0:y1, x0:x1]
        cv2.imwrite(str(SALIDA_DIR / f"lamina{n}_leyenda.png"), leyenda_crop)

    caras_por_color, union_mask = segmentar_caras(crop_rgb, swatches)

    piezas, labels_dilatadas = detectar_piezas(union_mask)
    if len(piezas) != 4:
        advertencias.append(f"lamina {n}: se detectaron {len(piezas)} piezas en vez de 4")
    piezas = numerar_piezas(piezas)

    # asignar cada cara a su pieza segun la etiqueta dilatada en su centroide
    caras_por_pieza = {p["numero"]: [] for p in piezas}
    label_a_numero = {p["label"]: p["numero"] for p in piezas}
    for nombre_color, comps in caras_por_color.items():
        for comp in comps:
            cx, cy = comp["centroide"]
            lbl = labels_dilatadas[int(round(cy)), int(round(cx))]
            numero_pieza = label_a_numero.get(int(lbl))
            if numero_pieza is None:
                advertencias.append(
                    f"lamina {n}: cara color {nombre_color} en ({cx:.0f},{cy:.0f}) no cayo dentro de ninguna pieza detectada"
                )
                continue
            comp["color"] = nombre_color
            caras_por_pieza[numero_pieza].append(comp)

    piezas_json = []
    todas_las_caras_info = []  # para dibujar anotada, en orden global
    indice_global = 1
    mask16 = np.zeros(crop_rgb.shape[:2], dtype=np.uint16)
    conteo_color_por_pieza = {}

    for p in piezas:
        numero = p["numero"]
        comps = caras_por_pieza[numero]
        # orden estable: arriba a abajo, izquierda a derecha
        comps.sort(key=lambda c: (int(c["centroide"][1] // 20), c["centroide"][0]))
        caras_json = []
        conteo_color = {}
        for idx, comp in enumerate(comps, start=1):
            cara_id = f"P{numero}-C{idx:02d}"
            punto, radio = punto_seguro_de_mascara(comp["mask"])
            if radio < 3:
                advertencias.append(
                    f"lamina {n} pieza {numero} cara {cara_id}: radio_seguro={radio:.2f} (cara muy delgada)"
                )
            x, y, w, h = comp["bbox"]
            cara_entry = {
                "id": cara_id,
                "color": comp["color"],
                "rgb": list(comp["rgb"]),
                "area": comp["area"],
                "centroide": [round(comp["centroide"][0], 1), round(comp["centroide"][1], 1)],
                "punto_seguro": [punto[0], punto[1]],
                "radio_seguro": round(radio, 2),
                "bbox": [x, y, w, h],
            }
            caras_json.append(cara_entry)
            mask16[comp["mask"] > 0] = indice_global
            todas_las_caras_info.append({"id": cara_id, "punto_seguro": punto})
            indice_global += 1
            conteo_color[comp["color"]] = conteo_color.get(comp["color"], 0) + 1
        conteo_color_por_pieza[numero] = conteo_color
        px, py, pw, ph = p["bbox"]
        piezas_json.append({"pieza": numero, "bbox": [px, py, pw, ph], "caras": caras_json})

    info_json = {
        "lamina": n,
        "tam": [int(crop_rgb.shape[1]), int(crop_rgb.shape[0])],
        "leyenda": leyenda,
        "leyenda_origen": origen,
        "piezas": piezas_json,
    }

    cv2.imwrite(str(SALIDA_DIR / f"lamina{n}_mask.png"), mask16)

    anotada = dibujar_anotada(crop_bgr, todas_las_caras_info)
    cv2.imwrite(str(SALIDA_DIR / f"lamina{n}_anotada.png"), anotada)

    with open(SALIDA_DIR / f"lamina{n}.json", "w", encoding="utf-8") as f:
        json.dump(info_json, f, ensure_ascii=False, indent=2)

    # filas de resumen
    colores_orden = ["rojo", "amarillo", "cyan", "naranjo", "verde", "azul", "marron"]
    filas = []
    total_lamina = {c: 0 for c in colores_orden}
    n_caras_total = 0
    for p in piezas:
        numero = p["numero"]
        conteo = conteo_color_por_pieza.get(numero, {})
        n_caras_pieza = sum(conteo.values())
        fila = {"lamina": n, "pieza": numero, "n_caras": n_caras_pieza}
        for c in colores_orden:
            fila[f"caras_{c}"] = conteo.get(c, 0)
            total_lamina[c] += conteo.get(c, 0)
        n_caras_total += n_caras_pieza
        filas.append(fila)
    fila_total = {"lamina": n, "pieza": "TOTAL", "n_caras": n_caras_total}
    for c in colores_orden:
        fila_total[f"caras_{c}"] = total_lamina[c]
    filas.append(fila_total)

    return info_json, filas, advertencias, n_caras_total, len(piezas)


def main():
    todas_filas = []
    resumen_validacion = []
    hubo_error_validacion = False

    for n in range(1, N_LAMINAS + 1):
        info_json, filas, advertencias, n_caras_total, n_piezas = procesar_lamina(n)
        todas_filas.extend(filas)
        for a in advertencias:
            print("ADVERTENCIA:", a)

        origen = info_json["leyenda_origen"]
        print(f"lamina {n}: {n_caras_total} caras, {n_piezas} piezas, leyenda por {origen}")

        if n_piezas != 4:
            hubo_error_validacion = True
            resumen_validacion.append(f"lamina {n}: {n_piezas} piezas (se esperaban 4)")
        # Rango de sanidad para el total de caras por lamina. Se parte de la
        # guia inicial (20-45) pero se amplia el limite superior a 55: se
        # verifico visualmente (zoom sobre lamina3_ref.png, lamina4_ref.png)
        # que las piezas mas complejas de las laminas 3, 4 y 5 realmente
        # tienen 14-18 caras por pieza (zigzags con muchas facetas chicas),
        # no hay caras duplicadas por artefactos de segmentacion.
        if not (20 <= n_caras_total <= 55):
            hubo_error_validacion = True
            resumen_validacion.append(f"lamina {n}: {n_caras_total} caras totales (fuera de rango 20-55)")

    colores_orden = ["rojo", "amarillo", "cyan", "naranjo", "verde", "azul", "marron"]
    columnas = ["lamina", "pieza", "n_caras"] + [f"caras_{c}" for c in colores_orden]
    csv_path = SALIDA_DIR / "resumen_pautas.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in todas_filas:
            writer.writerow(fila)

    print(f"\nresumen escrito en {csv_path}")

    if hubo_error_validacion:
        print("\nVALIDACION FALLIDA:")
        for msg in resumen_validacion:
            print(" -", msg)
        sys.exit(1)
    else:
        print("\nvalidacion OK: 5 laminas con 4 piezas cada una y totales de caras en rango razonable")


if __name__ == "__main__":
    main()
