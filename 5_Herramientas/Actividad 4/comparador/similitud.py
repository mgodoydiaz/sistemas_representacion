#!/usr/bin/env python3
"""
similitud.py - Motor de comparacion "trazo de alumno" vs "pauta" de la
Actividad 4 (Sistemas de Representacion).

Entrada: dos capas de trazo de 1000x1000 (PNG RGBA con trazo negro y alfa
variable, el mismo formato que escribe rectificador/nucleo.py y que
consume el visor). Salida: un porcentaje de parecido de 0 a 100 mas las
metricas de apoyo que lo explican.

Metodo (en este orden, ver tambien comparador/LEEME.md):

  1. Binarizar ambas capas de trazo con un umbral de alfa (UMBRAL_ALFA).
  2. Registro: buscar la traslacion, la escala (0.9-1.1) y la rotacion
     (pocos grados) del alumno que maximiza la coincidencia con la pauta.
     Es una busqueda gruesa a fina: primero en una version reducida de las
     mascaras (barata), despues se refina en la resolucion original. El
     desplazamiento hallado se reporta tal cual: un dibujo muy corrido es
     informacion util para el profesor, no solo un dato interno.
  3. Metricas sobre las mascaras ya alineadas: IoU con tolerancia (dilatando
     ambas mascaras unos pocos pixeles), F-score de cobertura y precision,
     y distancia de Chamfer en ambos sentidos (en pixeles y en "casillas"
     de reticula).
  4. Porcentaje final: combinacion ponderada y documentada de esas metricas
     (diccionario PESOS, mas abajo, pensado para ajustarse sin tener que
     leer el resto del archivo).
  5. Mapa de diferencia: PNG RGBA con lo que el alumno dibujo de mas, lo que
     falta, y lo que coincide.

Dependencias obligatorias: numpy y PIL (Pillow). cv2 es OPCIONAL: si esta
instalado se usa para acelerar la dilatacion y la transformada de
distancia, pero el modulo funciona igual sin el (ver _dilatar y
_distancia_transformada). Tampoco se requiere scipy: la transformada de
distancia euclidiana exacta esta implementada a mano (algoritmo de
Felzenszwalt & Huttenlocher, separable en pasadas por fila/columna).

Uso desde consola:
    python3 comparador/similitud.py <pauta_trazo.png> <alumno_trazo.png> \
        [--umbral 40] [--salida-diferencia diferencia.png]

Uso como libreria:
    from comparador import similitud as sim
    resultado = sim.comparar_desde_paths(ruta_pauta_trazo, ruta_alumno_trazo)
"""

import argparse
import json
import os

import numpy as np
from PIL import Image

try:
    import cv2
    _CV2 = True
except ImportError:
    _CV2 = False


# =============================================================================
# PARAMETROS AJUSTABLES - todo lo que se puede querer "afinar" vive aqui,
# nada de numeros magicos sueltos en medio de las funciones de mas abajo.
# =============================================================================

# --- Binarizacion ---
UMBRAL_ALFA = 40  # 0-255: un pixel de la capa de trazo cuenta como "tinta" si su alfa es >= este valor.

# --- Geometria de la reticula (para expresar la distancia de Chamfer en "casillas") ---
TAM_ESPERADO = 1000       # lado esperado de las mascaras (cuadros de 1000x1000).
CASILLAS_POR_LADO = 10.0  # la reticula impresa de cada cuadro tiene ~10x10 casillas.
CASILLA_PX = TAM_ESPERADO / CASILLAS_POR_LADO

# --- Tolerancia para el IoU "con tolerancia" y para precision/cobertura ---
TOLERANCIA_PX = 6  # radio (px) con el que se dilatan las mascaras antes de compararlas.

# --- Busqueda de registro (traslacion + escala + rotacion) ---
# La busqueda se hace en dos resoluciones: una reducida (barata, para probar
# muchas combinaciones de escala/rotacion) y despues se refina en la
# resolucion original solo para la mejor combinacion encontrada.
# --- Tolerancia para bordes exteriores y registro ---
MARGEN_BORDE_PX = 25  # px perimetrales que se limpian para ignorar lineas de recuadro impreso.
REGISTRO_FACTOR_DS = 5           # factor de reduccion para la busqueda barata (1000 -> 200 px).
REGISTRO_RANGO_GRUESO_DS = 20    # +-20 px reducidos = +-100 px reales: rango de la grilla gruesa.
REGISTRO_PASO_GRUESO_DS = 2      # paso de la grilla gruesa, en px reducidos (10 px reales).
REGISTRO_RANGO_FINO_DS = 3       # refinamiento (paso 1) alrededor del mejor punto de la grilla gruesa.
REGISTRO_RANGO_FINAL_PX = 8      # refinamiento final en resolucion completa (paso 1, en px reales).
REGISTRO_ESCALAS = [0.94, 0.97, 1.0, 1.03, 1.06]  # entre 0.9 y 1.1, mas denso cerca de 1.0.
REGISTRO_ROTACIONES = [-4, -2, 0, 2, 4]           # grados; "unos pocos grados" segun el enunciado.

