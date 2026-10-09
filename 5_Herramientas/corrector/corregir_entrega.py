# -*- coding: utf-8 -*-
"""
Corrige UNA entrega desde la linea de comandos.
PCI1119 Sistemas de Representacion.

Acepta lo que sea: una imagen suelta, un PDF, un .docx, o una carpeta con
varios archivos. Extrae las imagenes, decide cual es cada lamina, puntua cara
por cara y entrega el total sobre 212.

Ejemplos
--------
    python corregir_entrega.py "C:\\ruta\\entrega.pdf"
    python corregir_entrega.py "C:\\ruta\\carpeta_del_alumno"
    python corregir_entrega.py captura.png --lamina 3
    python corregir_entrega.py entrega.pdf --reportes
    python corregir_entrega.py entrega.pdf --csv notas.csv

Opciones
--------
    --lamina N    corrige la imagen contra la lamina N y no busca cual es
    --reportes    guarda los PNG de comparacion pauta / entrega
    --csv ARCH    agrega una linea al CSV (lo crea con encabezado si no existe)
    --detalle     lista todas las caras, no solo las erradas
"""

import argparse
import csv
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto
import nucleo_correccion as nc

IMAGENES = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff")

# Puertas para aceptar una asignacion automatica de lamina
MIN_CONFIANZA = 0.58
MIN_COBERTURA = 0.55
MIN_PUNTAJE = 25.0
CONFIANZA_SEGURA = 0.85


# ------------------------------------------------------------ extraccion

def _imagenes_de_pdf(ruta, destino):
    """Saca las imagenes embebidas y, si la pagina no trae ninguna util,
    rasteriza la pagina completa."""
    salidas = []
    try:
        from pypdf import PdfReader
        lector = PdfReader(ruta)
        for i, pagina in enumerate(lector.pages, start=1):
            encontradas = 0
            try:
                for j, img in enumerate(pagina.images):
                    d = os.path.join(destino, "p%02d_e%d.png" % (i, j))
                    try:
                        im = Image.open(__import__("io").BytesIO(img.data))
                    except Exception:
                        continue
                    if min(im.size) < 250:
                        continue
                    im.convert("RGB").save(d)
                    salidas.append(d)
                    encontradas += 1
            except Exception:
                pass
            if encontradas == 0:
                salidas.extend(_rasterizar(ruta, i, destino))
    except Exception as e:
        print("  aviso: no pude leer el PDF con pypdf (%s), rasterizo entero" % e)
        salidas.extend(_rasterizar(ruta, None, destino))
    return salidas


def _rasterizar(ruta, pagina, destino):
    """Convierte paginas del PDF a PNG con pdftoppm (poppler)."""
    exe = shutil.which("pdftoppm")
    if not exe:
        return []
    prefijo = os.path.join(destino, "rast_p%s" % (pagina or "all"))
    cmd = [exe, "-r", "200", "-png"]
    if pagina:
        cmd += ["-f", str(pagina), "-l", str(pagina)]
    cmd += [ruta, prefijo]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=120)
    except Exception:
        return []
    return sorted(glob.glob(prefijo + "*.png"))


def _imagenes_de_docx(ruta, destino):
    salidas = []
    try:
        with zipfile.ZipFile(ruta) as z:
            for n in z.namelist():
                if n.startswith("word/media/") and n.lower().endswith(IMAGENES):
                    d = os.path.join(destino, os.path.basename(n))
                    with open(d, "wb") as f:
                        f.write(z.read(n))
                    salidas.append(d)
    except Exception as e:
        print("  aviso: no pude abrir el .docx (%s)" % e)
    return salidas


def reunir_candidatas(entrada, temporal):
    """Devuelve la lista de imagenes a evaluar, sea lo que sea la entrada."""
    rutas = []
    if os.path.isdir(entrada):
        archivos = []
        for raiz, _, nombres in os.walk(entrada):
            # no reprocesar salidas propias
            if os.path.basename(raiz) in ("norm", "reportes"):
                continue
            for n in sorted(nombres):
                archivos.append(os.path.join(raiz, n))
    else:
        archivos = [entrada]

    for f in archivos:
        bajo = f.lower()
        if bajo.endswith(IMAGENES):
            rutas.append(f)
        elif bajo.endswith(".pdf"):
            sub = os.path.join(temporal, os.path.basename(f)[:20].replace(".", "_"))
            os.makedirs(sub, exist_ok=True)
            rutas.extend(_imagenes_de_pdf(f, sub))
        elif bajo.endswith(".docx"):
            sub = os.path.join(temporal, os.path.basename(f)[:20].replace(".", "_"))
            os.makedirs(sub, exist_ok=True)
            rutas.extend(_imagenes_de_docx(f, sub))
    return rutas


