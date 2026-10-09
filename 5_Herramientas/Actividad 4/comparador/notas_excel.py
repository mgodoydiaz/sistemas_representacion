#!/usr/bin/env python3
"""
notas_excel.py - Escritura del Excel de notas de la Actividad 4
(salida/Notas_Actividad4.xlsx), UNA FILA POR ALUMNO.

Columnas (en este orden): usuario, vistas_c1..vistas_c6, isometricos_c1..
isometricos_c6, promedio_vistas, promedio_isometricos, nota_sugerida,
nota_final, observaciones.

Reglas:
  - nota_sugerida SIEMPRE se recalcula a partir de los porcentajes que
    entrega comparador/similitud.py: es un dato derivado, nunca algo que
    esta funcion decida pisar a mano.
  - nota_final es la que decide el profesor. Este modulo no la calcula ni
    la corrige: escribe el valor que venga en el payload de cada llamada
    (el que el profesor tenga en pantalla al apretar "Registrar en Excel",
    que puede ser igual a la sugerida o distinto). El porcentaje sugiere,
    el profesor decide.
  - Escritura idempotente: si el usuario ya tiene una fila (columna
    "usuario"), se actualiza esa fila en el lugar; si no, se agrega una
    fila nueva. Nunca se duplica un alumno.
  - Escritura atomica: se escribe a un archivo temporal en la misma
    carpeta y se reemplaza el definitivo con os.replace(), para no dejar
    un .xlsx a medio escribir si algo falla a mitad de camino.

Si openpyxl no esta instalado en el equipo (por ejemplo el del profesor),
se cae a un CSV equivalente (mismo nombre, extension .csv) y se avisa en
el resultado en vez de reventar.
"""
import csv
import os
import tempfile

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    _OPENPYXL = True
except ImportError:
    _OPENPYXL = False


COLUMNAS_VISTAS = [f"vistas_c{n}" for n in range(1, 7)]
COLUMNAS_ISOMETRICOS = [f"isometricos_c{n}" for n in range(1, 7)]
ENCABEZADOS = (
    ["usuario"]
    + COLUMNAS_VISTAS
    + COLUMNAS_ISOMETRICOS
    + ["puntaje_vistas", "puntaje_isometricos", "puntaje_total", "nota_final", "observaciones"]
)

HOJA_TITULO = "Notas"


def _promedio(valores):
    presentes = [v for v in valores if v is not None]
    if not presentes:
        return None
    return sum(presentes) / len(presentes)

def _suma(valores):
    presentes = [v for v in valores if v is not None]
    if not presentes:
        return None
    return sum(presentes)

def calcular_fila(usuario, vistas, isometricos, nota_final=None, observaciones=""):
    """Arma la fila completa (lista de valores, en el orden de ENCABEZADOS)
    a partir de los puntajes.

    vistas: 0 a 3 puntos por celda.
    isometricos: 0 a 100 porcentaje por celda.
    """
    vistas = (list(vistas) + [None] * 6)[:6]
    isometricos = (list(isometricos) + [None] * 6)[:6]
    
    puntaje_v = _suma(vistas)
    prom_iso = _promedio(isometricos)
    
    puntaje_i = round(prom_iso * 0.06, 2) if prom_iso is not None else None
    
    disponibles = [p for p in (puntaje_v, puntaje_i) if p is not None]
    puntaje_total = round(sum(disponibles), 2) if disponibles else None
    
    return [usuario] + vistas + isometricos + [puntaje_v, puntaje_i, puntaje_total, nota_final, observaciones or ""]

def fila_a_dict(fila):
    return dict(zip(ENCABEZADOS, fila))


# =============================================================================
# Motor openpyxl (.xlsx)
# =============================================================================

def _abrir_o_crear_libro(ruta):
    if os.path.isfile(ruta):
        wb = openpyxl.load_workbook(ruta)
        ws = wb[HOJA_TITULO] if HOJA_TITULO in wb.sheetnames else wb.active
        return wb, ws
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = HOJA_TITULO
    ws.append(ENCABEZADOS)
    for c in range(1, len(ENCABEZADOS) + 1):
        celda = ws.cell(row=1, column=c)
        celda.font = Font(bold=True)
        celda.alignment = Alignment(horizontal="center", wrap_text=True)
        celda.fill = PatternFill("solid", fgColor="DCE8F2")
    ws.freeze_panes = "B2"
    anchos = [18] + [10] * 12 + [13, 15, 13, 11, 32]
    for i, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho
    return wb, ws


