# -*- coding: utf-8 -*-
"""
Corrige los alumnos que 03_normalizar.py no pudo resolver, trabajando
directamente sobre las imagenes crudas (paginas de PDF, screenshots, fotos).

Usa el detector de contenido mejorado de nucleo_correccion, que descarta barras
de estado, texto y el panel derecho del applet.

Uso:  python 06_pendientes.py [usuario1 usuario2 ...]
      python 06_pendientes.py --todos
Guarda el avance en salida/pendientes_estado.json y se puede reanudar.
"""

import glob
import json
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto
import nucleo_correccion as nc

B = contexto.raiz()
ESTADO = os.path.join(B, "salida", "pendientes_estado.json")
EXT = (".png", ".jpg", ".jpeg", ".bmp", ".webp")

# Umbral para aceptar una asignacion de lamina.
# Se usa SOLO la confianza de lectura de color. El IoU de trazo (alineacion) se
# degrada con fuentes de baja resolucion y ahi da cero aunque la lectura sea
# correcta, asi que sirve como desempate pero no como filtro.
MIN_CONFIANZA = 0.58
MIN_COBERTURA = 0.55
CONFIANZA_SEGURA = 0.85
# Una cobertura baja por si sola no descalifica: tambien baja cuando el alumno
# dejo caras sin pintar. Lo que descarta una imagen ajena es la combinacion de
# cobertura, confianza y puntaje minimo.
# Piso de puntaje para aceptar una asignacion automatica. Por debajo de esto la
# imagen casi nunca es esa lamina; y si de verdad lo fuera, es un caso que el
# profesor tiene que mirar igual, asi que mandarlo a revision manual es lo seguro.
MIN_PUNTAJE = 25.0


def candidatos(usuario):
    """Imagenes que vale la pena probar, de mas prometedoras a menos."""
    carpeta = os.path.join(B, "salida", "entregas", usuario)
    rutas = []
    for f in sorted(glob.glob(os.path.join(carpeta, "crudo", "*"))):
        if f.lower().endswith(EXT):
            rutas.append(f)
    for f in sorted(glob.glob(os.path.join(carpeta, "*"))):
        if f.lower().endswith(EXT):
            rutas.append(f)

    utiles = []
    for f in rutas:
        try:
            im = Image.open(f)
            w, h = im.size
            if min(w, h) < 250:
                continue
            # prefiltro barato: tiene que haber color fuerte suficiente
            chica = np.asarray(im.convert("RGB").resize(
                (160, max(1, int(160 * h / w))), nc.BILINEAL))
            frac = nc._mascara_saturada(chica).mean()
            if frac < 0.03:
                continue
            utiles.append((f, frac))
        except Exception:
            continue
    return [f for f, _ in utiles]


def procesar(usuario, pautas):
    """Evalua cada candidata contra las 5 laminas y hace una asignacion global.

    Un emparejamiento codicioso por lamina pierde laminas cuando dos imagenes
    compiten por la misma: la perdedora se descarta aunque fuera la unica
    candidata de otra lamina. Aqui se arma la matriz completa candidata x lamina
    y se asignan los mejores pares de a uno, retirando ambos del juego."""
    print("\n=== %s ===" % usuario)
    rutas = candidatos(usuario)
    print("  %d candidatas tras el prefiltro" % len(rutas))

    # Pre-pasada barata: una sola evaluacion automatica por candidata, para
    # descartar portadas, logos y paginas de texto antes de armar la matriz.
    if len(rutas) > 12:
        preseleccion = []
        for f in rutas:
            try:
                r = nc.corregir(Image.open(f), pautas)
            except Exception:
                continue
            if r["cobertura_color"] >= 0.50 and r["puntaje"] >= MIN_PUNTAJE * 0.6:
                preseleccion.append(f)
        print("  pre-pasada: %d de %d pasan a la matriz completa"
              % (len(preseleccion), len(rutas)))
        rutas = preseleccion

    matriz = {}
    evaluadas = []
    for f in rutas:
        nombre = os.path.basename(f)
        fila = {}
        for lam in sorted(pautas):
            try:
                r = nc.corregir(Image.open(f), pautas, lam)
            except Exception as e:
                print("  %-44s L%d ERROR %s" % (nombre[:44], lam, e))
                continue
            fila[lam] = {
                "archivo": os.path.relpath(f, B),
                "lamina": lam,
                "caras_correctas": r["caras_correctas"],
                "caras_total": r["caras_total"],
                "puntaje": r["puntaje"],
                "alineacion": r["score_alineacion"],
                "confianza": r["confianza"],
                "cobertura": r["cobertura_color"],
                "recorte": r.get("recorte", ""),
                "calidad": r["calidad"],
            }
        if not fila:
            continue
        matriz[nombre] = fila
        mejor = max(fila.values(), key=lambda e: e["calidad"])
        evaluadas.append(mejor)
        print("  %-44s mejor L%d %2d/%-2d cob %.2f conf %.2f cal %.3f (%s)" % (
            nombre[:44], mejor["lamina"], mejor["caras_correctas"],
            mejor["caras_total"], mejor["cobertura"], mejor["confianza"],
            mejor["calidad"], mejor["recorte"]))

    # Asignacion global: mejor par disponible, uno a la vez
    pares = []
    for nombre, fila in matriz.items():
        for lam, e in fila.items():
            if (e["confianza"] < MIN_CONFIANZA or e["cobertura"] < MIN_COBERTURA
                    or e["puntaje"] < MIN_PUNTAJE):
                continue
            pares.append((e["calidad"], nombre, lam, e))
    pares.sort(key=lambda t: -t[0])

    usados = set()
    mejores = {}
    for cal, nombre, lam, e in pares:
        if nombre in usados or lam in mejores:
            continue
        usados.add(nombre)
        mejores[lam] = e

    for lam, e in mejores.items():
        e["seguro"] = e["confianza"] >= CONFIANZA_SEGURA
    faltan = [l for l in range(1, 6) if l not in mejores]
    dudosas = sorted(l for l, e in mejores.items() if not e["seguro"])
    for lam in sorted(mejores):
        e = mejores[lam]
        print("     L%d <- %-40s %2d/%-2d  conf %.2f" % (
            lam, os.path.basename(e["archivo"])[:40], e["caras_correctas"],
            e["caras_total"], e["confianza"]))
    if dudosas:
        print("  ojo: laminas con confianza media, conviene verificar: %s" % dudosas)
    print("  --> laminas resueltas: %s   faltan: %s" % (sorted(mejores), faltan))
    return {"usuario": usuario, "evaluadas": evaluadas,
            "asignadas": {str(k): v for k, v in sorted(mejores.items())},
            "faltan": faltan}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    todos = "--todos" in sys.argv

    estado = {}
    if os.path.exists(ESTADO):
        with open(ESTADO, "r", encoding="utf-8") as f:
            estado = json.load(f)

    if todos or not args:
        carpeta = os.path.join(B, "salida", "entregas")
        args = sorted(d for d in os.listdir(carpeta)
                      if os.path.isdir(os.path.join(carpeta, d)))

    pautas = nc.cargar_pautas()
    t0 = time.time()
    for u in args:
        if u in estado and "--rehacer" not in sys.argv:
            print("(ya procesado, omito) %s" % u)
            continue
        estado[u] = procesar(u, pautas)
        with open(ESTADO, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=1)
    print("\nTiempo total %.0fs. Estado en %s" % (time.time() - t0, ESTADO))


if __name__ == "__main__":
    main()