def prefiltrar(rutas):
    """Descarta lo que claramente no es una lamina: miniaturas, logos,
    paginas de puro texto."""
    utiles = []
    for f in rutas:
        try:
            im = Image.open(f)
            w, h = im.size
            if min(w, h) < 250:
                continue
            chica = np.asarray(im.convert("RGB").resize(
                (160, max(1, int(160 * h / w))), nc.BILINEAL))
            if nc._mascara_saturada(chica).mean() < 0.03:
                continue
            utiles.append(f)
        except Exception:
            continue
    return utiles


# ------------------------------------------------------------- correccion

def asignar(rutas, pautas, lamina_forzada=None, verboso=True):
    """Evalua cada candidata contra las 5 laminas y asigna globalmente.

    Un emparejamiento codicioso pierde laminas cuando dos imagenes compiten por
    la misma: la perdedora se descarta aunque fuera la unica candidata de otra
    lamina. Aqui se arma la matriz completa y se toman los mejores pares de a
    uno, retirando imagen y lamina del juego en cada paso."""
    laminas = [lamina_forzada] if lamina_forzada else sorted(pautas)

    # Pre-pasada barata cuando hay muchas candidatas
    if len(rutas) > 12 and not lamina_forzada:
        corta = []
        for f in rutas:
            try:
                r = nc.corregir(Image.open(f), pautas)
            except Exception:
                continue
            if r["cobertura_color"] >= 0.50 and r["puntaje"] >= MIN_PUNTAJE * 0.6:
                corta.append(f)
        if verboso:
            print("  pre-pasada: %d de %d candidatas siguen" % (len(corta), len(rutas)))
        rutas = corta

    matriz = {}
    for f in rutas:
        fila = {}
        for lam in laminas:
            try:
                r = nc.corregir(Image.open(f), pautas, lam)
            except Exception:
                continue
            fila[lam] = {
                "archivo": f, "lamina": lam,
                "caras_correctas": r["caras_correctas"],
                "caras_total": r["caras_total"], "puntaje": r["puntaje"],
                "confianza": r["confianza"], "cobertura": r["cobertura_color"],
                "calidad": r["calidad"], "errores": r["errores"],
                "detalle": r["detalle"], "imagen": r["imagen_alineada"],
                "recorte": r.get("recorte", ""),
            }
        if fila:
            matriz[f] = fila

    pares = []
    for f, fila in matriz.items():
        for lam, e in fila.items():
            if (e["confianza"] < MIN_CONFIANZA or e["cobertura"] < MIN_COBERTURA
                    or e["puntaje"] < MIN_PUNTAJE):
                continue
            pares.append((e["calidad"], f, lam, e))
    pares.sort(key=lambda t: -t[0])

    usados, elegidas = set(), {}
    for _, f, lam, e in pares:
        if f in usados or lam in elegidas:
            continue
        usados.add(f)
        elegidas[lam] = e
    return elegidas, matriz


