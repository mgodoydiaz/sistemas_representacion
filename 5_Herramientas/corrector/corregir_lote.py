# -*- coding: utf-8 -*-
"""
Corrige en lote todas las laminas ya normalizadas por 03_normalizar.py.
Complemento del corrector por portapapeles: sirve para adelantar trabajo con
los alumnos cuya entrega se pudo recortar automaticamente.

Uso:  python corregir_lote.py
Salida: salida/lote_resultados.csv (una fila por lamina)
        salida/lote_resumen.csv    (una fila por alumno, con el puntaje 0-100)
        salida/reportes/<alumno>_L<N>.png  (pauta | entrega marcada)
"""

import csv
import glob
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto
import nucleo_correccion as nc

B = contexto.raiz()
CARAS_POR_LAMINA = {}


def main():
    pautas = nc.cargar_pautas()
    if not pautas:
        print("No hay pautas. Corre primero 02_pauta.py")
        return
    for n, p in pautas.items():
        CARAS_POR_LAMINA[n] = len(p.caras)
    universo = sum(CARAS_POR_LAMINA.values())
    print("Caras por lamina: %s   total %d" % (CARAS_POR_LAMINA, universo))

    carpeta = os.path.join(B, "salida", "entregas")
    usuarios = sorted(d for d in os.listdir(carpeta)
                      if os.path.isdir(os.path.join(carpeta, d)))

    filas = []
    resumen = []
    for u in usuarios:
        archivos = sorted(glob.glob(os.path.join(carpeta, u, "norm", "*.png")))
        correctas = 0
        laminas = []
        avisos = []
        for f in archivos:
            try:
                r = nc.corregir(Image.open(f), pautas)
            except Exception as e:
                avisos.append("%s fallo: %s" % (os.path.basename(f), e))
                continue
            laminas.append(r["lamina"])
            correctas += r["caras_correctas"]
            for d in r["detalle"]:
                filas.append([u, r["lamina"], d["pieza"], d["id"], d["esperado"],
                              d["detectado"], int(d["correcto"]), d["apoyo"]])
            if r["confianza"] < 0.85:
                avisos.append("L%d confianza %.0f%%" % (r["lamina"], 100 * r["confianza"]))
            vista = nc.render(r, pautas[r["lamina"]])
            vista.save(os.path.join(B, "salida", "reportes",
                                    "%s_L%d.png" % (u, r["lamina"])))
        puntaje = 100.0 * correctas / universo if universo else 0.0
        resumen.append([u, ";".join(str(x) for x in sorted(set(laminas))),
                        len(set(laminas)), correctas, universo,
                        round(puntaje, 1),
                        "SI" if (avisos or len(set(laminas)) < 5) else "no",
                        " | ".join(avisos)])
        print("%-24s laminas %-12s %3d/%3d caras  %5.1f pts %s" % (
            u, sorted(set(laminas)), correctas, universo, puntaje,
            "<- revisar" if (avisos or len(set(laminas)) < 5) else ""))

    with open(os.path.join(B, "salida", "lote_resultados.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["usuario", "lamina", "pieza", "cara_id", "color_esperado",
                    "color_detectado", "correcto", "certeza"])
        w.writerows(filas)

    with open(os.path.join(B, "salida", "lote_resumen.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["usuario", "laminas", "n_laminas", "caras_correctas",
                    "caras_totales", "puntaje_0_100", "revisar", "observacion"])
        w.writerows(resumen)

    print("\nEscrito: salida/lote_resultados.csv y salida/lote_resumen.csv")
    print("Reportes visuales en: salida/reportes/")


if __name__ == "__main__":
    main()