# --- Combinacion final del porcentaje ---
# Cada score de abajo vive en [0,1]; el porcentaje final es su promedio
# ponderado por PESOS (no hace falta que sumen 1: se normalizan solos).
# Para recalibrar la nota sugerida, alcanza con tocar estos tres numeros.
PESOS = {
    "iou_tolerante": 0.40,   # que tan bien se superponen las zonas de tinta (con tolerancia de TOLERANCIA_PX).
    "f_score": 0.35,         # balance entre "no le falto nada" (cobertura) y "no se paso de la raya" (precision).
    "chamfer": 0.25,         # que tan lejos, en promedio, esta cada trazo del mas cercano del otro.
}
# Distancia de Chamfer (promedio de ambos sentidos, en pixeles) a partir de
# la cual se considera que el dibujo esta "completamente perdido" para este
# componente del puntaje (score_chamfer = 0 en ese punto y mas alla).
CHAMFER_PX_MALO = 120.0

# --- Colores del mapa de diferencia (mismos que usa el visor en
# visor/js/imagenes.js:calcularDiferencia y las variables --alumno-color /
# --pauta-color de visor/css/estilo.css, para que ambas vistas se lean igual). ---
COLOR_SOLO_ALUMNO = (205, 60, 55)     # rojo: el alumno dibujo esto y la pauta no.
COLOR_SOLO_PAUTA = (60, 110, 210)     # azul: la pauta lo pide y al alumno le falta.
COLOR_COINCIDE = (120, 120, 120)      # gris: coincide en ambos.
COLOR_FONDO = (250, 250, 250)         # casi blanco: ninguno de los dos tiene trazo ahi.


# =============================================================================
# Carga de mascaras
# =============================================================================

def cargar_mascara_trazo(ruta, umbral_alfa=UMBRAL_ALFA):
    """Carga un PNG de capa de trazo (RGBA, trazo negro con alfa variable) y
    lo binariza segun el canal alfa. Devuelve un arreglo 2D booleano."""
    im = Image.open(ruta)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    alfa = np.array(im)[:, :, 3]
    return alfa >= umbral_alfa


# =============================================================================
# Operaciones geometricas basicas sobre mascaras booleanas (sin cv2/scipy)
# =============================================================================

def _reducir(mask_bool, factor):
    """Reduce la resolucion 'factor' veces con pooling OR (si algun pixel del
    bloque tiene trazo, el bloque reducido tambien). Con pooling OR un trazo
    fino no desaparece al reducir, que es lo que importa para guiar la
    busqueda de traslacion/escala/rotacion (no para medir con precision)."""
    h, w = mask_bool.shape
    h2, w2 = h // factor, w // factor
    recorte = mask_bool[: h2 * factor, : w2 * factor]
    bloques = recorte.reshape(h2, factor, w2, factor)
    return bloques.any(axis=(1, 3))


def _transformar(mask_bool, angulo_grados, escala):
    """Rota y escala (alrededor del centro del lienzo) una mascara booleana,
    conservando el tamaño de lienzo original (recorta o rellena con fondo
    segun corresponda). Implementado solo con PIL: nearest-neighbor porque
    trabajamos con una mascara binaria, no con imagenes en tonos de gris."""
    h, w = mask_bool.shape
    im = Image.fromarray((mask_bool.astype(np.uint8) * 255), mode="L")
    if abs(escala - 1.0) > 1e-6:
        nw, nh = max(1, round(w * escala)), max(1, round(h * escala))
        im = im.resize((nw, nh), Image.NEAREST)
        lienzo = Image.new("L", (w, h), 0)
        ox, oy = (w - nw) // 2, (h - nh) // 2
        # pega solo la parte que cae dentro del lienzo (si escala>1 y la
        # imagen escalada es mas grande, Image.paste recorta solo; si es mas
        # chica, ox/oy negativos no aplican porque escala<=1.1 en la practica).
        lienzo.paste(im, (ox, oy))
        im = lienzo
    if abs(angulo_grados) > 1e-6:
        im = im.rotate(angulo_grados, resample=Image.NEAREST, expand=False, fillcolor=0)
    return np.array(im) > 127


