#!/usr/bin/env python3
"""
Servidor web local de la Actividad 4 (Sistemas de Representacion).

Reemplaza a "python -m http.server": sirve los mismos archivos estaticos
(el visor, las entregas, las pautas, salida/...) y ademas expone dos
endpoints propios para el escaner manual de laminas (visor/escaner.html):

    GET  /api/imagenes   -> lista las imagenes de entregas/ y pautas/ que
                             el escaner puede ofrecer como "imagen ya
                             presente en el servidor".
    POST /api/guardar    -> recibe el resultado de una rectificacion manual
                             (imagenes en base64 + esquinas) y lo escribe en
                             salida/celdas/, salida/rectificadas/ y
                             salida/manifest.json, respetando el contrato
                             de manifest.json documentado en el propio
                             archivo (los mismos campos que genera
                             rectificador/rectificar.py).

Solo usa la biblioteca estandar de Python, mas PIL/numpy (para decodificar
los PNG que manda el navegador) y, si esta disponible, cv2 a traves de
rectificador/nucleo.py (para separar el trazo del alumno de la reticula
impresa y calcular las metricas de tinta). Si cv2 NO esta instalado en el
equipo, el guardado de la imagen en escala de grises de cada cuadro sigue
funcionando igual; simplemente no se genera la capa de trazo ni las
metricas, y el guardado avisa de esto en la respuesta (nunca revienta).

Ademas expone los endpoints de la pagina de comparacion
(visor/comparacion.html), que usan comparador/similitud.py y
comparador/notas_excel.py:

    GET  /api/comparacion/listado         -> usuarios, paginas y cuadros
                                              disponibles (a partir de
                                              manifest.json).
    GET  /api/comparacion/notas_alumno    -> resumen de porcentajes/nota
                                              sugerida de un alumno (a partir
                                              de la cache de comparaciones).
    POST /api/comparacion/comparar        -> compara un cuadro contra su
                                              pauta (con registro geometrico)
                                              y guarda el mapa de diferencia.
    POST /api/comparacion/comparar_pagina -> compara los 6 cuadros de una
                                              pagina de un alumno de una vez.
    POST /api/comparacion/registrar_nota  -> registra/actualiza la fila del
                                              alumno en salida/Notas_Actividad4.xlsx.

Y los de reetiquetado/deteccion de tipo de hoja (comparador/tipo_hoja.py),
pensados para el caso real de una hoja guardada bajo la parte equivocada
(ver comparador/LEEME.md, seccion "Deteccion de tipo de hoja"):

    POST /api/hoja/mover_parte  -> renombra una pagina completa de un
                                    alumno (celdas, hoja rectificada,
                                    manifest y cache de comparaciones) de
                                    una parte a la otra (por ejemplo
                                    "vistas" -> "isometricos").
    GET  /api/hoja/tipo         -> tipo detectado/confirmado de una pagina
                                    de un alumno (los calcula al vuelo si
                                    la pagina es antigua y no los tiene).

Ademas, /api/comparacion/comparar y /api/comparacion/comparar_pagina hacen
una verificacion cruzada de tipo ANTES de calcular el porcentaje: si el
cuadro del alumno no parece ser del mismo tipo que la pauta contra la que
se lo compara, devuelven una discrepancia en vez de un numero (con
confianza alta) o un aviso que no bloquea (con confianza baja).

Uso:
    python servidor.py [puerto]      (puerto por defecto: 8000)
"""

import base64
import datetime
import io
import json
import os
import re
import sys
import tempfile
import threading
import urllib.parse
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.abspath(__file__))
SALIDA_DIR = os.path.join(RAIZ, "salida")
CELDAS_DIR = os.path.join(SALIDA_DIR, "celdas")
RECTIFICADAS_DIR = os.path.join(SALIDA_DIR, "rectificadas")
MANIFEST_PATH = os.path.join(SALIDA_DIR, "manifest.json")
ENTREGAS_DIR = (
    os.path.join(RAIZ, "entradas", "entregas")
    if os.path.isdir(os.path.join(RAIZ, "entradas", "entregas"))
    else os.path.join(RAIZ, "entregas")
)
PAUTAS_DIR = (
    os.path.join(RAIZ, "entradas", "pautas_escaneadas")
    if os.path.isdir(os.path.join(RAIZ, "entradas", "pautas_escaneadas"))
    else os.path.join(RAIZ, "pautas")
)
SALIDA_PAUTAS_DIR = os.path.join(SALIDA_DIR, "pautas")
COMPARACION_DIR = os.path.join(SALIDA_DIR, "comparacion")
RESULTADOS_CACHE_PATH = os.path.join(COMPARACION_DIR, "resultados.json")
NOTAS_XLSX_PATH = os.path.join(SALIDA_DIR, "Notas_Actividad4.xlsx")

EXTENSIONES_IMAGEN = (".jpg", ".jpeg", ".png")

# Nombres de usuario/pagina: solo caracteres razonables de nombre de
# archivo (letras, numeros, guion, guion bajo, punto, parentesis). Evita que un valor
# raro termine escribiendo fuera de salida/celdas.
_RE_NOMBRE_SEGURO = re.compile(r"^[A-Za-z0-9_.\-()]{1,120}$")

# "vistas", "isometricos", o esos mismos nombres con un sufijo "_N" cuando un
# alumno entrego mas de una hoja del mismo tipo (ver rectificador/rectificar.py
# y visor/js/datos.js:tipoBasePagina, que resuelve el mismo caso en el visor).
_RE_TIPO_BASE_PAGINA = re.compile(r"^(vistas|isometricos)(?:_\d+)?$")

MANIFEST_LOCK = threading.Lock()
COMPARACION_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# comparador/similitud.py y comparador/notas_excel.py: motor de similitud y
# Excel de notas de la pagina de comparacion (visor/comparacion.html). Solo
# dependen de numpy/PIL (obligatorias, ya se usan arriba) y opcionalmente de
# cv2/openpyxl, asi que a diferencia de nucleo.py esta importacion no
# deberia fallar nunca en la practica; igual se protege para que un problema
# aqui no tumbe el resto del servidor (guardado de celdas, visor, escaner).
# ---------------------------------------------------------------------------
COMPARADOR_DISPONIBLE = False
COMPARADOR_ERROR = None
try:
    sys.path.insert(0, os.path.join(RAIZ, "comparador"))
    import similitud as csim  # noqa: E402
    import notas_excel as notas_xlsx  # noqa: E402
    import tipo_hoja as th_tipo  # noqa: E402  (deteccion de tipo de hoja: vistas/isometricos)
    COMPARADOR_DISPONIBLE = True
except Exception as e:
    COMPARADOR_ERROR = str(e)

# ---------------------------------------------------------------------------
# nucleo.py (separacion de trazo + metricas) es opcional: requiere cv2. Si
# no esta disponible en este equipo, se sigue guardando la imagen en gris
# igual (con PIL, que no depende de cv2), solo se omite la capa de trazo.
# ---------------------------------------------------------------------------
NUCLEO_DISPONIBLE = False
NUCLEO_ERROR = None
try:
    sys.path.insert(0, os.path.join(RAIZ, "rectificador"))
    import nucleo as nu  # noqa: E402  (import tardio a proposito)
    NUCLEO_DISPONIBLE = True
except Exception as e:  # ImportError si falta cv2, o cualquier otro problema
    NUCLEO_ERROR = str(e)


def listar_imagenes_carpeta(carpeta):
    if not os.path.isdir(carpeta):
        return []
    return sorted(f for f in os.listdir(carpeta) if os.path.splitext(f)[1].lower() in EXTENSIONES_IMAGEN)


