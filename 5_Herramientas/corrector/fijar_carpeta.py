# -*- coding: utf-8 -*-
"""
Fija sobre que carpeta trabajan los scripts, para no repetir --carpeta.

    python fijar_carpeta.py "..\\4_Correcciones\\Seccion 4\\Actividad 1"
    python fijar_carpeta.py            (muestra la que esta fijada ahora)
"""
import os, sys
D = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(D, "carpeta_actual.txt")
if len(sys.argv) > 1:
    ruta = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if not os.path.isdir(ruta):
        print("No existe esa carpeta:\n  %s" % ruta); raise SystemExit(1)
    with open(F, "w", encoding="utf-8") as f:
        f.write(ruta)
    print("Carpeta de trabajo fijada en:\n  %s" % ruta)
else:
    if os.path.exists(F):
        print("Carpeta de trabajo actual:\n  %s" % open(F, encoding="utf-8").read().strip())
    else:
        print("No hay carpeta fijada. Usa:\n  python fijar_carpeta.py \"<ruta>\"")