def _desplazar(mask_bool, dx, dy):
    """Traslada una mascara booleana (dx,dy) en pixeles, rellenando con False
    (fondo) las zonas que quedan fuera. dx>0 mueve el contenido a la derecha,
    dy>0 hacia abajo (convencion de imagen: eje y crece hacia abajo)."""
    h, w = mask_bool.shape
    out = np.zeros_like(mask_bool)
    x0d, x1d = max(0, dx), min(w, w + dx)
    y0d, y1d = max(0, dy), min(h, h + dy)
    x0s, x1s = max(0, -dx), min(w, w - dx)
    y0s, y1s = max(0, -dy), min(h, h - dy)
    if x1d > x0d and y1d > y0d:
        out[y0d:y1d, x0d:x1d] = mask_bool[y0s:y1s, x0s:x1s]
    return out


def _dilatar(mask_bool, radio):
    """Dilatacion morfologica (elemento estructurante cuadrado de lado
    2*radio+1). Usa cv2.dilate si esta disponible (mas rapido); si no, una
    version separable a mano (maximo en ventana horizontal, despues
    vertical), la misma estrategia que visor/js/imagenes.js:dilatarAlfa,
    sin depender de cv2 ni de scipy."""
    if radio <= 0:
        return mask_bool
    if _CV2:
        k = np.ones((2 * radio + 1, 2 * radio + 1), np.uint8)
        return cv2.dilate(mask_bool.astype(np.uint8), k).astype(bool)
    m = mask_bool.astype(np.uint8)
    tmp = np.zeros_like(m)
    for dx in range(-radio, radio + 1):
        if dx == 0:
            tmp |= m
        elif dx > 0:
            tmp[:, dx:] |= m[:, :-dx]
        else:
            tmp[:, :dx] |= m[:, -dx:]
    out = np.zeros_like(m)
    for dy in range(-radio, radio + 1):
        if dy == 0:
            out |= tmp
        elif dy > 0:
            out[dy:, :] |= tmp[:-dy, :]
        else:
            out[:dy, :] |= tmp[-dy:, :]
    return out.astype(bool)


def _dice(a, b):
    """Coeficiente de Dice (2*interseccion / suma de areas) entre dos
    mascaras booleanas. Se usa solo como puntaje interno para guiar la
    busqueda de registro (no es una de las metricas que se reportan)."""
    sa, sb = int(a.sum()), int(b.sum())
    if sa == 0 and sb == 0:
        return 1.0
    inter = int(np.logical_and(a, b).sum())
    return 2.0 * inter / (sa + sb)


def _mejor_traslacion(mascara, objetivo, dx_min, dx_max, dy_min, dy_max, paso=1):
    """Busca, en la grilla de traslaciones dada, la que maximiza el Dice
    entre `mascara` desplazada y `objetivo`. Fuerza bruta sobre la grilla:
    es la parte 'gruesa a fina' de la busqueda de registro (ver registrar())."""
    mejor_dice, mejor_dx, mejor_dy = -1.0, 0, 0
    for dy in range(dy_min, dy_max + 1, paso):
        for dx in range(dx_min, dx_max + 1, paso):
            cand = _desplazar(mascara, dx, dy)
            d = _dice(cand, objetivo)
            if d > mejor_dice:
                mejor_dice, mejor_dx, mejor_dy = d, dx, dy
    return {"dice": mejor_dice, "dx": mejor_dx, "dy": mejor_dy}


# =============================================================================
# Transformada de distancia (para Chamfer), sin depender de scipy
# =============================================================================

