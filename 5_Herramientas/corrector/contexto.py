# -*- coding: utf-8 -*-
"""
Contexto de trabajo del corrector.

Esta es una UNICA copia de los scripts, compartida por todas las secciones y
actividades. Lo que cambia entre una y otra (la nomina, el zip de Moodle, la
carpeta de salida) no esta escrito en el codigo: se indica al correr.

    python 01_extraer.py --carpeta "..\\4_Correcciones\\Seccion 4\\Actividad 1"

Si no se indica --carpeta, se usa la que este en el archivo `carpeta_actual.txt`
de esta misma carpeta, y si tampoco existe, la de la variable de entorno
PCI1119_CARPETA. Asi se puede fijar una vez y no repetirla en cada comando.

Estructura que se espera de la carpeta de trabajo:

    <Seccion N>/
        Nomina_*.xlsx                  <- nomina oficial de la seccion
        <Actividad X>/                 <- la carpeta de trabajo
            gradebook_*.zip            <- descarga de Moodle
            salida/                    <- lo que generan los scripts

La pauta procesada es comun a todas las secciones y vive en
5_Herramientas/pauta_actividad1/procesada.
"""

import argparse
import glob
import os
import re
import sys

CORRECTOR = os.path.dirname(os.path.abspath(__file__))
HERRAMIENTAS = os.path.dirname(CORRECTOR)
FIJADA = os.path.join(CORRECTOR, "carpeta_actual.txt")

# Pauta compartida: no se duplica por seccion
CARPETA_PAUTA = os.path.join(HERRAMIENTAS, "pauta_actividad1", "procesada")
PAUTA_IMAGENES = os.path.join(HERRAMIENTAS, "pauta_actividad1")


class FaltaArchivo(Exception):
    pass


def _leer_fijada():
    if os.path.exists(FIJADA):
        with open(FIJADA, "r", encoding="utf-8") as f:
            v = f.read().strip()
            if v:
                return v
    return None


def _resolver_raiz():
    """Carpeta de trabajo: --carpeta, carpeta_actual.txt, o PCI1119_CARPETA."""
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--carpeta")
    conocidos, _ = ap.parse_known_args(sys.argv[1:])
    ruta = conocidos.carpeta or _leer_fijada() or os.environ.get("PCI1119_CARPETA")
    if not ruta:
        raise FaltaArchivo(
            "No se indico sobre que carpeta trabajar.\n\n"
            "Usa una de estas tres formas:\n"
            "  1) python <script>.py --carpeta \"<ruta de la actividad>\"\n"
            "  2) python fijar_carpeta.py \"<ruta de la actividad>\"   (queda fija)\n"
            "  3) definir la variable de entorno PCI1119_CARPETA\n\n"
            "Ejemplo de ruta:\n"
            "  ..\\4_Correcciones\\Seccion 4\\Actividad 1")
    ruta = os.path.abspath(os.path.expanduser(ruta))
    if not os.path.isdir(ruta):
        raise FaltaArchivo("La carpeta indicada no existe:\n  %s" % ruta)
    return ruta


RAIZ = None
SECCION_DIR = None


def _asegurar():
    global RAIZ, SECCION_DIR
    if RAIZ is None:
        RAIZ = _resolver_raiz()
        SECCION_DIR = os.path.dirname(RAIZ)
    return RAIZ


def raiz():
    return _asegurar()


def seccion_dir():
    _asegurar()
    return SECCION_DIR


def _uno(patron, donde, que):
    encontrados = sorted(glob.glob(os.path.join(donde, patron)))
    if not encontrados:
        raise FaltaArchivo(
            "No encontre %s en:\n  %s\n(buscaba el patron %s)" % (que, donde, patron))
    if len(encontrados) > 1:
        print("Aviso: hay %d archivos que calzan con %s. Uso el primero:\n  %s"
              % (len(encontrados), patron, os.path.basename(encontrados[0])))
    return encontrados[0]


def ruta_nomina():
    _asegurar()
    return _uno("Nomina_*.xlsx", SECCION_DIR, "la nomina de la seccion")


def ruta_zip():
    return _uno("gradebook_*.zip", _asegurar(), "el zip de Moodle")


def codigo_seccion():
    try:
        nombre = os.path.basename(ruta_nomina())
    except FaltaArchivo:
        nombre = ""
    m = re.search(r"(PCI\s?\d{4})[-_ ]?(\d+)", nombre, re.IGNORECASE)
    if m:
        return "%s-%s" % (m.group(1).upper().replace(" ", ""), m.group(2))
    m = re.search(r"(\d+)", os.path.basename(seccion_dir()))
    return "PCI1119-%s" % m.group(1) if m else "PCI1119"


def numero_seccion():
    m = re.search(r"-(\d+)$", codigo_seccion())
    return m.group(1) if m else "?"


def semestre():
    try:
        nombre = os.path.basename(ruta_nomina())
    except FaltaArchivo:
        return ""
    m = re.search(r"Semestre[_ ]?(\d)[-_](\d{4})", nombre, re.IGNORECASE)
    return "Semestre %s - %s" % (m.group(1), m.group(2)) if m else ""


def actividad():
    """Numero de actividad, leido del nombre de la carpeta de trabajo."""
    m = re.search(r"(\d+)", os.path.basename(_asegurar()))
    return m.group(1) if m else "1"


def encabezado():
    partes = ["%s Sistemas de Representacion" % codigo_seccion(),
              "Seccion %s" % numero_seccion()]
    s = semestre()
    if s:
        partes.append(s)
    return "  |  ".join(partes)


def nombre_salida(plantilla):
    return plantilla % codigo_seccion()


def hoja_nomina(wb):
    for nombre in ("Nómina", "Nomina", "NÓMINA", "NOMINA"):
        if nombre in wb.sheetnames:
            return wb[nombre]
    return wb[wb.sheetnames[0]]


if __name__ == "__main__":
    try:
        print("Carpeta de trabajo   :", raiz())
        print("Carpeta de la seccion:", seccion_dir())
        print("Codigo               :", codigo_seccion())
        print("Actividad            :", actividad())
        print("Encabezado           :", encabezado())
        print("Pauta procesada      :", CARPETA_PAUTA,
              "(%d archivos)" % len(os.listdir(CARPETA_PAUTA))
              if os.path.isdir(CARPETA_PAUTA) else "(FALTA)")
        for etiqueta, fn in (("Nomina", ruta_nomina), ("Zip de Moodle", ruta_zip)):
            try:
                print("%-21s: %s" % (etiqueta, os.path.basename(fn())))
            except FaltaArchivo as e:
                print("%-21s: FALTA\n   %s" % (etiqueta, e))
    except FaltaArchivo as e:
        print(e)
        raise SystemExit(1)
