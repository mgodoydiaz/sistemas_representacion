#!/usr/bin/env python3
"""
tipo_hoja.py - Deteccion automatica del tipo de hoja de un cuadro de la
Actividad 4 (Sistemas de Representacion): "vistas" (ortogonales, reticula
cuadrada) o "isometricos" (reticula triangular a 30/90/150 grados).

Pensado para resolver un problema concreto: un cuadro rectificado se puede
guardar bajo la pagina equivocada (por ejemplo una hoja de isometricos
guardada como "vistas"), y eso hace que se compare contra la pauta que no
corresponde. Un porcentaje bajo por ese motivo se ve identico a un dibujo
malo. Este modulo detecta el tipo real del cuadro para que servidor.py
pueda avisar (o bloquear) esa comparacion antes de calcular un porcentaje
sin sentido (ver comparador/LEEME.md, seccion "Deteccion de tipo de hoja").

Entrada: UN cuadro ya rectificado de 1000x1000 (el mismo contrato que usa
comparador/similitud.py):
  - la imagen en escala de grises del cuadro (gris, con la reticula
    impresa y, si es de un alumno, tambien su dibujo encima).
  - opcionalmente, la capa de trazo (PNG RGBA, trazo negro con alfa
    variable, fondo transparente) separada por rectificador/nucleo.py.

Dos señales INDEPENDIENTES (si discrepan, se baja la confianza en vez de
elegir a la fuerza):

  a) Angulos de la reticula impresa (imagen en gris): en "vistas" dominan
     0 y 90 grados; en "isometricos" dominan 30, 90 y 150. Se mide con
     segmentos de recta (Hough probabilistica, cv2.HoughLinesP) si cv2
     esta disponible; si no, con la orientacion dominante del espectro de
     Fourier de la imagen (numpy puro).
  b) Angulos de los trazos del alumno (capa de trazo): un isometrico tiene
     la mayoria de sus aristas cerca de 30/150 grados; unas vistas son
     casi todas horizontales/verticales (0/90). Sirve de respaldo cuando
     la reticula impresa salio muy tenue en el escaneo. Si el cuadro esta
     vacio (poco trazo), esta señal se reporta como "indeterminado" en vez
     de forzar un tipo con muy pocos datos.

Dependencias obligatorias: numpy y Pillow (PIL). cv2 es OPCIONAL: si esta
instalado se usa para acelerar (Hough real en vez del respaldo por FFT),
pero el modulo funciona igual sin el.

Uso como libreria:
    from comparador import tipo_hoja as th
    resultado = th.detectar_tipo_hoja(ruta_gris, ruta_trazo)
    # {"tipo": "vistas"|"isometricos"|"indeterminado", "confianza": 0..1,
    #  "senales": {"reticula": {...}, "trazo": {...}}}

Uso desde consola:
    python3 comparador/tipo_hoja.py <cuadro_gris.png> [<cuadro_trazo.png>]
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
# PARAMETROS AJUSTABLES
# =============================================================================

TAM_ESPERADO = 1000

# Angulos "de interes" (grados, modulo 180: una linea a 170 grados es
# practicamente igual a una linea a -10 grados).
ANGULO_ORTOGONAL = 0.0
ANGULO_VERTICAL = 90.0
ANGULOS_DIAGONALES = (30.0, 150.0)

VENTANA_PICO_GRADOS = 9.0  # tolerancia alrededor de cada angulo "de interes".

# Por debajo de esta cantidad de pixeles con tinta, la señal del trazo se
# reporta como "indeterminado" (muy poca informacion para opinar: un cuadro
# casi vacio no deberia poder tirar la clasificacion para ningun lado).
MIN_PIXELES_TRAZO = 150

# Umbral de alfa para binarizar la capa de trazo (mismo valor que
# comparador/similitud.py, para ser consistentes).
UMBRAL_ALFA_TRAZO = 40

# Umbrales para decidir si el resultado de cv2.HoughLinesP alcanza para
# confiar solo en el (si no, se completa con el respaldo de FFT): cantidad
# minima de segmentos encontrados, y suma minima de "energia" (largo total
# de segmentos, en pixeles). Un puñado de segmentos sueltos (por ejemplo un
# solo artefacto de la foto) puede pasar el primer filtro pero no el
# segundo, y viceversa una reticula muy fragmentada puede dar muchos
# segmentos cortos sin superar el umbral de energia.
MIN_SEGMENTOS_RETICULA = 6
MIN_ENERGIA_RETICULA = 2500.0
MIN_SEGMENTOS_TRAZO = 3
MIN_ENERGIA_TRAZO = 800.0

# Ponderacion de cada señal cuando AMBAS dan un tipo determinado y COINCIDEN.
PESO_RETICULA = 0.6
PESO_TRAZO = 0.4

# La reticula es la señal PRINCIPAL (mide el papel impreso, que no depende
# de que tan bien o mal dibuje el alumno); el trazo es el RESPALDO para
# cuando la reticula salio demasiado tenue en el escaneo (ver enunciado del
# modulo). Por eso, si la reticula da un resultado con al menos esta
# confianza, manda su tipo aunque el trazo opine otra cosa (un dibujo con
# lados oblicuos validos, por ejemplo una cara inclinada en una vista, no
# deberia poder "ganarle" a una reticula cuadrada bien leida).
UMBRAL_RETICULA_CONFIABLE = 0.45

# Si las dos señales discrepan, la confianza final se calcula a partir de
# la diferencia entre ambas (ver _combinar_senales) y si queda por debajo
# de este umbral, se reporta "indeterminado" en vez de forzar un tipo.
UMBRAL_CONFIANZA_MINIMA = 0.30


# =============================================================================
# Carga de imagenes
# =============================================================================

def cargar_gris(ruta):
    """Carga un cuadro (PNG u otro formato de imagen) como arreglo 2D
    uint8 en escala de grises."""
    im = Image.open(ruta).convert("L")
    return np.array(im, dtype=np.uint8)


def cargar_mascara_trazo(ruta, umbral_alfa=UMBRAL_ALFA_TRAZO):
    """Carga una capa de trazo (PNG RGBA) y la binariza por alfa. Misma
    logica que comparador/similitud.py:cargar_mascara_trazo (duplicada a
    proposito: cada modulo de comparador/ es independiente y se puede usar
    solo, sin arrastrar al resto)."""
    im = Image.open(ruta)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    alfa = np.array(im)[:, :, 3]
    return alfa >= umbral_alfa


# =============================================================================
# Histogramas de angulo (0-179 grados, un bin por grado)
# =============================================================================

def _distancia_angular(indices, centro, periodo=180.0):
    d = np.abs(indices - centro) % periodo
    return np.minimum(d, periodo - d)


def _energia_cerca_de(hist, angulos, ventana=VENTANA_PICO_GRADOS):
    idx = np.arange(len(hist), dtype=np.float64)
    total = 0.0
    for centro in angulos:
        total += float(hist[_distancia_angular(idx, centro) <= ventana].sum())
    return total


def _histograma_angulos_cv2_lineas(gris_u8, umbral1=40, umbral2=120, min_largo=25, umbral_hough=35):
    """Detecta segmentos de recta con Canny + HoughLinesP (probabilistica) y
    arma un histograma de angulos ponderado por el largo de cada segmento
    (un segmento largo pesa mas que uno de 2 pixeles sueltos)."""
    bordes = cv2.Canny(gris_u8, umbral1, umbral2)
    segmentos = cv2.HoughLinesP(
        bordes, 1, np.pi / 360, threshold=umbral_hough,
        minLineLength=min_largo, maxLineGap=6,
    )
    hist = np.zeros(180, dtype=np.float64)
    if segmentos is None:
        return hist, 0
    for x1, y1, x2, y2 in segmentos[:, 0, :]:
        largo = float(np.hypot(x2 - x1, y2 - y1))
        if largo < 1:
            continue
        ang = float(np.degrees(np.arctan2(y2 - y1, x2 - x1))) % 180.0
        hist[int(round(ang)) % 180] += largo
    return hist, int(len(segmentos))


def _histograma_angulos_cv2_mascara(mask_bool, min_largo=18, umbral_hough=22):
    m = (mask_bool.astype(np.uint8)) * 255
    segmentos = cv2.HoughLinesP(
        m, 1, np.pi / 360, threshold=umbral_hough,
        minLineLength=min_largo, maxLineGap=8,
    )
    hist = np.zeros(180, dtype=np.float64)
    if segmentos is None:
        return hist, 0
    for x1, y1, x2, y2 in segmentos[:, 0, :]:
        largo = float(np.hypot(x2 - x1, y2 - y1))
        if largo < 1:
            continue
        ang = float(np.degrees(np.arctan2(y2 - y1, x2 - x1))) % 180.0
        hist[int(round(ang)) % 180] += largo
    return hist, int(len(segmentos))


def _histograma_angulos_fft(imagen, radio_min=8.0, margen_borde=4.0):
    """Respaldo sin cv2: estima que tan dominante es cada orientacion de
    linea a partir del espectro de Fourier 2D de la imagen (numpy puro).

    Una familia de lineas paralelas (periodicas, como la reticula impresa,
    o simplemente muy alineadas, como un trazo recto) concentra energia del
    espectro en una direccion PERPENDICULAR a la orientacion real de esas
    lineas (la intensidad de la imagen varia, con ese periodo, al cruzarlas).
    Por eso el histograma final se rota 90 grados antes de devolverlo."""
    g = imagen.astype(np.float64)
    g = g - g.mean()
    if g.std() < 1e-9:
        return np.zeros(180, dtype=np.float64), 0

    h, w = g.shape
    ventana = np.hanning(h)[:, None] * np.hanning(w)[None, :]  # atenua bordes, evita fugas espectrales
    espectro = np.fft.fftshift(np.fft.fft2(g * ventana))
    mag = np.abs(espectro)

    cy, cx = h // 2, w // 2
    # El pico central (frecuencia ~0, "brillo promedio") no dice nada de
    # orientacion: se apaga antes de acumular.
    mag[max(0, cy - 3):cy + 4, max(0, cx - 3):cx + 4] = 0.0

    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - cx).astype(np.float64)
    dy = (yy - cy).astype(np.float64)
    r = np.hypot(dx, dy)
    ang_espectro = np.degrees(np.arctan2(dy, dx)) % 180.0

    r_max = (min(h, w) / 2.0) - margen_borde
    sel = (r >= radio_min) & (r <= r_max)
    if not sel.any():
        return np.zeros(180, dtype=np.float64), 0

    bins = np.clip(np.round(ang_espectro[sel]).astype(int), 0, 179)
    pesos = mag[sel]
    hist = np.zeros(180, dtype=np.float64)
    np.add.at(hist, bins, pesos)

    hist = np.roll(hist, 90)  # angulo del espectro -> angulo de la linea real (son perpendiculares)
    return hist, int(sel.sum())


# =============================================================================
# Clasificacion a partir de un histograma de angulos
# =============================================================================
#
# Se usan DOS criterios sobre el MISMO histograma, porque cada uno falla en
# casos distintos, y se combinan (ver _clasificar_histograma al final):
#
#   1. _clasificar_por_ventanas: mira la energia cerca de los angulos
#      "de fabrica" (0/90 para vistas, 30/90/150 para isometricos). Es el
#      criterio mas directo, pero asume que la reticula quedo alineada con
#      los ejes de la imagen tras la rectificacion.
#   2. _clasificar_por_plegado: mira la SIMETRIA del histograma (si se
#      repite cada 90 grados -> cuadrada, si se repite cada 60 ->
#      triangular), sin importar en que angulo absoluto haya quedado esa
#      simetria. Es invariante a una rotacion global de la reticula (por
#      ejemplo, si la rectificacion de una hoja mal etiquetada dejo la
#      reticula girada unos grados de mas), un problema real observado con
#      hojas rectificadas con poca confianza (ver manifest, campo "avisos").
#
# Cuando ambos coinciden, se refuerza la confianza; cuando discrepan (senal
# de que algo salio raro: reticula muy rotada, ruido, etc.), se prefiere el
# que dio mas confianza pero se castiga fuerte el resultado final.

def _clasificar_por_ventanas(hist):
    """Energia cerca de los angulos "de fabrica" (0/90 vistas, 30/90/150
    isometricos). El 90 se excluye de la comparacion final porque aparece
    en ambos tipos de reticula y no ayuda a distinguir uno de otro."""
    total = float(hist.sum())
    if total <= 1e-9:
        return {"tipo": "indeterminado", "confianza": 0.0, "cobertura": 0.0}

    e_ortogonal = _energia_cerca_de(hist, [ANGULO_ORTOGONAL])
    e_vertical = _energia_cerca_de(hist, [ANGULO_VERTICAL])
    e_diagonal = _energia_cerca_de(hist, list(ANGULOS_DIAGONALES))

    señal_relevante = e_ortogonal + e_vertical + e_diagonal
    cobertura = señal_relevante / total  # cuanta energia del histograma cae en angulos "de interes" (vs. ruido disperso)

    if e_ortogonal + e_diagonal <= 1e-9:
        # Solo hay verticales (o nada): no alcanza para decidir entre los dos tipos.
        return {"tipo": "indeterminado", "confianza": 0.0, "cobertura": round(cobertura, 3)}

    if e_ortogonal >= e_diagonal:
        tipo = "vistas"
        dominancia = e_ortogonal / (e_ortogonal + e_diagonal)
    else:
        tipo = "isometricos"
        dominancia = e_diagonal / (e_ortogonal + e_diagonal)

    # Exige ademas que esa energia "de interes" no sea un resto marginal
    # del histograma completo (si domina el ruido, cobertura sera baja).
    confianza = dominancia * min(1.0, cobertura * 2.0)
    confianza = max(0.0, min(1.0, confianza))
    return {"tipo": tipo, "confianza": round(confianza, 3), "cobertura": round(cobertura, 3)}


def _clasificar_por_plegado(hist):
    """Simetria del histograma, sin importar la rotacion absoluta: se
    "pliega" el histograma cada 90 grados (h2, dos familias de lineas
    perpendiculares entre si: si es una reticula cuadrada, sus dos picos
    van a caer en el MISMO bin plegado) y cada 60 grados (h3, tres familias
    a 60 grados entre si: si es una reticula triangular, sus tres picos
    caen en el mismo bin plegado). El que quede mas concentrado en un solo
    bin (mayor "pico relativo") gana."""
    total = float(hist.sum())
    if total <= 1e-9:
        return {"tipo": "indeterminado", "confianza": 0.0}

    h2 = hist[:90] + hist[90:]
    h3 = hist[:60] + hist[60:120] + hist[120:]
    conc2 = float(h2.max() / h2.sum()) if h2.sum() > 0 else 0.0
    conc3 = float(h3.max() / h3.sum()) if h3.sum() > 0 else 0.0

    if conc2 >= conc3:
        tipo, dominancia = "vistas", conc2 - conc3
    else:
        tipo, dominancia = "isometricos", conc3 - conc2

    confianza = max(0.0, min(1.0, dominancia * 2.2))
    return {"tipo": tipo, "confianza": round(confianza, 3)}


def _clasificar_histograma(hist):
    """Combina _clasificar_por_ventanas y _clasificar_por_plegado sobre el
    mismo histograma (ver comentario mas arriba)."""
    por_ventanas = _clasificar_por_ventanas(hist)
    por_plegado = _clasificar_por_plegado(hist)

    if por_ventanas["tipo"] == "indeterminado" and por_plegado["tipo"] == "indeterminado":
        return {"tipo": "indeterminado", "confianza": 0.0, "cobertura": por_ventanas.get("cobertura", 0.0)}

    if por_ventanas["tipo"] == por_plegado["tipo"]:
        tipo = por_ventanas["tipo"] if por_ventanas["tipo"] != "indeterminado" else por_plegado["tipo"]
        confianza = min(1.0, max(por_ventanas["confianza"], por_plegado["confianza"]))
        return {"tipo": tipo, "confianza": round(confianza, 3), "cobertura": por_ventanas.get("cobertura", 0.0)}

    # Discrepan entre los dos criterios (probable reticula rotada o
    # histograma ruidoso): se prefiere el que dio mas confianza, pero se
    # castiga fuerte el resultado (mismo espiritu que _combinar_senales).
    if por_ventanas["confianza"] >= por_plegado["confianza"]:
        tipo, confianza = por_ventanas["tipo"], por_ventanas["confianza"]
    else:
        tipo, confianza = por_plegado["tipo"], por_plegado["confianza"]
    return {"tipo": tipo, "confianza": round(confianza * 0.5, 3), "cobertura": por_ventanas.get("cobertura", 0.0)}


# =============================================================================
# Señal (a): angulos de la reticula impresa (imagen en gris)
# =============================================================================

# Radio (px) con el que se dilata la mascara de trazo antes de "taparla" en
# la imagen en gris: el trazo de tinta suele ser mucho mas oscuro/grueso que
# la reticula impresa y, sin esto, una figura con lados oblicuos (valida en
# una hoja de VISTAS: una cara inclinada se proyecta como una linea a un
# angulo cualquiera) le gana en peso a la reticula y confunde la señal.
_RADIO_TAPAR_TRAZO = 5
_GRIS_RELLENO_TRAZO = 250  # valor tipico de fondo de hoja (ver comparador/LEEME.md)


def _limpiar_trazo_de_gris(gris, mascara_trazo):
    """Devuelve una copia de `gris` con la zona marcada por `mascara_trazo`
    (dilatada) rellenada al gris de fondo, para que la busqueda de angulos
    de la señal (a) vea solo la reticula impresa y no el dibujo del
    alumno/pauta encima. No cambia la mascara de trazo en si (la señal (b)
    sigue usando la mascara original, sin dilatar)."""
    if mascara_trazo is None or not mascara_trazo.any():
        return gris
    if mascara_trazo.shape != gris.shape:
        return gris
    if _CV2:
        k = np.ones((2 * _RADIO_TAPAR_TRAZO + 1, 2 * _RADIO_TAPAR_TRAZO + 1), np.uint8)
        dilatada = cv2.dilate(mascara_trazo.astype(np.uint8), k).astype(bool)
    else:
        m = mascara_trazo.astype(np.uint8)
        tmp = np.zeros_like(m)
        r = _RADIO_TAPAR_TRAZO
        for dx in range(-r, r + 1):
            if dx == 0:
                tmp |= m
            elif dx > 0:
                tmp[:, dx:] |= m[:, :-dx]
            else:
                tmp[:, :dx] |= m[:, -dx:]
        out = np.zeros_like(m)
        for dy in range(-r, r + 1):
            if dy == 0:
                out |= tmp
            elif dy > 0:
                out[dy:, :] |= tmp[:-dy, :]
            else:
                out[:dy, :] |= tmp[-dy:, :]
        dilatada = out.astype(bool)
    limpio = gris.copy()
    limpio[dilatada] = _GRIS_RELLENO_TRAZO
    return limpio


def detectar_por_reticula(ruta_o_gris, mascara_trazo=None):
    """`mascara_trazo`, si se entrega, se usa solo para tapar el dibujo
    (el trazo, sea del alumno o de la pauta) antes de buscar los angulos de
    la reticula impresa; no se usa para decidir el tipo (eso lo hace por su
    cuenta detectar_por_trazo, con la mascara original sin dilatar)."""
    gris = ruta_o_gris if isinstance(ruta_o_gris, np.ndarray) else cargar_gris(ruta_o_gris)
    gris = _limpiar_trazo_de_gris(gris, mascara_trazo)

    if _CV2:
        hist, n_segmentos = _histograma_angulos_cv2_lineas(gris)
        metodo = "hough_cv2"
        if n_segmentos < MIN_SEGMENTOS_RETICULA or hist.sum() < MIN_ENERGIA_RETICULA:
            # Muy pocos segmentos, o muy poca energia total detectada: no
            # alcanza para describir una reticula real (puede ser la
            # reticula tenue, una foto de mala calidad, o un puñado de
            # segmentos que son en realidad ruido/artefactos sueltos, por
            # ejemplo una sola sombra o un borde de la foto). En ese caso NO
            # se suma ese puñado de segmentos al respaldo de FFT: se
            # descarta y se usa el FFT solo, porque sumarlo puede sesgar
            # (con pocos datos) un resultado que de otro modo seria una
            # lectura limpia y bien calibrada del espectro completo.
            hist, _ = _histograma_angulos_fft(gris.astype(np.float64))
            metodo = "fft_respaldo"
    else:
        hist, _ = _histograma_angulos_fft(gris.astype(np.float64))
        metodo = "fft_numpy"

    resultado = _clasificar_histograma(hist)
    resultado["metodo"] = metodo
    return resultado


# =============================================================================
# Señal (b): angulos de los trazos del alumno (capa de trazo)
# =============================================================================

def detectar_por_trazo(ruta_o_mascara):
    mask = ruta_o_mascara if isinstance(ruta_o_mascara, np.ndarray) else cargar_mascara_trazo(ruta_o_mascara)
    n_trazo = int(mask.sum())

    if n_trazo < MIN_PIXELES_TRAZO:
        return {
            "tipo": "indeterminado", "confianza": 0.0, "cobertura": 0.0,
            "metodo": "sin_trazo_suficiente", "pixeles_trazo": n_trazo,
        }

    if _CV2:
        hist, n_segmentos = _histograma_angulos_cv2_mascara(mask)
        metodo = "hough_cv2"
        if n_segmentos < MIN_SEGMENTOS_TRAZO or hist.sum() < MIN_ENERGIA_TRAZO:
            # Mismo criterio que detectar_por_reticula: con pocos segmentos
            # no se suman al FFT (se descartan), para no sesgar una lectura
            # que de otro modo seria limpia.
            hist, _ = _histograma_angulos_fft(mask.astype(np.float64))
            metodo = "fft_respaldo"
    else:
        hist, _ = _histograma_angulos_fft(mask.astype(np.float64))
        metodo = "fft_numpy"

    resultado = _clasificar_histograma(hist)
    resultado["metodo"] = metodo
    resultado["pixeles_trazo"] = n_trazo
    return resultado


# =============================================================================
# Combinacion de ambas señales
# =============================================================================

def _combinar_senales(reticula, trazo):
    """Combina la señal de reticula (principal) con la de trazo (respaldo).

    La reticula manda cuando se leyo con confianza razonable
    (`UMBRAL_RETICULA_CONFIABLE`): un trazo con lados oblicuos validos (una
    cara inclinada en una vista, por ejemplo) no deberia poder "ganarle" a
    una reticula cuadrada o triangular bien leida. Aun asi, si el trazo
    discrepa, la confianza baja fuerte en vez de ignorarse del todo (queda
    registrado en `senales` para que se pueda revisar el porque). Solo
    cuando la reticula sale tenue/indeterminada se usa el trazo como señal
    principal de respaldo."""
    det_r = reticula["tipo"] != "indeterminado"
    det_t = trazo is not None and trazo["tipo"] != "indeterminado"
    reticula_confiable = det_r and reticula["confianza"] >= UMBRAL_RETICULA_CONFIABLE

    if not det_r and not det_t:
        return {"tipo": "indeterminado", "confianza": 0.0}

    if reticula_confiable:
        if det_t and trazo["tipo"] == reticula["tipo"]:
            confianza = PESO_RETICULA * reticula["confianza"] + PESO_TRAZO * trazo["confianza"]
            confianza = min(1.0, confianza + 0.1)  # bono: dos señales independientes coincidieron
            return {"tipo": reticula["tipo"], "confianza": round(confianza, 3)}
        if det_t:  # discrepan: manda la reticula, pero con la confianza bien castigada
            return {"tipo": reticula["tipo"], "confianza": round(reticula["confianza"] * 0.55, 3)}
        return {"tipo": reticula["tipo"], "confianza": round(reticula["confianza"] * 0.9, 3)}

    # Reticula tenue/indeterminada: se apoya en el trazo como respaldo.
    if det_t:
        return {"tipo": trazo["tipo"], "confianza": round(trazo["confianza"] * 0.75, 3)}
    if det_r:  # reticula determinada pero de baja confianza, y sin trazo util
        return {"tipo": reticula["tipo"], "confianza": round(reticula["confianza"] * 0.6, 3)}
    return {"tipo": "indeterminado", "confianza": 0.0}


def _con_piso_de_confianza(resultado):
    """Si, despues de combinar las señales, la confianza final queda por
    debajo de UMBRAL_CONFIANZA_MINIMA, se reporta "indeterminado" en vez de
    un tipo con muy poco respaldo (mejor no opinar que opinar casi al azar)."""
    if resultado["tipo"] != "indeterminado" and resultado["confianza"] < UMBRAL_CONFIANZA_MINIMA:
        return {"tipo": "indeterminado", "confianza": resultado["confianza"]}
    return resultado


def detectar_tipo_hoja(ruta_gris, ruta_trazo=None):
    """Detecta el tipo ("vistas"/"isometricos"/"indeterminado") de UN
    cuadro ya rectificado de 1000x1000, combinando la señal de la reticula
    impresa (obligatoria) con la señal del trazo del alumno (opcional: si
    no se entrega `ruta_trazo`, o el archivo no existe, se decide solo con
    la reticula, con la confianza levemente reducida).

    Devuelve {"tipo":..., "confianza": 0..1, "senales": {"reticula": {...},
    "trazo": {...} (si se pudo calcular)}}.
    """
    mascara_trazo = None
    if ruta_trazo and os.path.isfile(ruta_trazo):
        mascara_trazo = cargar_mascara_trazo(ruta_trazo)

    señal_reticula = detectar_por_reticula(ruta_gris, mascara_trazo=mascara_trazo)
    señal_trazo = detectar_por_trazo(mascara_trazo) if mascara_trazo is not None else None

    combinado = _con_piso_de_confianza(_combinar_senales(señal_reticula, señal_trazo))

    senales = {"reticula": señal_reticula}
    if señal_trazo is not None:
        senales["trazo"] = señal_trazo

    return {"tipo": combinado["tipo"], "confianza": combinado["confianza"], "senales": senales}


# =============================================================================
# CLI
# =============================================================================

def _main():
    ap = argparse.ArgumentParser(
        description="Detecta si un cuadro rectificado es de vistas o de isometricos."
    )
    ap.add_argument("gris", help="Ruta a la imagen en gris del cuadro (1000x1000).")
    ap.add_argument("trazo", nargs="?", default=None, help="Ruta a la capa de trazo (PNG RGBA), opcional.")
    args = ap.parse_args()
    resultado = detectar_tipo_hoja(args.gris, args.trazo)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