def _dt_1d(f):
    """Transformada de distancia 1D (al cuadrado): envolvente inferior de
    parabolas centradas en cada muestra de `f`. Algoritmo de Felzenszwalt &
    Huttenlocher (2004), exacto y O(n). f[i] es 0 si i es un pixel "frente"
    y un numero grande si no lo es; el resultado es, para cada posicion, el
    cuadrado de la distancia a la posicion "frente" mas cercana (en 1D)."""
    n = len(f)
    d = np.zeros(n)
    v = np.zeros(n, dtype=np.int64)
    z = np.zeros(n + 1)
    k = 0
    z[0] = -np.inf
    z[1] = np.inf
    for q in range(1, n):
        while True:
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2.0 * q - 2.0 * v[k])
            if s <= z[k]:
                k -= 1
                if k < 0:
                    k = 0
                    break
            else:
                break
        k += 1
        v[k] = q
        z[k] = s
        z[k + 1] = np.inf
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


def _edt_manual(mask_frente):
    """Transformada de distancia euclidiana exacta (sin cv2 ni scipy):
    aplica _dt_1d por columnas y despues por filas (separable), como
    describe Felzenszwalt & Huttenlocher. Devuelve la distancia (no al
    cuadrado) de cada pixel al pixel `True` mas cercano de `mask_frente`."""
    if not mask_frente.any():
        return np.full(mask_frente.shape, float(CHAMFER_PX_MALO * 4))
    inf = 1e10
    h, w = mask_frente.shape
    f = np.where(mask_frente, 0.0, inf)
    for x in range(w):
        f[:, x] = _dt_1d(f[:, x])
    for y in range(h):
        f[y, :] = _dt_1d(f[y, :])
    return np.sqrt(f)


def _distancia_transformada(mask_frente):
    """Para cada pixel del lienzo, la distancia al pixel `True` mas cercano
    de `mask_frente`. Usa cv2.distanceTransform si esta disponible (exacta
    y mucho mas rapida); si no, la implementacion manual de _edt_manual."""
    if not mask_frente.any():
        return np.full(mask_frente.shape, float(CHAMFER_PX_MALO * 4))
    if _CV2:
        # distanceTransform mide la distancia al pixel CERO mas cercano, asi
        # que el "frente" (mask_frente=True) debe quedar en 0 y el resto en 255.
        src = np.where(mask_frente, 0, 255).astype(np.uint8)
        return cv2.distanceTransform(src, cv2.DIST_L2, 5)
    return _edt_manual(mask_frente)


# =============================================================================
# Registro: traslacion + escala + rotacion
# =============================================================================

def registrar(mascara_pauta, mascara_alumno):
    """Busca la transformacion (traslacion dx,dy; escala; rotacion) del
    trazo del alumno que mejor lo alinea con la pauta. Devuelve un dict con
    esos parametros mas la mascara del alumno ya transformada al tamaño
    original (mascara_alineada), lista para calcular las metricas finales.

    Estrategia (gruesa a fina, documentada tambien en comparador/LEEME.md):
      1. Se reducen ambas mascaras (REGISTRO_FACTOR_DS) para que probar
         muchas combinaciones de escala/rotacion sea barato.
      2. Para cada (rotacion, escala) de REGISTRO_ROTACIONES x
         REGISTRO_ESCALAS: se rota/escala el alumno reducido UNA vez, y se
         evaluan todas las traslaciones de una grilla gruesa
         (REGISTRO_RANGO_GRUESO_DS, paso REGISTRO_PASO_GRUESO_DS) y despues
         una fina (paso 1) alrededor del mejor punto de esa grilla gruesa.
      3. Con la mejor (rotacion, escala) global, se repite el registro de
         traslacion en la resolucion COMPLETA (paso 1, rango
         REGISTRO_RANGO_FINAL_PX alrededor de la traslacion hallada en baja
         resolucion), para reportar un desplazamiento fiel a la imagen real.
    """
    pauta_ds = _reducir(mascara_pauta, REGISTRO_FACTOR_DS)
    alumno_ds = _reducir(mascara_alumno, REGISTRO_FACTOR_DS)

    mejor_global = None
    for rot in REGISTRO_ROTACIONES:
        for esc in REGISTRO_ESCALAS:
            transformado = _transformar(alumno_ds, rot, esc)
            grueso = _mejor_traslacion(
                transformado, pauta_ds,
                -REGISTRO_RANGO_GRUESO_DS, REGISTRO_RANGO_GRUESO_DS,
                -REGISTRO_RANGO_GRUESO_DS, REGISTRO_RANGO_GRUESO_DS,
                REGISTRO_PASO_GRUESO_DS,
            )
            fino = _mejor_traslacion(
                transformado, pauta_ds,
                grueso["dx"] - REGISTRO_RANGO_FINO_DS, grueso["dx"] + REGISTRO_RANGO_FINO_DS,
                grueso["dy"] - REGISTRO_RANGO_FINO_DS, grueso["dy"] + REGISTRO_RANGO_FINO_DS,
                1,
            )
            candidato = {"rot": rot, "esc": esc, "dx_ds": fino["dx"], "dy_ds": fino["dy"], "dice": fino["dice"]}
            if mejor_global is None or candidato["dice"] > mejor_global["dice"]:
                mejor_global = candidato

    dx0 = mejor_global["dx_ds"] * REGISTRO_FACTOR_DS
    dy0 = mejor_global["dy_ds"] * REGISTRO_FACTOR_DS

    transformado_full = _transformar(mascara_alumno, mejor_global["rot"], mejor_global["esc"])
    final = _mejor_traslacion(
        transformado_full, mascara_pauta,
        dx0 - REGISTRO_RANGO_FINAL_PX, dx0 + REGISTRO_RANGO_FINAL_PX,
        dy0 - REGISTRO_RANGO_FINAL_PX, dy0 + REGISTRO_RANGO_FINAL_PX,
        1,
    )
    mascara_alineada = _desplazar(transformado_full, final["dx"], final["dy"])

    return {
        "dx": int(final["dx"]),
        "dy": int(final["dy"]),
        "escala": float(mejor_global["esc"]),
        "rotacion": float(mejor_global["rot"]),
        "dice": float(final["dice"]),
        "mascara_alineada": mascara_alineada,
    }


