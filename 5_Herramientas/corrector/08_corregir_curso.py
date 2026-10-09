# -*- coding: utf-8 -*-
"""
Corrige en lote las entregas ya extraidas, alumno por alumno.

Reusa el mismo motor que corregir_entrega.py, pero recorre la carpeta de
entregas completa y guarda el avance en salida/curso_estado.json, asi que se
puede cortar y retomar sin perder lo hecho.

Uso:
    python 08_corregir_curso.py                 todos los que falten
    python 08_corregir_curso.py --tipo pdf      solo los que entregaron PDF
    python 08_corregir_curso.py --tipo docx     solo los Word
    python 08_corregir_curso.py --max 5         procesa como mucho 5 y para
    python 08_corregir_curso.py --rehacer u1 u2 fuerza a estos usuarios
    python 08_corregir_curso.py --tabla         solo imprime lo ya hecho
"""

import argparse
import csv
import json
import os
import shutil
import sys
import tempfile
import time

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto
import nucleo_correccion as nc
import corregir_entrega as ce

ESTADO = os.path.join(contexto.raiz(), "salida", "curso_estado.json")
SALIDA_CSV = os.path.join(contexto.raiz(), "salida", "curso_resultados.csv")


def cargar_estado():
    if os.path.exists(ESTADO):
        with open(ESTADO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_estado(e):
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(e, f, ensure_ascii=False, indent=1)


def inventario():
    p = os.path.join(contexto.raiz(), "salida", "inventario.csv")
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        return {r["usuario"]: r for r in csv.DictReader(f)}


def procesar(usuario, carpeta, pautas, universo):
    temporal = tempfile.mkdtemp(prefix="curso_")
    try:
        rutas = ce.prefiltrar(ce.reunir_candidatas(carpeta, temporal))
        if not rutas:
            return {"usuario": usuario, "error": "sin imagenes utilizables",
                    "laminas": {}, "caras": 0, "puntaje": 0.0, "n_candidatas": 0}
        elegidas, _ = ce.asignar(rutas, pautas, verboso=False)
        caras = sum(e["caras_correctas"] for e in elegidas.values())
        errores = []
        for lam in sorted(elegidas):
            for d in elegidas[lam]["errores"]:
                errores.append("L%d %s(%s->%s)" % (lam, d["id"], d["esperado"], d["detectado"]))
        return {
            "usuario": usuario,
            "n_candidatas": len(rutas),
            "laminas": {str(l): {"ok": e["caras_correctas"], "tot": e["caras_total"],
                                 "conf": e["confianza"], "archivo": os.path.basename(e["archivo"])}
                        for l, e in sorted(elegidas.items())},
            "faltan": [l for l in sorted(pautas) if l not in elegidas],
            "caras": caras,
            "universo": universo,
            "puntaje": round(100.0 * caras / universo, 1) if universo else 0.0,
            "conf_min": round(min([e["confianza"] for e in elegidas.values()] or [0]), 2),
            "errores": errores,
        }
    finally:
        shutil.rmtree(temporal, ignore_errors=True)


def tabla(estado, inv):
    print("\n%-24s %-26s %4s %-7s %-5s %s" % (
        "usuario", "L1  L2  L3  L4  L5", "car", "nota", "conf", "aviso"))
    print("-" * 104)
    for u in sorted(estado):
        r = estado[u]
        if r.get("error"):
            print("%-24s %-26s %4s %-7s %-5s %s" % (u, "-", 0, "0.0", "-", r["error"]))
            continue
        cel = []
        for l in range(1, 6):
            d = r["laminas"].get(str(l))
            cel.append("%-3s" % (d["ok"] if d else "-"))
        aviso = ""
        if r.get("faltan"):
            aviso = "faltan laminas %s" % r["faltan"]
        elif r.get("conf_min", 1) < 0.85:
            aviso = "confianza %.0f%%" % (100 * r["conf_min"])
        obs = (inv.get(u, {}) or {}).get("observacion", "")
        if "intentos" in obs:
            aviso = (aviso + " | " if aviso else "") + "VARIOS INTENTOS"
        print("%-24s %-26s %4s %-7s %-5s %s" % (
            u, " ".join(cel), r["caras"], r["puntaje"], r.get("conf_min", ""), aviso))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", help="filtrar por tipo_entrega del inventario")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--rehacer", nargs="*", default=[])
    ap.add_argument("--carpeta",
                    help="carpeta de la actividad; ver contexto.py")
    ap.add_argument("--tabla", action="store_true")
    args = ap.parse_args()

    pautas = nc.cargar_pautas()
    universo = sum(len(p.caras) for p in pautas.values())
    inv = inventario()
    estado = cargar_estado()

    if args.tabla:
        tabla(estado, inv)
        return

    base = os.path.join(contexto.raiz(), "salida", "entregas")
    usuarios = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    if args.tipo:
        usuarios = [u for u in usuarios
                    if (inv.get(u, {}) or {}).get("tipo_entrega") == args.tipo]
    pendientes = [u for u in usuarios if u not in estado or u in args.rehacer]
    if args.max:
        pendientes = pendientes[:args.max]

    print("Por procesar: %d de %d" % (len(pendientes), len(usuarios)))
    for u in pendientes:
        t = time.time()
        r = procesar(u, os.path.join(base, u), pautas, universo)
        estado[u] = r
        guardar_estado(estado)
        if r.get("error"):
            print("  %-24s %s  (%.0fs)" % (u, r["error"], time.time() - t))
        else:
            print("  %-24s %3d/%d caras  %5.1f  conf %.2f  faltan %s  (%.0fs)" % (
                u, r["caras"], r["universo"], r["puntaje"], r["conf_min"],
                r["faltan"] or "-", time.time() - t))

    with open(SALIDA_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["usuario", "nombre", "tipo_entrega", "L1", "L2", "L3", "L4", "L5",
                    "caras_correctas", "caras_totales", "puntaje_0_100",
                    "laminas_faltantes", "confianza_minima", "errores", "observacion"])
        for u in sorted(estado):
            r = estado[u]
            fila_inv = inv.get(u, {}) or {}
            if r.get("error"):
                w.writerow([u, fila_inv.get("nombre_completo", ""),
                            fila_inv.get("tipo_entrega", ""), "", "", "", "", "",
                            0, universo, 0.0, "1;2;3;4;5", 0, r["error"],
                            fila_inv.get("observacion", "")])
                continue
            w.writerow([u, fila_inv.get("nombre_completo", ""),
                        fila_inv.get("tipo_entrega", "")]
                       + [(r["laminas"].get(str(l)) or {}).get("ok", "") for l in range(1, 6)]
                       + [r["caras"], r["universo"], r["puntaje"],
                          ";".join(str(x) for x in r.get("faltan", [])),
                          r.get("conf_min", ""), " | ".join(r.get("errores", [])),
                          fila_inv.get("observacion", "")])
    print("\nCSV: %s" % SALIDA_CSV)


if __name__ == "__main__":
    main()