def listar_imagenes_servidor():
    entregas = {}
    if os.path.isdir(ENTREGAS_DIR):
        for usuario in sorted(os.listdir(ENTREGAS_DIR)):
            carpeta = os.path.join(ENTREGAS_DIR, usuario)
            if not os.path.isdir(carpeta):
                continue
            archivos = listar_imagenes_carpeta(carpeta)
            if archivos:
                entregas[usuario] = archivos
    pautas = listar_imagenes_carpeta(PAUTAS_DIR)
    return {"entregas": entregas, "pautas": pautas}


def decodificar_png_gris(png_bytes):
    """Decodifica un PNG (bytes) a un arreglo numpy 2D uint8 en escala de
    grises. Usa PIL exclusivamente: funciona aunque cv2 no este instalado.
    """
    im = Image.open(io.BytesIO(png_bytes))
    im = im.convert("L")
    return np.array(im, dtype=np.uint8)


def decodificar_png_rgb(png_bytes):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    return np.array(im, dtype=np.uint8)


def ruta_relativa_salida(ruta_absoluta):
    return os.path.relpath(ruta_absoluta, SALIDA_DIR).replace(os.sep, "/")


# ---------------------------------------------------------------------------
# manifest.json: lectura, actualizacion segura (upsert) y escritura atomica.
# ---------------------------------------------------------------------------

def manifest_vacio():
    return {
        "version": 1,
        "generado": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "pautas": {"vistas": {"celdas": []}, "isometricos": {"celdas": []}},
        "alumnos": [],
        "resumen": {"alumnos": 0, "paginas_ok": 0, "paginas_fallback": 0, "paginas_fallidas": 0},
    }