# =============================================================================
# Mapa de diferencia
# =============================================================================

def _mapa_diferencia(mascara_pauta, mascara_alumno_alineada):
    h, w = mascara_pauta.shape
    out = np.empty((h, w, 4), dtype=np.uint8)
    out[..., 0] = COLOR_FONDO[0]
    out[..., 1] = COLOR_FONDO[1]
    out[..., 2] = COLOR_FONDO[2]
    out[..., 3] = 255

    coincide = mascara_pauta & mascara_alumno_alineada
    solo_alumno = mascara_alumno_alineada & ~mascara_pauta
    solo_pauta = mascara_pauta & ~mascara_alumno_alineada

    out[coincide] = (*COLOR_COINCIDE, 255)
    out[solo_alumno] = (*COLOR_SOLO_ALUMNO, 255)
    out[solo_pauta] = (*COLOR_SOLO_PAUTA, 255)
    return out


def guardar_mapa_diferencia(ruta, arreglo_rgba):
    Image.fromarray(arreglo_rgba, mode="RGBA").save(ruta)


# =============================================================================
# Metricas + porcentaje final
# =============================================================================

def comparar_mascaras(mascara_pauta, mascara_alumno):
    """Compara dos mascaras booleanas del mismo tamaño (pauta y alumno) y
    devuelve el resultado completo: porcentaje, metricas de apoyo, la
    transformacion de registro aplicada y el mapa de diferencia (arreglo
    numpy HxWx4 uint8; el llamador decide si lo guarda a disco)."""
    if mascara_pauta.shape != mascara_alumno.shape:
        raise ValueError(
            f"Las mascaras deben tener el mismo tamaño (pauta={mascara_pauta.shape}, "
            f"alumno={mascara_alumno.shape})."
        )

    reg = registrar(mascara_pauta, mascara_alumno)
    alumno_alineado = reg["mascara_alineada"]

    pauta_dil = _dilatar(mascara_pauta, TOLERANCIA_PX)
    alumno_dil = _dilatar(alumno_alineado, TOLERANCIA_PX)

