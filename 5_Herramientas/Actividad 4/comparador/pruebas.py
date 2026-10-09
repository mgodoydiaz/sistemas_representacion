#!/usr/bin/env python3
"""
pruebas.py - Casos de prueba construidos a mano para comparador/similitud.py.

No son "tests" en el sentido de un framework: son los 4 casos que pide la
validacion del motor, con asserts sueltos y un print de los numeros reales
que arroja cada caso (para poder leerlos y juzgar si el comportamiento tiene
sentido, no solo si "paso" o "fallo"):

  1. La pauta contra si misma            -> debe dar un porcentaje muy alto.
  2. La pauta desplazada 20 px           -> debe seguir alto gracias al registro.
  3. La pauta con un segmento borrado    -> debe bajar de forma proporcional.
  4. Dos figuras claramente distintas    -> debe dar bajo.

Usa las pautas reales de salida/pautas si existen; si no, genera un par de
figuras sinteticas (rectangulo+diagonal / circulo) para poder probar el
motor igual, tal como pide el enunciado.

Ejecutar con:  python3 comparador/pruebas.py
"""
import os
import sys
import time

import numpy as np

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_AQUI)
sys.path.insert(0, _AQUI)
import similitud as sim  # noqa: E402

PAUTAS_DIR = os.path.join(_RAIZ, "salida", "pautas")


def _figura_sintetica_a():
    """Rectangulo + diagonal, 1000x1000: figura de respaldo si no hay pautas reales."""
    m = np.zeros((1000, 1000), dtype=bool)
    m[200:212, 200:800] = True
    m[788:800, 200:800] = True
    m[200:800, 200:212] = True
    m[200:800, 788:800] = True
    for i in range(590):
        m[205 + i, 205 + i] = True
        m[205 + i, 206 + i] = True
        m[206 + i, 205 + i] = True
    return m


def _figura_sintetica_b():
    """Circulo: figura bien distinta de la A, para el caso 4."""
    m = np.zeros((1000, 1000), dtype=bool)
    yy, xx = np.mgrid[0:1000, 0:1000]
    r = np.sqrt((xx - 500) ** 2 + (yy - 500) ** 2)
    m[(r > 250) & (r < 263)] = True
    return m


def _cargar_o_sintetica(nombre_archivo, generador):
    ruta = os.path.join(PAUTAS_DIR, nombre_archivo)
    if os.path.isfile(ruta):
        print(f"  usando pauta real: {ruta}")
        return sim.cargar_mascara_trazo(ruta)
    print(f"  no se encontro {ruta}; se usa una figura sintetica de prueba")
    return generador()


def borrar_segmento(m, frac=0.35):
    """Borra una franja horizontal central (simula que al alumno le falto dibujar
    una parte)."""
    m2 = m.copy()
    h = m.shape[0]
    y0 = int(h * (0.5 - frac / 2))
    y1 = int(h * (0.5 + frac / 2))
    m2[y0:y1, :] = False
    return m2


def _reportar(nombre, r, t0):
    m = r["metricas"]
    reg = r["registro"]
    print(f"  porcentaje = {r['porcentaje']}")
    print(
        f"  iou_tolerante={m['iou_tolerante']}  f_score={m['f_score']} "
        f"(precision={m['precision']}, cobertura={m['cobertura']})"
    )
    print(
        f"  chamfer_promedio_px={m['chamfer_promedio_px']}  "
        f"({m['chamfer_promedio_casillas']} casillas)  "
        f"pixeles_alumno={m['pixeles_alumno']} pixeles_pauta={m['pixeles_pauta']}"
    )
    print(
        f"  registro: dx={reg['dx']} dy={reg['dy']} escala={reg['escala']} "
        f"rotacion={reg['rotacion_grados']}  dice_interno={reg['puntaje_dice_registro']}"
    )
    print(f"  tiempo: {time.time() - t0:.2f} s")