def leer_manifest():
    if not os.path.isfile(MANIFEST_PATH):
        return manifest_vacio()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def escribir_manifest_atomico(manifest):
    os.makedirs(SALIDA_DIR, exist_ok=True)
    manifest["generado"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    fd, tmp_path = tempfile.mkstemp(prefix=".manifest_", suffix=".json.tmp", dir=SALIDA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, MANIFEST_PATH)  # atomico dentro del mismo filesystem
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def recomputar_resumen(manifest):
    """Recalcula manifest['resumen'] recorriendo todas las paginas de todos
    los alumnos (mismo criterio que usa rectificador/rectificar.py):
    'contornos' -> ok, 'fallido' -> fallida, cualquier otro metodo (incluido
    'manual') -> fallback/parcial.
    """
    alumnos = manifest.get("alumnos", [])
    ok = fallback = fallidas = 0
    for al in alumnos:
        for pg in al.get("paginas", []):
            metodo = pg.get("metodo")
            if metodo == "contornos":
                ok += 1
            elif metodo == "fallido":
                fallidas += 1
            else:
                fallback += 1
    manifest["resumen"] = {
        "alumnos": len(alumnos),
        "paginas_ok": ok,
        "paginas_fallback": fallback,
        "paginas_fallidas": fallidas,
    }


# ---------------------------------------------------------------------------
# Deteccion del tipo de hoja (comparador/tipo_hoja.py) a nivel de PAGINA:
# agrega la deteccion de cada cuadro (que opera sobre un solo cuadro de
# 1000x1000) en un solo veredicto para la pagina completa. Varios cuadros
# de acuerdo entre si pesan mas que uno solo muy seguro (ver `cobertura`
# mas abajo): una pagina de 6 cuadros donde solo 1 dio una señal fuerte no
# deberia terminar con la misma confianza que una donde los 6 coincidieron.
# ---------------------------------------------------------------------------

CONFIANZA_MINIMA_TIPO_PAGINA = 0.25


def _detectar_tipo_pagina(pag):
    """Devuelve {"tipo": "vistas"|"isometricos"|"indeterminado", "confianza":
    0..1} para la pagina `pag` (una entrada de alumno["paginas"]), o None si
    el modulo de deteccion no esta disponible. No escribe nada en el
    manifest: eso lo hace quien llama (actualizar_manifest_con_celdas u
    obtener_tipo_pagina)."""
    if not COMPARADOR_DISPONIBLE:
        return None

    resultados = []
    for c in pag.get("celdas", []):
        img = c.get("img")
        if not img:
            continue
        ruta_gris = os.path.join(SALIDA_DIR, img)
        if not os.path.isfile(ruta_gris):
            continue
        ruta_trazo = None
        if c.get("trazo"):
            candidata = os.path.join(SALIDA_DIR, c["trazo"])
            if os.path.isfile(candidata):
                ruta_trazo = candidata
        try:
            resultados.append(th_tipo.detectar_tipo_hoja(ruta_gris, ruta_trazo))
        except Exception:
            continue  # un cuadro que no se pudo leer/analizar no tumba la deteccion de toda la pagina

    if not resultados:
        return {"tipo": "indeterminado", "confianza": 0.0}

    pesos = {"vistas": 0.0, "isometricos": 0.0}
    for r in resultados:
        if r.get("tipo") in pesos:
            pesos[r["tipo"]] += r.get("confianza", 0.0)

    if pesos["vistas"] <= 1e-9 and pesos["isometricos"] <= 1e-9:
        return {"tipo": "indeterminado", "confianza": 0.0}

    tipo = max(pesos, key=pesos.get)
    otro = "isometricos" if tipo == "vistas" else "vistas"
    total = pesos[tipo] + pesos[otro]
    dominancia = pesos[tipo] / total if total > 0 else 0.0
    cobertura = sum(1 for r in resultados if r.get("tipo") == tipo) / len(resultados)
    confianza = round(max(0.0, min(1.0, dominancia * (0.5 + 0.5 * cobertura))), 3)

    if confianza < CONFIANZA_MINIMA_TIPO_PAGINA:
        return {"tipo": "indeterminado", "confianza": confianza}
    return {"tipo": tipo, "confianza": confianza}


_AVISO_MANUAL_PREFIJO = "Corregido a mano con el escaner"


def actualizar_manifest_con_celdas(usuario, pagina, celdas_nuevas, hoja_rel=None):
    """Aplica el guardado manual al manifest: crea al alumno/pagina si no
    existen, reemplaza (upsert) las celdas por numero, y marca la pagina
    como metodo="manual" con confianza 1.0. Devuelve la entrada de pagina
    resultante. Protegido por MANIFEST_LOCK para que dos guardados
    concurrentes no se pisen (lee-modifica-escribe atomico a nivel de
    proceso).
    """
    with MANIFEST_LOCK:
        manifest = leer_manifest()
        manifest.setdefault("alumnos", [])

        alumno = next((a for a in manifest["alumnos"] if a.get("usuario") == usuario), None)
        if alumno is None:
            alumno = {"usuario": usuario, "paginas": []}
            manifest["alumnos"].append(alumno)
            manifest["alumnos"].sort(key=lambda a: a.get("usuario", ""))

        pag = next((p for p in alumno["paginas"] if p.get("pagina") == pagina), None)
        if pag is None:
            pag = {
                "pagina": pagina,
                "origen": "manual (escaner)",
                "hoja": None,
                "metodo": "manual",
                "confianza": 1.0,
                "avisos": [],
                "celdas": [],
            }
            alumno["paginas"].append(pag)

        pag["metodo"] = "manual"
        pag["confianza"] = 1.0
        if hoja_rel is not None:
            pag["hoja"] = hoja_rel

        avisos = [a for a in pag.get("avisos", []) if not a.startswith(_AVISO_MANUAL_PREFIJO)]
        ahora = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
        avisos.append(f"{_AVISO_MANUAL_PREFIJO} el {ahora}.")
        pag["avisos"] = avisos

        por_n = {c["n"]: c for c in pag.get("celdas", [])}
        for c in celdas_nuevas:
            por_n[c["n"]] = c
        pag["celdas"] = [por_n[k] for k in sorted(por_n.keys())]

        # Deteccion de tipo (comparador/tipo_hoja.py): se recalcula siempre
        # que se guarda, porque el contenido de los cuadros pudo cambiar.
        # "tipo_confirmado" es lo que decide el profesor (por ahora, solo se
        # fija al usar /api/hoja/mover_parte); no se toca aqui si ya existia.
        deteccion = _detectar_tipo_pagina(pag)
        if deteccion is not None:
            pag["tipo_detectado"] = deteccion["tipo"]
            pag["confianza_tipo"] = deteccion["confianza"]
        pag.setdefault("tipo_confirmado", None)

        recomputar_resumen(manifest)
        escribir_manifest_atomico(manifest)
        return pag


# ---------------------------------------------------------------------------
# Procesamiento de una celda recibida: guarda el gris, y si nucleo.py esta
# disponible, tambien la capa de trazo y las metricas.
# ---------------------------------------------------------------------------

def procesar_celda(usuario, pagina, celda_in, avisos):
    n = celda_in["n"]
    prefijo = f"{usuario}_{pagina}"
    png_bytes = base64.b64decode(celda_in["imagen_png_base64"])
    gris = decodificar_png_gris(png_bytes)

    os.makedirs(CELDAS_DIR, exist_ok=True)
    nombre_gris = f"{prefijo}_c{n}.png"
    ruta_gris = os.path.join(CELDAS_DIR, nombre_gris)
    Image.fromarray(gris, mode="L").save(ruta_gris)
    archivos = [ruta_relativa_salida(ruta_gris)]

    esquinas = [[round(float(x), 1), round(float(y), 1)] for x, y in celda_in["esquinas"]]

    entrada = {
        "n": n,
        "img": ruta_relativa_salida(ruta_gris),
        "trazo": None,
        "tinta": None,
        "componentes": None,
        "vacio": None,
        "esquinas": esquinas,
    }

    if NUCLEO_DISPONIBLE:
        try:
            rgba, mascara, ncomp = nu.separar_trazo(gris)
            tinta, vacio = nu.metricas_celda(mascara, ncomp)
            nombre_trazo = f"{prefijo}_c{n}_trazo.png"
            ruta_trazo = os.path.join(CELDAS_DIR, nombre_trazo)
            Image.fromarray(rgba, mode="RGBA").save(ruta_trazo)
            entrada["trazo"] = ruta_relativa_salida(ruta_trazo)
            entrada["tinta"] = round(float(tinta), 4)
            entrada["componentes"] = int(ncomp)
            entrada["vacio"] = bool(vacio)
            archivos.append(ruta_relativa_salida(ruta_trazo))
        except Exception as e:
            avisos.append(f"Cuadro {n}: no se pudo generar la capa de trazo/metricas ({e}). Se guardo igual la imagen en gris.")
    else:
        avisos.append(
            "OpenCV (cv2) no esta disponible en este equipo: no se genero la capa de "
            "trazo ni las metricas de tinta de los cuadros guardados (solo la imagen "
            "en escala de grises, que se ve y compara igual en el visor)."
        )

    return entrada, archivos


def actualizar_manifest_pauta(pagina, celdas_nuevas, hoja_rel=None):
    """Guarda o actualiza la pauta oficial del profesor en manifest.json
    bajo manifest['pautas'][base].
    """
    base = _tipo_base_pagina(pagina) or pagina
    with MANIFEST_LOCK:
        manifest = leer_manifest()
        manifest.setdefault("pautas", {})
        p = manifest["pautas"].setdefault(base, {"celdas": []})
        p["origen"] = "manual (escaner)"
        p["metodo"] = "manual"
        p["confianza"] = 1.0
        ahora = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
        p["avisos"] = [f"Pauta cargada a mano con el escaner el {ahora}."]
        if hoja_rel:
            p["hoja"] = hoja_rel
        por_n = {c["n"]: c for c in p.get("celdas", [])}
        for c in celdas_nuevas:
            por_n[c["n"]] = c
        p["celdas"] = [por_n[k] for k in sorted(por_n.keys())]
        escribir_manifest_atomico(manifest)
        return p


def procesar_celda_pauta(pagina, celda_in, avisos):
    """Procesa una celda de la pauta del profesor y la guarda en salida/pautas/."""
    base = _tipo_base_pagina(pagina) or pagina
    n = celda_in["n"]
    prefijo = f"pauta_{base}"
    png_bytes = base64.b64decode(celda_in["imagen_png_base64"])
    gris = decodificar_png_gris(png_bytes)

    os.makedirs(SALIDA_PAUTAS_DIR, exist_ok=True)
    nombre_gris = f"{prefijo}_c{n}.png"
    ruta_gris = os.path.join(SALIDA_PAUTAS_DIR, nombre_gris)
    Image.fromarray(gris, mode="L").save(ruta_gris)
    archivos = [f"pautas/{nombre_gris}"]

    esquinas = [[round(float(x), 1), round(float(y), 1)] for x, y in celda_in.get("esquinas", [])]

    entrada = {
        "n": n,
        "img": f"pautas/{nombre_gris}",
        "trazo": None,
        "tinta": None,
        "componentes": None,
        "vacio": None,
        "esquinas": esquinas,
    }

    if NUCLEO_DISPONIBLE:
        try:
            rgba, mascara, ncomp = nu.separar_trazo(gris, base)
            tinta, vacio = nu.metricas_celda(mascara, ncomp)
            nombre_trazo = f"{prefijo}_c{n}_trazo.png"
            ruta_trazo = os.path.join(SALIDA_PAUTAS_DIR, nombre_trazo)
            Image.fromarray(rgba, mode="RGBA").save(ruta_trazo)
            entrada["trazo"] = f"pautas/{nombre_trazo}"
            entrada["tinta"] = round(float(tinta), 4)
            entrada["componentes"] = int(ncomp)
            entrada["vacio"] = bool(vacio)
            archivos.append(f"pautas/{nombre_trazo}")
        except Exception as e:
            avisos.append(f"Cuadro pauta {n}: no se pudo generar capa de trazo ({e}). Se guardo imagen en gris.")
    else:
        avisos.append("cv2 no disponible: pauta guardada solo en escala de grises.")
    return entrada, archivos


# ---------------------------------------------------------------------------
# Pagina de comparacion (visor/comparacion.html): listado de datos
# disponibles, comparacion de cuadros contra su pauta (con cache en disco) y
# registro de notas en el Excel. Todo esto se apoya en el mismo
# manifest.json que ya usan el visor y el escaner.
# ---------------------------------------------------------------------------

def _tipo_base_pagina(pagina):
    m = _RE_TIPO_BASE_PAGINA.match(pagina or "")
    return m.group(1) if m else None


def _buscar_alumno(manifest, usuario):
    for a in manifest.get("alumnos", []):
        if a.get("usuario") == usuario:
            return a
    return None


def _buscar_pagina_alumno(alumno, pagina):
    for p in (alumno or {}).get("paginas", []):
        if p.get("pagina") == pagina:
            return p
    return None


def _buscar_celda(pagina_entry, n):
    for c in (pagina_entry or {}).get("celdas", []):
        if c.get("n") == n:
            return c
    return None


def _celdas_pauta_en_disco(pagina):
    """Respaldo cuando el manifest no tiene registradas las pautas: busca en
    salida/pautas/ los archivos que siguen la convencion de nombres
    pauta_<pagina>_c<N>.png y pauta_<pagina>_c<N>_trazo.png. Asi el generador
    de pauta vectorial puede limitarse a dejar los PNG, sin tocar el manifest."""
    base = _tipo_base_pagina(pagina) or pagina
    carpeta = os.path.join(SALIDA_DIR, "pautas")
    if not os.path.isdir(carpeta):
        return []
    celdas = []
    for n in range(1, 7):
        trazo = f"pauta_{base}_c{n}_trazo.png"
        img = f"pauta_{base}_c{n}.png"
        if os.path.isfile(os.path.join(carpeta, trazo)):
            entrada = {"n": n, "trazo": f"pautas/{trazo}"}
            if os.path.isfile(os.path.join(carpeta, img)):
                entrada["img"] = f"pautas/{img}"
            celdas.append(entrada)
    return celdas


def _celdas_pauta(manifest, pagina):
    """Misma logica de respaldo que visor/js/datos.js:celdasPauta: si no hay
    una pauta con el nombre exacto de la pagina (por ejemplo "vistas_2"),
    cae al tipo base ("vistas"). Si el manifest no trae nada, se buscan los
    archivos directamente en salida/pautas/."""
    pautas = manifest.get("pautas", {})
    p = pautas.get(pagina)
    if not p or not p.get("celdas"):
        base = _tipo_base_pagina(pagina)
        p = pautas.get(base) if base else None
    celdas = (p or {}).get("celdas", [])
    if not celdas:
        celdas = _celdas_pauta_en_disco(pagina)
    return celdas


def _celda_pauta(manifest, pagina, n):
    for c in _celdas_pauta(manifest, pagina):
        if c.get("n") == n:
            return c
    return None


def _clave_cuadro_comparacion(usuario, pagina, n):
    return f"{usuario}|{pagina}|{n}"


def _leer_cache_comparacion():
    if not os.path.isfile(RESULTADOS_CACHE_PATH):
        return {"version": 1, "resultados": {}}
    try:
        with open(RESULTADOS_CACHE_PATH, "r", encoding="utf-8") as fh:
            datos = json.load(fh)
    except Exception:
        return {"version": 1, "resultados": {}}
    datos.setdefault("resultados", {})
    return datos


def _escribir_cache_comparacion_atomico(cache):
    os.makedirs(COMPARACION_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".resultados_", suffix=".json.tmp", dir=COMPARACION_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, RESULTADOS_CACHE_PATH)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _quitar_privados(entrada):
    return {k: v for k, v in entrada.items() if not k.startswith("_")}


_PARTES = ("vistas", "isometricos")


def _notas_finales_registradas():
    """{usuario: nota_final} de todos los que ya tienen una nota_final
    (no vacia) registrada en salida/Notas_Actividad4.xlsx (o el .csv de
    respaldo). Se lee UNA vez por llamada a listado_comparacion, no por
    alumno (leer_todas relee el archivo completo cada vez)."""
    if not COMPARADOR_DISPONIBLE:
        return {}
    try:
        filas = notas_xlsx.leer_todas(NOTAS_XLSX_PATH)
    except Exception:
        return {}
    return {
        f.get("usuario"): f.get("nota_final")
        for f in filas
        if f.get("usuario") and f.get("nota_final") not in (None, "")
    }


def listado_comparacion():
    """GET /api/comparacion/listado: usuarios, paginas y cuadros disponibles,
    leidos de manifest.json (que a su vez refleja lo que hay en
    salida/celdas: es el mismo archivo que mantiene sincronizado
    servidor.py al guardar y rectificador/rectificar.py al procesar).

    Ademas de lo que ya devolvia (por pagina: metodo, confianza, cuadros,
    tiene_pauta), agrega por pagina el tipo detectado/confirmado, y por
    alumno un resumen `partes` con el estado de cada parte de la actividad
    (sin_escanear/escaneada/comparada/con_nota) para que el visor lo pueda
    pintar sin tener que armar esa logica de nuevo del lado del cliente."""
    manifest = leer_manifest()
    cache = _leer_cache_comparacion() if COMPARADOR_DISPONIBLE else {"resultados": {}}
    notas_por_usuario = _notas_finales_registradas()

    alumnos = []
    for al in manifest.get("alumnos", []):
        usuario = al.get("usuario")
        paginas_alumno = al.get("paginas", [])

        paginas = []
        for pg in paginas_alumno:
            cuadros = sorted(c.get("n") for c in pg.get("celdas", []) if c.get("trazo") and c.get("n") is not None)
            paginas.append({
                "pagina": pg.get("pagina"),
                "tipo_base": _tipo_base_pagina(pg.get("pagina")),
                "metodo": pg.get("metodo"),
                "confianza": pg.get("confianza"),
                "cuadros": cuadros,
                "tiene_pauta": bool(_celdas_pauta(manifest, pg.get("pagina"))),
                "tipo_detectado": pg.get("tipo_detectado"),
                "confianza_tipo": pg.get("confianza_tipo"),
                "tipo_confirmado": pg.get("tipo_confirmado"),
            })

        partes = {}
        for parte in _PARTES:
            paginas_parte = [p for p in paginas_alumno if _tipo_base_pagina(p.get("pagina")) == parte]
            if not paginas_parte:
                partes[parte] = {"estado": "sin_escanear", "tipo_detectado": None, "confianza_tipo": None}
                continue

            # La pagina "principal" (sin sufijo _2, _3...) manda si existe;
            # si el alumno solo tiene la version con sufijo, se usa esa.
            principal = next((p for p in paginas_parte if p.get("pagina") == parte), paginas_parte[0])

            if usuario in notas_por_usuario:
                estado = "con_nota"
            else:
                tiene_comparacion = any(
                    clave.split("|", 2)[0] == usuario and _tipo_base_pagina(clave.split("|", 2)[1]) == parte
                    for clave in cache.get("resultados", {})
                )
                estado = "comparada" if tiene_comparacion else "escaneada"

            partes[parte] = {
                "estado": estado,
                "tipo_detectado": principal.get("tipo_detectado"),
                "confianza_tipo": principal.get("confianza_tipo"),
            }

        alumnos.append({"usuario": usuario, "paginas": paginas, "partes": partes})
    alumnos.sort(key=lambda a: a["usuario"])

    pautas = {}
    for nombre, entrada in manifest.get("pautas", {}).items():
        pautas[nombre] = sorted(
            c.get("n") for c in entrada.get("celdas", []) if c.get("trazo") and c.get("n") is not None
        )
    return {"alumnos": alumnos, "pautas": pautas}


def obtener_tipo_pagina(usuario, pagina):
    """GET /api/hoja/tipo: tipo_detectado/confianza_tipo/tipo_confirmado de
    `usuario`/`pagina`. Si la pagina es de antes de este cambio (no tiene
    esos campos), se calculan al vuelo y se dejan guardados en el manifest
    para no tener que recalcularlos en la proxima consulta."""
    manifest = leer_manifest()
    alumno = _buscar_alumno(manifest, usuario)
    if alumno is None:
        raise ValueError(f"No existe el alumno '{usuario}' en el manifest.")
    pag = _buscar_pagina_alumno(alumno, pagina)
    if pag is None:
        raise ValueError(f"El alumno '{usuario}' no tiene la pagina '{pagina}'.")

    if pag.get("tipo_detectado") is None:
        deteccion = _detectar_tipo_pagina(pag) or {"tipo": "indeterminado", "confianza": 0.0}
        with MANIFEST_LOCK:
            manifest2 = leer_manifest()
            alumno2 = _buscar_alumno(manifest2, usuario)
            pag2 = _buscar_pagina_alumno(alumno2, pagina) if alumno2 else None
            if pag2 is not None:
                pag2["tipo_detectado"] = deteccion["tipo"]
                pag2["confianza_tipo"] = deteccion["confianza"]
                pag2.setdefault("tipo_confirmado", None)
                escribir_manifest_atomico(manifest2)
                pag = pag2
            else:
                pag = dict(pag)
                pag["tipo_detectado"] = deteccion["tipo"]
                pag["confianza_tipo"] = deteccion["confianza"]

    return {
        "usuario": usuario,
        "pagina": pagina,
        "tipo_detectado": pag.get("tipo_detectado"),
        "confianza_tipo": pag.get("confianza_tipo"),
        "tipo_confirmado": pag.get("tipo_confirmado"),
    }


# ---------------------------------------------------------------------------
# Reetiquetado de una hoja completa (item 1 de la tarea): POST
# /api/hoja/mover_parte. Renombra en disco todos los archivos de la pagina
# de origen (celdas + hoja rectificada), actualiza el manifest y borra de
# la cache de comparaciones lo que quedo obsoleto (junto con sus mapas de
# diferencia). Si la pagina destino ya existe para ese alumno, no se toca
# nada: se corta con un error antes de renombrar el primer archivo.
# ---------------------------------------------------------------------------

def mover_parte_hoja(usuario, pagina_origen, pagina_destino):
    usuario = str(usuario or "").strip()
    pagina_origen = str(pagina_origen or "").strip()
    pagina_destino = str(pagina_destino or "").strip()

    if not usuario or not _RE_NOMBRE_SEGURO.match(usuario):
        raise ValueError("Usuario invalido o vacio.")
    if not pagina_origen or not _RE_NOMBRE_SEGURO.match(pagina_origen):
        raise ValueError("Pagina de origen invalida o vacia.")
    if not pagina_destino or not _RE_NOMBRE_SEGURO.match(pagina_destino):
        raise ValueError("Pagina de destino invalida o vacia.")
    if pagina_origen == pagina_destino:
        raise ValueError("La pagina de origen y la de destino son la misma: no hay nada que mover.")

    with MANIFEST_LOCK:
        manifest = leer_manifest()
        alumno = _buscar_alumno(manifest, usuario)
        if alumno is None:
            raise ValueError(f"No existe el alumno '{usuario}' en el manifest.")
        pag_origen = _buscar_pagina_alumno(alumno, pagina_origen)
        if pag_origen is None:
            raise ValueError(f"El alumno '{usuario}' no tiene la pagina '{pagina_origen}'.")
        if _buscar_pagina_alumno(alumno, pagina_destino) is not None:
            raise ValueError(
                f"El alumno '{usuario}' ya tiene una pagina '{pagina_destino}': no se puede "
                "reetiquetar sin pisarla. Si corresponde, primero hay que renombrar o eliminar "
                "esa pagina destino (por ejemplo con otro sufijo, '_2')."
            )

        prefijo_origen = f"{usuario}_{pagina_origen}_c"
        prefijo_destino = f"{usuario}_{pagina_destino}_c"

        # --- Fase 1: se junta TODO lo que hay que renombrar y se valida que
        #     ningun destino exista ya en disco, antes de mover nada (para
        #     que un choque a mitad de camino no deje la pagina a medias). ---
        renombres = []  # lista de (ruta_origen_abs, ruta_destino_abs)
        if os.path.isdir(CELDAS_DIR):
            for nombre in sorted(os.listdir(CELDAS_DIR)):
                if not nombre.startswith(prefijo_origen):
                    continue
                nuevo_nombre = prefijo_destino + nombre[len(prefijo_origen):]
                ruta_o = os.path.join(CELDAS_DIR, nombre)
                ruta_d = os.path.join(CELDAS_DIR, nuevo_nombre)
                if os.path.exists(ruta_d):
                    raise ValueError(
                        f"Ya existe '{ruta_relativa_salida(ruta_d)}': no se puede reetiquetar sin pisarlo."
                    )
                renombres.append((ruta_o, ruta_d))

        ruta_hoja_o = os.path.join(RECTIFICADAS_DIR, f"{usuario}_{pagina_origen}.png")
        ruta_hoja_d = os.path.join(RECTIFICADAS_DIR, f"{usuario}_{pagina_destino}.png")
        mueve_hoja = os.path.isfile(ruta_hoja_o)
        if mueve_hoja:
            if os.path.exists(ruta_hoja_d):
                raise ValueError(
                    f"Ya existe '{ruta_relativa_salida(ruta_hoja_d)}': no se puede reetiquetar sin pisarlo."
                )
            renombres.append((ruta_hoja_o, ruta_hoja_d))

        # --- Fase 2: ya se valido que ningun destino existe; se renombra
        #     todo. os.replace() es atomico por archivo (mismo filesystem),
        #     igual que el resto del servidor usa temp+os.replace() para
        #     los JSON: aqui no hay contenido que escribir, solo el nombre,
        #     asi que el rename atomico ES el equivalente correcto. ---
        movidos = []
        for ruta_o, ruta_d in renombres:
            os.replace(ruta_o, ruta_d)
            movidos.append({"de": ruta_relativa_salida(ruta_o), "a": ruta_relativa_salida(ruta_d)})

        # --- Manifest: renombra la pagina, las rutas de cada celda, la hoja
        #     completa, y deja tipo_confirmado = tipo de la pagina destino
        #     (mover la pagina ES la confirmacion explicita del profesor). ---
        pag_origen["pagina"] = pagina_destino
        for c in pag_origen.get("celdas", []):
            for campo in ("img", "trazo"):
                v = c.get(campo)
                if v and prefijo_origen in v:
                    c[campo] = v.replace(prefijo_origen, prefijo_destino)
        if mueve_hoja:
            pag_origen["hoja"] = ruta_relativa_salida(ruta_hoja_d)
        pag_origen["tipo_confirmado"] = _tipo_base_pagina(pagina_destino) or pagina_destino

        recomputar_resumen(manifest)
        escribir_manifest_atomico(manifest)

    # --- Cache de comparaciones: se invalida lo que quedo obsoleto de la
    #     pagina de ORIGEN (la pagina destino no tenia cache propia: recien
    #     se valido arriba que no existia antes de este movimiento). ---
    with COMPARACION_LOCK:
        cache = _leer_cache_comparacion()
        cambiado = False
        for n in range(1, 7):
            clave_vieja = _clave_cuadro_comparacion(usuario, pagina_origen, n)
            entrada = cache["resultados"].pop(clave_vieja, None)
            if entrada is None:
                continue
            cambiado = True
            mapa = entrada.get("mapa_diferencia")
            if mapa:
                try:
                    os.remove(os.path.join(SALIDA_DIR, mapa))
                except OSError:
                    pass
        if cambiado:
            _escribir_cache_comparacion_atomico(cache)

    return {"ok": True, "movidos": movidos, "pagina_destino": pagina_destino}


# ---------------------------------------------------------------------------
# Verificacion cruzada de tipo (item 2 de la tarea): antes de calcular el
# parecido de un cuadro contra su pauta, se compara el tipo detectado de
# ESE cuadro (o el que el profesor ya haya confirmado para la pagina, que
# manda sobre cualquier deteccion automatica) contra el tipo de la pauta
# que se va a usar. Resuelve el problema real que motiva este modulo: una
# hoja de isometricos guardada como pagina "vistas" se comparaba contra la
# pauta de vistas y entregaba un porcentaje bajo que se veia identico a un
# dibujo malo, cuando en realidad se estaban comparando dos cosas distintas.
# ---------------------------------------------------------------------------

UMBRAL_DISCREPANCIA_BLOQUEA = 0.55  # confianza a partir de la cual se bloquea el calculo del porcentaje.
UMBRAL_DISCREPANCIA_AVISA = 0.30    # confianza a partir de la cual se agrega un aviso (sin bloquear).


def verificar_tipo_antes_de_comparar(usuario, pagina_alumno, pag_alumno, celda, pagina_pauta, deteccion_tipo=None):
    """Devuelve None si no hay nada que avisar. Si el tipo del cuadro del
    alumno discrepa del tipo de la pauta con confianza alta, devuelve
    {"discrepancia_tipo": True, ...} (quien llama NO debe calcular ningun
    porcentaje en ese caso). Si discrepa con confianza baja, devuelve
    {"aviso_tipo": "..."} (no bloquea: se agrega al resultado normal).

    `pag_alumno` es la entrada de pagina del alumno (para leer
    "tipo_confirmado", que manda sobre la deteccion automatica). `celda` es
    la entrada de esa pagina para el cuadro que se va a comparar.
    `deteccion_tipo`, si se entrega, evita recalcular la deteccion (la usan
    las pruebas y quien ya la haya calculado para otro fin)."""
    tipo_pauta = _tipo_base_pagina(pagina_pauta) or pagina_pauta

    tipo_confirmado = (pag_alumno or {}).get("tipo_confirmado")
    if tipo_confirmado:
        if tipo_confirmado == tipo_pauta:
            return None
        return {
            "discrepancia_tipo": True,
            "tipo_alumno": tipo_confirmado,
            "tipo_pauta": tipo_pauta,
            "confianza": 1.0,
            "mensaje": (
                f"La pagina '{pagina_alumno}' de {usuario} fue confirmada como '{tipo_confirmado}', "
                f"pero se esta comparando contra la pauta de '{tipo_pauta}'. Esta hoja parece ser de "
                "la otra parte de la actividad: se puede corregir con POST /api/hoja/mover_parte."
            ),
        }

    if not COMPARADOR_DISPONIBLE:
        return None  # sin el modulo de deteccion disponible, no se puede verificar: se deja pasar.

    if deteccion_tipo is None:
        img = (celda or {}).get("img")
        if not img:
            return None
        ruta_gris = os.path.join(SALIDA_DIR, img)
        if not os.path.isfile(ruta_gris):
            return None
        ruta_trazo = None
        if celda.get("trazo"):
            candidata = os.path.join(SALIDA_DIR, celda["trazo"])
            if os.path.isfile(candidata):
                ruta_trazo = candidata
        try:
            deteccion_tipo = th_tipo.detectar_tipo_hoja(ruta_gris, ruta_trazo)
        except Exception:
            return None  # si la deteccion falla, no se bloquea la comparacion por eso.

    tipo_alumno = deteccion_tipo.get("tipo")
    confianza = deteccion_tipo.get("confianza", 0.0)

    if tipo_alumno in (None, "indeterminado") or tipo_alumno == tipo_pauta:
        return None

    n = (celda or {}).get("n")
    if confianza >= UMBRAL_DISCREPANCIA_BLOQUEA:
        return {
            "discrepancia_tipo": True,
            "tipo_alumno": tipo_alumno,
            "tipo_pauta": tipo_pauta,
            "confianza": confianza,
            "mensaje": (
                f"El cuadro {n} de {usuario}/{pagina_alumno} se detecta como '{tipo_alumno}' "
                f"(confianza {confianza:.2f}), pero se esta comparando contra la pauta de "
                f"'{tipo_pauta}'. Esta hoja parece ser de la otra parte de la actividad: se puede "
                "corregir con POST /api/hoja/mover_parte antes de volver a comparar."
            ),
        }

    if confianza >= UMBRAL_DISCREPANCIA_AVISA:
        return {
            "aviso_tipo": (
                f"El cuadro {n} de {usuario}/{pagina_alumno} podria ser de tipo '{tipo_alumno}' "
                f"(confianza {confianza:.2f}) en vez de '{tipo_pauta}', pero la confianza no alcanza "
                "para bloquear la comparacion automaticamente. Conviene revisar si esta pagina esta "
                "en la parte que corresponde (ver POST /api/hoja/mover_parte)."
            )
        }

    return None


def comparar_cuadro(usuario, pagina, n, forzar=False):
    """Compara el cuadro `n` de `usuario`/`pagina` contra su pauta. Usa la
    cache en disco (salida/comparacion/resultados.json) si los archivos de
    trazo involucrados no cambiaron desde el ultimo calculo; `forzar=True`
    recalcula igual. Guarda el mapa de diferencia en salida/comparacion/ y
    devuelve la entrada (publica, sin los campos internos "_mtime_*").

    Antes de calcular o leer nada, hace la verificacion cruzada de tipo
    (`verificar_tipo_antes_de_comparar`): si hay una discrepancia de tipo
    con confianza alta, devuelve esa discrepancia en vez de un porcentaje
    (sin tocar la cache); si la confianza es baja, sigue de largo pero deja
    un "aviso_tipo" en el resultado (cacheado o recien calculado)."""
    if not COMPARADOR_DISPONIBLE:
        raise RuntimeError(f"El motor de comparacion no esta disponible: {COMPARADOR_ERROR}")

    manifest = leer_manifest()
    alumno = _buscar_alumno(manifest, usuario)
    if alumno is None:
        raise ValueError(f"No existe el alumno '{usuario}' en el manifest.")
    pag = _buscar_pagina_alumno(alumno, pagina)
    if pag is None:
        raise ValueError(f"El alumno '{usuario}' no tiene la pagina '{pagina}'.")
    celda = _buscar_celda(pag, n)
    if celda is None or not celda.get("trazo"):
        raise ValueError(f"No hay capa de trazo para {usuario}/{pagina}, cuadro {n}.")
    celda_pauta = _celda_pauta(manifest, pagina, n)
    if celda_pauta is None or not celda_pauta.get("trazo"):
        raise ValueError(f"No hay pauta (capa de trazo) para la pagina '{pagina}', cuadro {n}.")

    ruta_alumno = os.path.join(SALIDA_DIR, celda["trazo"])
    ruta_pauta = os.path.join(SALIDA_DIR, celda_pauta["trazo"])
    if not os.path.isfile(ruta_alumno):
        raise ValueError(f"No se encuentra el archivo de trazo del alumno: {celda['trazo']}")
    if not os.path.isfile(ruta_pauta):
        raise ValueError(f"No se encuentra el archivo de trazo de la pauta: {celda_pauta['trazo']}")

    aviso_verificacion = verificar_tipo_antes_de_comparar(usuario, pagina, pag, celda, pagina)
    if aviso_verificacion and aviso_verificacion.get("discrepancia_tipo"):
        # verificar_tipo_antes_de_comparar() no conoce "usuario"/"pagina"/"n"
        # como campos propios (los usa solo para armar el mensaje): se
        # agregan aca para que este resultado tenga la misma forma que el
        # de una comparacion normal. Sin esto, POST /api/comparacion/comparar
        # devolvia una discrepancia sin "n", y comparar_pagina()/el front
        # (visor/js/comparacion/app.js, que indexa por "resultado.n" al
        # comparar la pagina completa) la guardaba bajo la clave
        # `undefined` en vez de bajo el cuadro que realmente es: la fila de
        # ese cuadro en la tabla se quedaba mostrando "sin comparar" en vez
        # del aviso, aunque el aviso SI aparecia igual arriba (el banner de
        # pagina y el panel de nota escanean por valor, no por "n").
        return {"usuario": usuario, "pagina": pagina, "n": n, **aviso_verificacion}

    mtime_alumno = os.path.getmtime(ruta_alumno)
    mtime_pauta = os.path.getmtime(ruta_pauta)
    clave = _clave_cuadro_comparacion(usuario, pagina, n)

    with COMPARACION_LOCK:
        cache = _leer_cache_comparacion()
        anterior = cache["resultados"].get(clave)
        if (
            not forzar
            and anterior
            and anterior.get("_mtime_alumno") == mtime_alumno
            and anterior.get("_mtime_pauta") == mtime_pauta
            and anterior.get("umbral_alfa") == csim.UMBRAL_ALFA
            and os.path.isfile(os.path.join(SALIDA_DIR, anterior.get("mapa_diferencia", "")))
        ):
            resultado_final = _quitar_privados(anterior)
            if aviso_verificacion:
                resultado_final = dict(resultado_final)
                resultado_final.update(aviso_verificacion)
            return resultado_final

    resultado = csim.comparar_desde_paths(ruta_pauta, ruta_alumno)
    mapa = resultado.pop("mapa_diferencia")

    os.makedirs(COMPARACION_DIR, exist_ok=True)
    nombre_dif = f"{usuario}_{pagina}_c{n}_dif.png"
    ruta_dif_abs = os.path.join(COMPARACION_DIR, nombre_dif)
    csim.guardar_mapa_diferencia(ruta_dif_abs, mapa)

    entrada = {
        "usuario": usuario,
        "pagina": pagina,
        "n": n,
        "porcentaje": resultado["porcentaje"],
        "puntos_vistas": resultado.get("puntos_vistas"),
        "metricas": resultado["metricas"],
        "registro": resultado["registro"],
        "pesos_usados": resultado["pesos_usados"],
        "mapa_diferencia": ruta_relativa_salida(ruta_dif_abs),
        "umbral_alfa": csim.UMBRAL_ALFA,
        "calculado": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "_mtime_alumno": mtime_alumno,
        "_mtime_pauta": mtime_pauta,
    }
    with COMPARACION_LOCK:
        cache = _leer_cache_comparacion()
        cache["resultados"][clave] = entrada
        _escribir_cache_comparacion_atomico(cache)

    resultado_final = _quitar_privados(entrada)
    if aviso_verificacion:
        resultado_final = dict(resultado_final)
        resultado_final.update(aviso_verificacion)
    return resultado_final


def comparar_pagina(usuario, pagina, forzar=False):
    """POST /api/comparacion/comparar_pagina: compara de una pasada los 6
    cuadros de `pagina`. Un cuadro que falle (no tiene trazo, no tiene
    pauta, etc.) no aborta a los demas: queda con su propio "error" en el
    resultado."""
    resultados = []
    for n in range(1, 7):
        try:
            resultados.append(comparar_cuadro(usuario, pagina, n, forzar=forzar))
        except Exception as e:
            resultados.append({"usuario": usuario, "pagina": pagina, "n": n, "error": str(e)})
    return {"usuario": usuario, "pagina": pagina, "resultados": resultados}


def _porcentajes_cacheados(cache, usuario, pagina):
    valores = [None] * 6
    for n in range(1, 7):
        entrada = cache["resultados"].get(_clave_cuadro_comparacion(usuario, pagina, n))
        if entrada:
            if pagina == "vistas":
                # Si tiene puntos_vistas (calculo nuevo), lo usa. Si no, fallback al porcentaje.
                valores[n - 1] = entrada.get("puntos_vistas", entrada.get("porcentaje"))
            else:
                valores[n - 1] = entrada.get("porcentaje")
    return valores


def notas_resumen_alumno(usuario):
    """GET /api/comparacion/notas_alumno: arma el resumen de porcentajes,
    promedios y nota sugerida de `usuario` a partir de lo que ya este en la
    cache de comparaciones (no calcula nada nuevo: si un cuadro no se ha
    comparado, sale en blanco). Si el alumno ya tenia una fila registrada en
    el Excel de notas, tambien informa esa nota_final/observaciones previas
    para que el profesor las vea al reabrir la pagina."""
    if not COMPARADOR_DISPONIBLE:
        raise RuntimeError(f"El motor de comparacion no esta disponible: {COMPARADOR_ERROR}")
    with COMPARACION_LOCK:
        cache = _leer_cache_comparacion()
    vistas = _porcentajes_cacheados(cache, usuario, "vistas")
    isometricos = _porcentajes_cacheados(cache, usuario, "isometricos")
    fila = notas_xlsx.calcular_fila(usuario, vistas, isometricos, None, "")
    resumen = notas_xlsx.fila_a_dict(fila)
    resumen["nota_final_registrada"] = None
    resumen["observaciones_registradas"] = None
    try:
        existentes = notas_xlsx.leer_todas(NOTAS_XLSX_PATH)
        previa = next((f for f in existentes if f.get("usuario") == usuario), None)
        if previa:
            resumen["nota_final_registrada"] = previa.get("nota_final")
            resumen["observaciones_registradas"] = previa.get("observaciones")
    except Exception:
        pass  # sin fila previa (o Excel/CSV aun no existe): se ignora, no es un error.
    return resumen


def registrar_nota(payload):
    """POST /api/comparacion/registrar_nota: registra (o actualiza) la fila
    de un alumno en salida/Notas_Actividad4.xlsx, usando los porcentajes ya
    calculados (cache de comparaciones) y la nota_final/observaciones que
    decidio el profesor."""
    if not COMPARADOR_DISPONIBLE:
        raise RuntimeError(f"El motor de comparacion no esta disponible: {COMPARADOR_ERROR}")
    usuario = str(payload.get("usuario", "")).strip()
    if not usuario or not _RE_NOMBRE_SEGURO.match(usuario):
        raise ValueError("Usuario invalido o vacio.")

    nota_final = payload.get("nota_final")
    if nota_final is not None and nota_final != "":
        try:
            nota_final = float(nota_final)
        except (TypeError, ValueError):
            raise ValueError("nota_final debe ser un numero.")
        if not (0 <= nota_final <= 100):
            raise ValueError("nota_final debe estar entre 0 y 100.")
    else:
        nota_final = None
    observaciones = str(payload.get("observaciones", "") or "")

    with COMPARACION_LOCK:
        cache = _leer_cache_comparacion()
    vistas = _porcentajes_cacheados(cache, usuario, "vistas")
    isometricos = _porcentajes_cacheados(cache, usuario, "isometricos")

    return notas_xlsx.registrar(NOTAS_XLSX_PATH, usuario, vistas, isometricos, nota_final, observaciones)


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class ManejadorEscaner(SimpleHTTPRequestHandler):
    server_version = "EscanerA4/1.0"

    def log_message(self, formato, *args):
        # Mensaje mas corto que el default, y sin frenar en errores de log.
        try:
            sys.stderr.write(f"[servidor] {self.address_string()} - {formato % args}\n")
        except Exception:
            pass

    def _responder_json(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def translate_path(self, path):
        # Mapea rutas solicitadas como /pautas/... o /entregas/... a sus carpetas reales
        ruta_limpia = urllib.parse.urlsplit(path).path
        if ruta_limpia.startswith("/pautas/"):
            nombre = ruta_limpia[len("/pautas/"):].lstrip("/")
            candidata_escaneada = os.path.join(PAUTAS_DIR, nombre)
            if os.path.isfile(candidata_escaneada):
                return candidata_escaneada
            candidata_salida = os.path.join(SALIDA_PAUTAS_DIR, nombre)
            if os.path.isfile(candidata_salida):
                return candidata_salida
        elif ruta_limpia.startswith("/entregas/"):
            sub = ruta_limpia[len("/entregas/"):].lstrip("/")
            candidata = os.path.join(ENTREGAS_DIR, sub.replace("/", os.sep))
            if os.path.isfile(candidata):
                return candidata
        return super().translate_path(path)

    def do_GET(self):
        ruta = urllib.parse.urlsplit(self.path)
        camino = ruta.path.rstrip("/") or "/"

        if camino == "/api/imagenes":
            try:
                self._responder_json(200, listar_imagenes_servidor())
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        if camino == "/api/comparacion/listado":
            try:
                self._responder_json(200, listado_comparacion())
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        if camino == "/api/comparacion/notas_alumno":
            try:
                params = urllib.parse.parse_qs(ruta.query)
                usuario = (params.get("usuario") or [""])[0].strip()
                if not usuario:
                    raise ValueError("Falta el parametro 'usuario'.")
                self._responder_json(200, notas_resumen_alumno(usuario))
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        if camino == "/api/hoja/tipo":
            try:
                params = urllib.parse.parse_qs(ruta.query)
                usuario = (params.get("usuario") or [""])[0].strip()
                pagina = (params.get("pagina") or [""])[0].strip()
                if not usuario or not pagina:
                    raise ValueError("Faltan parametros: se requiere 'usuario' y 'pagina'.")
                self._responder_json(200, obtener_tipo_pagina(usuario, pagina))
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        super().do_GET()

    def do_POST(self):
        camino = self.path.rstrip("/") or "/"
        try:
            largo = int(self.headers.get("Content-Length", "0"))
            crudo = self.rfile.read(largo) if largo > 0 else b"{}"
            payload = json.loads(crudo.decode("utf-8")) if crudo.strip() else {}
        except Exception as e:
            self._responder_json(400, {"error": f"Cuerpo de la solicitud invalido: {e}"})
            return

        if camino == "/api/guardar":
            try:
                resultado = self._guardar(payload)
                self._responder_json(200, resultado)
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": f"Error inesperado en el servidor: {e}"})
            return

        if camino == "/api/comparacion/comparar":
            try:
                usuario = str(payload.get("usuario", "")).strip()
                pagina = str(payload.get("pagina", "")).strip()
                n = payload.get("n")
                forzar = bool(payload.get("forzar", False))
                if not usuario or not pagina or not isinstance(n, int):
                    raise ValueError("Faltan campos: se requiere 'usuario', 'pagina' y 'n' (entero).")
                self._responder_json(200, comparar_cuadro(usuario, pagina, n, forzar=forzar))
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        if camino == "/api/comparacion/comparar_pagina":
            try:
                usuario = str(payload.get("usuario", "")).strip()
                pagina = str(payload.get("pagina", "")).strip()
                forzar = bool(payload.get("forzar", False))
                if not usuario or not pagina:
                    raise ValueError("Faltan campos: se requiere 'usuario' y 'pagina'.")
                self._responder_json(200, comparar_pagina(usuario, pagina, forzar=forzar))
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        if camino == "/api/comparacion/registrar_nota":
            try:
                self._responder_json(200, registrar_nota(payload))
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": str(e)})
            return

        if camino == "/api/hoja/mover_parte":
            try:
                usuario = str(payload.get("usuario", "")).strip()
                pagina_origen = str(payload.get("pagina_origen", "")).strip()
                pagina_destino = str(payload.get("pagina_destino", "")).strip()
                if not usuario or not pagina_origen or not pagina_destino:
                    raise ValueError(
                        "Faltan campos: se requiere 'usuario', 'pagina_origen' y 'pagina_destino'."
                    )
                self._responder_json(200, mover_parte_hoja(usuario, pagina_origen, pagina_destino))
            except ValueError as e:
                self._responder_json(400, {"error": str(e)})
            except Exception as e:
                self._responder_json(500, {"error": f"Error inesperado en el servidor: {e}"})
            return

        self._responder_json(404, {"error": "Ruta no encontrada."})

    def _guardar(self, payload):
        usuario = str(payload.get("usuario", "")).strip()
        pagina = str(payload.get("pagina", "")).strip()
        celdas_in = payload.get("celdas")

        es_pauta = bool(payload.get("es_pauta", False)) or usuario in ("(pauta)", "pauta")
        if es_pauta:
            usuario = "pauta"

        if not usuario or not _RE_NOMBRE_SEGURO.match(usuario):
            raise ValueError("Usuario invalido o vacio (solo letras, numeros, '_', '-' y '.').")
        if not pagina or not _RE_NOMBRE_SEGURO.match(pagina):
            raise ValueError("Pagina invalida o vacia (solo letras, numeros, '_', '-' y '.').")
        if not isinstance(celdas_in, list) or not celdas_in:
            raise ValueError("Falta el arreglo 'celdas' (debe traer al menos 1 cuadro).")

        avisos = []
        celdas_manifest = []
        archivos_guardados = []

        vistos = set()
        for celda_in in celdas_in:
            n = celda_in.get("n")
            if not isinstance(n, int) or not (1 <= n <= 6):
                raise ValueError(f"Numero de cuadro invalido: {n!r} (debe ser un entero entre 1 y 6).")
            if n in vistos:
                raise ValueError(f"El cuadro {n} vino repetido en el mismo guardado.")
            vistos.add(n)
            if not celda_in.get("imagen_png_base64"):
                raise ValueError(f"Falta la imagen del cuadro {n}.")
            esquinas = celda_in.get("esquinas")
            if not isinstance(esquinas, list) or len(esquinas) != 4:
                raise ValueError(f"El cuadro {n} debe traer exactamente 4 esquinas.")

            if es_pauta:
                entrada, archivos = procesar_celda_pauta(pagina, celda_in, avisos)
            else:
                entrada, archivos = procesar_celda(usuario, pagina, celda_in, avisos)
            celdas_manifest.append(entrada)
            archivos_guardados.extend(archivos)

        hoja_rel = None
        if payload.get("hoja_png_base64"):
            hoja_bytes = base64.b64decode(payload["hoja_png_base64"])
            hoja_rgb = decodificar_png_rgb(hoja_bytes)
            if es_pauta:
                os.makedirs(SALIDA_PAUTAS_DIR, exist_ok=True)
                base = _tipo_base_pagina(pagina) or pagina
                ruta_hoja = os.path.join(SALIDA_PAUTAS_DIR, f"pauta_{base}.png")
                Image.fromarray(hoja_rgb, mode="RGB").save(ruta_hoja)
                hoja_rel = f"pautas/pauta_{base}.png"
            else:
                os.makedirs(RECTIFICADAS_DIR, exist_ok=True)
                ruta_hoja = os.path.join(RECTIFICADAS_DIR, f"{usuario}_{pagina}.png")
                Image.fromarray(hoja_rgb, mode="RGB").save(ruta_hoja)
                hoja_rel = ruta_relativa_salida(ruta_hoja)
            archivos_guardados.append(hoja_rel)

        if es_pauta:
            actualizar_manifest_pauta(pagina, celdas_manifest, hoja_rel)
            return {"ok": True, "es_pauta": True, "archivos": archivos_guardados, "avisos": avisos}

        actualizar_manifest_con_celdas(usuario, pagina, celdas_manifest, hoja_rel)

        return {"ok": True, "archivos": archivos_guardados, "avisos": avisos}


def main():
    for d in (SALIDA_DIR, CELDAS_DIR, RECTIFICADAS_DIR, COMPARACION_DIR):
        os.makedirs(d, exist_ok=True)

    puerto = 8000
    if len(sys.argv) > 1:
        try:
            puerto = int(sys.argv[1])
        except ValueError:
            print(f"Puerto invalido: {sys.argv[1]!r}, se usa 8000.")

    if not NUCLEO_DISPONIBLE:
        print("AVISO: no se pudo importar rectificador/nucleo.py "
              f"({NUCLEO_ERROR}). El escaner manual seguira funcionando, "
              "pero el guardado no generara la capa de trazo ni las "
              "metricas de tinta (solo la imagen en escala de grises).")

    if not COMPARADOR_DISPONIBLE:
        print("AVISO: no se pudo importar comparador/similitud.py "
              f"({COMPARADOR_ERROR}). La pagina de comparacion "
              "(visor/comparacion.html) no va a poder comparar cuadros ni "
              "registrar notas.")
    elif not getattr(notas_xlsx, "_OPENPYXL", True):
        print("AVISO: openpyxl no esta instalado: el registro de notas caera "
              "a un CSV equivalente (salida/Notas_Actividad4.csv) en vez de "
              "un .xlsx.")

    Manejador = partial(ManejadorEscaner, directory=RAIZ)
    httpd = ThreadingHTTPServer(("0.0.0.0", puerto), Manejador)
    print(f"Sirviendo {RAIZ} en http://localhost:{puerto}/")
    print(f"Visor:       http://localhost:{puerto}/visor/index.html")
    print(f"Escaner:     http://localhost:{puerto}/visor/escaner.html")
    print(f"Comparacion: http://localhost:{puerto}/visor/comparacion.html")
    print("Presione Ctrl+C para detener.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")


if __name__ == "__main__":
    main()