def _puntaje_zona(pauta, alumno, pauta_dil, alumno_dil, dt_pauta, dt_alumno):
    n_alumno = int(alumno.sum())
    n_pauta = int(pauta.sum())

    inter_tol = np.logical_and(pauta_dil, alumno_dil)
    union_tol = np.logical_or(pauta_dil, alumno_dil)
    iou_tolerante = float(inter_tol.sum()) / float(union_tol.sum()) if union_tol.any() else 1.0

    if n_alumno == 0:
        precision = 0.0 if n_pauta > 0 else 1.0
    else:
        precision = float(np.logical_and(alumno, pauta_dil).sum()) / n_alumno

    if n_pauta == 0:
        cobertura = 1.0
    else:
        cobertura = float(np.logical_and(pauta, alumno_dil).sum()) / n_pauta

    f_score = (2 * precision * cobertura / (precision + cobertura)) if (precision + cobertura) > 0 else 0.0

    dist_alumno_a_pauta = float(dt_pauta[alumno].mean()) if n_alumno > 0 else float(CHAMFER_PX_MALO)
    dist_pauta_a_alumno = float(dt_alumno[pauta].mean()) if n_pauta > 0 else float(CHAMFER_PX_MALO)
    chamfer_promedio_px = (dist_alumno_a_pauta + dist_pauta_a_alumno) / 2.0

    score_iou = iou_tolerante
    score_f = f_score
    score_chamfer = max(0.0, 1.0 - chamfer_promedio_px / CHAMFER_PX_MALO)
    suma_pesos = sum(PESOS.values())
    porcentaje = 100.0 * (
        PESOS["iou_tolerante"] * score_iou
        + PESOS["f_score"] * score_f
        + PESOS["chamfer"] * score_chamfer
    ) / suma_pesos
    porcentaje = max(0.0, min(100.0, porcentaje))

    return {
        "porcentaje": porcentaje,
        "iou_tolerante": iou_tolerante,
        "precision": precision,
        "cobertura": cobertura,
        "f_score": f_score,
        "chamfer_alumno_a_pauta_px": dist_alumno_a_pauta,
        "chamfer_pauta_a_alumno_px": dist_pauta_a_alumno,
        "chamfer_promedio_px": chamfer_promedio_px,
        "pixeles_alumno": n_alumno,
        "pixeles_pauta": n_pauta,
    }


def comparar_mascaras(mascara_pauta, mascara_alumno):
    """Compara dos mascaras booleanas del mismo tamaño (pauta y alumno) y
    devuelve el resultado completo: porcentaje, metricas de apoyo, la
    transformacion de registro aplicada y el mapa de diferencia (arreglo
    numpy HxWx4 uint8; el llamador decide si lo guarda a disco)."""
    if mascara_pauta.shape != mascara_alumno.shape:
        raise ValueError(
            f"Las mascaras deben tener el mismo tamaño (pauta={mascara_pauta.shape}, "
            f"alumno={mascara_alumno.shape})."
        )

    reg = registrar(mascara_pauta, mascara_alumno)
    alumno_alineado = reg["mascara_alineada"]

    pauta_dil = _dilatar(mascara_pauta, TOLERANCIA_PX)
    alumno_dil = _dilatar(alumno_alineado, TOLERANCIA_PX)
    dt_pauta = _distancia_transformada(mascara_pauta)
    dt_alumno = _distancia_transformada(alumno_alineado)

    # Evaluación de la celda completa
    res_global = _puntaje_zona(mascara_pauta, alumno_alineado, pauta_dil, alumno_dil, dt_pauta, dt_alumno)

    # Evaluación por cuadrantes (para "vistas", 3 de los 4 cuadrantes tienen dibujo)
    h, w = mascara_pauta.shape
    h2, w2 = h // 2, w // 2
    zonas = [
        ("TL", 0, h2, 0, w2),
        ("TR", 0, h2, w2, w),
        ("BL", h2, h, 0, w2),
        ("BR", h2, h, w2, w),
    ]
    eval_cuadrantes = {}
    for nombre, y0, y1, x0, x1 in zonas:
        r_zona = _puntaje_zona(
            mascara_pauta[y0:y1, x0:x1], alumno_alineado[y0:y1, x0:x1],
            pauta_dil[y0:y1, x0:x1], alumno_dil[y0:y1, x0:x1],
            dt_pauta[y0:y1, x0:x1], dt_alumno[y0:y1, x0:x1]
        )
        # Asignar puntos (1 perfecto, 0.5 parcial, 0 mal)
        pct = r_zona["porcentaje"]
        if pct >= 80: pt = 1.0
        elif pct >= 40: pt = 0.5
        else: pt = 0.0
        
        eval_cuadrantes[nombre] = {
            "porcentaje": round(pct, 2),
            "pixeles_pauta": r_zona["pixeles_pauta"],
            "puntos": pt
        }
        
    # Filtrar los 3 cuadrantes con más dibujo en la pauta
    cuadrantes_activos = sorted(eval_cuadrantes.items(), key=lambda x: x[1]["pixeles_pauta"], reverse=True)[:3]
    puntos_vistas = sum(v["puntos"] for k, v in cuadrantes_activos)

    mapa_diferencia = _mapa_diferencia(mascara_pauta, alumno_alineado)

    return {
        "porcentaje": round(res_global["porcentaje"], 2),
        "puntos_vistas": puntos_vistas,
        "cuadrantes_activos": [k for k, v in cuadrantes_activos],
        "eval_cuadrantes": eval_cuadrantes,
        "metricas": {
            "iou_tolerante": round(res_global["iou_tolerante"], 4),
            "precision": round(res_global["precision"], 4),
            "cobertura": round(res_global["cobertura"], 4),
            "f_score": round(res_global["f_score"], 4),
            "chamfer_alumno_a_pauta_px": round(res_global["chamfer_alumno_a_pauta_px"], 2),
            "chamfer_pauta_a_alumno_px": round(res_global["chamfer_pauta_a_alumno_px"], 2),
            "chamfer_promedio_px": round(res_global["chamfer_promedio_px"], 2),
            "chamfer_promedio_casillas": round(res_global["chamfer_promedio_px"] / CASILLA_PX, 3),
            "pixeles_alumno": res_global["pixeles_alumno"],
            "pixeles_pauta": res_global["pixeles_pauta"],
            "tolerancia_px": TOLERANCIA_PX,
        },
        "registro": {
            "dx": reg["dx"],
            "dy": reg["dy"],
            "escala": round(reg["escala"], 3),
            "rotacion_grados": reg["rotacion"],
            "puntaje_dice_registro": round(reg["dice"], 4),
        },
        "pesos_usados": dict(PESOS),
        "mapa_diferencia": mapa_diferencia,
    }