def _buscar_fila_usuario(ws, usuario):
    for r in range(2, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == usuario:
            return r
    return None


def _registrar_xlsx(ruta, fila):
    wb, ws = _abrir_o_crear_libro(ruta)
    usuario = fila[0]
    destino = _buscar_fila_usuario(ws, usuario)
    actualizado = destino is not None
    if destino is None:
        destino = ws.max_row + 1

    col_porcentaje = list(range(2, 2 + 12))  # vistas_c1..c6, isometricos_c1..c6
    col_promedios = [15, 16, 17]  # promedio_vistas, promedio_isometricos, nota_sugerida
    col_nota_final = 18
    col_obs = 19

    for c, valor in enumerate(fila, start=1):
        celda = ws.cell(row=destino, column=c, value=valor)
        if c in col_porcentaje or c in col_promedios:
            celda.number_format = "0.0"
        if c == col_nota_final and valor is not None:
            celda.font = Font(bold=True)
            celda.fill = PatternFill("solid", fgColor="FFF3CD")
        if c == col_obs:
            celda.alignment = Alignment(wrap_text=True, vertical="top")

    _guardar_atomico_xlsx(wb, ruta)
    return {"fila": destino, "actualizado": actualizado}


def _guardar_atomico_xlsx(wb, ruta_final):
    directorio = os.path.dirname(os.path.abspath(ruta_final)) or "."
    os.makedirs(directorio, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".notas_", suffix=".xlsx.tmp", dir=directorio)
    os.close(fd)
    try:
        wb.save(tmp)
        os.replace(tmp, ruta_final)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


# =============================================================================
# Motor CSV (respaldo si no hay openpyxl)
# =============================================================================

def _leer_csv_filas(ruta):
    if not os.path.isfile(ruta):
        return []
    with open(ruta, "r", encoding="utf-8-sig", newline="") as fh:
        lector = csv.reader(fh)
        filas = list(lector)
    if not filas:
        return []
    return filas[1:]  # sin encabezado


def _valor_o_vacio(v):
    return "" if v is None else v


def _registrar_csv(ruta, fila):
    filas = _leer_csv_filas(ruta)
    usuario = fila[0]
    actualizado = False
    for i, f in enumerate(filas):
        if f and f[0] == usuario:
            filas[i] = [_valor_o_vacio(v) for v in fila]
            actualizado = True
            break
    if not actualizado:
        filas.append([_valor_o_vacio(v) for v in fila])

    directorio = os.path.dirname(os.path.abspath(ruta)) or "."
    os.makedirs(directorio, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".notas_", suffix=".csv.tmp", dir=directorio)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            escritor = csv.writer(fh)
            escritor.writerow(ENCABEZADOS)
            escritor.writerows(filas)
        os.replace(tmp, ruta)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return {"actualizado": actualizado}


# =============================================================================
# API publica
# =============================================================================

def registrar(ruta_xlsx, usuario, vistas, isometricos, nota_final=None, observaciones=""):
    """Registra (o actualiza) la fila de `usuario` en el Excel de notas.

    Devuelve un dict {ok, archivo, motor, actualizado, fila, aviso}.
    `archivo` es la ruta realmente escrita (puede ser el .csv de respaldo
    si openpyxl no esta disponible: revisar `motor` y `aviso`).
    """
    fila = calcular_fila(usuario, vistas, isometricos, nota_final, observaciones)
    if _OPENPYXL:
        info = _registrar_xlsx(ruta_xlsx, fila)
        return {
            "ok": True,
            "archivo": ruta_xlsx,
            "motor": "openpyxl",
            "actualizado": info["actualizado"],
            "fila": fila_a_dict(fila),
            "aviso": None,
        }
    ruta_csv = os.path.splitext(ruta_xlsx)[0] + ".csv"
    info = _registrar_csv(ruta_csv, fila)
    return {
        "ok": True,
        "archivo": ruta_csv,
        "motor": "csv",
        "actualizado": info["actualizado"],
        "fila": fila_a_dict(fila),
        "aviso": (
            "openpyxl no esta instalado en este equipo: la fila se registro en un "
            f"CSV equivalente ({os.path.basename(ruta_csv)}) en vez de un .xlsx."
        ),
    }


def leer_todas(ruta_xlsx):
    """Lee de vuelta todas las filas ya registradas (usa el .xlsx si existe,
    si no el .csv de respaldo). Devuelve una lista de dicts. Pensado para
    verificacion/depuracion, no lo usa el servidor en produccion."""
    if _OPENPYXL and os.path.isfile(ruta_xlsx):
        wb = openpyxl.load_workbook(ruta_xlsx, data_only=True)
        ws = wb[HOJA_TITULO] if HOJA_TITULO in wb.sheetnames else wb.active
        filas = []
        for r in range(2, ws.max_row + 1):
            valores = [ws.cell(row=r, column=c).value for c in range(1, len(ENCABEZADOS) + 1)]
            if valores[0] is None:
                continue
            filas.append(fila_a_dict(valores))
        return filas
    ruta_csv = os.path.splitext(ruta_xlsx)[0] + ".csv"
    return [fila_a_dict(f) for f in _leer_csv_filas(ruta_csv)]