def main():
    ap = argparse.ArgumentParser(
        description="Corrige una entrega de la Actividad 1 (reconocimiento de vistas con color)")
    ap.add_argument("entrada", help="archivo (imagen, PDF, docx) o carpeta")
    ap.add_argument("--lamina", type=int, choices=[1, 2, 3, 4, 5],
                    help="corregir contra esta lamina y no adivinar cual es")
    ap.add_argument("--reportes", action="store_true",
                    help="guardar los PNG de comparacion pauta / entrega")
    ap.add_argument("--csv", help="agregar el resultado a este CSV")
    ap.add_argument("--carpeta",
                    help="carpeta de la actividad; ver contexto.py")
    ap.add_argument("--detalle", action="store_true",
                    help="listar todas las caras, no solo las erradas")
    args = ap.parse_args()

    if not os.path.exists(args.entrada):
        print("No existe: %s" % args.entrada)
        return 2

    pautas = nc.cargar_pautas()
    if not pautas:
        print("No encontre las pautas en %s. Corre primero 02_pauta.py" % contexto.CARPETA_PAUTA)
        return 2
    universo = sum(len(p.caras) for p in pautas.values())

    etiqueta = os.path.basename(os.path.normpath(args.entrada))
    print("\n%s" % ("=" * 70))
    print("ENTREGA: %s" % etiqueta)
    print("=" * 70)

    temporal = tempfile.mkdtemp(prefix="corr_")
    try:
        rutas = prefiltrar(reunir_candidatas(args.entrada, temporal))
        print("  %d imagen(es) para evaluar" % len(rutas))
        if not rutas:
            print("\n  No encontre ninguna imagen utilizable.")
            print("  Revisa que la entrega tenga capturas de la actividad, no solo texto.")
            return 1

        elegidas, _ = asignar(rutas, pautas, args.lamina)

        print("\n  %-7s %-9s %-8s %-9s %s" % (
            "Lamina", "Caras", "Puntaje", "Confianza", "Archivo"))
        print("  " + "-" * 66)
        total_ok = 0
        for lam in sorted(elegidas):
            e = elegidas[lam]
            total_ok += e["caras_correctas"]
            marca = "" if e["confianza"] >= CONFIANZA_SEGURA else "  <- verificar"
            print("  %-7s %-9s %-8s %-9s %s%s" % (
                lam, "%d/%d" % (e["caras_correctas"], e["caras_total"]),
                "%.0f%%" % e["puntaje"], "%.0f%%" % (100 * e["confianza"]),
                os.path.basename(e["archivo"])[:28], marca))

        faltan = [l for l in sorted(pautas) if l not in elegidas]
        if args.lamina:
            universo = len(pautas[args.lamina].caras)
            faltan = []
        for lam in faltan:
            print("  %-7s %-9s %-8s %-9s %s" % (lam, "-", "0%", "-", "no encontrada"))

        puntaje = 100.0 * total_ok / universo if universo else 0.0
        print("  " + "-" * 66)
        print("  TOTAL   %d de %d caras correctas        NOTA BASE: %.1f / 100"
              % (total_ok, universo, puntaje))
        if len(faltan) == 5 and len(rutas) >= 3:
            print("\n  NINGUNA de las %d imagenes calza con las 5 laminas de esta actividad."
                  % len(rutas))
            print("  Lo mas probable es que la entrega sea de OTRO ejercicio. En el mismo sitio")
            print("  hay actividades parecidas con otro codigo de colores (rosa/verde/azul para")
            print("  vistas frontal-superior-perfil, o desarrollos de figuras en azul/violeta),")
            print("  y varios alumnos las confundieron. Abre el archivo y revisalo a ojo.")
            print("  Si igual quieres forzarlo:  --lamina 1")
        elif faltan:
            print("\n  Faltan las laminas %s. Puede ser que el alumno no las entregara,"
                  % faltan)
            print("  o que el recorte no se pudo resolver solo. Para forzar una:")
            print("     python corregir_entrega.py \"<archivo>\" --lamina %d" % faltan[0])

        # errores por lamina
        for lam in sorted(elegidas):
            e = elegidas[lam]
            filas = e["detalle"] if args.detalle else e["errores"]
            if not filas:
                print("\n  Lamina %d: sin errores." % lam)
                continue
            print("\n  Lamina %d, %d cara(s) %s:" % (
                lam, len(filas), "en detalle" if args.detalle else "erradas"))
            for d in sorted(filas, key=lambda x: x["id"]):
                estado = "ok  " if d["correcto"] else "MAL "
                print("    %s %-8s pieza %d   esperaba %-9s  pinto %-13s certeza %3.0f%%"
                      % (estado, d["id"], d["pieza"], d["esperado"],
                         d["detectado"], 100 * d["apoyo"]))

        if args.reportes:
            destino = os.path.join(contexto.raiz(), "salida", "reportes")
            os.makedirs(destino, exist_ok=True)
            base = "".join(c for c in etiqueta if c.isalnum() or c in "._-")[:40]
            for lam in sorted(elegidas):
                e = elegidas[lam]
                res = {"errores": e["errores"], "imagen_alineada": e["imagen"]}
                img = nc.render(res, pautas[lam])
                d = os.path.join(destino, "%s_L%d.png" % (base, lam))
                img.save(d)
            print("\n  Reportes visuales en: salida\\reportes\\%s_L*.png" % base)

        if args.csv:
            nuevo = not os.path.exists(args.csv)
            with open(args.csv, "a", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                if nuevo:
                    w.writerow(["entrega", "L1", "L2", "L3", "L4", "L5",
                                "caras_correctas", "caras_totales",
                                "puntaje_0_100", "laminas_faltantes",
                                "confianza_minima"])
                conf = min([e["confianza"] for e in elegidas.values()] or [0])
                w.writerow([etiqueta]
                           + [elegidas[l]["caras_correctas"] if l in elegidas else ""
                              for l in range(1, 6)]
                           + [total_ok, universo, round(puntaje, 1),
                              ";".join(str(x) for x in faltan), round(conf, 2)])
            print("  Agregado a %s" % args.csv)

        print("")
        return 0
    finally:
        shutil.rmtree(temporal, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