def limpiar_bordes_mascara(mask_bool, margen_px=MARGEN_BORDE_PX):
    """Descarta trazos en los margenes exteriores de la mascara para ignorar
    lineas del recuadro o marco de hoja impreso."""
    if margen_px <= 0:
        return mask_bool
    m = mask_bool.copy()
    m[:margen_px, :] = False
    m[-margen_px:, :] = False
    m[:, :margen_px] = False
    m[:, -margen_px:] = False
    return m


def comparar_desde_paths(ruta_trazo_pauta, ruta_trazo_alumno, umbral_alfa=UMBRAL_ALFA, limpiar_bordes=True):
    """Version de comparar_mascaras() que recibe rutas a los PNG de trazo
    (pauta y alumno) en vez de mascaras ya cargadas."""
    mascara_pauta = cargar_mascara_trazo(ruta_trazo_pauta, umbral_alfa)
    mascara_alumno = cargar_mascara_trazo(ruta_trazo_alumno, umbral_alfa)
    if limpiar_bordes:
        mascara_alumno = limpiar_bordes_mascara(mascara_alumno)
    if mascara_pauta.shape != mascara_alumno.shape:
        # Defensivo: en la practica ambos deberian venir a 1000x1000 segun
        # el contrato de salida/, pero si algo no cumplio el contrato, se
        # reescala el alumno al tamaño de la pauta antes de comparar.
        alto, ancho = mascara_pauta.shape
        im = Image.fromarray(mascara_alumno.astype(np.uint8) * 255)
        im = im.resize((ancho, alto), Image.NEAREST)
        mascara_alumno = np.array(im) > 127
    return comparar_mascaras(mascara_pauta, mascara_alumno)


# =============================================================================
# CLI
# =============================================================================

def _main():
    ap = argparse.ArgumentParser(
        description="Compara el trazo de un alumno contra su pauta y muestra el porcentaje de parecido."
    )
    ap.add_argument("pauta_trazo", help="Ruta al PNG de la capa de trazo de la PAUTA (RGBA).")
    ap.add_argument("alumno_trazo", help="Ruta al PNG de la capa de trazo del ALUMNO (RGBA).")
    ap.add_argument("--umbral", type=int, default=UMBRAL_ALFA, help=f"Umbral de alfa para binarizar (0-255, por defecto {UMBRAL_ALFA}).")
    ap.add_argument("--salida-diferencia", default=None, help="Si se entrega, guarda ahi el mapa de diferencia (PNG RGBA).")
    args = ap.parse_args()

    resultado = comparar_desde_paths(args.pauta_trazo, args.alumno_trazo, args.umbral)
    mapa = resultado.pop("mapa_diferencia")
    if args.salida_diferencia:
        os.makedirs(os.path.dirname(os.path.abspath(args.salida_diferencia)) or ".", exist_ok=True)
        guardar_mapa_diferencia(args.salida_diferencia, mapa)
        resultado["mapa_diferencia_guardado_en"] = args.salida_diferencia
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