def correr():
    resultados = {}

    print("=== Prueba 1: pauta contra si misma ===")
    pauta = _cargar_o_sintetica("pauta_vistas_c1_trazo.png", _figura_sintetica_a)
    t0 = time.time()
    r1 = sim.comparar_mascaras(pauta, pauta.copy())
    _reportar("misma", r1, t0)
    assert r1["porcentaje"] >= 97, f"Se esperaba un porcentaje muy alto (>=97), dio {r1['porcentaje']}"
    resultados["misma"] = r1["porcentaje"]

    print("\n=== Prueba 2: pauta desplazada 20 px (dx=20, dy=20) ===")
    alumno_desplazado = sim._desplazar(pauta, 20, 20)
    t0 = time.time()
    r2 = sim.comparar_mascaras(pauta, alumno_desplazado)
    _reportar("desplazada", r2, t0)
    assert r2["porcentaje"] >= 90, f"El registro deberia recuperar casi todo el porcentaje (>=90), dio {r2['porcentaje']}"
    reg2 = r2["registro"]
    assert abs(reg2["dx"] - (-20)) <= 3 and abs(reg2["dy"] - (-20)) <= 3, (
        f"El registro deberia detectar un desplazamiento cercano a (-20,-20) "
        f"para compensar el corrimiento aplicado, dio dx={reg2['dx']} dy={reg2['dy']}"
    )
    resultados["desplazada"] = r2["porcentaje"]

    print("\n=== Prueba 3: pauta con un segmento borrado (35% del alto) ===")
    alumno_incompleto = borrar_segmento(pauta, 0.35)
    t0 = time.time()
    r3 = sim.comparar_mascaras(pauta, alumno_incompleto)
    _reportar("incompleta", r3, t0)
    assert r3["porcentaje"] < r1["porcentaje"] - 15, (
        f"El porcentaje deberia bajar claramente al faltar trazo "
        f"(prueba1={r1['porcentaje']}, prueba3={r3['porcentaje']})"
    )
    resultados["incompleta"] = r3["porcentaje"]

    print("\n=== Prueba 4: dos figuras distintas ===")
    otra = _cargar_o_sintetica("pauta_isometricos_c1_trazo.png", _figura_sintetica_b)
    if otra.shape != pauta.shape:
        alto, ancho = pauta.shape
        otra = otra[:alto, :ancho]
    t0 = time.time()
    r4 = sim.comparar_mascaras(pauta, otra)
    _reportar("distinta", r4, t0)
    assert r4["porcentaje"] < r3["porcentaje"], (
        f"Dos figuras distintas deberian dar menos que un trazo incompleto de la "
        f"misma figura (prueba3={r3['porcentaje']}, prueba4={r4['porcentaje']})"
    )
    resultados["distinta"] = r4["porcentaje"]

    print("\n=== Prueba extra: transformada de distancia manual (sin cv2) ===")
    m = np.zeros((50, 50), dtype=bool)
    m[25, 25] = True
    dt_manual = sim._edt_manual(m)
    dt_cv2 = sim._distancia_transformada(m) if sim._CV2 else None
    err_max = None
    if dt_cv2 is not None:
        err_max = float(np.abs(dt_manual - dt_cv2).max())
        print(f"  error maximo entre transformada manual y cv2: {err_max:.4f} px")
        assert err_max < 0.5, f"La transformada de distancia manual no coincide con cv2 (error max {err_max})"
    print(f"  dt_manual[0,0] (esquina, deberia ser ~{np.hypot(25,25):.2f}) = {dt_manual[0,0]:.3f}")
    assert abs(dt_manual[0, 0] - np.hypot(25, 25)) < 0.5

    print("\nResumen final:")
    for k, v in resultados.items():
        print(f"  {k:12s} -> {v}%")
    print("\nTodas las pruebas pasaron.")
    return resultados


if __name__ == "__main__":
    correr()
